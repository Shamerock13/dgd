from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal
from urllib.parse import urlparse
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from .database import get_db
from .models import Fragrance
from .price_models import FragranceOffer, PriceObservation, Retailer

router = APIRouter(prefix="/api/prices", tags=["prices"])


class RetailerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    base_url: str | None = Field(default=None, max_length=2000)
    active: bool = True


class OfferCheckIn(BaseModel):
    fragrance_id: UUID
    retailer_id: UUID
    product_url: str = Field(min_length=8, max_length=3000)
    product_name: str | None = Field(default=None, max_length=500)
    size_ml: float | None = Field(default=None, gt=0, le=5000)
    product_type: Literal["bottle", "tester", "set", "sample", "refill"] = "bottle"
    price_eur: float = Field(gt=0, le=100000)
    shipping_eur: float = Field(default=0, ge=0, le=10000)
    in_stock: bool = True
    checked_at: datetime | None = None


def _valid_web_url(value: str | None) -> bool:
    if not value:
        return True
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _retailer_out(row: Retailer) -> dict:
    return {
        "id": str(row.id),
        "name": row.name,
        "base_url": row.base_url,
        "active": row.active,
        "created_at": row.created_at,
    }


def _offer_out(row: FragranceOffer) -> dict:
    total = round(row.price_eur + row.shipping_eur, 2)
    return {
        "id": str(row.id),
        "fragrance_id": str(row.fragrance_id),
        "retailer": _retailer_out(row.retailer),
        "product_url": row.product_url,
        "product_name": row.product_name,
        "size_ml": row.size_ml,
        "product_type": row.product_type,
        "price_eur": round(row.price_eur, 2),
        "shipping_eur": round(row.shipping_eur, 2),
        "total_eur": total,
        "price_per_100ml_eur": round(total / row.size_ml * 100, 2) if row.size_ml else None,
        "in_stock": row.in_stock,
        "checked_at": row.checked_at,
    }


@router.get("/retailers")
def list_retailers(active_only: bool = False, db: Session = Depends(get_db)):
    stmt = select(Retailer)
    if active_only:
        stmt = stmt.where(Retailer.active.is_(True))
    return [_retailer_out(row) for row in db.scalars(stmt.order_by(Retailer.name))]


@router.post("/retailers", status_code=201)
def create_retailer(payload: RetailerCreate, db: Session = Depends(get_db)):
    name = " ".join(payload.name.split())
    if payload.base_url and not _valid_web_url(payload.base_url):
        raise HTTPException(422, "Die Händler-URL muss eine gültige HTTP- oder HTTPS-Adresse sein.")
    row = Retailer(name=name, base_url=payload.base_url, active=payload.active)
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Dieser Händler ist bereits vorhanden.")
    db.refresh(row)
    return _retailer_out(row)


@router.post("/offers/check", status_code=201)
def record_offer_check(payload: OfferCheckIn, db: Session = Depends(get_db)):
    if not _valid_web_url(payload.product_url):
        raise HTTPException(422, "Die Produkt-URL muss eine gültige HTTP- oder HTTPS-Adresse sein.")
    if not db.get(Fragrance, payload.fragrance_id):
        raise HTTPException(404, "Duft nicht gefunden.")
    retailer = db.get(Retailer, payload.retailer_id)
    if not retailer:
        raise HTTPException(404, "Händler nicht gefunden.")
    if not retailer.active:
        raise HTTPException(409, "Für einen deaktivierten Händler können keine neuen Preisprüfungen gespeichert werden.")

    checked_at = payload.checked_at or datetime.utcnow()
    offer = db.scalar(
        select(FragranceOffer)
        .where(
            FragranceOffer.retailer_id == payload.retailer_id,
            FragranceOffer.product_url == payload.product_url,
        )
        .options(joinedload(FragranceOffer.retailer))
    )
    created = offer is None
    if offer is None:
        offer = FragranceOffer(
            fragrance_id=payload.fragrance_id,
            retailer_id=payload.retailer_id,
            product_url=payload.product_url,
        )
        db.add(offer)
    elif offer.fragrance_id != payload.fragrance_id:
        raise HTTPException(409, "Diese Händler-URL ist bereits einem anderen Duft zugeordnet.")

    offer.product_name = payload.product_name
    offer.size_ml = payload.size_ml
    offer.product_type = payload.product_type
    offer.price_eur = payload.price_eur
    offer.shipping_eur = payload.shipping_eur
    offer.in_stock = payload.in_stock
    offer.checked_at = checked_at
    db.flush()

    db.add(PriceObservation(
        offer_id=offer.id,
        price_eur=payload.price_eur,
        shipping_eur=payload.shipping_eur,
        in_stock=payload.in_stock,
        observed_at=checked_at,
    ))
    db.commit()
    return {"created": created, "offer": _offer_out(offer)}


@router.get("/fragrances/{fragrance_id}")
def fragrance_prices(
    fragrance_id: UUID,
    days: int = Query(default=90, ge=1, le=1095),
    db: Session = Depends(get_db),
):
    fragrance = db.get(Fragrance, fragrance_id)
    if not fragrance:
        raise HTTPException(404, "Duft nicht gefunden.")

    offers = list(db.scalars(
        select(FragranceOffer)
        .where(FragranceOffer.fragrance_id == fragrance_id)
        .options(joinedload(FragranceOffer.retailer))
        .order_by(FragranceOffer.checked_at.desc())
    ).unique())
    offer_rows = [_offer_out(row) for row in offers]
    available = [row for row in offer_rows if row["in_stock"]]
    available.sort(key=lambda row: (row["total_eur"], row["price_per_100ml_eur"] or float("inf")))

    cutoff = datetime.utcnow() - timedelta(days=days)
    history = list(db.execute(
        select(
            PriceObservation.observed_at,
            PriceObservation.price_eur,
            PriceObservation.shipping_eur,
            PriceObservation.in_stock,
            FragranceOffer.id,
            Retailer.name,
            FragranceOffer.size_ml,
        )
        .join(FragranceOffer, FragranceOffer.id == PriceObservation.offer_id)
        .join(Retailer, Retailer.id == FragranceOffer.retailer_id)
        .where(
            FragranceOffer.fragrance_id == fragrance_id,
            PriceObservation.observed_at >= cutoff,
        )
        .order_by(PriceObservation.observed_at)
    ))
    history_rows = [{
        "observed_at": row.observed_at,
        "offer_id": str(row.id),
        "retailer": row.name,
        "size_ml": row.size_ml,
        "price_eur": round(row.price_eur, 2),
        "shipping_eur": round(row.shipping_eur, 2),
        "total_eur": round(row.price_eur + row.shipping_eur, 2),
        "in_stock": row.in_stock,
    } for row in history]

    historic_low = db.scalar(
        select(func.min(PriceObservation.price_eur + PriceObservation.shipping_eur))
        .join(FragranceOffer, FragranceOffer.id == PriceObservation.offer_id)
        .where(
            FragranceOffer.fragrance_id == fragrance_id,
            PriceObservation.in_stock.is_(True),
        )
    )

    return {
        "fragrance_id": str(fragrance_id),
        "currency": "EUR",
        "checked_offers": len(offer_rows),
        "available_offers": len(available),
        "cheapest": available[0] if available else None,
        "historic_low_total_eur": round(historic_low, 2) if historic_low is not None else None,
        "offers": available + [row for row in offer_rows if not row["in_stock"]],
        "history_days": days,
        "history": history_rows,
    }
