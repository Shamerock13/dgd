from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import get_db
from .research_adapters import scan_source_adapter
from .research_routes import _public_url

router = APIRouter(tags=["research-sources"])


class SourcePayload(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    url: str = Field(min_length=8, max_length=2000)
    adapter_type: str = Field(default="SINGLE", max_length=30)
    link_pattern: str | None = Field(default=None, max_length=1000)
    max_pages: int = Field(default=20, ge=1, le=100)
    same_domain_only: bool = True
    interval_hours: int = Field(default=24, ge=1, le=8760)
    active: bool = True
    note: str | None = None

    @field_validator("adapter_type")
    @classmethod
    def validate_adapter(cls, value: str):
        value = value.upper().strip()
        if value not in {"SINGLE", "LIST"}:
            raise ValueError("Erlaubt sind SINGLE und LIST.")
        return value

    @field_validator("link_pattern")
    @classmethod
    def validate_pattern(cls, value: str | None):
        if not value:
            return None
        import re
        try:
            re.compile(value)
        except re.error as exc:
            raise ValueError(f"Ungültiger Link-Filter: {exc}") from exc
        return value


class ScannerControlPayload(BaseModel):
    enabled: bool
    poll_seconds: int = Field(default=300, ge=60, le=86400)


def _source(db: Session, source_id: UUID):
    row = db.execute(text("SELECT * FROM research_sources WHERE id=:id"), {"id": source_id}).mappings().first()
    if not row:
        raise HTTPException(404, "Recherchequelle nicht gefunden")
    return row


def _scanner_status(db: Session):
    row = db.execute(text("SELECT * FROM scanner_control WHERE id=1")).mappings().first()
    if not row:
        db.execute(text("INSERT INTO scanner_control(id,enabled,poll_seconds) VALUES(1,FALSE,300)"))
        db.commit()
        row = db.execute(text("SELECT * FROM scanner_control WHERE id=1")).mappings().first()
    result = dict(row)
    heartbeat = result.get("heartbeat_at")
    poll_seconds = int(result.get("poll_seconds") or 300)
    result["worker_online"] = bool(heartbeat and heartbeat >= datetime.now(timezone.utc) - timedelta(seconds=max(180, poll_seconds * 2)))
    return result


@router.get("/sources")
def list_sources(db: Session = Depends(get_db)):
    return list(db.execute(text("""
        SELECT s.*, CASE WHEN s.last_run_at IS NULL THEN CURRENT_TIMESTAMP
        ELSE s.last_run_at + make_interval(hours => s.interval_hours) END AS next_run_at
        FROM research_sources s ORDER BY active DESC, name
    """)).mappings())


@router.post("/sources", status_code=201)
def create_source(payload: SourcePayload, db: Session = Depends(get_db)):
    url = _public_url(payload.url)
    row = db.execute(text("""
        INSERT INTO research_sources
        (id,name,url,adapter_type,link_pattern,max_pages,same_domain_only,interval_hours,active,note,created_at,updated_at)
        VALUES (:id,:name,:url,:adapter,:pattern,:max_pages,:same_domain,:interval,:active,:note,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
        RETURNING *
    """), {
        "id": uuid4(), "name": payload.name, "url": url, "adapter": payload.adapter_type,
        "pattern": payload.link_pattern, "max_pages": payload.max_pages,
        "same_domain": payload.same_domain_only, "interval": payload.interval_hours,
        "active": payload.active, "note": payload.note,
    }).mappings().first()
    db.commit()
    return row


@router.put("/sources/{source_id}")
def update_source(source_id: UUID, payload: SourcePayload, db: Session = Depends(get_db)):
    _source(db, source_id)
    url = _public_url(payload.url)
    row = db.execute(text("""
        UPDATE research_sources SET name=:name,url=:url,adapter_type=:adapter,
        link_pattern=:pattern,max_pages=:max_pages,same_domain_only=:same_domain,
        interval_hours=:interval,active=:active,note=:note,updated_at=CURRENT_TIMESTAMP
        WHERE id=:id RETURNING *
    """), {
        "id": source_id, "name": payload.name, "url": url, "adapter": payload.adapter_type,
        "pattern": payload.link_pattern, "max_pages": payload.max_pages,
        "same_domain": payload.same_domain_only, "interval": payload.interval_hours,
        "active": payload.active, "note": payload.note,
    }).mappings().first()
    db.commit()
    return row


@router.delete("/sources/{source_id}", status_code=204)
def delete_source(source_id: UUID, db: Session = Depends(get_db)):
    changed = db.execute(text("DELETE FROM research_sources WHERE id=:id"), {"id": source_id}).rowcount
    if not changed:
        raise HTTPException(404, "Recherchequelle nicht gefunden")
    db.commit()


async def _run_source(row, db: Session):
    lock_key = f"dgd-research-source:{row['id']}"
    locked = bool(db.execute(text("SELECT pg_try_advisory_lock(hashtext(:key))"), {"key": lock_key}).scalar())
    if not locked:
        return {"source_id": str(row["id"]), "name": row["name"], "status": "SKIPPED_LOCKED"}

    started = datetime.now(timezone.utc)
    run_id = uuid4()
    try:
        db.execute(text("""
            INSERT INTO research_scan_runs (id,source_id,status,started_at)
            VALUES (:id,:source,'RUNNING',:started)
        """), {"id": run_id, "source": row["id"], "started": started})
        db.commit()
        result = await scan_source_adapter(row, db)
        db.execute(text("""
            UPDATE research_scan_runs SET status='SUCCESS',finished_at=CURRENT_TIMESTAMP,
            found_count=:found,created_count=:created,duplicate_count=:duplicates,
            pages_scanned=:pages,links_discovered=:links WHERE id=:id
        """), {
            "id": run_id, "found": result["found"], "created": result["created"],
            "duplicates": result["possible_duplicates"], "pages": result.get("pages_scanned", 0),
            "links": result.get("links_discovered", 0),
        })
        db.execute(text("UPDATE research_sources SET last_run_at=CURRENT_TIMESTAMP,last_status='SUCCESS',last_error=NULL,updated_at=CURRENT_TIMESTAMP WHERE id=:id"), {"id": row["id"]})
        db.commit()
        return {"source_id": str(row["id"]), "name": row["name"], "status": "SUCCESS", **result}
    except Exception as exc:
        db.rollback()
        message = str(getattr(exc, "detail", exc))[:1000]
        db.execute(text("UPDATE research_scan_runs SET status='FAILED',finished_at=CURRENT_TIMESTAMP,error_message=:error WHERE id=:id"), {"id": run_id, "error": message})
        db.execute(text("UPDATE research_sources SET last_run_at=CURRENT_TIMESTAMP,last_status='FAILED',last_error=:error,updated_at=CURRENT_TIMESTAMP WHERE id=:id"), {"id": row["id"], "error": message})
        db.commit()
        return {"source_id": str(row["id"]), "name": row["name"], "status": "FAILED", "error": message}
    finally:
        db.execute(text("SELECT pg_advisory_unlock(hashtext(:key))"), {"key": lock_key})
        db.commit()


@router.post("/sources/{source_id}/scan")
async def scan_source(source_id: UUID, db: Session = Depends(get_db)):
    return await _run_source(_source(db, source_id), db)


@router.post("/sources/scan-active")
async def scan_active_sources(due_only: bool = False, db: Session = Depends(get_db)):
    rows = list(db.execute(text("SELECT * FROM research_sources WHERE active=true ORDER BY name")).mappings())
    now = datetime.now(timezone.utc)
    selected = [row for row in rows if not due_only or not row["last_run_at"] or row["last_run_at"] + timedelta(hours=row["interval_hours"]) <= now]
    results = [await _run_source(row, db) for row in selected]
    return {
        "requested": len(selected),
        "successful": sum(r["status"] == "SUCCESS" for r in results),
        "failed": sum(r["status"] == "FAILED" for r in results),
        "skipped_locked": sum(r["status"] == "SKIPPED_LOCKED" for r in results),
        "results": results,
    }


@router.get("/scanner/status")
def scanner_status(db: Session = Depends(get_db)):
    return _scanner_status(db)


@router.put("/scanner/status")
def update_scanner_status(payload: ScannerControlPayload, db: Session = Depends(get_db)):
    db.execute(text("""
        INSERT INTO scanner_control(id,enabled,poll_seconds,updated_at)
        VALUES(1,:enabled,:poll,CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET enabled=EXCLUDED.enabled,poll_seconds=EXCLUDED.poll_seconds,updated_at=CURRENT_TIMESTAMP
    """), {"enabled": payload.enabled, "poll": payload.poll_seconds})
    db.commit()
    return _scanner_status(db)


@router.get("/scan-runs")
def list_scan_runs(limit: int = 30, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 200))
    return list(db.execute(text("""
        SELECT r.*, s.name AS source_name, s.adapter_type FROM research_scan_runs r
        JOIN research_sources s ON s.id=r.source_id ORDER BY r.started_at DESC LIMIT :limit
    """), {"limit": limit}).mappings())
