from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from .fragrance_dna import FragranceDNAProfile, FragranceDNAValues


SELECT_DNA = text("""
    SELECT fragrance_dna, fragrance_dna_source, fragrance_dna_status,
           fragrance_dna_source_count, fragrance_dna_confidence,
           fragrance_dna_disagreement, fragrance_dna_researched_at,
           personal_fragrance_dna
    FROM fragrances
    WHERE id = :fragrance_id
""")


def _ensure_fragrance(db: Session, fragrance_id: UUID):
    row = db.execute(SELECT_DNA, {"fragrance_id": fragrance_id}).mappings().first()
    if row is None:
        raise LookupError("Duft nicht gefunden")
    return row


def read_fragrance_dna(db: Session, fragrance_id: UUID) -> dict:
    row = _ensure_fragrance(db, fragrance_id)
    values = row["fragrance_dna"]
    if values is None:
        return {
            "values": None,
            "metadata": {
                "source": row["fragrance_dna_source"],
                "status": row["fragrance_dna_status"] or "OPEN",
                "source_count": row["fragrance_dna_source_count"],
                "confidence": row["fragrance_dna_confidence"],
                "disagreement": row["fragrance_dna_disagreement"],
                "researched_at": row["fragrance_dna_researched_at"],
            },
            "personal_values": row["personal_fragrance_dna"],
        }
    return {
        "values": values,
        "metadata": {
            "source": row["fragrance_dna_source"],
            "status": row["fragrance_dna_status"] or "OPEN",
            "source_count": row["fragrance_dna_source_count"],
            "confidence": row["fragrance_dna_confidence"],
            "disagreement": row["fragrance_dna_disagreement"],
            "researched_at": row["fragrance_dna_researched_at"],
        },
        "personal_values": row["personal_fragrance_dna"],
    }


def write_fragrance_dna(db: Session, fragrance_id: UUID, profile: FragranceDNAProfile) -> dict:
    _ensure_fragrance(db, fragrance_id)
    payload = profile.model_dump(mode="json")
    db.execute(text("""
        UPDATE fragrances
        SET fragrance_dna = CAST(:values AS JSONB),
            fragrance_dna_source = :source,
            fragrance_dna_status = :status,
            fragrance_dna_source_count = :source_count,
            fragrance_dna_confidence = :confidence,
            fragrance_dna_disagreement = :disagreement,
            fragrance_dna_researched_at = :researched_at
        WHERE id = :fragrance_id
    """), {
        "fragrance_id": fragrance_id,
        "values": json.dumps(payload["values"], ensure_ascii=False),
        **payload["metadata"],
    })
    db.commit()
    return read_fragrance_dna(db, fragrance_id)


def write_personal_fragrance_dna(
    db: Session,
    fragrance_id: UUID,
    values: FragranceDNAValues,
) -> dict:
    _ensure_fragrance(db, fragrance_id)
    db.execute(text("""
        UPDATE fragrances
        SET personal_fragrance_dna = CAST(:values AS JSONB)
        WHERE id = :fragrance_id
    """), {
        "fragrance_id": fragrance_id,
        "values": values.model_dump_json(exclude_none=True),
    })
    db.commit()
    return read_fragrance_dna(db, fragrance_id)
