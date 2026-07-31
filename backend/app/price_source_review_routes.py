from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Literal
from urllib.parse import urlparse
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from .database import get_db
from .models import Fragrance
from .price_models import FragranceOffer
from .price_resilient_scanner import refresh_offer
from .price_scanner import SUPPORTED_RETAILER_HOSTS
from .price_source_review_models import PriceSourceReviewEvent

router = APIRouter(prefix="/api/prices/review", tags=["price-source-review"])


class ReviewDecision(BaseModel):
    action: Literal["approve", "reject"]
    activate_retailer: bool = False
    note: str | None = Field(default=None, max_length=2000)


class ScannerDecision(BaseModel):
    enabled: bool
    activate_retailer: bool = False
    note: str | None = Field(default=None, max_length=2000)


def _host(value: str | None) -> str:
    return (urlparse(value or "").hostname or "").casefold().removeprefix("www.")


def _validate_source(offer: FragranceOffer) -> None:
    parsed = urlparse(offer.product_url or "")
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(409, "Die Preisquelle besitzt keine gültige Produkt-URL.")
    retailer_host = _host(offer.retailer.base_url if offer.retailer else None)
    product_host = _host(offer.product_url)
    if not retailer_host:
        raise HTTPException(409, "Beim Händler fehlt eine gültige Basis-URL.")
    if product_host != retailer_host and not product_host.endswith(f".{retailer_host}"):
        raise HTTPException(409, "Die Produkt-URL gehört nicht zur hinterlegten Händler-Domain.")


def _validate_scanner_adapter(offer: FragranceOffer) -> None:
    retailer_host = _host(offer.retailer.base_url if offer.retailer else None)
    if retailer_host not in SUPPORTED_RETAILER_HOSTS:
        raise HTTPException(
            409,
            "Für diesen Händler ist noch kein automatischer Preisadapter freigegeben.",
        )


def _event_out(event: PriceSourceReviewEvent) -> dict:
    return {
        "id": str(event.id),
        "action": event.action,
        "previous_status": event.previous_status,
        "new_status": event.new_status,
        "scanner_active": bool(event.scanner_active),
        "retailer_activated": bool(event.retailer_activated),
        "note": event.note,
        "created_at": event.created_at,
    }


def _offer_out(
    offer: FragranceOffer,
    fragrance: Fragrance | None,
    events: list[PriceSourceReviewEvent] | None = None,
) -> dict:
    retailer = offer.retailer
    return {
        "id": str(offer.id),
        "offer_source_id": offer.offer_source_id,
        "review_status": offer.review_status,
        "scanner_active": bool(offer.scanner_active),
        "trust_status": offer.trust_status,
        "fragrance": {
            "id": str(offer.fragrance_id),
            "name": fragrance.name if fragrance else "Unbekannter Duft",
            "brand_name": fragrance.brand.name if fragrance and fragrance.brand else "",
        },
        "retailer": {
            "id": str(retailer.id) if retailer else None,
            "name": retailer.name if retailer else "Unbekannter Händler",
            "base_url": retailer.base_url if retailer else None,
            "active": bool(retailer.active) if retailer else False,
            "scanner_supported": _host(retailer.base_url if retailer else None) in SUPPORTED_RETAILER_HOSTS,
        },
        "product_url": offer.product_url,
        "product_name": offer.product_name,
        "product_variant": offer.product_variant,
        "size_ml": offer.size_ml,
        "concentration": offer.concentration,
        "product_type": offer.product_type,
        "price_eur": round(float(offer.price_eur or 0), 2),
        "shipping_eur": round(float(offer.shipping_eur or 0), 2),
        "total_eur": round(float(offer.price_eur or 0) + float(offer.shipping_eur or 0), 2),
        "currency": offer.currency,
        "availability": offer.availability,
        "ean_gtin": offer.ean_gtin,
        "merchant_sku": offer.merchant_sku,
        "market_country": offer.market_country,
        "scan_interval": offer.scan_interval,
        "extraction_hint": offer.extraction_hint,
        "variant_warning": offer.variant_warning,
        "checked_at": offer.checked_at,
        "created_at": offer.created_at,
        "updated_at": offer.updated_at,
        "events": [_event_out(item) for item in (events or [])],
    }


