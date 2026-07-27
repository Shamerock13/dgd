import json
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import get_db
from .enrichment_routes import _scan_gaps
from .gemini_research import _clean_list, gemini_configured, run_gemini_research
from .robust_search_service import _query_variants, _search_once

router = APIRouter(prefix="/api/enrichment", tags=["combined-research"])

CLEANUP_FIELDS = ("top_notes", "heart_notes", "base_notes", "accords")


@router.post("/run")
async def run_combined_research(
    twin_limit: int = Query(default=5, ge=1, le=10),
    finding_limit: int = Query(default=5, ge=1, le=10),
    db: Session = Depends(get_db),
):
    gaps = _scan_gaps(db)
    limit = min(twin_limit, finding_limit, 5)
    research = await run_gemini_research(db, limit)
    twins = {
        "provider": "gemini",
        "configured": research.get("configured", False),
        "created": research.get("twins_created", 0),
        "errors": research.get("errors", 0),
    }
    return {"gaps": gaps, "findings": research, "twins": twins}


@router.get("/provider-status")
def provider_status():
    return {
        "provider": "gemini",
        "configured": gemini_configured(),
        "message": "Gemini mit Google Search" if gemini_configured() else "GEMINI_API_KEY fehlt",
    }


def _clean_storage_value(value) -> list[str]:
    return _clean_list(value, translate_notes=True)


def _cleanup_fragrance_fields(db: Session, apply: bool, changes: list[dict]) -> tuple[int, int]:
    checked = changed = 0
    rows = db.execute(text("""
        SELECT id, name, top_notes, heart_notes, base_notes, accords
        FROM fragrances
        WHERE top_notes IS NOT NULL OR heart_notes IS NOT NULL
           OR base_notes IS NOT NULL OR accords IS NOT NULL
        ORDER BY name
    """)).mappings()
    for row in rows:
        checked += 1
        updates = {}
        for field in CLEANUP_FIELDS:
            old = row[field]
            if old in (None, ""):
                continue
            cleaned = ", ".join(_clean_storage_value(old))
            if cleaned != old:
                updates[field] = cleaned or None
                if len(changes) < 50:
                    changes.append({
                        "storage": "fragrances",
                        "id": str(row["id"]),
                        "fragrance": row["name"],
                        "field": field,
                        "before": old,
                        "after": cleaned,
                    })
        if updates:
            changed += 1
            if apply:
                assignments = ", ".join(f"{field}=:{field}" for field in updates)
                db.execute(
                    text(f"UPDATE fragrances SET {assignments} WHERE id=:id"),
                    {"id": row["id"], **updates},
                )
    return checked, changed


def _cleanup_findings(db: Session, apply: bool, changes: list[dict]) -> tuple[int, int]:
    checked = changed = 0
    rows = db.execute(text("""
        SELECT ef.id, ef.field_name, ef.proposed_value, ef.status,
               f.name AS fragrance_name
        FROM enrichment_findings ef
        JOIN fragrances f ON f.id=ef.fragrance_id
        WHERE ef.field_name IN ('top_notes','heart_notes','base_notes','accords')
        ORDER BY ef.updated_at, ef.id
    """)).mappings()
    for row in rows:
        checked += 1
        cleaned = _clean_storage_value(row["proposed_value"])
        current = row["proposed_value"]
        current_list = current if isinstance(current, list) else _clean_list(current)
        if cleaned == current_list:
            continue
        changed += 1
        if len(changes) < 50:
            changes.append({
                "storage": "enrichment_findings",
                "id": str(row["id"]),
                "fragrance": row["fragrance_name"],
                "field": row["field_name"],
                "status": row["status"],
                "before": current,
                "after": cleaned,
            })
        if apply:
            db.execute(text("""
                UPDATE enrichment_findings
                SET proposed_value=CAST(:value AS JSONB), updated_at=CURRENT_TIMESTAMP
                WHERE id=:id
            """), {"id": row["id"], "value": json.dumps(cleaned, ensure_ascii=False)})
    return checked, changed


