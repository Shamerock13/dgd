from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from .data_standards import FIELD_LIMITS, compact_list, compact_name, compact_text
from .research_enrichment import _upsert_finding

MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
TRANSIENT_STATUSES = {429, 502, 503, 504}

RESEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "year": {"type": ["integer", "null"]},
        "concentration": {"type": ["string", "null"], "maxLength": 80},
        "perfumer": {"type": ["string", "null"], "maxLength": 160},
        "description": {"type": ["string", "null"], "maxLength": 350},
        "image": {"type": ["string", "null"], "maxLength": 2000},
        "accords": {"type": "array", "maxItems": 8, "items": {"type": "string", "maxLength": 80}},
        "top_notes": {"type": "array", "maxItems": 10, "items": {"type": "string", "maxLength": 80}},
        "heart_notes": {"type": "array", "maxItems": 10, "items": {"type": "string", "maxLength": 80}},
        "base_notes": {"type": "array", "maxItems": 10, "items": {"type": "string", "maxLength": 80}},
        "twins": {
            "type": "array", "maxItems": 5,
            "items": {
                "type": "object",
                "properties": {
                    "alternative_brand": {"type": "string", "maxLength": 160},
                    "alternative_name": {"type": "string", "maxLength": 200},
                    "reason": {"type": "string", "maxLength": 240},
                    "evidence": {"type": "string", "maxLength": 500},
                    "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
                },
                "required": ["alternative_brand", "alternative_name", "reason", "evidence", "confidence"],
            },
        },
    },
    "required": ["year", "concentration", "perfumer", "description", "image", "accords", "top_notes", "heart_notes", "base_notes", "twins"],
}

NOTE_TRANSLATIONS = {
    "lemon": "Zitrone", "mandarin orange": "Mandarine", "mandarin": "Mandarine",
    "cardamom": "Kardamom", "pink pepper": "Rosa Pfeffer", "black pepper": "Schwarzer Pfeffer",
    "bergamot": "Bergamotte", "orange blossom": "Orangenblüte", "lavender": "Lavendel",
    "vanilla": "Vanille", "amber": "Amber", "musk": "Moschus", "cedar": "Zedernholz",
    "sandalwood": "Sandelholz", "patchouli": "Patchouli", "rose": "Rose", "jasmine": "Jasmin",
    "apple": "Apfel", "pear": "Birne", "pineapple": "Ananas", "grapefruit": "Grapefruit",
    "cinnamon": "Zimt", "tobacco": "Tabak", "leather": "Leder", "coffee": "Kaffee",
    "coconut": "Kokosnuss", "violet": "Veilchen", "iris": "Iris", "tonka bean": "Tonkabohne",
}


def gemini_configured() -> bool:
    return bool(os.getenv("GEMINI_API_KEY", "").strip())


def _json_from_text(value: str) -> dict:
    value = re.sub(r"^```(?:json)?\s*|\s*```$", "", value.strip(), flags=re.I)
    return json.loads(value)


def _clean_text(value) -> str:
    return compact_text(value, 2000)


def _clean_list(value, translate_notes: bool = False, max_items: int = 10) -> list[str]:
    values = compact_list(value, max_items=max_items, item_limit=FIELD_LIMITS["note"])
    if translate_notes:
        values = [NOTE_TRANSLATIONS.get(item.casefold(), item) for item in values]
    result, seen = [], set()
    for item in values:
        key = item.casefold()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _normalize_research_data(data: dict) -> dict:
    normalized = dict(data)
    normalized["accords"] = _clean_list(data.get("accords"), True, 8)
    for field in ("top_notes", "heart_notes", "base_notes"):
        normalized[field] = _clean_list(data.get(field), True, 10)
    normalized["concentration"] = compact_name(data.get("concentration"), "concentration") or None
    normalized["perfumer"] = compact_name(data.get("perfumer"), "perfumer") or None
    normalized["description"] = compact_text(data.get("description"), FIELD_LIMITS["description"]) or None
    normalized["image"] = compact_text(data.get("image"), FIELD_LIMITS["url"], sentence_boundary=False) or None
    normalized["twins"] = []
    for twin in data.get("twins") or []:
        brand = compact_name(twin.get("alternative_brand"), "brand_name")
        name = compact_name(twin.get("alternative_name"), "fragrance_name")
        reason = compact_text(twin.get("reason"), FIELD_LIMITS["comparison_reason"])
        evidence = compact_text(twin.get("evidence"), FIELD_LIMITS["source_excerpt"])
        if brand and name and reason and evidence:
            normalized["twins"].append({"alternative_brand": brand, "alternative_name": name, "reason": reason, "evidence": evidence, "confidence": max(0, min(100, int(twin.get("confidence") or 65)))})
    return normalized


