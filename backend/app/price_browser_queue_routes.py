from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .database import get_db
from .models import Fragrance
from .price_models import FragranceOffer, Retailer
from .price_scan_capability import BROWSER_REQUIRED_TRUST_STATUS
from .price_source_review_models import PriceSourceReviewEvent

router = APIRouter(
    prefix="/api/prices/browser-connector",
    tags=["price-browser-connector"],
)

_DEFAULT_INTERVAL_HOURS = 24


def _normalized_interval(value: str | None) -> str:
    return " ".join((value or "").casefold().replace("_", " ").replace("-", " ").split())


def _interval_hours(value: str | None) -> int:
    normalized = _normalized_interval(value)
    aliases = {
        "hourly": 1,
        "hour": 1,
        "stündlich": 1,
        "1h": 1,
        "daily": 24,
        "day": 24,
        "täglich": 24,
        "24h": 24,
        "weekly": 24 * 7,
        "week": 24 * 7,
        "wöchentlich": 24 * 7,
        "7d": 24 * 7,
        "monthly": 24 * 30,
        "month": 24 * 30,
        "monatlich": 24 * 30,
        "30d": 24 * 30,
    }
    if normalized in aliases:
        return aliases[normalized]

    compact = normalized.replace(" ", "")
    if compact.endswith("h") and compact[:-1].isdigit():
        return max(1, min(int(compact[:-1]), 24 * 365))
    if compact.endswith("d") and compact[:-1].isdigit():
        return max(1, min(int(compact[:-1]) * 24, 24 * 365))
    return _DEFAULT_INTERVAL_HOURS


def _manual_status(
    manual_checked_at: datetime | None,
    interval_hours: int,
    now: datetime,
) -> tuple[str, bool, datetime | None]:
    if manual_checked_at is None:
        return "NEVER_CHECKED", True, None
    next_due_at = manual_checked_at + timedelta(hours=interval_hours)
    if next_due_at <= now:
        return "DUE", True, next_due_at
    return "CURRENT", False, next_due_at


def _event_map(
    db: Session,
    offer_ids: set[UUID],
) -> dict[UUID, datetime]:
    if not offer_ids:
        return {}
    events = list(db.scalars(
        select(PriceSourceReviewEvent)
        .where(
            PriceSourceReviewEvent.offer_id.in_(offer_ids),
            PriceSourceReviewEvent.action == "BROWSER_IMPORT_SUCCESS",
        )
        .order_by(PriceSourceReviewEvent.created_at.desc())
    ))
    latest: dict[UUID, datetime] = {}
    for event in events:
        latest.setdefault(event.offer_id, event.created_at)
    return latest


def _fragrance_map(
    db: Session,
    fragrance_ids: set[UUID],
) -> dict[UUID, Fragrance]:
    if not fragrance_ids:
        return {}
    return {
        row.id: row
        for row in db.scalars(
            select(Fragrance)
            .where(Fragrance.id.in_(fragrance_ids))
            .options(joinedload(Fragrance.brand))
        ).unique()
    }


@router.get("/queue")
def browser_price_queue(
    due_only: bool = Query(default=True),
    limit: int = Query(default=250, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    offers = list(db.scalars(
        select(FragranceOffer)
        .join(Retailer, Retailer.id == FragranceOffer.retailer_id)
        .where(
            FragranceOffer.review_status == "APPROVED",
            FragranceOffer.trust_status == BROWSER_REQUIRED_TRUST_STATUS,
            FragranceOffer.scanner_active.is_(False),
            Retailer.active.is_(True),
        )
        .options(joinedload(FragranceOffer.retailer))
        .order_by(FragranceOffer.created_at)
        .limit(1000)
    ).unique())

    offer_ids = {row.id for row in offers}
    manual_checks = _event_map(db, offer_ids)
    fragrances = _fragrance_map(db, {row.fragrance_id for row in offers})
    now = datetime.utcnow()

    items: list[dict] = []
    status_counts = {"NEVER_CHECKED": 0, "DUE": 0, "CURRENT": 0}
    for offer in offers:
        manual_checked_at = manual_checks.get(offer.id)
        interval_hours = _interval_hours(offer.scan_interval)
        status, due, next_due_at = _manual_status(manual_checked_at, interval_hours, now)
        status_counts[status] += 1
        fragrance = fragrances.get(offer.fragrance_id)
        items.append({
            "offer_id": str(offer.id),
            "offer_source_id": offer.offer_source_id,
            "fragrance_id": str(offer.fragrance_id),
            "fragrance_name": fragrance.name if fragrance else "Unbekannter Duft",
            "brand_name": fragrance.brand.name if fragrance and fragrance.brand else "",
            "retailer_name": offer.retailer.name if offer.retailer else "Unbekannter Händler",
            "product_url": offer.product_url,
            "product_name": offer.product_name,
            "product_variant": offer.product_variant,
            "product_type": offer.product_type,
            "size_ml": offer.size_ml,
            "concentration": offer.concentration,
            "price_eur": round(float(offer.price_eur or 0), 2),
            "shipping_eur": round(float(offer.shipping_eur or 0), 2),
            "total_eur": round(float(offer.price_eur or 0) + float(offer.shipping_eur or 0), 2),
            "in_stock": bool(offer.in_stock),
            "scan_interval": offer.scan_interval,
            "interval_hours": interval_hours,
            "manual_status": status,
            "manual_check_due": due,
            "manual_checked_at": manual_checked_at,
            "next_due_at": next_due_at,
        })

    items.sort(key=lambda row: (
        0 if row["manual_checked_at"] is None else 1,
        row["manual_checked_at"] or datetime.min,
        row["retailer_name"].casefold(),
        row["fragrance_name"].casefold(),
    ))
    visible = [row for row in items if row["manual_check_due"]] if due_only else items
    visible = visible[:limit]
    for index, row in enumerate(visible, start=1):
        row["queue_position"] = index

    return {
        "generated_at": now,
        "due_only": due_only,
        "summary": {
            "total": len(items),
            "due": status_counts["NEVER_CHECKED"] + status_counts["DUE"],
            "never_checked": status_counts["NEVER_CHECKED"],
            "current": status_counts["CURRENT"],
            "returned": len(visible),
        },
        "items": visible,
    }
