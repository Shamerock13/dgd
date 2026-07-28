from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone

from sqlalchemy import text

from .database import Base, SessionLocal, engine
from .price_scanner import refresh_due_offers
from .research_source_routes import _run_source

# Import main so all models and metadata listeners are registered before create_all.
from . import main as _main  # noqa: F401,E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("dgd-scanner-worker")


def _price_scanner_enabled() -> bool:
    return os.getenv("PRICE_SCANNER_ENABLED", "true").strip().casefold() in {"1", "true", "yes", "on"}


def _price_interval_hours() -> int:
    try:
        value = int(os.getenv("PRICE_SCAN_INTERVAL_HOURS", "24"))
    except ValueError:
        value = 24
    return max(1, min(value, 720))


async def _cycle() -> int:
    with SessionLocal() as db:
        control = db.execute(text("SELECT * FROM scanner_control WHERE id=1")).mappings().first()
        if not control:
            db.execute(text("INSERT INTO scanner_control(id,enabled,poll_seconds) VALUES(1,FALSE,300)"))
            db.commit()
            control = db.execute(text("SELECT * FROM scanner_control WHERE id=1")).mappings().first()

        poll_seconds = max(60, min(int(control["poll_seconds"] or 300), 86400))
        db.execute(text("UPDATE scanner_control SET heartbeat_at=CURRENT_TIMESTAMP WHERE id=1"))
        db.commit()

        research_rows = []
        if control["enabled"]:
            research_rows = list(db.execute(text("""
                SELECT * FROM research_sources
                WHERE active=TRUE
                  AND (last_run_at IS NULL OR last_run_at + make_interval(hours => interval_hours) <= CURRENT_TIMESTAMP)
                ORDER BY COALESCE(last_run_at, TIMESTAMPTZ '1970-01-01'), name
            """)).mappings())

        successful = failed = skipped = 0
        price_result = {"due": 0, "successful": 0, "failed": 0, "results": []}
        try:
            for row in research_rows:
                result = await _run_source(row, db)
                successful += result["status"] == "SUCCESS"
                failed += result["status"] == "FAILED"
                skipped += result["status"] == "SKIPPED_LOCKED"

            if _price_scanner_enabled():
                price_result = await refresh_due_offers(
                    db,
                    interval_hours=_price_interval_hours(),
                    limit=100,
                )

            total_failed = failed + price_result["failed"]
            status = "SUCCESS" if total_failed == 0 else "PARTIAL"
            db.execute(text("""
                UPDATE scanner_control
                SET heartbeat_at=CURRENT_TIMESTAMP,last_cycle_at=CURRENT_TIMESTAMP,
                    last_cycle_status=:status,last_cycle_error=NULL,updated_at=CURRENT_TIMESTAMP
                WHERE id=1
            """), {"status": status})
            db.commit()
            logger.info(
                "Scanner cycle complete: research_due=%s research_success=%s research_failed=%s locked=%s price_due=%s price_success=%s price_failed=%s",
                len(research_rows), successful, failed, skipped,
                price_result["due"], price_result["successful"], price_result["failed"],
            )
            for result in price_result["results"]:
                if result["status"] == "FAILED":
                    logger.warning(
                        "Price check failed: retailer=%s offer=%s error=%s",
                        result.get("retailer"), result.get("offer_id"), result.get("error"),
                    )
        except Exception as exc:
            db.rollback()
            message = f"{type(exc).__name__}: {exc}"[:1000]
            db.execute(text("""
                UPDATE scanner_control
                SET heartbeat_at=CURRENT_TIMESTAMP,last_cycle_at=CURRENT_TIMESTAMP,
                    last_cycle_status='FAILED',last_cycle_error=:error,updated_at=CURRENT_TIMESTAMP
                WHERE id=1
            """), {"error": message})
            db.commit()
            logger.exception("Scanner cycle failed")

        return poll_seconds


async def run_forever() -> None:
    Base.metadata.create_all(bind=engine)
    logger.info(
        "DGD scanner worker started (price_scanner=%s interval_hours=%s)",
        _price_scanner_enabled(), _price_interval_hours(),
    )
    while True:
        try:
            delay = await _cycle()
        except Exception:
            logger.exception("Worker loop failed before cycle completion")
            delay = 60
        await asyncio.sleep(delay)


if __name__ == "__main__":
    asyncio.run(run_forever())
