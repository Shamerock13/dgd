from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .database import get_db
from .models import Fragrance
from .price_discovery import active_retailers, discover_products, verify_candidate
from .price_models import FragranceOffer, PriceObservation, Retailer
from .price_scanner import _host_matches

router = APIRouter(prefix="/api/prices/discovery", tags=["prices"])


class DiscoverySearchIn(BaseModel):
    fragrance_id: UUID
    retailer_ids: list[UUID] | None = None


class DiscoveryAcceptIn(BaseModel):
    fragrance_id: UUID
    retailer_id: UUID
    product_url: str = Field(min_length=8, max_length=3000)
    size_ml: float | None = Field(default=None, gt=0, le=5000)
    product_type: str = Field(default="bottle", max_length=30)
    shipping_eur: float = Field(default=0, ge=0, le=10000)


@router.post("/search")
async def search_price_products(payload: DiscoverySearchIn, db: Session = Depends(get_db)):
    fragrance = db.scalar(
        select(Fragrance)
        .where(Fragrance.id == payload.fragrance_id)
        .options(joinedload(Fragrance.brand))
    )
    if not fragrance:
        raise HTTPException(404, "Duft nicht gefunden.")
    retailers = active_retailers(db, payload.retailer_ids)
    results = []
    for retailer in retailers:
        results.append(await discover_products(fragrance, retailer))
    return {
        "fragrance_id": str(fragrance.id),
        "fragrance": f"{fragrance.brand.name} – {fragrance.name}",
        "retailers_checked": len(retailers),
        "candidates": sum(len(row["candidates"]) for row in results),
        "results": results,
    }


@router.post("/accept", status_code=201)
async def accept_price_candidate(payload: DiscoveryAcceptIn, db: Session = Depends(get_db)):
    fragrance = db.get(Fragrance, payload.fragrance_id)
    retailer = db.get(Retailer, payload.retailer_id)
    if not fragrance:
        raise HTTPException(404, "Duft nicht gefunden.")
    if not retailer or not retailer.active:
        raise HTTPException(404, "Aktiver Händler nicht gefunden.")

    from urllib.parse import urlparse
    product_host = urlparse(payload.product_url).hostname or ""
    retailer_host = urlparse(retailer.base_url or "").hostname or ""
    if not retailer_host or not _host_matches(product_host, retailer_host):
        raise HTTPException(422, "Die Produkt-URL gehört nicht zum ausgewählten Händler.")

    try:
        verified = await verify_candidate(payload.product_url)
    except Exception as exc:
        raise HTTPException(422, f"Produktseite konnte nicht bestätigt werden: {exc}")

    existing = db.scalar(
        select(FragranceOffer).where(
            FragranceOffer.retailer_id == retailer.id,
            FragranceOffer.product_url == verified["product_url"],
        )
    )
    if existing and existing.fragrance_id != fragrance.id:
        raise HTTPException(409, "Diese Produktseite ist bereits einem anderen Duft zugeordnet.")

    checked_at = datetime.utcnow()
    offer = existing or FragranceOffer(
        fragrance_id=fragrance.id,
        retailer_id=retailer.id,
        product_url=verified["product_url"],
    )
    if not existing:
        db.add(offer)
    offer.product_name = verified.get("product_name")
    offer.size_ml = payload.size_ml
    offer.product_type = payload.product_type
    offer.price_eur = verified["price_eur"]
    offer.shipping_eur = payload.shipping_eur
    offer.in_stock = verified["in_stock"]
    offer.checked_at = checked_at
    db.flush()
    db.add(PriceObservation(
        offer_id=offer.id,
        price_eur=offer.price_eur,
        shipping_eur=offer.shipping_eur,
        in_stock=offer.in_stock,
        observed_at=checked_at,
    ))
    db.commit()
    return {
        "offer_id": str(offer.id),
        "retailer": retailer.name,
        "product_name": offer.product_name,
        "product_url": offer.product_url,
        "price_eur": round(offer.price_eur, 2),
        "shipping_eur": round(offer.shipping_eur, 2),
        "total_eur": round(offer.price_eur + offer.shipping_eur, 2),
        "in_stock": offer.in_stock,
    }
