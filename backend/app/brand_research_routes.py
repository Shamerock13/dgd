from __future__ import annotations

import asyncio
import json
import os
from uuid import UUID, uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from .data_standards import compact_name, compact_text
from .database import get_db
from .gemini_research import API_URL, MODEL, TRANSIENT_STATUSES, gemini_configured

router = APIRouter(prefix="/api/enrichment", tags=["brand-research"])

BRAND_SCHEMA = {
    "type": "object",
    "properties": {
        "fragrances": {
            "type": "array",
            "maxItems": 25,
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "maxLength": 200},
                    "year": {"type": ["integer", "null"]},
                    "concentration": {"type": ["string", "null"], "maxLength": 80},
                    "description": {"type": ["string", "null"], "maxLength": 350},
                    "image": {"type": ["string", "null"], "maxLength": 2000},
                    "evidence": {"type": "string", "maxLength": 500},
                    "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
                },
                "required": ["name", "year", "concentration", "description", "image", "evidence", "confidence"],
            },
        }
    },
    "required": ["fragrances"],
}


def _prompt(brand_name: str, known_names: list[str], limit: int) -> str:
    known = "\n".join(f"- {name}" for name in known_names[:300]) or "- keine"
    return f"""Suche mit Google Search nach weiteren Parfüms der Marke {brand_name}.
Liefere höchstens {limit} Düfte, die noch nicht in der folgenden DGD-Liste stehen.

Bereits vorhanden oder bereits vorgeschlagen:
{known}

Regeln:
- Nur echte Düfte dieser Marke aufnehmen, keine Sets, Größenvarianten, Körperpflege oder Raumdüfte.
- Namen nicht übersetzen und exakt wie auf belastbaren Quellen schreiben.
- Bereits vorhandene Namen auch bei kleiner Schreibabweichung nicht erneut liefern.
- Beschreibung sachlich auf Deutsch, maximal 350 Zeichen.
- evidence maximal 500 Zeichen und konkret zur Existenz des Duftes.
- Unbelegte Werte null lassen; nichts erfinden.
- Offizielle Markenseite bevorzugen, danach etablierte Duftdatenbanken oder Händlerseiten.
"""


@router.post("/brands/{brand_id}/research-fragrances")
async def research_brand_fragrances(
    brand_id: UUID,
    limit: int = Query(default=15, ge=1, le=25),
    db: Session = Depends(get_db),
):
    if not gemini_configured():
        raise HTTPException(503, "Gemini ist nicht konfiguriert.")
    brand = db.execute(text("SELECT id,name FROM brands WHERE id=:id"), {"id": brand_id}).mappings().first()
    if not brand:
        raise HTTPException(404, "Marke nicht gefunden")
    known_names = [row[0] for row in db.execute(text("""
        SELECT name FROM fragrances WHERE brand_id=:id
        UNION
        SELECT fragrance_name FROM research_candidates WHERE lower(trim(brand_name))=lower(trim(:brand))
    """), {"id": brand_id, "brand": brand["name"]}).all()]
    request = {
        "contents": [{"role": "user", "parts": [{"text": _prompt(brand["name"], known_names, limit)}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 8192, "responseMimeType": "application/json", "responseJsonSchema": BRAND_SCHEMA},
    }
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(75.0, connect=15.0), follow_redirects=True) as client:
            response = None
            for attempt in range(3):
                response = await client.post(API_URL.format(model=MODEL), headers={"x-goog-api-key": os.getenv("GEMINI_API_KEY", "").strip(), "Content-Type": "application/json"}, json=request)
                if response.status_code not in TRANSIENT_STATUSES or attempt == 2:
                    break
                await asyncio.sleep(2 ** attempt)
            response.raise_for_status()
        payload = response.json()
        parts = payload.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        data = json.loads("".join(part.get("text", "") for part in parts).strip())
    except Exception as exc:
        raise HTTPException(502, f"Markenrecherche fehlgeschlagen: {type(exc).__name__}: {exc}") from exc

    known_keys = {compact_name(name, "fragrance_name").casefold() for name in known_names if name}
    created = skipped = 0
    for item in (data.get("fragrances") or [])[:limit]:
        name = compact_name(item.get("name"), "fragrance_name")
        if not name or name.casefold() in known_keys:
            skipped += 1
            continue
        duplicate = db.execute(text("SELECT id FROM fragrances WHERE brand_id=:brand_id AND lower(trim(name))=lower(trim(:name)) LIMIT 1"), {"brand_id": brand_id, "name": name}).scalar()
        pending = db.execute(text("SELECT id FROM research_candidates WHERE lower(trim(brand_name))=lower(trim(:brand)) AND lower(trim(fragrance_name))=lower(trim(:name)) LIMIT 1"), {"brand": brand["name"], "name": name}).scalar()
        if duplicate or pending:
            skipped += 1
            continue
        fingerprint = f'gemini-brand::{brand_id}::{name.casefold()}'
        db.execute(text("""
            INSERT INTO research_candidates
            (id,fingerprint,source_name,source_url,brand_name,fragrance_name,year,concentration,description,image_url,status,confidence,raw_data,created_at,updated_at)
            VALUES(:id,:fingerprint,'Gemini mit Google Search','https://www.google.com/search',:brand,:name,:year,:concentration,:description,:image,'PENDING',:confidence,CAST(:raw AS JSONB),CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
            ON CONFLICT(fingerprint) DO NOTHING
        """), {
            "id": uuid4(), "fingerprint": fingerprint, "brand": brand["name"], "name": name,
            "year": item.get("year"), "concentration": compact_name(item.get("concentration"), "concentration") or None,
            "description": compact_text(item.get("description"), 350) or None,
            "image": compact_text(item.get("image"), 2000, sentence_boundary=False) or None,
            "confidence": max(0, min(100, int(item.get("confidence") or 70))),
            "raw": json.dumps(item, ensure_ascii=False),
        })
        known_keys.add(name.casefold())
        created += 1
    db.commit()
    usage = payload.get("usageMetadata") or {}
    return {"brand_id": str(brand_id), "brand_name": brand["name"], "created": created, "skipped_existing": skipped, "known_before": len(known_names), "prompt_tokens": int(usage.get("promptTokenCount") or 0), "output_tokens": int(usage.get("candidatesTokenCount") or 0)}