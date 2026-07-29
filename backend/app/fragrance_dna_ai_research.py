from __future__ import annotations

import json
import os
import re
from urllib.parse import urlparse
from uuid import UUID

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from .fragrance_dna_proposal_service import create_proposal
from .fragrance_dna_proposals import FragranceDNAProposalCreate, FragranceDNAValues
from .gemini_research import API_URL, MODEL, TRANSIENT_STATUSES

DNA_DIMENSIONS = (
    "fresh", "citrus", "green", "aquatic", "floral", "fruity",
    "sweet", "gourmand", "spicy", "woody", "smoky", "earthy",
    "resinous", "leathery", "powdery", "animalic",
)

DNA_RESEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "values": {
            "type": "object",
            "properties": {
                key: {"type": ["number", "null"], "minimum": 0, "maximum": 10}
                for key in DNA_DIMENSIONS
            },
            "required": list(DNA_DIMENSIONS),
        },
        "rationale": {"type": "string", "maxLength": 1200},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": ["values", "rationale", "confidence"],
}


def _json_from_text(value: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", value.strip(), flags=re.I)
    return json.loads(cleaned)


def _prompt(brand: str, name: str) -> str:
    return f"""Recherchiere mit Google Search die Duftcharakteristik von {brand} {name}.
Bewerte ausschließlich die 16 vorgegebenen Duft-DNA-Dimensionen auf einer Skala von 0 bis 10.
0 bedeutet nicht wahrnehmbar, 10 bedeutet sehr stark prägend. Nutze null, wenn eine Dimension nicht belastbar bewertbar ist.

Regeln:
- Werte müssen aus belegbaren Duftnoten, Akkorden, Herstellerangaben und seriösen Duftbeschreibungen abgeleitet werden.
- Keine Werte erfinden und nicht jede Dimension zwanghaft füllen.
- Die Begründung soll auf Deutsch knapp erklären, welche belegten Noten oder Akkorde die wichtigsten Bewertungen tragen.
- Offizielle Herstellerseiten bevorzugen; etablierte Duftdatenbanken und seriöse Rezensionen nur ergänzend verwenden.
- Gib ausschließlich JSON entsprechend dem Schema zurück.
"""


def _grounding_sources(payload: dict) -> list[dict]:
    chunks = payload.get("candidates", [{}])[0].get("groundingMetadata", {}).get("groundingChunks", [])
    result, seen = [], set()
    for chunk in chunks:
        web = chunk.get("web") or {}
        uri = web.get("uri")
        if not uri or uri in seen:
            continue
        seen.add(uri)
        result.append({
            "name": str(web.get("title") or urlparse(uri).hostname or "Google Search")[:255],
            "url": uri[:2000],
        })
    return result


def _normalize_values(raw: dict) -> dict[str, float]:
    values: dict[str, float] = {}
    for key in DNA_DIMENSIONS:
        value = raw.get(key)
        if value is None:
            continue
        number = round(max(0.0, min(10.0, float(value))), 1)
        values[key] = number
    if not values:
        raise ValueError("Gemini konnte keine belastbaren Duft-DNA-Werte ermitteln")
    return values


async def research_dna_proposal(db: Session, fragrance_id: UUID) -> dict:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY ist nicht konfiguriert")

    fragrance = db.execute(text("""
        SELECT f.id, f.name, b.name AS brand_name
        FROM fragrances f
        JOIN brands b ON b.id = f.brand_id
        WHERE f.id = :fragrance_id
    """), {"fragrance_id": fragrance_id}).mappings().first()
    if fragrance is None:
        raise LookupError("Duft nicht gefunden")

    existing = db.execute(text("""
        SELECT id FROM fragrance_dna_proposals
        WHERE fragrance_id = :fragrance_id AND status = 'OPEN' AND source = 'AI_ASSISTED'
        ORDER BY created_at DESC LIMIT 1
    """), {"fragrance_id": fragrance_id}).scalar()
    if existing:
        raise ValueError("Für diesen Duft existiert bereits ein offener KI-Vorschlag")

    request = {
        "contents": [{"role": "user", "parts": [{"text": _prompt(fragrance["brand_name"], fragrance["name"])}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json",
            "responseJsonSchema": DNA_RESEARCH_SCHEMA,
        },
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(75.0, connect=15.0), follow_redirects=True) as client:
        response = None
        for attempt in range(3):
            response = await client.post(
                API_URL.format(model=MODEL),
                headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
                json=request,
            )
            if response.status_code not in TRANSIENT_STATUSES or attempt == 2:
                break
        response.raise_for_status()

    payload = response.json()
    parts = payload.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    text_value = "".join(part.get("text", "") for part in parts)
    if not text_value:
        raise ValueError("Gemini hat keine auswertbare Antwort geliefert")

    result = _json_from_text(text_value)
    values = _normalize_values(result.get("values") or {})
    sources = _grounding_sources(payload)
    primary = sources[0] if sources else {
        "name": "Gemini mit Google Search",
        "url": "https://www.google.com/search",
    }
    rationale = str(result.get("rationale") or "").strip()[:1200] or None
    confidence = max(0.0, min(1.0, float(result.get("confidence") or 0.5)))
    if sources:
        source_summary = ", ".join(source["name"] for source in sources[:4])
        rationale = f"{rationale or 'KI-gestützte Duft-DNA-Recherche.'} Quellen: {source_summary}"[:1200]

    proposal = FragranceDNAProposalCreate(
        fragrance_id=fragrance_id,
        values=FragranceDNAValues(**values),
        source="AI_ASSISTED",
        source_label=primary["name"],
        source_url=primary["url"],
        rationale=rationale,
        confidence=confidence,
    )
    return create_proposal(db, proposal)