def _sources(payload: dict) -> list[dict]:
    chunks = payload.get("candidates", [{}])[0].get("groundingMetadata", {}).get("groundingChunks", [])
    result, seen = [], set()
    for chunk in chunks:
        web = chunk.get("web") or {}
        uri = web.get("uri")
        if uri and uri not in seen:
            seen.add(uri)
            result.append({"name": compact_text(web.get("title") or urlparse(uri).hostname or "Google Search", 300), "url": uri[:2000]})
    return result


def _prompt(brand: str, name: str, missing_fields: list[str]) -> str:
    return f"""Recherchiere den Duft {brand} {name} mit Google Search und liefere ausschließlich die Felder des vorgegebenen JSON-Schemas.
Antworte vollständig auf Deutsch. Erfinde nichts; verwende null oder leere Listen, wenn belastbare Belege fehlen.
Besonders gesucht werden: {', '.join(missing_fields)}.

Datenstandard:
- Beschreibung: sachlich, keine Werbung, keine Einleitung, höchstens 350 Zeichen.
- Konzentration: kurze Standardbezeichnung wie Eau de Parfum, Eau de Toilette oder Extrait de Parfum.
- Parfümeur: ausschließlich Name oder Namen, höchstens 160 Zeichen.
- Akkorde: höchstens 8 deutsche Einzelbegriffe.
- Kopf-, Herz- und Basisnoten: jeweils höchstens 10 deutsche Einzelbegriffe.
- Keine Klammern, Anführungszeichen, JSON-Zeichen oder Wiederholungen in Listenwerten.
- Markennamen, Duftnamen und Namen von Parfümeuren nicht übersetzen.
- Duftzwillinge nur bei ausdrücklich belegtem Webvergleich aufnehmen.
- Bei Duftzwillingen Marke und Duftname getrennt ausgeben.
- reason: kurze deutsche Zusammenfassung des Vergleichs, höchstens 240 Zeichen.
- evidence: konkreter deutscher Quellenbeleg, höchstens 500 Zeichen, kein kompletter Webseitenabsatz.
- Offizielle Markenseiten bevorzugen, danach etablierte Duftdatenbanken.
"""


