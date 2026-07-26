from __future__ import annotations

from urllib.parse import quote_plus, urlparse
from uuid import uuid4

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from .enrichment_routes import _profile_for_host, _proposal_from_result
from .research_enrichment import FIELD_ALIASES, _extract, _profile, _upsert_finding
from .research_routes import _public_url
from .search_result_parser import parse_search_results


async def _search(client: httpx.AsyncClient, query: str, limit: int = 8) -> tuple[list[dict], str]:
    encoded = quote_plus(query)
    endpoints = (
        ("html", f"https://html.duckduckgo.com/html/?q={encoded}"),
        ("lite", f"https://lite.duckduckgo.com/lite/?q={encoded}"),
    )
    for provider, url in endpoints:
        response = await client.get(_public_url(url))
        response.raise_for_status()
        rows = parse_search_results(response.text[:1_500_000], limit)
        if rows:
            return rows, provider
    return [], "none"


async def discover_findings_robust(db: Session, limit: int = 10) -> dict:
    tasks = list(db.execute(text("""
        SELECT t.fragrance_id,t.missing_fields,f.name,b.name AS brand_name,b.website_url
        FROM enrichment_tasks t
        JOIN fragrances f ON f.id=t.fragrance_id
        JOIN brands b ON b.id=f.brand_id
        WHERE t.status='PENDING'
        ORDER BY t.updated_at,b.name,f.name
        LIMIT :limit
    """), {"limit": max(1, min(limit, 30))}).mappings())
    profiles = [dict(row) for row in db.execute(text(
        "SELECT * FROM research_source_profiles ORDER BY priority DESC"
    )).mappings()]
    stats = {
        "fragrances_searched": 0, "search_results": 0, "empty_searches": 0,
        "pages_fetched": 0, "findings_created": 0, "unusable_results": 0,
        "blocked_results": 0, "html_fallbacks": 0, "errors": 0,
    }
    headers = {"User-Agent": "DGD-EnrichmentResearch/1.2 (+private editorial database)"}
    async with httpx.AsyncClient(timeout=18, follow_redirects=False, headers=headers) as client:
        for task in tasks:
            missing = set(task["missing_fields"] or [])
            terms = sorted({term for field in missing for term in FIELD_ALIASES.get(field, ())})
            query = f'"{task["brand_name"]}" "{task["name"]}" ' + " OR ".join(f'"{term}"' for term in terms[:8])
            try:
                results, provider = await _search(client, query, 8)
                stats["fragrances_searched"] += 1
                stats["search_results"] += len(results)
                if provider == "lite":
                    stats["html_fallbacks"] += 1
                if not results:
                    stats["empty_searches"] += 1
                    continue
                official_host = (urlparse(task["website_url"]).hostname or "").casefold().removeprefix("www.") if task["website_url"] else ""
                for result in results[:5]:
                    host = (urlparse(result["url"]).hostname or "").casefold().removeprefix("www.")
                    profile = _profile(host, profiles)
                    if profile and profile.get("blocked"):
                        stats["blocked_results"] += 1
                        continue
                    official = bool(official_host and (host == official_host or host.endswith(f".{official_host}")))
                    source_name = task["brand_name"] if official else (profile["name"] if profile else host or "Webquelle")
                    source = {"name": source_name, "url": result["url"], "excerpt": result["snippet"][:1500]}
                    priority = 100 if official else int(profile["priority"] if profile else 40)
                    extracted = _extract(f'{result["title"]} {result["snippet"]}')
                    may_fetch = official or bool(profile and profile.get("auto_allowed"))
                    if may_fetch:
                        page = await client.get(_public_url(result["url"]))
                        if page.status_code == 200 and "text/html" in page.headers.get("content-type", ""):
                            stats["pages_fetched"] += 1
                            extracted.update(_extract(f'{result["title"]} {result["snippet"]}', page.text[:1_500_000]))
                    allowed = set()
                    for field in missing:
                        if field == "notes":
                            allowed.update({"top_notes", "heart_notes", "base_notes"})
                        elif field in {"year", "concentration", "perfumer", "description", "image", "accords"}:
                            allowed.add(field)
                    usable = 0
                    confidence = min(95, 40 + round(priority * 0.4) + (15 if official else 0))
                    for field, value in extracted.items():
                        if field in allowed and _upsert_finding(db, task["fragrance_id"], field, value, source, confidence):
                            stats["findings_created"] += 1
                            usable += 1
                    if not usable:
                        stats["unusable_results"] += 1
                db.commit()
            except Exception:
                db.rollback()
                stats["errors"] += 1
    return stats


