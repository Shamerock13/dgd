from __future__ import annotations

import hashlib
import json
import os
import re
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from .research_enrichment import _upsert_finding


MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

RESEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "year": {"type": ["integer", "null"]},
        "concentration": {"type": ["string", "null"]},
        "perfumer": {"type": ["string", "null"]},
        "description": {"type": ["string", "null"]},
        "image": {"type": ["string", "null"]},
        "accords": {"type": "array", "items": {"type": "string"}},
        "top_notes": {"type": "array", "items": {"type": "string"}},
        "heart_notes": {"type": "array", "items": {"type": "string"}},
        "base_notes": {"type": "array", "items": {"type": "string"}},
        "twins": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "alternative": {"type": "string"},
                    "evidence": {"type": "string"},
                    "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
                },
                "required": ["alternative", "evidence", "confidence"],
            },
        },
    },
    "required": [
        "year", "concentration", "perfumer", "description", "image", "accords",
        "top_notes", "heart_notes", "base_notes", "twins",
    ],
}


def gemini_configured() -> bool:
    return bool(os.getenv("GEMINI_API_KEY", "").strip())


def _json_from_text(value: str) -> dict:
    value = value.strip()
    value = re.sub(r"^```(?:json)?\s*", "", value, flags=re.I)
    value = re.sub(r"\s*```$", "", value)
    return json.loads(value)


def _sources(payload: dict) -> list[dict]:
    chunks = payload.get("candidates", [{}])[0].get("groundingMetadata", {}).get("groundingChunks", [])
    result = []
    seen = set()
    for chunk in chunks:
        web = chunk.get("web") or {}
        uri = web.get("uri")
        if uri and uri not in seen:
            seen.add(uri)
            result.append({"name": web.get("title") or urlparse(uri).hostname or "Google Search", "url": uri})
    return result


def _prompt(brand: str, name: str, missing_fields: list[str]) -> str:
    return f"""Research the fragrance {brand} {name} using Google Search.
Never invent facts. Use null or empty arrays when evidence is insufficient.
Focus on these missing fields: {', '.join(missing_fields)}.
Also look for explicitly documented fragrance alternatives, dupes, clones, inspired-by products, or 'smells like' comparisons.

Rules:
- confidence must be 0-100.
- only include twins when a web source explicitly states the comparison.
- prefer official brand pages, then established fragrance databases.
- keep description factual and concise.
"""


async def _ask_gemini(client: httpx.AsyncClient, brand: str, name: str, missing_fields: list[str]) -> tuple[dict, list[dict], dict]:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    response = await client.post(
        API_URL.format(model=MODEL),
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        json={
            "contents": [{"role": "user", "parts": [{"text": _prompt(brand, name, missing_fields)}]}],
            "tools": [{"google_search": {}}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 8192,
                "responseMimeType": "application/json",
                "responseJsonSchema": RESEARCH_SCHEMA,
            },
        },
    )
    response.raise_for_status()
    payload = response.json()
    parts = payload.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    text_value = "".join(part.get("text", "") for part in parts)
    if not text_value:
        raise ValueError("Gemini returned no text response")
    usage = payload.get("usageMetadata") or {}
    return _json_from_text(text_value), _sources(payload), usage


def _allowed_fields(missing: set[str]) -> set[str]:
    allowed = set()
    for field in missing:
        if field == "notes":
            allowed.update({"top_notes", "heart_notes", "base_notes"})
        elif field in {"year", "concentration", "perfumer", "description", "image", "accords"}:
            allowed.add(field)
    return allowed


def _twin_fingerprint(fragrance_id, proposal: str) -> str:
    raw = f"gemini::{fragrance_id}::{proposal.casefold()}".encode("utf-8")
    return f"gemini::{hashlib.sha256(raw).hexdigest()}"