def _cleanup_note_catalog(db: Session, apply: bool, changes: list[dict]) -> tuple[int, int, int]:
    checked = changed = merged = 0
    rows = list(db.execute(text("SELECT id, name FROM notes ORDER BY name, id")).mappings())
    for row in rows:
        checked += 1
        values = _clean_storage_value(row["name"])
        cleaned = values[0] if values else ""
        if not cleaned or cleaned == row["name"]:
            continue
        target_id = db.execute(text("""
            SELECT id FROM notes
            WHERE id<>:id AND lower(name)=lower(:name)
            LIMIT 1
        """), {"id": row["id"], "name": cleaned}).scalar()
        changed += 1
        action = "merge" if target_id else "rename"
        if target_id:
            merged += 1
        if len(changes) < 50:
            changes.append({
                "storage": "notes",
                "id": str(row["id"]),
                "field": "name",
                "before": row["name"],
                "after": cleaned,
                "action": action,
                "target_id": str(target_id) if target_id else None,
            })
        if not apply:
            continue
        if target_id:
            db.execute(text("""
                UPDATE fragrance_notes source_link
                SET note_id=:target
                WHERE source_link.note_id=:source
                  AND NOT EXISTS (
                    SELECT 1 FROM fragrance_notes target_link
                    WHERE target_link.note_id=:target
                      AND target_link.fragrance_id=source_link.fragrance_id
                      AND target_link.pyramid=source_link.pyramid
                  )
            """), {"source": row["id"], "target": target_id})
            db.execute(text("DELETE FROM fragrance_notes WHERE note_id=:source"), {"source": row["id"]})
            db.execute(text("DELETE FROM notes WHERE id=:source"), {"source": row["id"]})
        else:
            db.execute(text("UPDATE notes SET name=:name WHERE id=:id"), {"id": row["id"], "name": cleaned})
    return checked, changed, merged


@router.post("/cleanup-existing-values")
def cleanup_existing_values(
    dry_run: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    changes: list[dict] = []
    apply = not dry_run
    try:
        fragrance_checked, fragrance_changed = _cleanup_fragrance_fields(db, apply, changes)
        findings_checked, findings_changed = _cleanup_findings(db, apply, changes)
        notes_checked, notes_changed, notes_merged = _cleanup_note_catalog(db, apply, changes)
        if apply:
            db.commit()
        else:
            db.rollback()
    except Exception:
        db.rollback()
        raise
    return {
        "dry_run": dry_run,
        "applied": apply,
        "fragrances": {"checked": fragrance_checked, "changed": fragrance_changed},
        "findings": {"checked": findings_checked, "changed": findings_changed},
        "notes": {"checked": notes_checked, "changed": notes_changed, "merged": notes_merged},
        "total_changes": fragrance_changed + findings_changed + notes_changed,
        "sample_changes": changes,
    }


async def _diagnose(fragrance, db: Session):
    variants = _query_variants(
        fragrance["brand_name"], fragrance["name"], "findings", fragrance["website_url"]
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; DGD-SearchDiagnostic/1.0)",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.7",
    }
    attempts = []
    async with httpx.AsyncClient(timeout=12, follow_redirects=False, headers=headers) as client:
        for label, query in variants:
            try:
                rows, provider, blocked = await _search_once(client, query, 8)
                attempts.append({
                    "variant": label,
                    "query": query,
                    "provider": provider,
                    "blocked": blocked,
                    "result_count": len(rows),
                    "results": rows[:5],
                })
            except Exception as exc:
                attempts.append({
                    "variant": label,
                    "query": query,
                    "provider": "error",
                    "blocked": False,
                    "result_count": 0,
                    "results": [],
                    "error": f"{type(exc).__name__}: {exc}",
                })
    return {
        "fragrance": {
            "id": str(fragrance["id"]),
            "brand_name": fragrance["brand_name"],
            "name": fragrance["name"],
        },
        "attempts": attempts,
        "total_results": sum(item["result_count"] for item in attempts),
        "blocked_attempts": sum(1 for item in attempts if item["blocked"]),
    }


@router.get("/search-diagnostic")
async def search_diagnostic_first(db: Session = Depends(get_db)):
    fragrance = db.execute(text("""
        SELECT f.id, f.name, b.name AS brand_name, b.website_url
        FROM enrichment_tasks t
        JOIN fragrances f ON f.id=t.fragrance_id
        JOIN brands b ON b.id=f.brand_id
        WHERE t.status='PENDING'
        ORDER BY t.updated_at, b.name, f.name
        LIMIT 1
    """)).mappings().first()
    if not fragrance:
        raise HTTPException(404, "Kein offener Datenauftrag gefunden")
    return await _diagnose(fragrance, db)


@router.get("/search-diagnostic/{fragrance_id}")
async def search_diagnostic(fragrance_id: UUID, db: Session = Depends(get_db)):
    fragrance = db.execute(text("""
        SELECT f.id, f.name, b.name AS brand_name, b.website_url
        FROM fragrances f JOIN brands b ON b.id=f.brand_id
        WHERE f.id=:id
    """), {"id": fragrance_id}).mappings().first()
    if not fragrance:
        raise HTTPException(404, "Duft nicht gefunden")
    return await _diagnose(fragrance, db)