async def search_twins_robust(db: Session, limit: int = 10) -> dict:
    fragrances = list(db.execute(text("""
        SELECT f.id,f.name,b.name AS brand_name,b.website_url
        FROM fragrances f JOIN brands b ON b.id=f.brand_id
        WHERE NOT EXISTS (SELECT 1 FROM twin_matches t WHERE t.original_id=f.id OR t.alternative_id=f.id)
        ORDER BY f.created_at NULLS FIRST,b.name,f.name LIMIT :limit
    """), {"limit": max(1, min(limit, 30))}).mappings())
    profiles = [dict(row) for row in db.execute(text("SELECT * FROM research_source_profiles ORDER BY priority DESC")).mappings()]
    stats = {"fragrances_searched": 0, "search_results": 0, "empty_searches": 0, "created": 0, "unusable_results": 0, "blocked_results": 0, "html_fallbacks": 0, "errors": 0}
    async with httpx.AsyncClient(timeout=18, follow_redirects=False, headers={"User-Agent": "DGD-TwinResearch/1.2"}) as client:
        for fragrance in fragrances:
            query = f'"{fragrance["brand_name"]}" "{fragrance["name"]}" (dupe OR clone OR "inspired by" OR alternative OR "smells like")'
            try:
                results, provider = await _search(client, query, 10)
                stats["fragrances_searched"] += 1
                stats["search_results"] += len(results)
                if provider == "lite":
                    stats["html_fallbacks"] += 1
                if not results:
                    stats["empty_searches"] += 1
                    continue
                official_host = (urlparse(fragrance["website_url"]).hostname or "").casefold().removeprefix("www.") if fragrance["website_url"] else ""
                for result in results:
                    result_host = (urlparse(result["url"]).hostname or "").casefold().removeprefix("www.")
                    profile = _profile_for_host(result_host, profiles)
                    if profile and profile["blocked"]:
                        stats["blocked_results"] += 1
                        continue
                    combined = f'{result["title"]} {result["snippet"]}'.casefold()
                    phrases = [p for p in ("inspired by", "smells like", "alternative", "clone", "dupe", "ähnlich") if p in combined]
                    if not phrases:
                        stats["unusable_results"] += 1
                        continue
                    proposal = _proposal_from_result(fragrance["name"], result["title"])
                    alternative_id = db.execute(text("""
                        SELECT f.id FROM fragrances f JOIN brands b ON b.id=f.brand_id
                        WHERE lower(b.name || ' ' || f.name)=lower(:proposal) OR lower(f.name)=lower(:proposal) LIMIT 1
                    """), {"proposal": proposal}).scalar()
                    fingerprint = f'{fragrance["id"]}::{result["url"]}'.casefold()
                    if db.execute(text("SELECT id FROM twin_research_suggestions WHERE fingerprint=:fp"), {"fp": fingerprint}).scalar():
                        continue
                    official = bool(official_host and (result_host == official_host or result_host.endswith(f".{official_host}")))
                    category = "OFFICIAL_BRAND" if official else (profile["category"] if profile else "WEB_RESULT")
                    priority = 100 if official else int(profile["priority"] if profile else 40)
                    source_name = fragrance["brand_name"] if official else (profile["name"] if profile else result_host or "Webquelle")
                    confidence = min(95, 35 + len(phrases) * 10 + (15 if alternative_id else 0) + round(priority * 0.25))
                    db.execute(text("""
                        INSERT INTO twin_research_suggestions
                        (id,original_fragrance_id,alternative_fragrance_id,proposed_alternative,source_name,source_url,
                         source_excerpt,evidence_phrase,confidence,status,fingerprint,source_category,source_priority)
                        VALUES(:id,:original,:alternative,:proposal,:source,:url,:excerpt,:phrase,:confidence,'PENDING',
                               :fingerprint,:category,:priority)
                    """), {"id": uuid4(), "original": fragrance["id"], "alternative": alternative_id, "proposal": proposal, "source": source_name, "url": result["url"], "excerpt": result["snippet"][:1000], "phrase": ", ".join(phrases), "confidence": confidence, "fingerprint": fingerprint, "category": category, "priority": priority})
                    stats["created"] += 1
                db.commit()
            except Exception:
                db.rollback()
                stats["errors"] += 1
    return stats
