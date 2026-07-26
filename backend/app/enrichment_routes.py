from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import event, text
from sqlalchemy.orm import Session

from .database import Base, get_db

router = APIRouter(prefix="/api/enrichment", tags=["enrichment"])


@event.listens_for(Base.metadata, "after_create")
def ensure_enrichment_tables(target, connection, **kwargs):
    if connection.dialect.name != "postgresql":
        return
    statements = (
        """CREATE TABLE IF NOT EXISTS enrichment_tasks (
            id UUID PRIMARY KEY,
            fragrance_id UUID NOT NULL REFERENCES fragrances(id) ON DELETE CASCADE,
            missing_fields JSONB NOT NULL,
            status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(fragrance_id)
        )""",
        """CREATE TABLE IF NOT EXISTS dupe_evidence (
            id UUID PRIMARY KEY,
            candidate_id UUID REFERENCES research_candidates(id) ON DELETE CASCADE,
            fragrance_id UUID REFERENCES fragrances(id) ON DELETE CASCADE,
            matched_fragrance_id UUID REFERENCES fragrances(id) ON DELETE SET NULL,
            source_name VARCHAR(300) NOT NULL,
            source_url TEXT NOT NULL,
            found_brand VARCHAR(160),
            found_name VARCHAR(200),
            found_year INTEGER,
            found_concentration VARCHAR(80),
            classification VARCHAR(40) NOT NULL DEFAULT 'POSSIBLE_DUPLICATE',
            reason TEXT,
            confidence FLOAT NOT NULL DEFAULT 0,
            status VARCHAR(30) NOT NULL DEFAULT 'OPEN',
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""",
        "CREATE INDEX IF NOT EXISTS ix_enrichment_tasks_status ON enrichment_tasks(status)",
        "CREATE INDEX IF NOT EXISTS ix_dupe_evidence_candidate ON dupe_evidence(candidate_id)",
        "CREATE INDEX IF NOT EXISTS ix_dupe_evidence_fragrance ON dupe_evidence(fragrance_id)",
    )
    for statement in statements:
        connection.execute(text(statement))


class EvidencePayload(BaseModel):
    candidate_id: UUID | None = None
    fragrance_id: UUID | None = None
    matched_fragrance_id: UUID | None = None
    source_name: str = Field(min_length=1, max_length=300)
    source_url: str = Field(min_length=8, max_length=2000)
    found_brand: str | None = Field(default=None, max_length=160)
    found_name: str | None = Field(default=None, max_length=200)
    found_year: int | None = Field(default=None, ge=1800, le=2200)
    found_concentration: str | None = Field(default=None, max_length=80)
    classification: str = Field(default="POSSIBLE_DUPLICATE", max_length=40)
    reason: str | None = None
    confidence: float = Field(default=0, ge=0, le=100)


@router.post("/scan-gaps")
def scan_gaps(db: Session = Depends(get_db)):
    rows = list(db.execute(text("""
        SELECT f.id, f.year, f.concentration, f.perfumer, f.description, f.image_url,
               f.top_notes, f.heart_notes, f.base_notes,
               EXISTS(SELECT 1 FROM master_sources s WHERE upper(coalesce(s.object_type,''))='FRAGRANCE' AND s.object_id=f.id::text) AS has_source,
               EXISTS(SELECT 1 FROM fragrance_notes fn WHERE fn.fragrance_id=f.id) AS has_structured_notes
        FROM fragrances f
    """)).mappings())
    created = updated = complete = 0
    for row in rows:
        missing = []
        if row["year"] is None: missing.append("year")
        if not row["concentration"]: missing.append("concentration")
        if not row["perfumer"]: missing.append("perfumer")
        if not row["description"]: missing.append("description")
        if not row["image_url"]: missing.append("image")
        if not row["has_source"]: missing.append("source")
        if not row["has_structured_notes"] and not any((row["top_notes"], row["heart_notes"], row["base_notes"])):
            missing.append("notes")
        existing = db.execute(text("SELECT id FROM enrichment_tasks WHERE fragrance_id=:id"), {"id": row["id"]}).scalar()
        if not missing:
            complete += 1
            if existing:
                db.execute(text("UPDATE enrichment_tasks SET status='COMPLETE',missing_fields='[]'::jsonb,updated_at=CURRENT_TIMESTAMP WHERE fragrance_id=:id"), {"id": row["id"]})
            continue
        if existing:
            db.execute(text("UPDATE enrichment_tasks SET missing_fields=CAST(:fields AS JSONB),status='PENDING',updated_at=CURRENT_TIMESTAMP WHERE fragrance_id=:id"), {"id": row["id"], "fields": __import__('json').dumps(missing)})
            updated += 1
        else:
            db.execute(text("INSERT INTO enrichment_tasks(id,fragrance_id,missing_fields,status) VALUES(:id,:fragrance,CAST(:fields AS JSONB),'PENDING')"), {"id": uuid4(), "fragrance": row["id"], "fields": __import__('json').dumps(missing)})
            created += 1
    db.commit()
    return {"checked": len(rows), "created": created, "updated": updated, "complete": complete}


@router.get("/tasks")
def list_tasks(status: str = "PENDING", db: Session = Depends(get_db)):
    query = """SELECT t.*, f.name AS fragrance_name, b.name AS brand_name
               FROM enrichment_tasks t JOIN fragrances f ON f.id=t.fragrance_id JOIN brands b ON b.id=f.brand_id"""
    params = {}
    if status != "ALL":
        query += " WHERE t.status=:status"
        params["status"] = status
    query += " ORDER BY b.name,f.name"
    return list(db.execute(text(query), params).mappings())


@router.post("/dupe-evidence", status_code=201)
def add_dupe_evidence(payload: EvidencePayload, db: Session = Depends(get_db)):
    if not payload.candidate_id and not payload.fragrance_id:
        raise HTTPException(400, "Kandidat oder Duft muss angegeben werden.")
    classification = payload.classification.upper().strip()
    if classification not in {"LIKELY_SAME", "CONCENTRATION_VARIANT", "FLANKER", "POSSIBLE_DUPLICATE", "SIMILAR_NAME"}:
        raise HTTPException(400, "Ungültige Dublettenklassifikation.")
    row = db.execute(text("""
        INSERT INTO dupe_evidence(id,candidate_id,fragrance_id,matched_fragrance_id,source_name,source_url,
        found_brand,found_name,found_year,found_concentration,classification,reason,confidence,status)
        VALUES(:id,:candidate,:fragrance,:matched,:source_name,:source_url,:brand,:name,:year,:concentration,
        :classification,:reason,:confidence,'OPEN') RETURNING *
    """), {"id": uuid4(), "candidate": payload.candidate_id, "fragrance": payload.fragrance_id,
           "matched": payload.matched_fragrance_id, "source_name": payload.source_name,
           "source_url": payload.source_url, "brand": payload.found_brand, "name": payload.found_name,
           "year": payload.found_year, "concentration": payload.found_concentration,
           "classification": classification, "reason": payload.reason, "confidence": payload.confidence}).mappings().first()
    db.commit()
    return row


@router.get("/dupe-evidence")
def list_dupe_evidence(candidate_id: UUID | None = None, fragrance_id: UUID | None = None, db: Session = Depends(get_db)):
    query = "SELECT * FROM dupe_evidence WHERE 1=1"
    params = {}
    if candidate_id:
        query += " AND candidate_id=:candidate"
        params["candidate"] = candidate_id
    if fragrance_id:
        query += " AND fragrance_id=:fragrance"
        params["fragrance"] = fragrance_id
    query += " ORDER BY created_at DESC"
    return list(db.execute(text(query), params).mappings())