def _load_offer(db: Session, offer_id: UUID) -> FragranceOffer:
    offer = db.scalar(
        select(FragranceOffer)
        .where(FragranceOffer.id == offer_id)
        .options(joinedload(FragranceOffer.retailer))
    )
    if not offer:
        raise HTTPException(404, "Preisquelle nicht gefunden.")
    return offer


@router.get("/offers")
def list_review_offers(
    status: str = Query(default="ALL", max_length=30),
    limit: int = Query(default=250, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    normalized = status.strip().upper()
    allowed = {"PENDING_REVIEW", "APPROVED", "REJECTED"}
    if normalized != "ALL" and normalized not in allowed:
        raise HTTPException(422, "Unbekannter Prüfstatus.")

    stmt = (
        select(FragranceOffer)
        .options(joinedload(FragranceOffer.retailer))
        .order_by(FragranceOffer.updated_at.desc(), FragranceOffer.created_at.desc())
        .limit(limit)
    )
    if normalized != "ALL":
        stmt = stmt.where(FragranceOffer.review_status == normalized)
    offers = list(db.scalars(stmt).unique())

    fragrance_ids = {item.fragrance_id for item in offers}
    fragrances: dict[UUID, Fragrance] = {}
    if fragrance_ids:
        fragrances = {
            item.id: item
            for item in db.scalars(
                select(Fragrance)
                .where(Fragrance.id.in_(fragrance_ids))
                .options(joinedload(Fragrance.brand))
            ).unique()
        }

    events_by_offer: dict[UUID, list[PriceSourceReviewEvent]] = defaultdict(list)
    offer_ids = {item.id for item in offers}
    if offer_ids:
        events = list(db.scalars(
            select(PriceSourceReviewEvent)
            .where(PriceSourceReviewEvent.offer_id.in_(offer_ids))
            .order_by(PriceSourceReviewEvent.created_at.desc())
        ))
        for event in events:
            if len(events_by_offer[event.offer_id]) < 12:
                events_by_offer[event.offer_id].append(event)

    counts = dict(db.execute(
        select(FragranceOffer.review_status, func.count(FragranceOffer.id))
        .group_by(FragranceOffer.review_status)
    ).all())
    return {
        "summary": {
            "pending": int(counts.get("PENDING_REVIEW", 0)),
            "approved": int(counts.get("APPROVED", 0)),
            "rejected": int(counts.get("REJECTED", 0)),
            "scanner_active": int(db.scalar(
                select(func.count(FragranceOffer.id)).where(FragranceOffer.scanner_active.is_(True))
            ) or 0),
        },
        "offers": [
            _offer_out(
                item,
                fragrances.get(item.fragrance_id),
                events_by_offer.get(item.id),
            )
            for item in offers
        ],
    }


@router.post("/offers/{offer_id}/decision")
def review_offer(
    offer_id: UUID,
    payload: ReviewDecision,
    db: Session = Depends(get_db),
):
    offer = _load_offer(db, offer_id)
    previous = offer.review_status
    retailer_activated = False

    if payload.action == "approve":
        _validate_source(offer)
        if not offer.offer_source_id:
            raise HTTPException(409, "Die Preisquelle besitzt keine stabile offer_source_id.")
        offer.review_status = "APPROVED"
        offer.scanner_active = False
        if payload.activate_retailer and offer.retailer and not offer.retailer.active:
            offer.retailer.active = True
            retailer_activated = True
        action = "APPROVED"
    else:
        offer.review_status = "REJECTED"
        offer.scanner_active = False
        action = "REJECTED"

    offer.updated_at = datetime.utcnow()
    db.add(PriceSourceReviewEvent(
        id=uuid4(),
        offer_id=offer.id,
        action=action,
        previous_status=previous,
        new_status=offer.review_status,
        scanner_active=False,
        retailer_activated=retailer_activated,
        note=(payload.note or "").strip() or None,
    ))
    db.commit()
    return {
        "status": offer.review_status,
        "scanner_active": offer.scanner_active,
        "retailer_active": bool(offer.retailer.active) if offer.retailer else False,
    }


@router.post("/offers/{offer_id}/scanner")
def set_offer_scanner(
    offer_id: UUID,
    payload: ScannerDecision,
    db: Session = Depends(get_db),
):
    offer = _load_offer(db, offer_id)
    retailer_activated = False

    if payload.enabled:
        if offer.review_status != "APPROVED":
            raise HTTPException(409, "Nur freigegebene Preisquellen dürfen den Scanner verwenden.")
        _validate_source(offer)
        _validate_scanner_adapter(offer)
        if not offer.offer_source_id:
            raise HTTPException(409, "Die Preisquelle besitzt keine stabile offer_source_id.")
        if not offer.retailer:
            raise HTTPException(409, "Der Preisquelle ist kein Händler zugeordnet.")
        if not offer.retailer.active:
            if not payload.activate_retailer:
                raise HTTPException(409, "Der Händler ist deaktiviert und muss zuerst bewusst aktiviert werden.")
            offer.retailer.active = True
            retailer_activated = True
        offer.scanner_active = True
        action = "SCANNER_ENABLED"
    else:
        offer.scanner_active = False
        action = "SCANNER_DISABLED"

    offer.updated_at = datetime.utcnow()
    db.add(PriceSourceReviewEvent(
        id=uuid4(),
        offer_id=offer.id,
        action=action,
        previous_status=offer.review_status,
        new_status=offer.review_status,
        scanner_active=offer.scanner_active,
        retailer_activated=retailer_activated,
        note=(payload.note or "").strip() or None,
    ))
    db.commit()
    return {
        "status": offer.review_status,
        "scanner_active": bool(offer.scanner_active),
        "retailer_active": bool(offer.retailer.active) if offer.retailer else False,
    }


@router.post("/offers/{offer_id}/test")
async def test_offer_adapter(
    offer_id: UUID,
    db: Session = Depends(get_db),
):
    offer = _load_offer(db, offer_id)
    if offer.review_status != "APPROVED":
        raise HTTPException(409, "Nur freigegebene Preisquellen dürfen getestet werden.")
    if not offer.retailer or not offer.retailer.active:
        raise HTTPException(409, "Der Händler muss für einen Einzeltest aktiv sein.")
    _validate_source(offer)
    _validate_scanner_adapter(offer)
    if not offer.offer_source_id:
        raise HTTPException(409, "Die Preisquelle besitzt keine stabile offer_source_id.")

    try:
        result = await refresh_offer(offer, db)
    except Exception as exc:
        db.rollback()
        message = f"{type(exc).__name__}: {exc}"[:600]
        db.add(PriceSourceReviewEvent(
            id=uuid4(),
            offer_id=offer.id,
            action="TEST_FAILED",
            previous_status=offer.review_status,
            new_status=offer.review_status,
            scanner_active=bool(offer.scanner_active),
            retailer_activated=False,
            note=message,
        ))
        db.commit()
        raise HTTPException(502, f"Preisprüfung fehlgeschlagen: {message}") from exc

    renderer = result.get("renderer", "http")
    db.add(PriceSourceReviewEvent(
        id=uuid4(),
        offer_id=offer.id,
        action="TEST_SUCCESS",
        previous_status=offer.review_status,
        new_status=offer.review_status,
        scanner_active=bool(offer.scanner_active),
        retailer_activated=False,
        note=(
            f"{float(result['price_eur']):.2f} EUR · "
            f"{'lieferbar' if result['in_stock'] else 'nicht lieferbar'} · {renderer}"
        ),
    ))
    db.commit()
    return result
