from __future__ import annotations

from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from .data_standards import compact_text
from .database import get_db
from .gemini_research import (
    MODEL,
    _allowed_fields,
    _ask_gemini,
    _insert_twins,
    gemini_configured,
)
from .research_enrichment import _upsert_finding

router = APIRouter(prefix="/api/enrichment", tags=["targeted-research"])


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
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(75.0, connect=15.0),
            follow_redirects=True,
        ) as client:
            data, sources, usage = await _ask_gemini(
                client,
                task["brand_name"],
                task["name"],
                task["missing_fields"] or [],
            )

        primary = sources[0] if sources else {
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

        findings_created = 0
        for field in _allowed_fields(set(task["missing_fields"] or [])):
            value = data.get(field)
            if value not in (None, "", []) and _upsert_finding(
                db, task["fragrance_id"], field, value, source, 85
            ):
                findings_created += 1

        twins_created = _insert_twins(db, task, data.get("twins") or [], primary)
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
        "findings_created": findings_created,
        "twins_created": twins_created,
        "sources_found": len(sources),
        "prompt_tokens": int(usage.get("promptTokenCount") or 0),
        "output_tokens": int(usage.get("candidatesTokenCount") or 0),
    }
