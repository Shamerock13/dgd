from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import get_db
from .enrichment_routes import _scan_gaps
from .robust_search_service import (
    _query_variants,
    _search_once,
    discover_findings_robust,
    search_twins_robust,
)

router = APIRouter(prefix="/api/enrichment", tags=["combined-research"])


@router.post("/run")
async def run_combined_research(
    twin_limit: int = Query(default=10, ge=1, le=30),
    finding_limit: int = Query(default=10, ge=1, le=30),
    db: Session = Depends(get_db),
):
    gaps = _scan_gaps(db)
    findings = await discover_findings_robust(db, finding_limit)
    twins = await search_twins_robust(db, twin_limit)
    return {"gaps": gaps, "findings": findings, "twins": twins}


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
