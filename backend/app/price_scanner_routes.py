from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .database import get_db
from .price_models import FragranceOffer, PriceObservation, Retailer
from .price_scanner import SUPPORTED_RETAILER_HOSTS
from .price_scanner_guard import refresh_due_offers

router = APIRouter(prefix="/api/prices/scanner", tags=["prices"])


@router.get("/status")
def price_scanner_status(db: Session = Depends(get_db)):
    configured = db.scalar(select(func.count(Retailer.id)).where(Retailer.active.is_(True))) or 0
    offers = db.scalar(
        select(func.count(FragranceOffer.id)).where(
            FragranceOffer.review_status == "APPROVED",
            FragranceOffer.scanner_active.is_(True),
        )
    ) or 0
    observations = db.scalar(select(func.count(PriceObservation.id))) or 0
    latest = db.scalar(select(func.max(PriceObservation.observed_at)))
    return {
        "enabled_by_default": False,
        "interval_hours_default": 24,
        "supported_hosts": sorted(SUPPORTED_RETAILER_HOSTS),
        "active_retailers": configured,
        "tracked_offers": offers,
        "observations": observations,
        "last_observation_at": latest,
    }


@router.post("/run-due")
async def run_due_price_checks(
    interval_hours: int = Query(default=24, ge=1, le=720),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return await refresh_due_offers(db, interval_hours=interval_hours, limit=limit)
