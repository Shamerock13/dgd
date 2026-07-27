import ipaddress
import json
import re
import socket
from html import unescape
from urllib.parse import urlparse
from uuid import UUID, uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from .data_standards import FIELD_LIMITS, compact_name, compact_text, normalize_candidate
from .database import get_db

router = APIRouter(prefix="/api/research", tags=["research"])


class ScanRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2000)
    source_name: str | None = Field(default=None, max_length=300)


class CandidateUpdate(BaseModel):
    brand_name: str = Field(min_length=1, max_length=160)
    fragrance_name: str = Field(min_length=1, max_length=200)
    year: int | None = Field(default=None, ge=1800, le=2200)
    concentration: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=350)
    image_url: str | None = Field(default=None, max_length=2000)


def _public_url(value: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(400, "Nur vollständige HTTP- oder HTTPS-Adressen sind erlaubt.")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, parsed.port or 443)}
    except socket.gaierror as exc:
        raise HTTPException(400, "Die Adresse konnte nicht aufgelöst werden.") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise HTTPException(400, "Interne oder private Netzwerkziele sind nicht erlaubt.")
    return value.strip()


def _clean(value, limit: int = 2000):
    if value is None:
        return None
    if isinstance(value, dict):
        value = value.get("name") or value.get("value")
    if isinstance(value, list):
        value = ", ".join(str(part) for part in value if part)
    cleaned = compact_text(unescape(str(value)), limit)
    return cleaned or None


def _json_ld_candidates(html: str):
    blocks = re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.I | re.S)
    rows = []
    for block in blocks:
        try:
            payload = json.loads(unescape(block.strip()))
        except Exception:
            continue
        stack = payload if isinstance(payload, list) else [payload]
        while stack:
            entry = stack.pop()
            if not isinstance(entry, dict):
                continue
            graph = entry.get("@graph")
            if isinstance(graph, list):
                stack.extend(graph)
            kind = entry.get("@type")
            kinds = set(kind if isinstance(kind, list) else [kind])
            if not kinds.intersection({"Product", "IndividualProduct"}):
                continue
            name = _clean(entry.get("name"), 200)
            brand = _clean(entry.get("brand") or entry.get("manufacturer"), 160)
            if name:
                rows.append(normalize_candidate({
                    "fragrance_name": name,
                    "brand_name": brand or "Unbekannte Marke",
                    "description": _clean(entry.get("description"), FIELD_LIMITS["description"]),
                    "image_url": _clean(entry.get("image"), FIELD_LIMITS["url"]),
                }))
    return rows


def _fallback_candidate(html: str):
    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    description = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', html, re.I | re.S)
    if not title:
        return []
    raw = _clean(title.group(1), 360)
    parts = re.split(r"\s+[|–—-]\s+", raw or "", maxsplit=1)
    return [normalize_candidate({
        "fragrance_name": parts[0],
        "brand_name": parts[1] if len(parts) > 1 else "Unbekannte Marke",
        "description": _clean(description.group(1), FIELD_LIMITS["description"]) if description else None,
        "image_url": None,
    })]


def _duplicate(db: Session, brand: str, name: str):
    return db.execute(text("""
        SELECT f.id::text, b.name AS brand_name, f.name AS fragrance_name
        FROM fragrances f JOIN brands b ON b.id=f.brand_id
        WHERE lower(trim(b.name))=lower(trim(:brand)) AND lower(trim(f.name))=lower(trim(:name))
        LIMIT 1
    """), {"brand": brand, "name": name}).mappings().first()


@router.get("/candidates")
def list_candidates(status: str = "PENDING", db: Session = Depends(get_db)):
    query = "SELECT * FROM research_candidates"
    params = {}
    if status != "ALL":
        query += " WHERE status=:status"
        params["status"] = status
    return list(db.execute(text(query + " ORDER BY created_at DESC"), params).mappings())


