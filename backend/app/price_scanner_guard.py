from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .price_models import FragranceOffer, Retailer
from .price_resilient_scanner import refresh_offer


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
            results.append({
                "offer_id": str(offer.id),
                "retailer": offer.retailer.name if offer.retailer else "Unbekannt",
                "status": "FAILED",
                "error": f"{type(exc).__name__}: {exc}"[:600],
            })

    successful = sum(row["status"] == "SUCCESS" for row in results)
    return {
        "due": len(offers),
        "successful": successful,
        "failed": len(results) - successful,
        "results": results,
    }
