from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import get_db
from .models import Fragrance
from .price_alert_models import PriceAlert
from .price_alert_service import (
    evaluate_price_alert,
    find_variant_offers,
    price_alert_out,
    variant_identity,
)

router = APIRouter(prefix="/api/prices", tags=["price-alerts"])


class PriceAlertUpsert(BaseModel):
    active: bool = True
    target_total_eur: float | None = Field(default=None, gt=0, le=100_000)
    max_percent_above_low: float | None = Field(default=None, ge=0, le=500)

    @model_validator(mode="after")
    def validate_threshold(self):
        if self.target_total_eur is None and self.max_percent_above_low is None:
            raise ValueError("Mindestens ein Zielpreis oder ein Abstand zum historischen Tief ist erforderlich.")
        return self


def _load_fragrance(db: Session, fragrance_id: UUID) -> Fragrance:
    fragrance = db.get(Fragrance, fragrance_id)
    if not fragrance:
        raise HTTPException(404, "Duft nicht gefunden.")
    return fragrance


def _load_alert(db: Session, fragrance_id: UUID, variant_key: str) -> PriceAlert:
    alert = db.scalar(
        select(PriceAlert).where(
            PriceAlert.fragrance_id == fragrance_id,
            PriceAlert.variant_key == variant_key,
        )
    )
    if not alert:
        raise HTTPException(404, "Für diese Preisvariante ist kein Alarm gespeichert.")
    return alert


@router.get("/fragrances/{fragrance_id}/alerts")
def list_price_alerts(
    fragrance_id: UUID,
    db: Session = Depends(get_db),
):
    _load_fragrance(db, fragrance_id)
    alerts = list(db.scalars(
        select(PriceAlert)
        .where(PriceAlert.fragrance_id == fragrance_id)
        .order_by(PriceAlert.created_at)
    ))
    changed = False
    for alert in alerts:
        before = (
            alert.status,
            alert.current_total_eur,
            alert.historic_low_total_eur,
            alert.last_evaluated_at,
            alert.last_triggered_at,
            alert.trigger_count,
        )
        evaluate_price_alert(db, alert)
        after = (
            alert.status,
            alert.current_total_eur,
            alert.historic_low_total_eur,
            alert.last_evaluated_at,
            alert.last_triggered_at,
            alert.trigger_count,
        )
        changed = changed or before != after
    if changed:
        db.commit()
    return {"alerts": [price_alert_out(alert) for alert in alerts]}


@router.put("/fragrances/{fragrance_id}/alerts/{variant_key}")
def upsert_price_alert(
    fragrance_id: UUID,
    variant_key: str,
    payload: PriceAlertUpsert,
    db: Session = Depends(get_db),
):
    _load_fragrance(db, fragrance_id)
    if not variant_key.startswith("pv-") or len(variant_key) > 40:
        raise HTTPException(422, "Ungültiger Variantenschlüssel.")

    offers = find_variant_offers(db, fragrance_id, variant_key)
    if not offers:
        raise HTTPException(
            409,
            "Die Preisvariante ist nicht mehr vorhanden oder besitzt keine freigegebene Quelle bei einem aktiven Händler.",
        )
    identity = variant_identity(offers[0])
    if not identity["variant_complete"]:
        raise HTTPException(
            409,
            "Für einen Preisalarm müssen Größe und Konzentration der Variante vollständig gepflegt sein.",
        )

    alert = db.scalar(
        select(PriceAlert).where(
            PriceAlert.fragrance_id == fragrance_id,
            PriceAlert.variant_key == variant_key,
        )
    )
    created = alert is None
    if alert is None:
        alert = PriceAlert(
            id=uuid4(),
            fragrance_id=fragrance_id,
            variant_key=variant_key,
            product_type=identity["product_type"],
            size_ml=identity["size_ml"],
            concentration=identity["concentration"],
        )
        db.add(alert)

    alert.product_type = identity["product_type"]
    alert.size_ml = identity["size_ml"]
    alert.concentration = identity["concentration"]
    alert.active = payload.active
    alert.target_total_eur = (
        round(float(payload.target_total_eur), 2)
        if payload.target_total_eur is not None
        else None
    )
    alert.max_percent_above_low = (
        round(float(payload.max_percent_above_low), 1)
        if payload.max_percent_above_low is not None
        else None
    )
    alert.updated_at = datetime.utcnow()
    evaluate_price_alert(db, alert)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Für diese Preisvariante existiert bereits ein Alarm.") from exc
    db.refresh(alert)
    return {"created": created, "alert": price_alert_out(alert)}


@router.delete("/fragrances/{fragrance_id}/alerts/{variant_key}", status_code=204)
def delete_price_alert(
    fragrance_id: UUID,
    variant_key: str,
    db: Session = Depends(get_db),
):
    alert = _load_alert(db, fragrance_id, variant_key)
    db.delete(alert)
    db.commit()
    return None
