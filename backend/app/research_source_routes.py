from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import get_db
from .research_routes import ScanRequest, scan_page, _public_url

router = APIRouter(prefix="/api/research", tags=["research-sources"])


class SourcePayload(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    url: str = Field(min_length=8, max_length=2000)
    interval_hours: int = Field(default=24, ge=1, le=8760)
    active: bool = True
    note: str | None = None


def _source(db: Session, source_id: UUID):
    row = db.execute(text("SELECT * FROM research_sources WHERE id=:id"), {"id": source_id}).mappings().first()
    if not row:
        raise HTTPException(404, "Recherchequelle nicht gefunden")
    return row


@router.get("/sources")
def list_sources(db: Session = Depends(get_db)):
    return list(db.execute(text("SELECT * FROM research_sources ORDER BY active DESC, name")).mappings())


@router.post("/sources", status_code=201)
def create_source(payload: SourcePayload, db: Session = Depends(get_db)):
    url = _public_url(payload.url)
    row = db.execute(text("""
        INSERT INTO research_sources (id,name,url,interval_hours,active,note,created_at,updated_at)
        VALUES (:id,:name,:url,:interval,:active,:note,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
        RETURNING *
    """), {"id": uuid4(), "name": payload.name, "url": url, "interval": payload.interval_hours, "active": payload.active, "note": payload.note}).mappings().first()
    db.commit()
    return row


@router.put("/sources/{source_id}")
def update_source(source_id: UUID, payload: SourcePayload, db: Session = Depends(get_db)):
    _source(db, source_id)
    url = _public_url(payload.url)
    row = db.execute(text("""
        UPDATE research_sources SET name=:name,url=:url,interval_hours=:interval,active=:active,note=:note,updated_at=CURRENT_TIMESTAMP
        WHERE id=:id RETURNING *
    """), {"id": source_id, "name": payload.name, "url": url, "interval": payload.interval_hours, "active": payload.active, "note": payload.note}).mappings().first()
    db.commit()
    return row


@router.delete("/sources/{source_id}", status_code=204)
def delete_source(source_id: UUID, db: Session = Depends(get_db)):
    changed = db.execute(text("DELETE FROM research_sources WHERE id=:id"), {"id": source_id}).rowcount
    if not changed:
        raise HTTPException(404, "Recherchequelle nicht gefunden")
    db.commit()


async def _run_source(row, db: Session):
    started = datetime.now(timezone.utc)
    run_id = uuid4()
    db.execute(text("""
        INSERT INTO research_scan_runs (id,source_id,status,started_at)
        VALUES (:id,:source,'RUNNING',:started)
    """), {"id": run_id, "source": row["id"], "started": started})
    db.commit()
    try:
        result = await scan_page(ScanRequest(url=row["url"], source_name=row["name"]), db)
        db.execute(text("""
            UPDATE research_scan_runs SET status='SUCCESS',finished_at=CURRENT_TIMESTAMP,found_count=:found,created_count=:created,duplicate_count=:duplicates WHERE id=:id
        """), {"id": run_id, "found": result["found"], "created": result["created"], "duplicates": result["possible_duplicates"]})
        db.execute(text("UPDATE research_sources SET last_run_at=CURRENT_TIMESTAMP,last_status='SUCCESS',last_error=NULL,updated_at=CURRENT_TIMESTAMP WHERE id=:id"), {"id": row["id"]})
        db.commit()
        return {"source_id": str(row["id"]), "name": row["name"], "status": "SUCCESS", **result}
    except Exception as exc:
        message = str(getattr(exc, "detail", exc))[:1000]
        db.execute(text("UPDATE research_scan_runs SET status='FAILED',finished_at=CURRENT_TIMESTAMP,error_message=:error WHERE id=:id"), {"id": run_id, "error": message})
        db.execute(text("UPDATE research_sources SET last_run_at=CURRENT_TIMESTAMP,last_status='FAILED',last_error=:error,updated_at=CURRENT_TIMESTAMP WHERE id=:id"), {"id": row["id"], "error": message})
        db.commit()
        return {"source_id": str(row["id"]), "name": row["name"], "status": "FAILED", "error": message}


@router.post("/sources/{source_id}/scan")
async def scan_source(source_id: UUID, db: Session = Depends(get_db)):
    return await _run_source(_source(db, source_id), db)


@router.post("/sources/scan-active")
async def scan_active_sources(due_only: bool = False, db: Session = Depends(get_db)):
    rows = list(db.execute(text("SELECT * FROM research_sources WHERE active=true ORDER BY name")).mappings())
    now = datetime.now(timezone.utc)
    selected = []
    for row in rows:
        if not due_only or not row["last_run_at"] or row["last_run_at"] + timedelta(hours=row["interval_hours"]) <= now:
            selected.append(row)
    results = [await _run_source(row, db) for row in selected]
    return {"requested": len(selected), "successful": sum(r["status"] == "SUCCESS" for r in results), "failed": sum(r["status"] == "FAILED" for r in results), "results": results}


@router.get("/scan-runs")
def list_scan_runs(limit: int = 30, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 200))
    return list(db.execute(text("""
        SELECT r.*, s.name AS source_name FROM research_scan_runs r
        JOIN research_sources s ON s.id=r.source_id ORDER BY r.started_at DESC LIMIT :limit
    """), {"limit": limit}).mappings())
