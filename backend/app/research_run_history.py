from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

COOLDOWN_MINUTES = 15


def ensure_research_run_table(db: Session) -> None:
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS gemini_research_runs (
            id UUID PRIMARY KEY,
            fragrance_id UUID NOT NULL REFERENCES fragrances(id) ON DELETE CASCADE,
            run_type VARCHAR(40) NOT NULL DEFAULT 'TARGETED',
            status VARCHAR(30) NOT NULL,
            model VARCHAR(120),
            requested_fields JSONB NOT NULL DEFAULT '[]'::jsonb,
            sources_found INTEGER NOT NULL DEFAULT 0,
            findings_created INTEGER NOT NULL DEFAULT 0,
            twins_created INTEGER NOT NULL DEFAULT 0,
            prompt_tokens INTEGER NOT NULL DEFAULT 0,
            output_tokens INTEGER NOT NULL DEFAULT 0,
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.execute(text("CREATE INDEX IF NOT EXISTS ix_gemini_runs_fragrance_created ON gemini_research_runs(fragrance_id, created_at DESC)"))


def latest_successful_run(db: Session, fragrance_id):
    ensure_research_run_table(db)
    return db.execute(text("""
        SELECT *
        FROM gemini_research_runs
        WHERE fragrance_id=:fragrance_id AND status='SUCCESS'
        ORDER BY created_at DESC
        LIMIT 1
    """), {"fragrance_id": fragrance_id}).mappings().first()


def cooldown_remaining_minutes(row) -> int:
    if not row or not row.get("created_at"):
        return 0
    created_at = row["created_at"]
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age_minutes = (datetime.now(timezone.utc) - created_at).total_seconds() / 60
    return max(0, int(COOLDOWN_MINUTES - age_minutes + 0.999))


def record_research_run(
    db: Session,
    *,
    fragrance_id,
    status: str,
    model: str,
    requested_fields: list[str],
    sources_found: int = 0,
    findings_created: int = 0,
    twins_created: int = 0,
    prompt_tokens: int = 0,
    output_tokens: int = 0,
    error_message: str | None = None,
) -> None:
    ensure_research_run_table(db)
    db.execute(text("""
        INSERT INTO gemini_research_runs
        (id, fragrance_id, run_type, status, model, requested_fields, sources_found,
         findings_created, twins_created, prompt_tokens, output_tokens, error_message)
        VALUES(:id, :fragrance_id, 'TARGETED', :status, :model, CAST(:requested_fields AS JSONB),
               :sources_found, :findings_created, :twins_created, :prompt_tokens, :output_tokens, :error_message)
    """), {
        "id": uuid4(),
        "fragrance_id": fragrance_id,
        "status": status,
        "model": model,
        "requested_fields": json.dumps(requested_fields, ensure_ascii=False),
        "sources_found": max(0, int(sources_found or 0)),
        "findings_created": max(0, int(findings_created or 0)),
        "twins_created": max(0, int(twins_created or 0)),
        "prompt_tokens": max(0, int(prompt_tokens or 0)),
        "output_tokens": max(0, int(output_tokens or 0)),
        "error_message": (error_message or "")[:1000] or None,
    })
