from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import urlparse
from uuid import UUID, uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import get_db
from .gemini_research import API_URL, MODEL, TRANSIENT_STATUSES

router = APIRouter(prefix="/api/performance-research", tags=["performance-research"])

PERFORMANCE_FIELDS = (
    "longevity_min_hours", "longevity_max_hours", "longevity_score", "projection",
    "projection_first_hour", "projection_after_three_hours", "sillage",
    "drydown_strength", "performance_score", "performance_source_count",
    "performance_confidence", "performance_disagreement", "performance_version",
    "performance_production_period",
)

SCORE_FIELDS = {
    "longevity_score", "projection", "projection_first_hour",
    "projection_after_three_hours", "sillage", "drydown_strength", "performance_score",
}
RATIO_FIELDS = {"performance_confidence", "performance_disagreement"}


class PerformanceValues(BaseModel):
    model_config = ConfigDict(extra="forbid")

    longevity_min_hours: float | None = Field(default=None, ge=0, le=72)
    longevity_max_hours: float | None = Field(default=None, ge=0, le=72)
    longevity_score: float | None = Field(default=None, ge=0, le=10)
    projection: float | None = Field(default=None, ge=0, le=10)
    projection_first_hour: float | None = Field(default=None, ge=0, le=10)
    projection_after_three_hours: float | None = Field(default=None, ge=0, le=10)
    sillage: float | None = Field(default=None, ge=0, le=10)
    drydown_strength: float | None = Field(default=None, ge=0, le=10)
    performance_score: float | None = Field(default=None, ge=0, le=10)
    performance_source_count: int | None = Field(default=None, ge=0, le=100)
    performance_confidence: float | None = Field(default=None, ge=0, le=1)
    performance_disagreement: float | None = Field(default=None, ge=0, le=1)
    performance_version: str | None = Field(default=None, max_length=120)
    performance_production_period: str | None = Field(default=None, max_length=120)


class PerformanceReview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: str
    accepted_values: PerformanceValues | None = None
    review_note: str | None = Field(default=None, max_length=2000)


RESEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "values": {
            "type": "object",
            "properties": {
                "longevity_min_hours": {"type": ["number", "null"], "minimum": 0, "maximum": 72},
                "longevity_max_hours": {"type": ["number", "null"], "minimum": 0, "maximum": 72},
                "longevity_score": {"type": ["number", "null"], "minimum": 0, "maximum": 10},
                "projection": {"type": ["number", "null"], "minimum": 0, "maximum": 10},
                "projection_first_hour": {"type": ["number", "null"], "minimum": 0, "maximum": 10},
                "projection_after_three_hours": {"type": ["number", "null"], "minimum": 0, "maximum": 10},
                "sillage": {"type": ["number", "null"], "minimum": 0, "maximum": 10},
                "drydown_strength": {"type": ["number", "null"], "minimum": 0, "maximum": 10},
                "performance_score": {"type": ["number", "null"], "minimum": 0, "maximum": 10},
                "performance_source_count": {"type": ["integer", "null"], "minimum": 0, "maximum": 100},
                "performance_confidence": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
                "performance_disagreement": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
                "performance_version": {"type": ["string", "null"], "maxLength": 120},
                "performance_production_period": {"type": ["string", "null"], "maxLength": 120},
            },
            "required": list(PERFORMANCE_FIELDS),
        },
        "rationale": {"type": "string", "maxLength": 1600},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": ["values", "rationale", "confidence"],
}