def _insert_twins(db: Session, fragrance: dict, twins: list[dict], source: dict) -> int:
    created = 0
    for twin in twins[:5]:
        proposal = str(twin.get("alternative") or "").strip()
        evidence = str(twin.get("evidence") or "").strip()
        if not proposal or not evidence:
            continue
        fingerprint = _twin_fingerprint(fragrance["fragrance_id"], proposal)
        if db.execute(text("SELECT id FROM twin_research_suggestions WHERE fingerprint=:fp"), {"fp": fingerprint}).scalar():
            continue
        alternative_id = db.execute(text("""
            SELECT f.id FROM fragrances f JOIN brands b ON b.id=f.brand_id
            WHERE lower(b.name || ' ' || f.name)=lower(:proposal) OR lower(f.name)=lower(:proposal) LIMIT 1
        """), {"proposal": proposal}).scalar()
        db.execute(text("""
            INSERT INTO twin_research_suggestions
            (id,original_fragrance_id,alternative_fragrance_id,proposed_alternative,source_name,source_url,
             source_excerpt,evidence_phrase,confidence,status,fingerprint,source_category,source_priority)
            VALUES(:id,:original,:alternative,:proposal,:source,:url,:excerpt,:phrase,:confidence,'PENDING',
                   :fingerprint,'AI_GROUNDED',90)
        """), {
            "id": uuid4(), "original": fragrance["fragrance_id"], "alternative": alternative_id,
            "proposal": proposal, "source": source["name"], "url": source["url"],
            "excerpt": evidence[:1000], "phrase": evidence[:300],
            "confidence": max(0, min(100, int(twin.get("confidence") or 65))), "fingerprint": fingerprint,
        })
        created += 1
    return created


async def run_gemini_research(db: Session, limit: int = 5) -> dict:
    if not gemini_configured():
        return {"provider": "gemini", "configured": False, "errors": 1, "message": "GEMINI_API_KEY is not configured"}

    tasks = list(db.execute(text("""
        SELECT t.fragrance_id,t.missing_fields,f.name,b.name AS brand_name
        FROM enrichment_tasks t
        JOIN fragrances f ON f.id=t.fragrance_id
        JOIN brands b ON b.id=f.brand_id
        WHERE t.status='PENDING'
        ORDER BY t.updated_at,b.name,f.name
        LIMIT :limit
    """), {"limit": max(1, min(limit, 10))}).mappings())

    stats = {
        "provider": "gemini", "configured": True, "model": MODEL, "fragrances_searched": 0,
        "findings_created": 0, "twins_created": 0, "sources_found": 0, "errors": 0,
        "prompt_tokens": 0, "output_tokens": 0,
    }
    timeout = httpx.Timeout(75.0, connect=15.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        for task_row in tasks:
            task = dict(task_row)
            try:
                data, sources, usage = await _ask_gemini(client, task["brand_name"], task["name"], task["missing_fields"] or [])
                primary = sources[0] if sources else {"name": "Gemini mit Google Search", "url": "https://www.google.com/search"}
                source = {"name": primary["name"], "url": primary["url"], "excerpt": f'Gemini research for {task["brand_name"]} {task["name"]}'}
                allowed = _allowed_fields(set(task["missing_fields"] or []))
                findings_created = 0
                for field in allowed:
                    value = data.get(field)
                    if value not in (None, "", []):
                        if _upsert_finding(db, task["fragrance_id"], field, value, source, 85):
                            findings_created += 1
                twins_created = _insert_twins(db, task, data.get("twins") or [], primary)
                db.commit()
                stats["fragrances_searched"] += 1
                stats["sources_found"] += len(sources)
                stats["prompt_tokens"] += int(usage.get("promptTokenCount") or 0)
                stats["output_tokens"] += int(usage.get("candidatesTokenCount") or 0)
                stats["findings_created"] += findings_created
                stats["twins_created"] += twins_created
            except Exception as exc:
                db.rollback()
                stats["errors"] += 1
                stats.setdefault("error_messages", []).append(f'{task["brand_name"]} {task["name"]}: {type(exc).__name__}: {exc}')
    return stats