async def _ask_gemini(client: httpx.AsyncClient, brand: str, name: str, missing_fields: list[str]) -> tuple[dict, list[dict], dict]:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    request = {
        "contents": [{"role": "user", "parts": [{"text": _prompt(brand, name, missing_fields)}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 8192, "responseMimeType": "application/json", "responseJsonSchema": RESEARCH_SCHEMA},
    }
    response = None
    for attempt in range(3):
        response = await client.post(API_URL.format(model=MODEL), headers={"x-goog-api-key": api_key, "Content-Type": "application/json"}, json=request)
        if response.status_code not in TRANSIENT_STATUSES or attempt == 2:
            break
        await asyncio.sleep(2 ** attempt)
    response.raise_for_status()
    payload = response.json()
    parts = payload.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    text_value = "".join(part.get("text", "") for part in parts)
    if not text_value:
        raise ValueError("Gemini returned no text response")
    return _normalize_research_data(_json_from_text(text_value)), _sources(payload), payload.get("usageMetadata") or {}


def _allowed_fields(missing: set[str]) -> set[str]:
    allowed = set()
    for field in missing:
        if field == "notes":
            allowed.update({"top_notes", "heart_notes", "base_notes"})
        elif field in {"year", "concentration", "perfumer", "description", "image", "accords"}:
            allowed.add(field)
    return allowed


def _twin_fingerprint(fragrance_id, proposal: str) -> str:
    return f"gemini::{hashlib.sha256(f'gemini::{fragrance_id}::{proposal.casefold()}'.encode()).hexdigest()}"


def _insert_twins(db: Session, fragrance: dict, twins: list[dict], source: dict) -> int:
    created = 0
    for twin in twins[:5]:
        brand, name = twin["alternative_brand"], twin["alternative_name"]
        proposal = compact_text(f"{brand} – {name}", 300, sentence_boundary=False)
        reason, evidence = twin["reason"], twin["evidence"]
        fingerprint = _twin_fingerprint(fragrance["fragrance_id"], proposal)
        if db.execute(text("SELECT id FROM twin_research_suggestions WHERE fingerprint=:fp"), {"fp": fingerprint}).scalar():
            continue
        alternative_id = db.execute(text("""
            SELECT f.id FROM fragrances f JOIN brands b ON b.id=f.brand_id
            WHERE lower(trim(b.name))=lower(trim(:brand)) AND lower(trim(f.name))=lower(trim(:name)) LIMIT 1
        """), {"brand": brand, "name": name}).scalar()
        db.execute(text("""
            INSERT INTO twin_research_suggestions
            (id,original_fragrance_id,alternative_fragrance_id,proposed_alternative,source_name,source_url,
             source_excerpt,evidence_phrase,confidence,status,fingerprint,source_category,source_priority)
            VALUES(:id,:original,:alternative,:proposal,:source,:url,:excerpt,:phrase,:confidence,'PENDING',:fingerprint,'AI_GROUNDED',90)
        """), {"id": uuid4(), "original": fragrance["fragrance_id"], "alternative": alternative_id, "proposal": proposal,
                "source": compact_text(source["name"], 300), "url": source["url"][:2000], "excerpt": evidence[:500],
                "phrase": reason[:80], "confidence": twin["confidence"], "fingerprint": fingerprint})
        created += 1
    return created


async def run_gemini_research(db: Session, limit: int = 5) -> dict:
    if not gemini_configured():
        return {"provider": "gemini", "configured": False, "errors": 1, "message": "GEMINI_API_KEY is not configured"}
    tasks = list(db.execute(text("""
        SELECT t.fragrance_id,t.missing_fields,f.name,b.name AS brand_name
        FROM enrichment_tasks t JOIN fragrances f ON f.id=t.fragrance_id JOIN brands b ON b.id=f.brand_id
        WHERE t.status='PENDING' ORDER BY t.updated_at,b.name,f.name LIMIT :limit
    """), {"limit": max(1, min(limit, 10))}).mappings())
    stats = {"provider": "gemini", "configured": True, "model": MODEL, "fragrances_searched": 0, "findings_created": 0, "twins_created": 0, "sources_found": 0, "errors": 0, "prompt_tokens": 0, "output_tokens": 0}
    async with httpx.AsyncClient(timeout=httpx.Timeout(75.0, connect=15.0), follow_redirects=True) as client:
        for task_row in tasks:
            task = dict(task_row)
            try:
                data, sources, usage = await _ask_gemini(client, task["brand_name"], task["name"], task["missing_fields"] or [])
                primary = sources[0] if sources else {"name": "Gemini mit Google Search", "url": "https://www.google.com/search"}
                source = {"name": primary["name"], "url": primary["url"], "excerpt": compact_text(f'Gemini-Recherche für {task["brand_name"]} {task["name"]}', 500)}
                findings_created = 0
                for field in _allowed_fields(set(task["missing_fields"] or [])):
                    value = data.get(field)
                    if value not in (None, "", []) and _upsert_finding(db, task["fragrance_id"], field, value, source, 85):
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
