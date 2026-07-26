from __future__ import annotations

import json
import re
from html import unescape
from urllib.parse import parse_qs, quote_plus, urlparse
from uuid import UUID, uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import event, text
from sqlalchemy.orm import Session

from .database import Base, get_db
from .research_routes import _public_url

router = APIRouter(prefix="/api/enrichment", tags=["enrichment"])

DEFAULT_SOURCE_PROFILES = (
    {
        "domain": "parfumo.de",
        "name": "Parfumo",
        "category": "COMMUNITY_DATABASE",
        "priority": 80,
        "auto_allowed": False,
        "blocked": False,
        "note": "Gute Recherche- und Gegenprüfungsquelle. Nur begrenzte Abrufe; direkte Fundseite speichern.",
    },
    {
        "domain": "basenotes.com",
        "name": "Basenotes",
        "category": "COMMUNITY_DATABASE",
        "priority": 65,
        "auto_allowed": False,
        "blocked": False,
        "note": "Community- und Archivquelle. Aussagen als Hinweis behandeln und möglichst gegenprüfen.",
    },
    {
        "domain": "wikiparfum.com",
        "name": "Wikiparfum",
        "category": "REFERENCE_DATABASE",
        "priority": 60,
        "auto_allowed": False,
        "blocked": False,
        "note": "Zusätzliche Referenz für Duftnoten und Zuordnungen; nicht allein automatisch übernehmen.",
    },
    {
        "domain": "fragrantica.com",
        "name": "Fragrantica",
        "category": "BLOCKED_AUTOMATION",
        "priority": 0,
        "auto_allowed": False,
        "blocked": True,
        "note": "Nicht automatisiert abrufen. Aktuelle Nutzungsbedingungen untersagen Scraping und unautorisierte Automation.",
    },
)


@event.listens_for(Base.metadata, "after_create")
def ensure_enrichment_tables(target, connection, **kwargs):
    if connection.dialect.name != "postgresql":
        return
    statements = (
        """CREATE TABLE IF NOT EXISTS enrichment_tasks (
            id UUID PRIMARY KEY,
            fragrance_id UUID NOT NULL REFERENCES fragrances(id) ON DELETE CASCADE,
            missing_fields JSONB NOT NULL,
            status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(fragrance_id)
        )""",
        """CREATE TABLE IF NOT EXISTS dupe_evidence (
            id UUID PRIMARY KEY,
            candidate_id UUID REFERENCES research_candidates(id) ON DELETE CASCADE,
            fragrance_id UUID REFERENCES fragrances(id) ON DELETE CASCADE,
            matched_fragrance_id UUID REFERENCES fragrances(id) ON DELETE SET NULL,
            source_name VARCHAR(300) NOT NULL,
            source_url TEXT NOT NULL,
            found_brand VARCHAR(160), found_name VARCHAR(200), found_year INTEGER,
            found_concentration VARCHAR(80), classification VARCHAR(40) NOT NULL DEFAULT 'POSSIBLE_DUPLICATE',
            reason TEXT, confidence FLOAT NOT NULL DEFAULT 0,
            status VARCHAR(30) NOT NULL DEFAULT 'OPEN', created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS twin_research_suggestions (
            id UUID PRIMARY KEY,
            original_fragrance_id UUID NOT NULL REFERENCES fragrances(id) ON DELETE CASCADE,
            alternative_fragrance_id UUID REFERENCES fragrances(id) ON DELETE SET NULL,
            proposed_alternative VARCHAR(300) NOT NULL,
            source_name VARCHAR(300) NOT NULL,
            source_url TEXT NOT NULL,
            source_excerpt TEXT,
            evidence_phrase VARCHAR(80),
            confidence FLOAT NOT NULL DEFAULT 0,
            status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
            fingerprint VARCHAR(1000) NOT NULL UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS research_source_profiles (
            id UUID PRIMARY KEY,
            domain VARCHAR(300) NOT NULL UNIQUE,
            name VARCHAR(300) NOT NULL,
            category VARCHAR(50) NOT NULL,
            priority INTEGER NOT NULL DEFAULT 50,
            auto_allowed BOOLEAN NOT NULL DEFAULT FALSE,
            blocked BOOLEAN NOT NULL DEFAULT FALSE,
            note TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""",
        "ALTER TABLE twin_research_suggestions ADD COLUMN IF NOT EXISTS source_category VARCHAR(50)",
        "ALTER TABLE twin_research_suggestions ADD COLUMN IF NOT EXISTS source_priority INTEGER",
        "CREATE INDEX IF NOT EXISTS ix_enrichment_tasks_status ON enrichment_tasks(status)",
        "CREATE INDEX IF NOT EXISTS ix_dupe_evidence_candidate ON dupe_evidence(candidate_id)",
        "CREATE INDEX IF NOT EXISTS ix_dupe_evidence_fragrance ON dupe_evidence(fragrance_id)",
        "CREATE INDEX IF NOT EXISTS ix_twin_research_status ON twin_research_suggestions(status)",
        "CREATE INDEX IF NOT EXISTS ix_twin_research_original ON twin_research_suggestions(original_fragrance_id)",
        "CREATE INDEX IF NOT EXISTS ix_source_profiles_priority ON research_source_profiles(priority DESC)",
    )
    for statement in statements:
        connection.execute(text(statement))


