from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from .database import Base, SessionLocal, engine
from .research_source_routes import _run_source

# Import main so all models and metadata listeners are registered before create_all.
from . import main as _main  # noqa: F401,E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("dgd-scanner-worker")


async def _cycle() -> int:
    with SessionLocal() as db:
        control = db.execute(text("SELECT * FROM scanner_control WHERE id=1")).mappings().first()
        if not control:
            db.execute(text("INSERT INTO scanner_control(id,enabled,poll_seconds) VALUES(1,FALSE,300)"))
            db.commit()
            return 300

        poll_seconds = max(60, min(int(control["poll_seconds"] or 300), 86400))
        db.execute(text("UPDATE scanner_control SET heartbeat_at=CURRENT_TIMESTAMP WHERE id=1"))
        db.commit()

        if not control["enabled"]:
            return poll_seconds

        now = datetime.now(timezone.utc)
        rows = list(db.execute(text("""
            SELECT * FROM research_sources
            WHERE active=TRUE
              AND (last_run_at IS NULL OR last_run_at + make_interval(hours => interval_hours) <= CURRENT_TIMESTAMP)
            ORDER BY COALESCE(last_run_at, TIMESTAMPTZ '1970-01-01'), name
        """)).mappings())

        successful = failed = skipped = 0
        try:
            for row in rows:
                result = await _run_source(row, db)
                successful += result["status"] == "SUCCESS"
                failed += result["status"] == "FAILED"
                skipped += result["status"] == "SKIPPED_LOCKED"
            status = "SUCCESS" if failed == 0 else "PARTIAL"
            db.execute(text("""
                UPDATE scanner_control
                SET heartbeat_at=CURRENT_TIMESTAMP,last_cycle_at=CURRENT_TIMESTAMP,
                    last_cycle_status=:status,last_cycle_error=NULL,updated_at=CURRENT_TIMESTAMP
                WHERE id=1
            """), {"status": status})
            db.commit()
            logger.info(
                "Scanner cycle complete: due=%s success=%s failed=%s locked=%s",
                len(rows), successful, failed, skipped,
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
    logger.info("DGD scanner worker started")
    while True:
        try:
            delay = await _cycle()
        except Exception:
            logger.exception("Worker loop failed before cycle completion")
            delay = 60
        await asyncio.sleep(delay)


if __name__ == "__main__":
    asyncio.run(run_forever())
