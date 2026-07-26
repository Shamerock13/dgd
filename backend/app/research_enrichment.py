from __future__ import annotations

import json
import re
from html import unescape
from urllib.parse import parse_qs, quote_plus, urlparse
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import get_db
from .research_routes import _public_url

router = APIRouter(prefix="/api/enrichment", tags=["enrichment-discovery"])

FIELD_ALIASES = {
    "year": ("release year", "released", "launch year", "erscheinungsjahr", "lanciert", "jahr"),
    "concentration": ("concentration", "eau de parfum", "eau de toilette", "extrait", "parfum", "edp", "edt"),
    "perfumer": ("perfumer", "nose", "parfümeur", "parfumeur", "created by", "komponiert von"),
    "description": ("description", "beschreibung"),
    "image": ("image", "bild"),
    "notes": ("top notes", "heart notes", "base notes", "duftnoten", "kopfnote", "herznote", "basisnote"),
    "accords": ("accords", "akkorde", "main accords"),
}

CONCENTRATIONS = (
    "Extrait de Parfum", "Parfum", "Eau de Parfum", "Eau de Toilette",
    "Eau de Cologne", "Cologne", "EDP", "EDT", "EDC",
)


def _clean(value: object, limit: int = 2000) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        value = ", ".join(str(item) for item in value if item)
    value = unescape(re.sub(r"<[^>]+>", " ", str(value)))
    return re.sub(r"\s+", " ", value).strip()[:limit]


def _search_results(html: str) -> list[dict]:
    links = re.findall(
        r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        html, re.I | re.S,
    )
    snippets = re.findall(
        r'<(?:a|div)[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</(?:a|div)>',
        html, re.I | re.S,
    )
    rows = []
    for index, (href, title) in enumerate(links):
        parsed = urlparse(unescape(href))
        target = parse_qs(parsed.query).get("uddg", [unescape(href)])[0]
        if not target.startswith(("http://", "https://")):
            continue
        rows.append({
            "url": target,
            "title": _clean(title, 500),
            "snippet": _clean(snippets[index] if index < len(snippets) else "", 1500),
        })
    return rows[:6]


def _json_ld(html: str) -> list[dict]:
    blocks = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.I | re.S,
    )
    found: list[dict] = []

    def walk(value):
        if isinstance(value, dict):
            found.append(value)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    for block in blocks:
        try:
            walk(json.loads(unescape(block).strip()))
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
    return found


def _first(mapping_rows: list[dict], *keys: str):
    wanted = {key.casefold() for key in keys}
    for row in mapping_rows:
        for key, value in row.items():
            if str(key).casefold() in wanted and value not in (None, "", []):
                if isinstance(value, dict):
                    value = value.get("name") or value.get("url") or value.get("@id")
                return value
    return None


def _extract(text_value: str, html: str = "") -> dict[str, object]:
    text_value = _clean(text_value + " " + html, 250_000)
    structured = _json_ld(html) if html else []
    result: dict[str, object] = {}

    date_value = _first(structured, "releaseDate", "datePublished", "productionDate")
    year_match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2}|21\d{2})\b", _clean(date_value) or text_value)
    if year_match:
        result["year"] = int(year_match.group(1))

    concentration_pattern = "|".join(re.escape(item) for item in CONCENTRATIONS)
    concentration_match = re.search(rf"\b({concentration_pattern})\b", text_value, re.I)
    if concentration_match:
        value = concentration_match.group(1)
        result["concentration"] = next(
            (item for item in CONCENTRATIONS if item.casefold() == value.casefold()), value
        )

    description = _first(structured, "description")
    if description:
        cleaned = _clean(description, 1800)
        if len(cleaned) >= 40:
            result["description"] = cleaned

    image = _first(structured, "image", "thumbnailUrl", "contentUrl")
    if isinstance(image, list):
        image = image[0] if image else None
    if image and str(image).startswith(("http://", "https://")):
        result["image"] = str(image)[:2000]

    perfumer_match = re.search(
        r"(?:perfumer|nose|parf(?:ü|u)meur|parfumeur|created by|komponiert von)\s*[:\-–]?\s*([A-ZÀ-ÖØ-Ý][\wÀ-ÖØ-öø-ÿ.'-]+(?:\s+[A-ZÀ-ÖØ-Ý][\wÀ-ÖØ-öø-ÿ.'-]+){1,3})",
        text_value, re.I,
    )
    if perfumer_match:
        result["perfumer"] = _clean(perfumer_match.group(1), 160)

    note_patterns = {
        "top_notes": r"(?:top notes?|kopfnoten?)\s*[:\-–]\s*([^.;|]{3,300})",
        "heart_notes": r"(?:heart notes?|middle notes?|herznoten?)\s*[:\-–]\s*([^.;|]{3,300})",
        "base_notes": r"(?:base notes?|basisnoten?)\s*[:\-–]\s*([^.;|]{3,300})",
        "accords": r"(?:main accords?|accords?|akkorde?)\s*[:\-–]\s*([^.;|]{3,300})",
    }
    for field, pattern in note_patterns.items():
        match = re.search(pattern, text_value, re.I)
        if match:
            result[field] = _clean(match.group(1), 500)
    return result