class EvidencePayload(BaseModel):
    candidate_id: UUID | None = None
    fragrance_id: UUID | None = None
    matched_fragrance_id: UUID | None = None
    source_name: str = Field(min_length=1, max_length=300)
    source_url: str = Field(min_length=8, max_length=2000)
    found_brand: str | None = Field(default=None, max_length=160)
    found_name: str | None = Field(default=None, max_length=200)
    found_year: int | None = Field(default=None, ge=1800, le=2200)
    found_concentration: str | None = Field(default=None, max_length=80)
    classification: str = Field(default="POSSIBLE_DUPLICATE", max_length=40)
    reason: str | None = None
    confidence: float = Field(default=0, ge=0, le=100)


def _scan_gaps(db: Session):
    rows = list(db.execute(text("""
        SELECT f.id, f.year, f.concentration, f.perfumer, f.description, f.image_url,
               f.top_notes, f.heart_notes, f.base_notes,
               EXISTS(SELECT 1 FROM master_sources s WHERE upper(coalesce(s.object_type,''))='FRAGRANCE' AND s.object_id=f.id::text) AS has_source,
               EXISTS(SELECT 1 FROM fragrance_notes fn WHERE fn.fragrance_id=f.id) AS has_structured_notes
        FROM fragrances f
    """)).mappings())
    created = updated = complete = 0
    for row in rows:
        missing = []
        if row["year"] is None: missing.append("year")
        if not row["concentration"]: missing.append("concentration")
        if not row["perfumer"]: missing.append("perfumer")
        if not row["description"]: missing.append("description")
        if not row["image_url"]: missing.append("image")
        if not row["has_source"]: missing.append("source")
        if not row["has_structured_notes"] and not any((row["top_notes"], row["heart_notes"], row["base_notes"])):
            missing.append("notes")
        existing = db.execute(text("SELECT id FROM enrichment_tasks WHERE fragrance_id=:id"), {"id": row["id"]}).scalar()
        if not missing:
            complete += 1
            if existing:
                db.execute(text("UPDATE enrichment_tasks SET status='COMPLETE',missing_fields='[]'::jsonb,updated_at=CURRENT_TIMESTAMP WHERE fragrance_id=:id"), {"id": row["id"]})
        elif existing:
            db.execute(text("UPDATE enrichment_tasks SET missing_fields=CAST(:fields AS JSONB),status='PENDING',updated_at=CURRENT_TIMESTAMP WHERE fragrance_id=:id"), {"id": row["id"], "fields": json.dumps(missing)})
            updated += 1
        else:
            db.execute(text("INSERT INTO enrichment_tasks(id,fragrance_id,missing_fields,status) VALUES(:id,:fragrance,CAST(:fields AS JSONB),'PENDING')"), {"id": uuid4(), "fragrance": row["id"], "fields": json.dumps(missing)})
            created += 1
    db.commit()
    return {"checked": len(rows), "created": created, "updated": updated, "complete": complete}


@router.post("/scan-gaps")
def scan_gaps(db: Session = Depends(get_db)):
    return _scan_gaps(db)


