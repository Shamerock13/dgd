from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .price_models import FragranceOffer, Retailer
from .price_resilient_scanner import refresh_offer
from .price_scan_capability import (
    BROWSER_REQUIRED_TRUST_STATUS,
    requires_browser_connector,
)
from .price_source_review_models import PriceSourceReviewEvent


async def refresh_due_offers(
    db: Session,
    interval_hours: int = 24,
    limit: int = 100,
) -> dict:
    """Scannt ausschließlich bewusst freigegebene und aktivierte Preisquellen."""
    cutoff = datetime.utcnow() - timedelta(hours=max(1, min(interval_hours, 720)))
    offers = list(db.scalars(
        select(FragranceOffer)
        .join(Retailer, Retailer.id == FragranceOffer.retailer_id)
        .where(
            Retailer.active.is_(True),
            FragranceOffer.review_status == "APPROVED",
            FragranceOffer.scanner_active.is_(True),
            FragranceOffer.trust_status != BROWSER_REQUIRED_TRUST_STATUS,
            FragranceOffer.checked_at <= cutoff,
        )
        .options(joinedload(FragranceOffer.retailer))
        .order_by(FragranceOffer.checked_at)
        .limit(max(1, min(limit, 500)))
    ).unique())

    results: list[dict] = []
    for offer in offers:
        try:
            if offer.review_status != "APPROVED" or not offer.scanner_active:
                raise ValueError("Preisquelle ist nicht für den Scanner freigegeben")
            if not offer.retailer or not offer.retailer.active:
                raise ValueError("Händler ist nicht aktiv")
            results.append(await refresh_offer(offer, db))
        except Exception as exc:
            db.rollback()
            message = f"{type(exc).__name__}: {exc}"[:600]
            if requires_browser_connector(exc):
                offer.scanner_active = False
                offer.trust_status = BROWSER_REQUIRED_TRUST_STATUS
                offer.updated_at = datetime.utcnow()
                db.add(PriceSourceReviewEvent(
                    id=uuid4(),
                    offer_id=offer.id,
                    action="BROWSER_REQUIRED",
                    previous_status=offer.review_status,
                    new_status=offer.review_status,
                    scanner_active=False,
                    retailer_activated=False,
                    note=message,
                ))
                db.commit()
            results.append({
                "offer_id": str(offer.id),
                "retailer": offer.retailer.name if offer.retailer else "Unbekannt",
                "status": "FAILED",
                "error": message,
                "browser_connector_required": requires_browser_connector(exc),
            })

    successful = sum(row["status"] == "SUCCESS" for row in results)
    return {
        "due": len(offers),
        "successful": successful,
        "failed": len(results) - successful,
        "results": results,
    }
