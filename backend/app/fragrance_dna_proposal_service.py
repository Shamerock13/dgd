from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from .fragrance_dna_proposals import (
    FragranceDNAProposalCreate,
    FragranceDNAProposalReview,
)


SELECT_PROPOSAL = text("""
    SELECT id, fragrance_id, values, source, source_label, source_url,
           rationale, confidence, status, created_at, reviewed_at, review_note
    FROM fragrance_dna_proposals
    WHERE id = :proposal_id
""")


def _serialize(row) -> dict:
    return {
        "id": row["id"],
        "fragrance_id": row["fragrance_id"],
        "values": row["values"],
        "source": row["source"],
        "source_label": row["source_label"],
        "source_url": row["source_url"],
        "rationale": row["rationale"],
        "confidence": row["confidence"],
        "status": row["status"],
        "created_at": row["created_at"],
        "reviewed_at": row["reviewed_at"],
        "review_note": row["review_note"],
    }


def _get_proposal(db: Session, proposal_id: UUID):
    row = db.execute(SELECT_PROPOSAL, {"proposal_id": proposal_id}).mappings().first()
    if row is None:
        raise LookupError("Duft-DNA-Vorschlag nicht gefunden")
    return row


def create_proposal(db: Session, payload: FragranceDNAProposalCreate) -> dict:
    fragrance_exists = db.execute(
        text("SELECT 1 FROM fragrances WHERE id = :fragrance_id"),
        {"fragrance_id": payload.fragrance_id},
    ).scalar()
    if not fragrance_exists:
        raise LookupError("Duft nicht gefunden")

    proposal_id = uuid4()
    values = payload.values.model_dump(exclude_none=True)
    db.execute(text("""
        INSERT INTO fragrance_dna_proposals (
            id, fragrance_id, values, source, source_label, source_url,
            rationale, confidence, status
        ) VALUES (
            :id, :fragrance_id, CAST(:values AS JSONB), :source, :source_label,
            :source_url, :rationale, :confidence, 'OPEN'
        )
    """), {
        "id": proposal_id,
        "fragrance_id": payload.fragrance_id,
        "values": json.dumps(values, ensure_ascii=False),
        "source": payload.source,
        "source_label": payload.source_label,
        "source_url": payload.source_url,
        "rationale": payload.rationale,
        "confidence": payload.confidence,
    })
    db.commit()
    return _serialize(_get_proposal(db, proposal_id))


def list_proposals(
    db: Session,
    *,
    status: str | None = None,
    fragrance_id: UUID | None = None,
) -> list[dict]:
    clauses = []
    params: dict = {}
    if status:
        clauses.append("status = :status")
        params["status"] = status
    if fragrance_id:
        clauses.append("fragrance_id = :fragrance_id")
        params["fragrance_id"] = fragrance_id
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = db.execute(text(f"""
        SELECT id, fragrance_id, values, source, source_label, source_url,
               rationale, confidence, status, created_at, reviewed_at, review_note
        FROM fragrance_dna_proposals
        {where}
        ORDER BY created_at DESC
        LIMIT 500
    """), params).mappings().all()
    return [_serialize(row) for row in rows]


def review_proposal(
    db: Session,
    proposal_id: UUID,
    payload: FragranceDNAProposalReview,
) -> dict:
    proposal = _get_proposal(db, proposal_id)
    if proposal["status"] != "OPEN":
        raise ValueError("Dieser Vorschlag wurde bereits geprüft")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if payload.decision == "REJECT":
        db.execute(text("""
            UPDATE fragrance_dna_proposals
            SET status = 'REJECTED', reviewed_at = :reviewed_at, review_note = :review_note
            WHERE id = :proposal_id
        """), {
            "proposal_id": proposal_id,
            "reviewed_at": now,
            "review_note": payload.review_note,
        })
        db.commit()
        return _serialize(_get_proposal(db, proposal_id))

    accepted = (
        payload.accepted_values.model_dump(exclude_none=True)
        if payload.accepted_values is not None
        else dict(proposal["values"])
    )
    if not accepted:
        raise ValueError("Für die Freigabe muss mindestens eine Dimension bestätigt werden")

    fragrance = db.execute(text("""
        SELECT fragrance_dna, fragrance_dna_source_count
        FROM fragrances
        WHERE id = :fragrance_id
        FOR UPDATE
    """), {"fragrance_id": proposal["fragrance_id"]}).mappings().first()
    if fragrance is None:
        raise LookupError("Duft nicht gefunden")

    merged = dict(fragrance["fragrance_dna"] or {})
    merged.update(accepted)
    published_source = "RULE_BASED" if proposal["source"] == "RULE_BASED" else "RESEARCH"
    source_count = (fragrance["fragrance_dna_source_count"] or 0) + 1

    db.execute(text("""
        UPDATE fragrances
        SET fragrance_dna = CAST(:values AS JSONB),
            fragrance_dna_source = :source,
            fragrance_dna_status = 'VERIFIED',
            fragrance_dna_source_count = :source_count,
            fragrance_dna_confidence = :confidence,
            fragrance_dna_researched_at = :researched_at
        WHERE id = :fragrance_id
    """), {
        "fragrance_id": proposal["fragrance_id"],
        "values": json.dumps(merged, ensure_ascii=False),
        "source": published_source,
        "source_count": source_count,
        "confidence": proposal["confidence"],
        "researched_at": now,
    })
    db.execute(text("""
        UPDATE fragrance_dna_proposals
        SET status = 'APPROVED', reviewed_at = :reviewed_at, review_note = :review_note
        WHERE id = :proposal_id
    """), {
        "proposal_id": proposal_id,
        "reviewed_at": now,
        "review_note": payload.review_note,
    })
    db.commit()
    return _serialize(_get_proposal(db, proposal_id))