@router.get("/tasks")
def list_tasks(status: str = "PENDING", db: Session = Depends(get_db)):
    query = """SELECT t.*, f.name AS fragrance_name, b.name AS brand_name
               FROM enrichment_tasks t JOIN fragrances f ON f.id=t.fragrance_id JOIN brands b ON b.id=f.brand_id"""
    params = {}
    if status != "ALL":
        query += " WHERE t.status=:status"
        params["status"] = status
    return list(db.execute(text(query + " ORDER BY b.name,f.name"), params).mappings())


@router.get("/source-profiles")
def list_source_profiles(db: Session = Depends(get_db)):
    return list(db.execute(text("SELECT * FROM research_source_profiles ORDER BY blocked, priority DESC, name")).mappings())


@router.post("/source-profiles/install-defaults")
def install_default_source_profiles(db: Session = Depends(get_db)):
    for profile in DEFAULT_SOURCE_PROFILES:
        db.execute(text("""
            INSERT INTO research_source_profiles
            (id,domain,name,category,priority,auto_allowed,blocked,note)
            VALUES(:id,:domain,:name,:category,:priority,:auto_allowed,:blocked,:note)
            ON CONFLICT(domain) DO UPDATE SET name=EXCLUDED.name,category=EXCLUDED.category,
            priority=EXCLUDED.priority,auto_allowed=EXCLUDED.auto_allowed,blocked=EXCLUDED.blocked,
            note=EXCLUDED.note,updated_at=CURRENT_TIMESTAMP
        """), {"id": uuid4(), **profile})
    db.commit()
    return {"installed": len(DEFAULT_SOURCE_PROFILES)}


def _extract_search_results(html: str):
    pattern = re.compile(r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.I | re.S)
    snippets = re.findall(r'<a[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>|<div[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</div>', html, re.I | re.S)
    clean_snippets = [re.sub(r'<[^>]+>', ' ', a or b) for a, b in snippets]
    rows = []
    for index, (href, title) in enumerate(pattern.findall(html)):
        parsed = urlparse(unescape(href))
        target = parse_qs(parsed.query).get("uddg", [unescape(href)])[0]
        if not target.startswith(("http://", "https://")):
            continue
        rows.append({
            "url": target,
            "title": re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]+>', ' ', title))).strip(),
            "snippet": re.sub(r'\s+', ' ', unescape(clean_snippets[index] if index < len(clean_snippets) else '')).strip(),
        })
    return rows[:8]


def _proposal_from_result(original: str, title: str):
    value = re.sub(r'(?i)\b(dupe|clone|inspired by|alternative(?: to)?|smells like|ähnlich(?: wie)?)\b', ' ', title)
    value = re.sub(re.escape(original), ' ', value, flags=re.I)
    value = re.sub(r'\s+[|–—]\s+.*$', '', value).strip(' -–—|:')
    return value[:300] or title[:300]


def _profile_for_host(host: str, profiles: list[dict]):
    host = (host or "").casefold().removeprefix("www.")
    for profile in profiles:
        domain = str(profile["domain"]).casefold().removeprefix("www.")
        if host == domain or host.endswith(f".{domain}"):
            return profile
    return None