def _profile(host: str, profiles: list[dict]) -> dict | None:
    host = (host or "").casefold().removeprefix("www.")
    for item in profiles:
        domain = str(item["domain"]).casefold().removeprefix("www.")
        if host == domain or host.endswith(f".{domain}"):
            return item
    return None


def _upsert_finding(db: Session, fragrance_id, field: str, value: object, source: dict, confidence: float) -> bool:
    if value in (None, "", []):
        return False
    changed = db.execute(text("""
        INSERT INTO enrichment_findings
        (id,fragrance_id,field_name,proposed_value,source_name,source_url,source_excerpt,confidence,status)
        VALUES(:id,:fragrance,:field,CAST(:value AS JSONB),:source,:url,:excerpt,:confidence,'PENDING')
        ON CONFLICT(fragrance_id,field_name,source_url) DO UPDATE SET
          proposed_value=EXCLUDED.proposed_value,source_name=EXCLUDED.source_name,
          source_excerpt=EXCLUDED.source_excerpt,confidence=EXCLUDED.confidence,
          status=CASE WHEN enrichment_findings.status IN ('APPROVED','REJECTED')
                      THEN enrichment_findings.status ELSE 'PENDING' END,
          updated_at=CURRENT_TIMESTAMP
        RETURNING id
    """), {
        "id": uuid4(), "fragrance": fragrance_id, "field": field,
        "value": json.dumps(value, ensure_ascii=False), "source": source["name"],
        "url": source["url"], "excerpt": source.get("excerpt"), "confidence": confidence,
    }).scalar()
    return bool(changed)


async def discover_findings(db: Session, limit: int = 10) -> dict:
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
    stats = {"fragrances_searched": 0, "pages_fetched": 0, "findings_created": 0, "blocked_results": 0, "errors": 0}
    headers = {"User-Agent": "DGD-EnrichmentResearch/1.0 (+private editorial database)"}

    async with httpx.AsyncClient(timeout=15, follow_redirects=False, headers=headers) as client:
        for task in tasks:
            missing = set(task["missing_fields"] or [])
            terms = sorted({term for field in missing for term in FIELD_ALIASES.get(field, ())})
            query = f'"{task["brand_name"]}" "{task["name"]}" ' + " OR ".join(f'"{term}"' for term in terms[:8])
            try:
                search_url = _public_url(f"https://html.duckduckgo.com/html/?q={quote_plus(query)}")
                response = await client.get(search_url)
                response.raise_for_status()
                stats["fragrances_searched"] += 1
                official_host = (urlparse(task["website_url"]).hostname or "").casefold().removeprefix("www.") if task["website_url"] else ""
                for result in _search_results(response.text[:1_500_000])[:4]:
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

                    # Vollseitenabrufe nur bei offiziellen Domains oder ausdrücklich erlaubten Profilen.
                    may_fetch = official or bool(profile and profile.get("auto_allowed"))
                    if may_fetch:
                        page_url = _public_url(result["url"])
                        page = await client.get(page_url)
                        if page.status_code == 200 and "text/html" in page.headers.get("content-type", ""):
                            stats["pages_fetched"] += 1
                            extracted.update(_extract(f'{result["title"]} {result["snippet"]}', page.text[:1_500_000]))
                    confidence = min(95, 40 + round(priority * 0.4) + (15 if official else 0))
                    allowed = set()
                    for field in missing:
                        if field == "notes":
                            allowed.update({"top_notes", "heart_notes", "base_notes"})
                        elif field in {"year", "concentration", "perfumer", "description", "image", "accords"}:
                            allowed.add(field)
                    for field, value in extracted.items():
                        if field in allowed and _upsert_finding(db, task["fragrance_id"], field, value, source, confidence):
                            stats["findings_created"] += 1
                db.commit()
            except Exception:
                db.rollback()
                stats["errors"] += 1
    return stats


@router.post("/discover-findings")
async def discover_findings_route(
    limit: int = Query(default=10, ge=1, le=30),
    db: Session = Depends(get_db),
):
    return await discover_findings(db, limit)
