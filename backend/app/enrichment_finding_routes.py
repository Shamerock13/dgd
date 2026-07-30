from __future__ import annotations

import json
import re
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import event, text
from sqlalchemy.orm import Session

from .database import Base, get_db
from .research_routes import _public_url

router = APIRouter(prefix="/api/enrichment", tags=["enrichment-findings"])

ALLOWED_FIELDS = {
    "year": "year",
    "concentration": "concentration",
    "perfumer": "perfumer",
    "description": "description",
    "image": "image_url",
    "image_url": "image_url",
    "top_notes": "top_notes",
    "heart_notes": "heart_notes",
    "base_notes": "base_notes",
    "accords": "accords",
}

NOTE_PYRAMIDS = {
    "top_notes": "top",
    "heart_notes": "heart",
    "base_notes": "base",
}


@event.listens_for(Base.metadata, "after_create")
def ensure_enrichment_finding_tables(target, connection, **kwargs):
    if connection.dialect.name != "postgresql":
        return
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS enrichment_findings (
            id UUID PRIMARY KEY,
            fragrance_id UUID NOT NULL REFERENCES fragrances(id) ON DELETE CASCADE,
            field_name VARCHAR(80) NOT NULL,
            proposed_value JSONB NOT NULL,
            source_name VARCHAR(300) NOT NULL,
            source_url TEXT NOT NULL,
            source_excerpt TEXT,
            confidence FLOAT NOT NULL DEFAULT 0,
            status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
            decision_note TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(fragrance_id, field_name, source_url)
        )
    """))
    connection.execute(text("CREATE INDEX IF NOT EXISTS ix_enrichment_findings_status ON enrichment_findings(status)"))
    connection.execute(text("CREATE INDEX IF NOT EXISTS ix_enrichment_findings_fragrance ON enrichment_findings(fragrance_id)"))


class FindingCreate(BaseModel):
    fragrance_id: UUID
    field_name: str = Field(min_length=1, max_length=80)
    proposed_value: object
    source_name: str = Field(min_length=1, max_length=300)
    source_url: str = Field(min_length=8, max_length=2000)
    source_excerpt: str | None = Field(default=None, max_length=2000)
    confidence: float = Field(default=0, ge=0, le=100)


class FindingDecision(BaseModel):
    note: str | None = Field(default=None, max_length=2000)


def _field_column(field_name: str) -> str:
    column = ALLOWED_FIELDS.get(field_name.strip().lower())
    if not column:
        raise HTTPException(400, "Dieses Duftfeld kann nicht über die Anreicherung geändert werden.")
    return column


def _finding(db: Session, finding_id: UUID):
    row = db.execute(text("SELECT * FROM enrichment_findings WHERE id=:id FOR UPDATE"), {"id": finding_id}).mappings().first()
    if not row:
        raise HTTPException(404, "Datenfund nicht gefunden")
    return row


def _note_names(value: object) -> list[str]:
    if isinstance(value, list):
        raw = value
    else:
        raw = re.split(r"[,;|\n]+", str(value or ""))
    result: list[str] = []
    seen: set[str] = set()
    for item in raw:
        name = re.sub(r"\s+", " ", str(item).strip(" \t\r\n-–—•"))[:120]
        key = name.casefold()
        if name and key not in seen:
            seen.add(key)
            result.append(name)
    return result


def _sync_structured_notes(db: Session, fragrance_id: UUID, field_name: str, value: object) -> None:
    pyramid = NOTE_PYRAMIDS.get(field_name)
    if not pyramid:
        return
    names = _note_names(value)
    if not names:
        raise HTTPException(400, "Der gefundene Duftnotenwert enthält keine verwertbaren Noten.")

    db.execute(text(
        "DELETE FROM fragrance_notes WHERE fragrance_id=:fragrance_id AND pyramid=:pyramid"
    ), {"fragrance_id": fragrance_id, "pyramid": pyramid})

    for position, name in enumerate(names):
        note_id = db.execute(text(
            "SELECT id FROM notes WHERE lower(trim(name))=lower(trim(:name)) LIMIT 1"
        ), {"name": name}).scalar()
        if note_id is None:
            note_id = uuid4()
            db.execute(text(
                "INSERT INTO notes(id,name,category) VALUES(:id,:name,'Sonstige')"
            ), {"id": note_id, "name": name})
        db.execute(text("""
            INSERT INTO fragrance_notes(id,fragrance_id,note_id,pyramid,position)
            VALUES(:id,:fragrance_id,:note_id,:pyramid,:position)
            ON CONFLICT(fragrance_id,note_id,pyramid)
            DO UPDATE SET position=EXCLUDED.position
        """), {
            "id": uuid4(),
            "fragrance_id": fragrance_id,
            "note_id": note_id,
            "pyramid": pyramid,
            "position": position,
        })

    column = ALLOWED_FIELDS[field_name]
    db.execute(text(f"UPDATE fragrances SET {column}=:value WHERE id=:id"), {
        "value": ", ".join(names),
        "id": fragrance_id,
    })


@router.post("/findings", status_code=201)
def create_finding(payload: FindingCreate, db: Session = Depends(get_db)):
    _field_column(payload.field_name)
    if not db.execute(text("SELECT 1 FROM fragrances WHERE id=:id"), {"id": payload.fragrance_id}).scalar():
        raise HTTPException(404, "Duft nicht gefunden")
    source_url = _public_url(payload.source_url)
    row = db.execute(text("""
        INSERT INTO enrichment_findings
        (id, fragrance_id, field_name, proposed_value, source_name, source_url, source_excerpt, confidence, status)
        VALUES (:id, :fragrance, :field, CAST(:value AS JSONB), :source, :url, :excerpt, :confidence, 'PENDING')
        ON CONFLICT(fragrance_id, field_name, source_url) DO UPDATE SET
            proposed_value=EXCLUDED.proposed_value, source_name=EXCLUDED.source_name,
            source_excerpt=EXCLUDED.source_excerpt, confidence=EXCLUDED.confidence,
            status='PENDING', updated_at=CURRENT_TIMESTAMP
        RETURNING *
    """), {
        "id": uuid4(), "fragrance": payload.fragrance_id, "field": payload.field_name.strip().lower(),
        "value": json.dumps(payload.proposed_value, ensure_ascii=False), "source": payload.source_name,
        "url": source_url, "excerpt": payload.source_excerpt, "confidence": payload.confidence,
    }).mappings().first()
    db.commit()
    return row


@router.get("/findings")
def list_findings(status: str = "PENDING", db: Session = Depends(get_db)):
    query = """
        SELECT x.*, f.name AS fragrance_name, b.name AS brand_name,
               CASE x.field_name
                 WHEN 'image' THEN to_jsonb(f.image_url)
                 WHEN 'image_url' THEN to_jsonb(f.image_url)
                 WHEN 'year' THEN to_jsonb(f.year)
                 WHEN 'concentration' THEN to_jsonb(f.concentration)
                 WHEN 'perfumer' THEN to_jsonb(f.perfumer)
                 WHEN 'description' THEN to_jsonb(f.description)
                 WHEN 'top_notes' THEN to_jsonb(f.top_notes)
                 WHEN 'heart_notes' THEN to_jsonb(f.heart_notes)
                 WHEN 'base_notes' THEN to_jsonb(f.base_notes)
                 WHEN 'accords' THEN to_jsonb(f.accords)
               END AS current_value
        FROM enrichment_findings x
        JOIN fragrances f ON f.id=x.fragrance_id
        JOIN brands b ON b.id=f.brand_id
    """
    params = {}
    if status != "ALL":
        query += " WHERE x.status=:status"
        params["status"] = status.upper()
    query += " ORDER BY x.confidence DESC, x.created_at DESC"
    return list(db.execute(text(query), params).mappings())


@router.post("/findings/{finding_id}/approve")
def approve_finding(finding_id: UUID, payload: FindingDecision | None = None, db: Session = Depends(get_db)):
    row = _finding(db, finding_id)
    if row["status"] != "PENDING":
        raise HTTPException(409, "Dieser Datenfund wurde bereits bearbeitet.")
    column = _field_column(row["field_name"])
    current = db.execute(text(f"SELECT {column} FROM fragrances WHERE id=:id"), {"id": row["fragrance_id"]}).scalar()
    proposed = row["proposed_value"]
    if current not in (None, "") and str(current).strip() != str(proposed).strip():
        raise HTTPException(409, "Das Zielfeld enthält bereits einen abweichenden Wert. Bitte als Konflikt markieren oder den Duft manuell bearbeiten.")

    if row["field_name"] in NOTE_PYRAMIDS:
        _sync_structured_notes(db, row["fragrance_id"], row["field_name"], proposed)
    else:
        db.execute(text(f"UPDATE fragrances SET {column}=:value WHERE id=:id"), {"value": proposed, "id": row["fragrance_id"]})

    source_id = f"SRC-{uuid4().hex[:12].upper()}"
    db.execute(text("""
        INSERT INTO master_sources
        (id,name,object_type,object_id,source_type,file_or_url,usage_status,trust_status,note)
        VALUES(:id,:name,'FRAGRANCE',:object_id,'DATABASE',:url,'RESTRICTED','REVIEW',:note)
    """), {
        "id": source_id, "name": row["source_name"], "object_id": str(row["fragrance_id"]),
        "url": row["source_url"], "note": f"Übernommenes Feld {row['field_name']}: {row['source_excerpt'] or ''}"[:4000],
    })
    db.execute(text("UPDATE enrichment_findings SET status='APPROVED',decision_note=:note,updated_at=CURRENT_TIMESTAMP WHERE id=:id"), {"id": finding_id, "note": payload.note if payload else None})
    db.commit()
    return {"status": "APPROVED", "field_name": row["field_name"]}


@router.post("/findings/{finding_id}/reject")
def reject_finding(finding_id: UUID, payload: FindingDecision | None = None, db: Session = Depends(get_db)):
    row = _finding(db, finding_id)
    if row["status"] != "PENDING":
        raise HTTPException(409, "Dieser Datenfund wurde bereits bearbeitet.")
    db.execute(text("UPDATE enrichment_findings SET status='REJECTED',decision_note=:note,updated_at=CURRENT_TIMESTAMP WHERE id=:id"), {"id": finding_id, "note": payload.note if payload else None})
    db.commit()
    return {"status": "REJECTED"}


@router.post("/findings/{finding_id}/conflict")
def conflict_finding(finding_id: UUID, payload: FindingDecision | None = None, db: Session = Depends(get_db)):
    row = _finding(db, finding_id)
    if row["status"] != "PENDING":
        raise HTTPException(409, "Dieser Datenfund wurde bereits bearbeitet.")
    db.execute(text("UPDATE enrichment_findings SET status='CONFLICT',decision_note=:note,updated_at=CURRENT_TIMESTAMP WHERE id=:id"), {"id": finding_id, "note": payload.note if payload else None})
    db.commit()
    return {"status": "CONFLICT"}
