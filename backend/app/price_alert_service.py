from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from .price_alert_models import PriceAlert
from .price_models import FragranceOffer, PriceObservation, Retailer
from .price_routes import _variant_identity


ALERT_STATUSES = {
    "INACTIVE",
    "WAITING",
    "TRIGGERED",
    "NO_ELIGIBLE_OFFER",
    "VARIANT_MISSING",
}


def price_alert_out(alert: PriceAlert) -> dict:
    return {
        "id": str(alert.id),
        "fragrance_id": str(alert.fragrance_id),
        "variant_key": alert.variant_key,
        "product_type": alert.product_type,
        "size_ml": alert.size_ml,
        "concentration": alert.concentration,
        "active": bool(alert.active),
        "target_total_eur": round(float(alert.target_total_eur), 2) if alert.target_total_eur is not None else None,
        "max_percent_above_low": (
            round(float(alert.max_percent_above_low), 1)
            if alert.max_percent_above_low is not None
            else None
        ),
        "status": alert.status,
        "current_total_eur": round(float(alert.current_total_eur), 2) if alert.current_total_eur is not None else None,
        "historic_low_total_eur": (
            round(float(alert.historic_low_total_eur), 2)
            if alert.historic_low_total_eur is not None
            else None
        ),
        "last_evaluated_at": alert.last_evaluated_at,
        "last_triggered_at": alert.last_triggered_at,
        "trigger_count": int(alert.trigger_count or 0),
        "created_at": alert.created_at,
        "updated_at": alert.updated_at,
    }


def _approved_offers(db: Session, fragrance_id: UUID) -> list[FragranceOffer]:
    return list(db.scalars(
        select(FragranceOffer)
        .join(Retailer, Retailer.id == FragranceOffer.retailer_id)
        .where(
            FragranceOffer.fragrance_id == fragrance_id,
            FragranceOffer.review_status == "APPROVED",
            Retailer.active.is_(True),
        )
        .options(joinedload(FragranceOffer.retailer))
    ).unique())


def find_variant_offers(
    db: Session,
    fragrance_id: UUID,
    variant_key: str,
) -> list[FragranceOffer]:
    return [
        offer
        for offer in _approved_offers(db, fragrance_id)
        if _variant_identity(offer)["variant_key"] == variant_key
    ]


def _historic_low(db: Session, offer_ids: list[UUID]) -> float | None:
    if not offer_ids:
        return None
    value = db.scalar(
        select(func.min(PriceObservation.price_eur + PriceObservation.shipping_eur))
        .where(
            PriceObservation.offer_id.in_(offer_ids),
            PriceObservation.in_stock.is_(True),
        )
    )
    return round(float(value), 2) if value is not None else None


def evaluate_price_alert(
    db: Session,
    alert: PriceAlert,
    *,
    evaluated_at: datetime | None = None,
) -> PriceAlert:
    now = evaluated_at or datetime.utcnow()
    previous_status = alert.status
    alert.last_evaluated_at = now
    alert.updated_at = now

    if not alert.active:
        alert.status = "INACTIVE"
        return alert

    offers = find_variant_offers(db, alert.fragrance_id, alert.variant_key)
    if not offers:
        alert.status = "VARIANT_MISSING"
        alert.current_total_eur = None
        alert.historic_low_total_eur = None
        return alert

    offer_ids = [offer.id for offer in offers]
    historic_low = _historic_low(db, offer_ids)
    alert.historic_low_total_eur = historic_low

    available = [offer for offer in offers if offer.in_stock]
    if not available:
        alert.status = "NO_ELIGIBLE_OFFER"
        alert.current_total_eur = None
        return alert

    current = min(round(float(offer.price_eur) + float(offer.shipping_eur), 2) for offer in available)
    alert.current_total_eur = current

    target_hit = (
        alert.target_total_eur is not None
        and current <= round(float(alert.target_total_eur), 2)
    )
    low_rule_hit = (
        alert.max_percent_above_low is not None
        and historic_low is not None
        and current <= historic_low * (1 + float(alert.max_percent_above_low) / 100)
    )
    alert.status = "TRIGGERED" if target_hit or low_rule_hit else "WAITING"

    if alert.status == "TRIGGERED" and previous_status != "TRIGGERED":
        alert.last_triggered_at = now
        alert.trigger_count = int(alert.trigger_count or 0) + 1
    return alert


def evaluate_price_alerts_for_fragrance(
    db: Session,
    fragrance_id: UUID,
    *,
    evaluated_at: datetime | None = None,
) -> list[PriceAlert]:
    alerts = list(db.scalars(
        select(PriceAlert).where(
            PriceAlert.fragrance_id == fragrance_id,
            PriceAlert.active.is_(True),
        )
    ))
    for alert in alerts:
        evaluate_price_alert(db, alert, evaluated_at=evaluated_at)
    return alerts
