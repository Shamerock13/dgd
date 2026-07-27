from __future__ import annotations

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from .data_standards import compact_text
from .finding_history import exclusion_prompt, is_known_value, known_finding_values, known_value_count
from .gemini_research import MODEL, _allowed_fields, _ask_gemini, _insert_twins, gemini_configured
from .grounding_policy import grounded_twin_counts, usable_grounding_sources
from .research_enrichment import _upsert_finding


def _known_twin_names(db: Session, fragrance_id) -> list[str]:
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


async def run_smart_gemini_research(db: Session, limit: int = 5) -> dict:
    if not gemini_configured():
        return {"provider": "gemini", "configured": False, "errors": 1, "message": "GEMINI_API_KEY is not configured"}
    tasks = list(db.execute(text("""
        SELECT t.fragrance_id,t.missing_fields,f.name,b.name AS brand_name
        FROM enrichment_tasks t JOIN fragrances f ON f.id=t.fragrance_id JOIN brands b ON b.id=f.brand_id
        WHERE t.status='PENDING' ORDER BY t.updated_at,b.name,f.name LIMIT :limit
    """), {"limit": max(1, min(limit, 10))}).mappings())
    stats = {
        "provider": "gemini", "configured": True, "model": MODEL,
        "fragrances_searched": 0, "findings_created": 0, "findings_skipped_known": 0,
        "known_findings_excluded": 0, "twins_created": 0,
        "twins_blocked_ungrounded": 0, "sources_found": 0,
        "known_twins_excluded": 0, "errors": 0, "prompt_tokens": 0, "output_tokens": 0,
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(75.0, connect=15.0), follow_redirects=True) as client:
        for task_row in tasks:
            task = dict(task_row)
            try:
                allowed_fields = _allowed_fields(set(task["missing_fields"] or []))
                known_findings = known_finding_values(db, task["fragrance_id"], allowed_fields)
                known_twins = _known_twin_names(db, task["fragrance_id"])
                exclusion = exclusion_prompt(known_findings)
                if known_twins:
                    exclusion += "\nBereits bekannte, geprüfte oder abgelehnte Duftzwillinge – nicht erneut vorschlagen:\n" + "\n".join(f"- {name}" for name in known_twins)
                data, sources, usage = await _ask_gemini(client, task["brand_name"], f'{task["name"]}{exclusion}', task["missing_fields"] or [])
                grounded_sources = usable_grounding_sources(sources)
                primary = grounded_sources[0] if grounded_sources else {"name": "Gemini mit Google Search", "url": "https://www.google.com/search"}
                source = {"name": primary["name"], "url": primary["url"], "excerpt": compact_text(f'Gemini-Recherche für {task["brand_name"]} {task["name"]}', 500)}
                findings_created = findings_skipped = 0
                for field in allowed_fields:
                    value = data.get(field)
                    if value in (None, "", []):
                        continue
                    if is_known_value(field, value, known_findings):
                        findings_skipped += 1
                        continue
                    if _upsert_finding(db, task["fragrance_id"], field, value, source, 85):
                        findings_created += 1
                twins = data.get("twins") or []
                _, blocked = grounded_twin_counts(twins, grounded_sources)
                twins_created = _insert_twins(db, task, twins, grounded_sources[0]) if grounded_sources else 0
                db.commit()
                stats["fragrances_searched"] += 1
                stats["sources_found"] += len(grounded_sources)
                stats["known_twins_excluded"] += len(known_twins)
                stats["known_findings_excluded"] += known_value_count(known_findings)
                stats["findings_skipped_known"] += findings_skipped
                stats["prompt_tokens"] += int(usage.get("promptTokenCount") or 0)
                stats["output_tokens"] += int(usage.get("candidatesTokenCount") or 0)
                stats["findings_created"] += findings_created
                stats["twins_created"] += twins_created
                stats["twins_blocked_ungrounded"] += blocked
            except Exception as exc:
                db.rollback()
                stats["errors"] += 1
                stats.setdefault("error_messages", []).append(f'{task["brand_name"]} {task["name"]}: {type(exc).__name__}: {exc}')
    return stats
