from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .import_service import map_rows, validate_fragrance_row, validate_twin_row
from .models import Brand, Fragrance, TwinMatch

SIMILARITY_REVIEW_THRESHOLD = 0.88


def normalize_identity(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.casefold().replace("&", " and ")
    text = re.sub(r"[®™©]", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def identity_similarity(left: Any, right: Any) -> float:
    a, b = normalize_identity(left), normalize_identity(right)
    return SequenceMatcher(None, a, b).ratio() if a and b else 0.0


def _fragrances(db: Session) -> list[Fragrance]:
    return list(db.scalars(
        select(Fragrance).join(Brand).options(joinedload(Fragrance.brand)).order_by(Brand.name, Fragrance.name)
    ).unique())


def _payload(fragrance: Fragrance, score: float, match_type: str) -> dict[str, Any]:
    return {
        "id": str(fragrance.id),
        "brand": fragrance.brand.name,
        "name": fragrance.name,
        "score": round(score, 4),
        "match_type": match_type,
    }


def _visible_rows(rows: list[dict[str, Any]], row_limit: int | None) -> list[dict[str, Any]]:
    return rows if row_limit is None else rows[:row_limit]


def find_candidates(fragrances: list[Fragrance], brand: str | None, name: str | None) -> list[dict[str, Any]]:
    if not brand or not name:
        return []
    exact, normalized, similar = [], [], []
    brand_key, name_key = normalize_identity(brand), normalize_identity(name)
    for fragrance in fragrances:
        db_brand, db_name = fragrance.brand.name, fragrance.name
        if db_brand.casefold() == brand.casefold() and db_name.casefold() == name.casefold():
            exact.append(_payload(fragrance, 1.0, "exact"))
        elif normalize_identity(db_brand) == brand_key and normalize_identity(db_name) == name_key:
            normalized.append(_payload(fragrance, 1.0, "normalized"))
        else:
            brand_score = identity_similarity(brand, db_brand)
            name_score = identity_similarity(name, db_name)
            if brand_score >= 0.9 and name_score >= SIMILARITY_REVIEW_THRESHOLD:
                similar.append(_payload(fragrance, brand_score * 0.35 + name_score * 0.65, "similar"))
    return exact or normalized or sorted(similar, key=lambda row: row["score"], reverse=True)[:5]


def analyze_fragrance_import(
    db: Session,
    rows: list[dict[str, Any]],
    row_limit: int | None = 500,
) -> dict[str, Any]:
    mapped, fragrances = map_rows(rows, "fragrances"), _fragrances(db)
    seen: dict[tuple[str, str], int] = {}
    result, counts = [], {"CREATE": 0, "DUPLICATE": 0, "REVIEW": 0, "BLOCK": 0}
    for raw in mapped:
        parsed, errors = validate_fragrance_row(raw)
        key = (normalize_identity(parsed.get("brand")), normalize_identity(parsed.get("name")))
        duplicate_in_file = bool(all(key) and key in seen)
        first_row = seen.get(key)
        if all(key) and not duplicate_in_file:
            seen[key] = parsed["_row"]
        candidates = find_candidates(fragrances, parsed.get("brand"), parsed.get("name"))
        if errors or duplicate_in_file:
            action = "BLOCK"
            reason = "Validierungsfehler oder doppelte Duftidentität in der Datei."
        elif candidates and candidates[0]["match_type"] in {"exact", "normalized"}:
            action = "DUPLICATE"
            reason = "Vorhandener Duft eindeutig erkannt."
        elif candidates:
            action = "REVIEW"
            reason = "Ähnlicher vorhandener Duft gefunden; manuelle Prüfung erforderlich."
        else:
            action = "CREATE"
            reason = "Kein vorhandener oder ähnlicher Duft gefunden."
        row_errors = list(errors)
        if duplicate_in_file:
            row_errors.append(f"Doppelte Duftidentität; erste Zeile: {first_row}")
        counts[action] += 1
        result.append({
            "row": parsed["_row"],
            "brand": parsed.get("brand"),
            "name": parsed.get("name"),
            "normalized_brand": key[0],
            "normalized_name": key[1],
            "action": action,
            "reason": reason,
            "errors": row_errors,
            "candidates": candidates,
        })
    return {
        "import_type": "fragrances",
        "total_rows": len(result),
        "counts": counts,
        "safe_to_commit": counts["BLOCK"] == 0 and counts["REVIEW"] == 0,
        "rows": _visible_rows(result, row_limit),
        "rows_truncated": row_limit is not None and len(result) > row_limit,
        "rules": {
            "normalized_duplicate": "sicherer Dublettenfund",
            "similar_candidate": "nur Prüfhinweis",
            "similarity_threshold": SIMILARITY_REVIEW_THRESHOLD,
        },
    }


def analyze_twin_import(
    db: Session,
    rows: list[dict[str, Any]],
    row_limit: int | None = 500,
) -> dict[str, Any]:
    mapped, fragrances = map_rows(rows, "twins"), _fragrances(db)
    existing = {(str(row.original_id), str(row.alternative_id)) for row in db.scalars(select(TwinMatch))}
    result, counts = [], {"CREATE": 0, "DUPLICATE": 0, "REVIEW": 0, "BLOCK": 0}
    for raw in mapped:
        parsed, errors = validate_twin_row(raw)
        original = find_candidates(fragrances, parsed.get("original_brand"), parsed.get("original_name"))
        alternative = find_candidates(fragrances, parsed.get("alternative_brand"), parsed.get("alternative_name"))
        resolved_original = original[0] if original and original[0]["match_type"] in {"exact", "normalized"} else None
        resolved_alternative = alternative[0] if alternative and alternative[0]["match_type"] in {"exact", "normalized"} else None
        if not original:
            errors.append("Original-Duft nicht gefunden")
        if not alternative:
            errors.append("Alternative nicht gefunden")
        if errors:
            action, reason = "BLOCK", "Fehler oder ungelöste Duftreferenz."
        elif not resolved_original or not resolved_alternative:
            action, reason = "REVIEW", "Mindestens eine Referenz ist nur ähnlich."
        elif resolved_original["id"] == resolved_alternative["id"]:
            action, reason = "BLOCK", "Original und Alternative sind identisch."
            errors.append("Original und Alternative sind identisch")
        elif (resolved_original["id"], resolved_alternative["id"]) in existing:
            action, reason = "DUPLICATE", "Zuordnung bereits vorhanden."
        else:
            action, reason = "CREATE", "Beide Duftreferenzen sind eindeutig."
        counts[action] += 1
        result.append({
            "row": parsed["_row"],
            "original": f'{parsed.get("original_brand") or ""} – {parsed.get("original_name") or ""}',
            "alternative": f'{parsed.get("alternative_brand") or ""} – {parsed.get("alternative_name") or ""}',
            "action": action,
            "reason": reason,
            "errors": errors,
            "original_candidates": original,
            "alternative_candidates": alternative,
        })
    return {
        "import_type": "twins",
        "total_rows": len(result),
        "counts": counts,
        "safe_to_commit": counts["BLOCK"] == 0 and counts["REVIEW"] == 0,
        "rows": _visible_rows(result, row_limit),
        "rows_truncated": row_limit is not None and len(result) > row_limit,
    }