async def _search_twins(db: Session, limit: int):
    fragrances = list(db.execute(text("""
        SELECT f.id, f.name, b.name AS brand_name, b.website_url
        FROM fragrances f JOIN brands b ON b.id=f.brand_id
        WHERE NOT EXISTS (SELECT 1 FROM twin_matches t WHERE t.original_id=f.id OR t.alternative_id=f.id)
        ORDER BY f.created_at NULLS FIRST, b.name, f.name LIMIT :limit
    """), {"limit": max(1, min(limit, 30))}).mappings())
    profiles = [dict(row) for row in db.execute(text("SELECT * FROM research_source_profiles ORDER BY priority DESC")).mappings()]
    created = searched = errors = blocked = 0
    async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers={"User-Agent": "DGD-TwinResearch/1.1"}) as client:
        for fragrance in fragrances:
            query = f'"{fragrance["brand_name"]}" "{fragrance["name"]}" (dupe OR clone OR "inspired by" OR alternative)'
            try:
                search_url = _public_url(f"https://html.duckduckgo.com/html/?q={quote_plus(query)}")
                response = await client.get(search_url)
                response.raise_for_status()
                searched += 1
                official_host = (urlparse(fragrance["website_url"]).hostname or "").casefold().removeprefix("www.") if fragrance["website_url"] else ""
                for result in _extract_search_results(response.text[:1_500_000]):
                    result_host = (urlparse(result["url"]).hostname or "").casefold().removeprefix("www.")
                    profile = _profile_for_host(result_host, profiles)
                    if profile and profile["blocked"]:
                        blocked += 1
                        continue
                    combined = f'{result["title"]} {result["snippet"]}'.casefold()
                    phrases = [phrase for phrase in ("inspired by", "smells like", "alternative", "clone", "dupe", "ähnlich") if phrase in combined]
                    if not phrases:
                        continue
                    proposal = _proposal_from_result(fragrance["name"], result["title"])
                    alternative_id = db.execute(text("""
                        SELECT f.id FROM fragrances f JOIN brands b ON b.id=f.brand_id
                        WHERE lower(b.name || ' ' || f.name)=lower(:proposal) OR lower(f.name)=lower(:proposal) LIMIT 1
                    """), {"proposal": proposal}).scalar()
                    fingerprint = f'{fragrance["id"]}::{result["url"]}'.casefold()
                    if db.execute(text("SELECT id FROM twin_research_suggestions WHERE fingerprint=:fp"), {"fp": fingerprint}).scalar():
                        continue
                    is_official = bool(official_host and (result_host == official_host or result_host.endswith(f".{official_host}")))
                    category = "OFFICIAL_BRAND" if is_official else (profile["category"] if profile else "WEB_RESULT")
                    priority = 100 if is_official else int(profile["priority"] if profile else 40)
                    source_name = fragrance["brand_name"] if is_official else (profile["name"] if profile else result_host or "Webquelle")
                    confidence = min(95, 35 + len(phrases) * 10 + (15 if alternative_id else 0) + round(priority * 0.25))
                    db.execute(text("""
                        INSERT INTO twin_research_suggestions
                        (id,original_fragrance_id,alternative_fragrance_id,proposed_alternative,source_name,source_url,
                         source_excerpt,evidence_phrase,confidence,status,fingerprint,source_category,source_priority)
                        VALUES(:id,:original,:alternative,:proposal,:source,:url,:excerpt,:phrase,:confidence,'PENDING',
                               :fingerprint,:category,:priority)
                    """), {
                        "id": uuid4(), "original": fragrance["id"], "alternative": alternative_id,
                        "proposal": proposal, "source": source_name, "url": result["url"],
                        "excerpt": result["snippet"][:1000], "phrase": ", ".join(phrases),
                        "confidence": confidence, "fingerprint": fingerprint, "category": category,
                        "priority": priority,
                    })
                    created += 1
                db.commit()
            except Exception:
                db.rollback()
                errors += 1
    return {"fragrances_searched": searched, "created": created, "errors": errors, "blocked_results": blocked}


@router.post("/run")
async def run_combined_research(twin_limit: int = 10, db: Session = Depends(get_db)):
    gaps = _scan_gaps(db)
    twins = await _search_twins(db, twin_limit)
    return {"gaps": gaps, "twins": twins}


@router.get("/twin-suggestions")
def twin_suggestions(status: str = "PENDING", db: Session = Depends(get_db)):
    query = """SELECT s.*, f.name AS original_name, b.name AS original_brand,
               af.name AS matched_name, ab.name AS matched_brand
               FROM twin_research_suggestions s
               JOIN fragrances f ON f.id=s.original_fragrance_id JOIN brands b ON b.id=f.brand_id
               LEFT JOIN fragrances af ON af.id=s.alternative_fragrance_id LEFT JOIN brands ab ON ab.id=af.brand_id"""
    params = {}
    if status != "ALL":
        query += " WHERE s.status=:status"
        params["status"] = status
    return list(db.execute(text(query + " ORDER BY s.confidence DESC,s.created_at DESC"), params).mappings())