def _json_from_text(value: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", value.strip(), flags=re.I)
    return json.loads(cleaned)


def _prompt(brand: str, name: str) -> str:
    return f"""Recherchiere mit Google Search die Performance von {brand} {name}.
Ermittle nur Werte, die durch Herstellerangaben, etablierte Duftdatenbanken oder mehrere belastbare Rezensionen gestützt werden.

Regeln:
- Haltbarkeit als realistischen Stundenbereich angeben.
- Scores von 0 bis 10 nur vergeben, wenn die Quellenlage das trägt.
- Opening, Projektion nach drei Stunden und Drydown nur befüllen, wenn diese Zeitpunkte ausdrücklich beschrieben werden.
- Keine Zwischenwerte erfinden oder aus anderen Feldern mathematisch ableiten.
- Reformulierungen, Batch-Unterschiede und Produktionszeiträume kenntlich machen.
- Unbekannte oder widersprüchliche Werte bleiben null.
- confidence und disagreement liegen zwischen 0 und 1.
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


def _serialize(row) -> dict:
    return dict(row)


@router.get("/proposals")
def list_proposals(status: str = "OPEN", fragrance_id: UUID | None = None, db: Session = Depends(get_db)):
    clauses = ["p.status = :status"] if status != "ALL" else []
    params: dict = {"status": status}
    if fragrance_id:
        clauses.append("p.fragrance_id = :fragrance_id")
        params["fragrance_id"] = fragrance_id
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return list(db.execute(text(f"""
        SELECT p.*, f.name AS fragrance_name, b.name AS brand_name
        FROM performance_research_proposals p
        JOIN fragrances f ON f.id=p.fragrance_id
        JOIN brands b ON b.id=f.brand_id
        {where}
        ORDER BY p.created_at DESC
        LIMIT 500
    """), params).mappings())


@router.post("/research/{fragrance_id}")
async def research_performance(fragrance_id: UUID, db: Session = Depends(get_db)):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(503, "GEMINI_API_KEY ist nicht konfiguriert")

    fragrance = db.execute(text("""
        SELECT f.id, f.name, b.name AS brand_name
        FROM fragrances f JOIN brands b ON b.id=f.brand_id
        WHERE f.id=:id
    """), {"id": fragrance_id}).mappings().first()
    if not fragrance:
        raise HTTPException(404, "Duft nicht gefunden")

    existing = db.execute(text("""
        SELECT id FROM performance_research_proposals
        WHERE fragrance_id=:id AND status='OPEN'
        LIMIT 1
    """), {"id": fragrance_id}).scalar()
    if existing:
        raise HTTPException(409, "Für diesen Duft existiert bereits ein offener Performance-Vorschlag")

    request = {
        "contents": [{"role": "user", "parts": [{"text": _prompt(fragrance["brand_name"], fragrance["name"])}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json",
            "responseJsonSchema": RESEARCH_SCHEMA,
        },
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=15.0), follow_redirects=True) as client:
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
        raise HTTPException(502, "Gemini hat keine auswertbare Antwort geliefert")

    result = _json_from_text(text_value)
    values = PerformanceValues(**(result.get("values") or {})).model_dump(exclude_none=True)
    if not values:
        raise HTTPException(422, "Gemini konnte keine belastbaren Performance-Werte ermitteln")
    if values.get("longevity_min_hours") is not None and values.get("longevity_max_hours") is not None:
        if values["longevity_min_hours"] > values["longevity_max_hours"]:
            raise HTTPException(422, "Ungültiger Haltbarkeitsbereich aus der Recherche")

    sources = _grounding_sources(payload)
    primary = sources[0] if sources else {"name": "Gemini mit Google Search", "url": "https://www.google.com/search"}
    rationale = str(result.get("rationale") or "").strip()[:1600] or None
    confidence = max(0.0, min(1.0, float(result.get("confidence") or 0.5)))
    proposal_id = uuid4()
    db.execute(text("""
        INSERT INTO performance_research_proposals
        (id,fragrance_id,values,source_label,source_url,sources,rationale,confidence,status)
        VALUES(:id,:fragrance_id,CAST(:values AS JSONB),:source_label,:source_url,
               CAST(:sources AS JSONB),:rationale,:confidence,'OPEN')
    """), {
        "id": proposal_id,
        "fragrance_id": fragrance_id,
        "values": json.dumps(values, ensure_ascii=False),
        "source_label": primary["name"],
        "source_url": primary["url"],
        "sources": json.dumps(sources, ensure_ascii=False),
        "rationale": rationale,
        "confidence": confidence,
    })
    db.commit()
    return db.execute(text("SELECT * FROM performance_research_proposals WHERE id=:id"), {"id": proposal_id}).mappings().first()


@router.post("/proposals/{proposal_id}/review")
def review_proposal(proposal_id: UUID, payload: PerformanceReview, db: Session = Depends(get_db)):
    proposal = db.execute(text("SELECT * FROM performance_research_proposals WHERE id=:id FOR UPDATE"), {"id": proposal_id}).mappings().first()
    if not proposal:
        raise HTTPException(404, "Performance-Vorschlag nicht gefunden")
    if proposal["status"] != "OPEN":
        raise HTTPException(409, "Dieser Vorschlag wurde bereits geprüft")

    decision = payload.decision.upper().strip()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if decision == "REJECT":
        db.execute(text("""
            UPDATE performance_research_proposals
            SET status='REJECTED',reviewed_at=:now,review_note=:note
            WHERE id=:id
        """), {"id": proposal_id, "now": now, "note": payload.review_note})
        db.commit()
        return {"status": "REJECTED"}
    if decision != "APPROVE":
        raise HTTPException(400, "Entscheidung muss APPROVE oder REJECT sein")

    accepted = payload.accepted_values.model_dump(exclude_none=True) if payload.accepted_values else dict(proposal["values"] or {})
    if not accepted:
        raise HTTPException(400, "Mindestens ein Wert muss bestätigt werden")
    invalid = set(accepted) - set(PERFORMANCE_FIELDS)
    if invalid:
        raise HTTPException(400, f"Ungültige Performance-Felder: {', '.join(sorted(invalid))}")

    assignments = []
    params = {"fragrance_id": proposal["fragrance_id"]}
    for index, (field, value) in enumerate(accepted.items()):
        key = f"v{index}"
        assignments.append(f"{field}=:{key}")
        params[key] = value
    assignments.extend([
        "performance_status='VERIFIED'",
        "performance_researched_at=:researched_at",
    ])
    params["researched_at"] = now
    db.execute(text(f"UPDATE fragrances SET {', '.join(assignments)} WHERE id=:fragrance_id"), params)
    db.execute(text("""
        UPDATE performance_research_proposals
        SET status='APPROVED',reviewed_at=:now,review_note=:note,accepted_values=CAST(:accepted AS JSONB)
        WHERE id=:id
    """), {
        "id": proposal_id,
        "now": now,
        "note": payload.review_note,
        "accepted": json.dumps(accepted, ensure_ascii=False),
    })
    db.commit()
    return {"status": "APPROVED", "accepted_values": accepted}
