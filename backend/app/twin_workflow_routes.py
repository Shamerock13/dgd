from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from .data_standards import compact_name, compact_text, FIELD_LIMITS, split_brand_fragrance
from .database import get_db

router = APIRouter(prefix="/api/enrichment", tags=["twin-workflow"])


class TwinCreatePayload(BaseModel):
    brand_name: str | None = Field(default=None, max_length=160)
    fragrance_name: str | None = Field(default=None, max_length=200)


def _create_twin_match(db: Session, row, alternative_id: UUID) -> UUID:
    existing = db.execute(text("""
        SELECT id FROM twin_matches WHERE
        (original_id=:original AND alternative_id=:alternative) OR
        (original_id=:alternative AND alternative_id=:original) LIMIT 1
    """), {"original": row["original_fragrance_id"], "alternative": alternative_id}).scalar()
    if existing:
        db.execute(text("""
            UPDATE twin_research_suggestions
            SET status='DUPLICATE',alternative_fragrance_id=:alternative,updated_at=CURRENT_TIMESTAMP
            WHERE id=:id
        """), {"id": row["id"], "alternative": alternative_id})
        db.commit()
        raise HTTPException(409, "Dieses Duftzwilling-Paar existiert bereits.")

    twin_id = uuid4()
    reason = compact_text(
        row.get("comparison_reason") or row.get("source_excerpt") or row.get("evidence_phrase") or "Mögliche Ähnlichkeit laut Webquelle.",
        FIELD_LIMITS["comparison_reason"],
    )
    db.execute(text("""
        INSERT INTO twin_matches(id,original_id,alternative_id,similarity,commonalities,differences,source_note)
        VALUES(:id,:original,:alternative,:similarity,:commonalities,:differences,:source_note)
    """), {
        "id": twin_id,
        "original": row["original_fragrance_id"],
        "alternative": alternative_id,
        "similarity": round(float(row["confidence"] or 0)),
        "commonalities": reason,
        "differences": "Noch redaktionell zu prüfen.",
        "source_note": compact_text(f'{row["source_name"]}: {row["source_url"]}', 2000, sentence_boundary=False),
    })
    db.execute(text("""
        UPDATE twin_research_suggestions
        SET status='APPROVED',alternative_fragrance_id=:alternative,updated_at=CURRENT_TIMESTAMP
        WHERE id=:id
    """), {"id": row["id"], "alternative": alternative_id})
    return twin_id


@router.post("/twin-suggestions/{suggestion_id}/approve-with-create")
def approve_twin_with_create(
    suggestion_id: UUID,
    payload: TwinCreatePayload,
    db: Session = Depends(get_db),
):
    row = db.execute(text("""
        SELECT * FROM twin_research_suggestions
        WHERE id=:id AND status='PENDING' FOR UPDATE
    """), {"id": suggestion_id}).mappings().first()
    if not row:
        raise HTTPException(404, "Offener Duftzwilling-Vorschlag nicht gefunden")

    alternative_id = row["alternative_fragrance_id"]
    created_fragrance = False
    created_brand = False

    if not alternative_id:
        guessed_brand, guessed_name = split_brand_fragrance(row["proposed_alternative"])
        brand_name = compact_name(payload.brand_name or guessed_brand, "brand_name")
        fragrance_name = compact_name(payload.fragrance_name or guessed_name, "fragrance_name")
        if not brand_name or not fragrance_name:
            raise HTTPException(422, "Marke und Duftname müssen vor dem Übernehmen angegeben werden.")

        brand_id = db.execute(text("""
            SELECT id FROM brands WHERE lower(trim(name))=lower(trim(:name)) LIMIT 1
        """), {"name": brand_name}).scalar()
        if not brand_id:
            brand_id = uuid4()
            db.execute(text("""
                INSERT INTO brands(id,name,verification_status,active)
                VALUES(:id,:name,'OPEN',true)
            """), {"id": brand_id, "name": brand_name})
            created_brand = True

        alternative_id = db.execute(text("""
            SELECT f.id FROM fragrances f
            WHERE f.brand_id=:brand AND lower(trim(f.name))=lower(trim(:name)) LIMIT 1
        """), {"brand": brand_id, "name": fragrance_name}).scalar()
        if not alternative_id:
            alternative_id = uuid4()
            db.execute(text("""
                INSERT INTO fragrances(id,name,brand_id,gender,image_status,created_at)
                VALUES(:id,:name,:brand,'Unisex','OPEN',CURRENT_TIMESTAMP)
            """), {"id": alternative_id, "name": fragrance_name, "brand": brand_id})
            db.execute(text("""
                INSERT INTO enrichment_tasks(id,fragrance_id,missing_fields,status)
                VALUES(:id,:fragrance,'["year","concentration","perfumer","description","image","source","notes","accords"]'::jsonb,'PENDING')
                ON CONFLICT(fragrance_id) DO UPDATE SET
                  missing_fields=EXCLUDED.missing_fields,status='PENDING',updated_at=CURRENT_TIMESTAMP
            """), {"id": uuid4(), "fragrance": alternative_id})
            created_fragrance = True

    twin_id = _create_twin_match(db, row, alternative_id)
    db.commit()
    return {
        "status": "APPROVED",
        "twin_id": twin_id,
        "alternative_fragrance_id": alternative_id,
        "created_brand": created_brand,
        "created_fragrance": created_fragrance,
    }