@router.post("/scan")
async def scan_page(payload: ScanRequest, db: Session = Depends(get_db)):
    url = _public_url(payload.url)
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15, headers={"User-Agent": "DGD-Research/1.1"}) as client:
            response = await client.get(url)
            response.raise_for_status()
            if "text/html" not in response.headers.get("content-type", ""):
                raise HTTPException(415, "Die Quelle liefert keine HTML-Seite.")
            html = response.text[:2_000_000]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Quelle konnte nicht gelesen werden: {exc}") from exc

    json_rows = _json_ld_candidates(html)
    discovered = json_rows or _fallback_candidate(html)
    created = duplicates = 0
    for raw_row in discovered[:50]:
        row = normalize_candidate(raw_row)
        if not row["fragrance_name"]:
            continue
        duplicate = _duplicate(db, row["brand_name"], row["fragrance_name"])
        fingerprint = f'{row["brand_name"].casefold()}::{row["fragrance_name"].casefold()}::{url}'
        if db.execute(text("SELECT id FROM research_candidates WHERE fingerprint=:fingerprint"), {"fingerprint": fingerprint}).first():
            continue
        db.execute(text("""
            INSERT INTO research_candidates
            (id,fingerprint,source_name,source_url,brand_name,fragrance_name,description,image_url,status,confidence,duplicate_fragrance_id,raw_data,created_at,updated_at)
            VALUES(:id,:fingerprint,:source_name,:source_url,:brand_name,:fragrance_name,:description,:image_url,'PENDING',:confidence,:duplicate_id,CAST(:raw_data AS JSONB),CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
        """), {
            "id": uuid4(), "fingerprint": fingerprint,
            "source_name": compact_text(payload.source_name or urlparse(url).hostname, FIELD_LIMITS["source_name"]),
            "source_url": url[:FIELD_LIMITS["url"]], "brand_name": row["brand_name"], "fragrance_name": row["fragrance_name"],
            "description": row.get("description"), "image_url": row.get("image_url"),
            "confidence": 90 if json_rows else 55, "duplicate_id": UUID(duplicate["id"]) if duplicate else None,
            "raw_data": json.dumps(row, ensure_ascii=False),
        })
        created += 1
        duplicates += 1 if duplicate else 0
    db.commit()
    return {"found": len(discovered), "created": created, "possible_duplicates": duplicates}


@router.put("/candidates/{candidate_id}")
def update_candidate(candidate_id: UUID, payload: CandidateUpdate, db: Session = Depends(get_db)):
    row = normalize_candidate(payload.model_dump())
    result = db.execute(text("""
        UPDATE research_candidates SET brand_name=:brand,fragrance_name=:name,year=:year,
        concentration=:concentration,description=:description,image_url=:image_url,updated_at=CURRENT_TIMESTAMP
        WHERE id=:id AND status='PENDING' RETURNING *
    """), {"id": candidate_id, "brand": row["brand_name"], "name": row["fragrance_name"], "year": payload.year,
           "concentration": row["concentration"], "description": row["description"], "image_url": row["image_url"]}).mappings().first()
    if not result:
        raise HTTPException(404, "Offener Vorschlag nicht gefunden")
    db.commit()
    return result


@router.post("/candidates/{candidate_id}/approve")
def approve_candidate(candidate_id: UUID, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT * FROM research_candidates WHERE id=:id AND status='PENDING' FOR UPDATE"), {"id": candidate_id}).mappings().first()
    if not row:
        raise HTTPException(404, "Offener Vorschlag nicht gefunden")
    normalized = normalize_candidate(dict(row))
    duplicate = _duplicate(db, normalized["brand_name"], normalized["fragrance_name"])
    if duplicate:
        db.execute(text("UPDATE research_candidates SET status='DUPLICATE',duplicate_fragrance_id=:duplicate,updated_at=CURRENT_TIMESTAMP WHERE id=:id"), {"id": candidate_id, "duplicate": UUID(duplicate["id"])})
        db.commit()
        raise HTTPException(409, "Der Duft existiert bereits und wurde als Dublette markiert.")
    brand_id = db.execute(text("SELECT id FROM brands WHERE lower(trim(name))=lower(trim(:name)) LIMIT 1"), {"name": normalized["brand_name"]}).scalar()
    if not brand_id:
        brand_id = uuid4()
        db.execute(text("INSERT INTO brands(id,name,verification_status,active) VALUES(:id,:name,'OPEN',true)"), {"id": brand_id, "name": normalized["brand_name"]})
    fragrance_id = uuid4()
    db.execute(text("""
        INSERT INTO fragrances(id,name,brand_id,year,gender,concentration,description,image_url,image_source_name,image_source_url,image_status,created_at)
        VALUES(:id,:name,:brand_id,:year,'Unisex',:concentration,:description,:image_url,:source_name,:source_url,'OPEN',CURRENT_TIMESTAMP)
    """), {"id": fragrance_id, "name": normalized["fragrance_name"], "brand_id": brand_id, "year": row["year"],
           "concentration": normalized["concentration"], "description": normalized["description"], "image_url": normalized["image_url"],
           "source_name": compact_text(row["source_name"], FIELD_LIMITS["source_name"]), "source_url": row["source_url"][:FIELD_LIMITS["url"]]})
    db.execute(text("UPDATE research_candidates SET status='APPROVED',approved_fragrance_id=:fragrance,updated_at=CURRENT_TIMESTAMP WHERE id=:id"), {"id": candidate_id, "fragrance": fragrance_id})
    db.commit()
    return {"status": "APPROVED", "fragrance_id": fragrance_id}


@router.post("/candidates/{candidate_id}/reject")
def reject_candidate(candidate_id: UUID, db: Session = Depends(get_db)):
    changed = db.execute(text("UPDATE research_candidates SET status='REJECTED',updated_at=CURRENT_TIMESTAMP WHERE id=:id AND status='PENDING'"), {"id": candidate_id}).rowcount
    if not changed:
        raise HTTPException(404, "Offener Vorschlag nicht gefunden")
    db.commit()
    return {"status": "REJECTED"}
