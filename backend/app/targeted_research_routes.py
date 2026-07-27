from __future__ import annotations

from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from .data_standards import compact_text
from .database import get_db
from .finding_history import exclusion_prompt, is_known_value, known_finding_values, known_value_count
from .gemini_research import (
    MODEL,
    _allowed_fields,
    _ask_gemini,
    _insert_twins,
    gemini_configured,
)
from .grounding_policy import grounded_twin_counts, usable_grounding_sources
from .research_enrichment import _upsert_finding

router = APIRouter(prefix="/api/enrichment", tags=["targeted-research"])


def _known_twin_names(db: Session, fragrance_id: UUID) -> list[str]:
    return [row[0] for row in db.execute(text("""
        SELECT DISTINCT value FROM (
            SELECT b.name || ' – ' || f.name AS value
            FROM twin_matches tm
            JOIN fragrances f ON f.id=CASE WHEN tm.original_id=:id THEN tm.alternative_id ELSE tm.original_id END
            JOIN brands b ON b.id=f.brand_id
            WHERE tm.original_id=:id OR tm.alternative_id=:id
            UNION
            SELECT proposed_alternative AS value
            FROM twin_research_suggestions
            WHERE original_fragrance_id=:id
              AND status IN ('PENDING','APPROVED','REJECTED','DUPLICATE')
        ) known
        WHERE value IS NOT NULL AND trim(value)<>''
        ORDER BY value
        LIMIT 100
    """), {"id": fragrance_id}).all()]


@router.post("/tasks/{fragrance_id}/research")
async def research_single_fragrance(fragrance_id: UUID, db: Session = Depends(get_db)):
    if not gemini_configured():
        raise HTTPException(503, "Gemini ist nicht konfiguriert.")

    task = db.execute(text("""
        SELECT t.fragrance_id, t.missing_fields, f.name, b.name AS brand_name
        FROM enrichment_tasks t
        JOIN fragrances f ON f.id=t.fragrance_id
        JOIN brands b ON b.id=f.brand_id
        WHERE t.fragrance_id=:fragrance_id AND t.status='PENDING'
        LIMIT 1
    """), {"fragrance_id": fragrance_id}).mappings().first()
    if not task:
        raise HTTPException(404, "Für diesen Duft gibt es keinen offenen Datenauftrag.")

    task = dict(task)
    allowed_fields = _allowed_fields(set(task["missing_fields"] or []))
    known_findings = known_finding_values(db, fragrance_id, allowed_fields)
    known_twins = _known_twin_names(db, fragrance_id)
    exclusion = exclusion_prompt(known_findings)
    if known_twins:
        exclusion += "\nBereits bekannte, geprüfte oder abgelehnte Duftzwillinge – nicht erneut vorschlagen:\n" + "\n".join(f"- {name}" for name in known_twins)
    research_name = f'{task["name"]}{exclusion}'

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(75.0, connect=15.0),
            follow_redirects=True,
        ) as client:
            data, sources, usage = await _ask_gemini(
                client,
                task["brand_name"],
                research_name,
                task["missing_fields"] or [],
            )

        grounded_sources = usable_grounding_sources(sources)
        primary = grounded_sources[0] if grounded_sources else {
            "name": "Gemini mit Google Search",
            "url": "https://www.google.com/search",
        }
        source = {
            "name": primary["name"],
            "url": primary["url"],
            "excerpt": compact_text(
                f'Gezielte Gemini-Recherche für {task["brand_name"]} {task["name"]}',
                500,
            ),
        }

        findings_created = findings_skipped_known = 0
        for field in allowed_fields:
            value = data.get(field)
            if value in (None, "", []):
                continue
            if is_known_value(field, value, known_findings):
                findings_skipped_known += 1
                continue
            if _upsert_finding(db, task["fragrance_id"], field, value, source, 85):
                findings_created += 1

        twins = data.get("twins") or []
        _, twins_blocked_ungrounded = grounded_twin_counts(twins, grounded_sources)
        twins_created = _insert_twins(db, task, twins, grounded_sources[0]) if grounded_sources else 0
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(502, f"Gemini-Recherche fehlgeschlagen: {type(exc).__name__}: {exc}") from exc

    return {
        "provider": "gemini",
        "model": MODEL,
        "fragrance_id": str(fragrance_id),
        "brand_name": task["brand_name"],
        "fragrance_name": task["name"],
        "requested_fields": task["missing_fields"] or [],
        "known_twins_excluded": len(known_twins),
        "known_findings_excluded": known_value_count(known_findings),
        "findings_skipped_known": findings_skipped_known,
        "findings_created": findings_created,
        "twins_created": twins_created,
        "twins_blocked_ungrounded": twins_blocked_ungrounded,
        "sources_found": len(grounded_sources),
        "prompt_tokens": int(usage.get("promptTokenCount") or 0),
        "output_tokens": int(usage.get("candidatesTokenCount") or 0),
    }