@router.post("/twin-suggestions/{suggestion_id}/approve")
def approve_twin_suggestion(suggestion_id: UUID, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT * FROM twin_research_suggestions WHERE id=:id AND status='PENDING' FOR UPDATE"), {"id": suggestion_id}).mappings().first()
    if not row:
        raise HTTPException(404, "Offener Duftzwilling-Vorschlag nicht gefunden")
    if not row["alternative_fragrance_id"]:
        raise HTTPException(409, "Die gefundene Alternative muss zuerst als DGD-Duft zugeordnet oder importiert werden.")
    existing = db.execute(text("""
        SELECT id FROM twin_matches WHERE
        (original_id=:original AND alternative_id=:alternative) OR
        (original_id=:alternative AND alternative_id=:original) LIMIT 1
    """), {"original": row["original_fragrance_id"], "alternative": row["alternative_fragrance_id"]}).scalar()
    if existing:
        db.execute(text("UPDATE twin_research_suggestions SET status='DUPLICATE',updated_at=CURRENT_TIMESTAMP WHERE id=:id"), {"id": suggestion_id})
        db.commit()
        raise HTTPException(409, "Dieses Duftzwilling-Paar existiert bereits.")
    twin_id = uuid4()
    db.execute(text("""
        INSERT INTO twin_matches(id,original_id,alternative_id,similarity,commonalities,differences,source_note)
        VALUES(:id,:original,:alternative,:similarity,:commonalities,:differences,:source_note)
    """), {
        "id": twin_id,
        "original": row["original_fragrance_id"],
        "alternative": row["alternative_fragrance_id"],
        "similarity": round(float(row["confidence"] or 0)),
        "commonalities": f'Webhinweis: {row["evidence_phrase"] or "mögliche Ähnlichkeit"}',
        "differences": "Noch redaktionell zu prüfen.",
        "source_note": f'{row["source_name"]}: {row["source_url"]}',
    })
    db.execute(text("UPDATE twin_research_suggestions SET status='APPROVED',updated_at=CURRENT_TIMESTAMP WHERE id=:id"), {"id": suggestion_id})
    db.commit()
    return {"status": "APPROVED", "twin_id": twin_id}


@router.post("/twin-suggestions/{suggestion_id}/reject")
def reject_twin_suggestion(suggestion_id: UUID, db: Session = Depends(get_db)):
    changed = db.execute(text("UPDATE twin_research_suggestions SET status='REJECTED',updated_at=CURRENT_TIMESTAMP WHERE id=:id AND status='PENDING'"), {"id": suggestion_id}).rowcount
    if not changed:
        raise HTTPException(404, "Offener Duftzwilling-Vorschlag nicht gefunden")
    db.commit()
    return {"status": "REJECTED"}


@router.post("/dupe-evidence", status_code=201)
def add_dupe_evidence(payload: EvidencePayload, db: Session = Depends(get_db)):
    if not payload.candidate_id and not payload.fragrance_id:
        raise HTTPException(400, "Kandidat oder Duft muss angegeben werden.")
    classification = payload.classification.upper().strip()
    if classification not in {"LIKELY_SAME", "CONCENTRATION_VARIANT", "FLANKER", "POSSIBLE_DUPLICATE", "SIMILAR_NAME"}:
        raise HTTPException(400, "Ungültige Dublettenklassifikation.")
    row = db.execute(text("""
        INSERT INTO dupe_evidence(id,candidate_id,fragrance_id,matched_fragrance_id,source_name,source_url,
        found_brand,found_name,found_year,found_concentration,classification,reason,confidence,status)
        VALUES(:id,:candidate,:fragrance,:matched,:source_name,:source_url,:brand,:name,:year,:concentration,
        :classification,:reason,:confidence,'OPEN') RETURNING *
    """), {
        "id": uuid4(), "candidate": payload.candidate_id, "fragrance": payload.fragrance_id,
        "matched": payload.matched_fragrance_id, "source_name": payload.source_name,
        "source_url": payload.source_url, "brand": payload.found_brand, "name": payload.found_name,
        "year": payload.found_year, "concentration": payload.found_concentration,
        "classification": classification, "reason": payload.reason, "confidence": payload.confidence,
    }).mappings().first()
    db.commit()
    return row


@router.get("/dupe-evidence")
def list_dupe_evidence(candidate_id: UUID | None = None, fragrance_id: UUID | None = None, db: Session = Depends(get_db)):
    query = "SELECT * FROM dupe_evidence WHERE 1=1"
    params = {}
    if candidate_id:
        query += " AND candidate_id=:candidate"
        params["candidate"] = candidate_id
    if fragrance_id:
        query += " AND fragrance_id=:fragrance"
        params["fragrance"] = fragrance_id
    return list(db.execute(text(query + " ORDER BY created_at DESC"), params).mappings())
