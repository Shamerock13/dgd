from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from .import_service import (
    get_database_maps,
    get_or_create_brand,
    map_rows,
    replace_notes,
    validate_fragrance_row,
    validate_twin_row,
)
from .models import Fragrance, TwinMatch


class ReviewDecisionError(ValueError):
    pass


def _decision_map(decisions: Any) -> dict[int, dict[str, Any]]:
    if decisions is None:
        return {}
    if not isinstance(decisions, list):
        raise ReviewDecisionError("Die REVIEW-Entscheidungen müssen als Liste übertragen werden.")
    result: dict[int, dict[str, Any]] = {}
    for decision in decisions:
        if not isinstance(decision, dict):
            raise ReviewDecisionError("Eine REVIEW-Entscheidung ist ungültig.")
        try:
            row = int(decision.get("row"))
        except (TypeError, ValueError) as exc:
            raise ReviewDecisionError("Eine REVIEW-Entscheidung enthält keine gültige Zeilennummer.") from exc
        if row in result:
            raise ReviewDecisionError(f"Für Zeile {row} wurden mehrere Entscheidungen übertragen.")
        result[row] = decision
    return result


def _candidate(candidates: list[dict[str, Any]], candidate_id: Any, label: str) -> dict[str, Any]:
    candidate_id = str(candidate_id or "")
    match = next((candidate for candidate in candidates if candidate.get("id") == candidate_id), None)
    if not match:
        raise ReviewDecisionError(f"Der gewählte {label} ist nicht mehr als aktueller Kandidat verfügbar.")
    return match


def _resolved_candidate(
    candidates: list[dict[str, Any]],
    candidate_id: Any,
    label: str,
) -> dict[str, Any]:
    if candidate_id:
        return _candidate(candidates, candidate_id, label)
    exact = next(
        (candidate for candidate in candidates if candidate.get("match_type") in {"exact", "normalized"}),
        None,
    )
    if exact:
        return exact
    raise ReviewDecisionError(f"Für {label} muss ein vorhandener Duft ausgewählt werden.")


def _bind_fragrance_candidate(parsed: dict[str, Any], candidate: dict[str, Any]) -> None:
    parsed["brand"] = candidate["brand"]
    parsed["name"] = candidate["name"]
    parsed["_resolved_existing_id"] = candidate["id"]


def _bind_twin_candidates(
    parsed: dict[str, Any],
    original: dict[str, Any],
    alternative: dict[str, Any],
) -> None:
    if original["id"] == alternative["id"]:
        raise ReviewDecisionError(f"Zeile {parsed['_row']}: Original und Alternative dürfen nicht identisch sein.")
    parsed["original_brand"] = original["brand"]
    parsed["original_name"] = original["name"]
    parsed["alternative_brand"] = alternative["brand"]
    parsed["alternative_name"] = alternative["name"]
    parsed["_resolved_original_id"] = original["id"]
    parsed["_resolved_alternative_id"] = alternative["id"]


def resolve_review_rows(
    rows: list[dict[str, Any]],
    import_type: str,
    quality: dict[str, Any],
    decisions: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    decision_map = _decision_map(decisions)
    quality_rows = {int(row["row"]): row for row in quality.get("rows") or []}
    review_rows = {row_number for row_number, row in quality_rows.items() if row.get("action") == "REVIEW"}
    block_rows = sorted(row_number for row_number, row in quality_rows.items() if row.get("action") == "BLOCK")

    if block_rows:
        raise ReviewDecisionError(
            f"Blockierte Zeilen können nicht manuell freigegeben werden: {', '.join(map(str, block_rows[:20]))}"
        )

    unknown = sorted(set(decision_map) - review_rows)
    if unknown:
        raise ReviewDecisionError(
            f"Entscheidungen wurden für Zeilen ohne aktuellen REVIEW-Status übertragen: {', '.join(map(str, unknown[:20]))}"
        )

    missing = sorted(review_rows - set(decision_map))
    if missing:
        raise ReviewDecisionError(
            f"Für folgende REVIEW-Zeilen fehlt eine Entscheidung: {', '.join(map(str, missing[:20]))}"
        )

    mapped = map_rows(rows, import_type)
    resolved: list[dict[str, Any]] = []
    report: list[dict[str, Any]] = []
    excluded = 0

    for raw in mapped:
        row_number = int(raw["_row"])
        quality_row = quality_rows.get(row_number)
        if not quality_row:
            raise ReviewDecisionError(f"Zeile {row_number} konnte in der aktuellen Qualitätsprüfung nicht gefunden werden.")

        if import_type == "fragrances":
            parsed, errors = validate_fragrance_row(raw)
        else:
            parsed, errors = validate_twin_row(raw)
        if errors:
            raise ReviewDecisionError(f"Zeile {row_number} enthält weiterhin Validierungsfehler.")

        if quality_row.get("action") != "REVIEW":
            if import_type == "fragrances" and quality_row.get("action") == "DUPLICATE":
                candidate = _resolved_candidate(quality_row.get("candidates") or [], None, "Duft")
                _bind_fragrance_candidate(parsed, candidate)
            elif import_type == "twins":
                original = _resolved_candidate(quality_row.get("original_candidates") or [], None, "Original")
                alternative = _resolved_candidate(quality_row.get("alternative_candidates") or [], None, "Alternative")
                _bind_twin_candidates(parsed, original, alternative)
            resolved.append(parsed)
            continue

        decision = decision_map[row_number]
        choice = str(decision.get("choice") or "")

        if choice == "exclude":
            excluded += 1
            report.append({"row": row_number, "choice": "exclude", "summary": "Zeile ausgeschlossen"})
            continue

        if import_type == "fragrances":
            if choice == "create":
                resolved.append(parsed)
                report.append({
                    "row": row_number,
                    "choice": "create",
                    "summary": f'{parsed["brand"]} – {parsed["name"]} als neuen Duft anlegen',
                })
                continue
            if choice != "use_existing":
                raise ReviewDecisionError(f"Für Zeile {row_number} wurde keine gültige Entscheidung gewählt.")
            candidate = _candidate(quality_row.get("candidates") or [], decision.get("candidate_id"), "Duft")
            _bind_fragrance_candidate(parsed, candidate)
            resolved.append(parsed)
            report.append({
                "row": row_number,
                "choice": "use_existing",
                "candidate_id": candidate["id"],
                "summary": f'{candidate["brand"]} – {candidate["name"]} verwenden',
            })
            continue

        if choice != "use_candidates":
            raise ReviewDecisionError(f"Für Zeile {row_number} muss die Zuordnung verwendet oder ausgeschlossen werden.")
        original = _resolved_candidate(
            quality_row.get("original_candidates") or [],
            decision.get("original_id"),
            "Original",
        )
        alternative = _resolved_candidate(
            quality_row.get("alternative_candidates") or [],
            decision.get("alternative_id"),
            "Alternative",
        )
        _bind_twin_candidates(parsed, original, alternative)
        resolved.append(parsed)
        report.append({
            "row": row_number,
            "choice": "use_candidates",
            "original_id": original["id"],
            "alternative_id": alternative["id"],
            "summary": f'{original["brand"]} – {original["name"]} → {alternative["brand"]} – {alternative["name"]}',
        })

    _validate_resolved_duplicates(resolved, import_type)
    return resolved, report, excluded


def _validate_resolved_duplicates(rows: list[dict[str, Any]], import_type: str) -> None:
    seen: dict[tuple[str, str], int] = {}
    for row in rows:
        if import_type == "fragrances":
            key = (str(row.get("brand") or "").casefold(), str(row.get("name") or "").casefold())
        else:
            key = (
                str(row.get("_resolved_original_id") or f'{row.get("original_brand")}::{row.get("original_name")}').casefold(),
                str(row.get("_resolved_alternative_id") or f'{row.get("alternative_brand")}::{row.get("alternative_name")}').casefold(),
            )
        first_row = seen.get(key)
        if first_row is not None:
            raise ReviewDecisionError(
                f"Die Entscheidungen führen Zeile {row['_row']} und Zeile {first_row} auf dieselbe Identität zusammen."
            )
        seen[key] = int(row["_row"])


def apply_resolved_import(
    db: Session,
    rows: list[dict[str, Any]],
    import_type: str,
    duplicate_mode: str,
) -> dict[str, Any]:
    if duplicate_mode not in {"skip", "update"}:
        raise ReviewDecisionError("Ungültiger Dublettenmodus.")
    if import_type == "fragrances":
        return _apply_fragrances(db, rows, duplicate_mode)
    return _apply_twins(db, rows, duplicate_mode)


def _apply_fragrances(db: Session, rows: list[dict[str, Any]], duplicate_mode: str) -> dict[str, Any]:
    brand_map, note_map, fragrance_map = get_database_maps(db)
    created = updated = skipped = failed = 0
    messages: list[dict[str, Any]] = []

    for parsed in rows:
        key = (parsed["brand"].casefold(), parsed["name"].casefold())
        existing = None
        if parsed.get("_resolved_existing_id"):
            existing = db.get(Fragrance, UUID(parsed["_resolved_existing_id"]))
            if not existing:
                raise ReviewDecisionError(f"Zeile {parsed['_row']}: Der bestätigte Duft existiert nicht mehr.")
        else:
            existing = fragrance_map.get(key)

        if existing and duplicate_mode == "skip":
            skipped += 1
            continue

        brand = existing.brand if existing else get_or_create_brand(db, brand_map, parsed["brand"])
        if existing:
            fragrance = existing
            updated += 1
        else:
            fragrance = Fragrance(name=parsed["name"], brand_id=brand.id, gender=parsed["gender"])
            db.add(fragrance)
            db.flush()
            fragrance.brand = brand
            fragrance_map[key] = fragrance
            created += 1

        for field in [
            "year", "gender", "concentration", "perfumer", "price_eur",
            "image_url", "image_source_name", "image_source_url",
            "image_usage_note", "image_status", "description", "accords",
            "longevity", "projection", "sweetness", "freshness",
        ]:
            value = parsed[field]
            if value is not None:
                setattr(fragrance, field, value)
        replace_notes(db, fragrance, parsed, note_map)
        messages.append({"row": parsed["_row"], "fragrance_id": str(fragrance.id)})

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "failed": failed,
        "messages": messages[:100],
    }


def _apply_twins(db: Session, rows: list[dict[str, Any]], duplicate_mode: str) -> dict[str, Any]:
    _, _, fragrance_map = get_database_maps(db)
    existing_map = {
        (row.original_id, row.alternative_id): row
        for row in db.scalars(select(TwinMatch)).all()
    }
    created = updated = skipped = failed = 0
    messages: list[dict[str, Any]] = []

    for parsed in rows:
        if parsed.get("_resolved_original_id"):
            original = db.get(Fragrance, UUID(parsed["_resolved_original_id"]))
        else:
            original = fragrance_map.get((parsed["original_brand"].casefold(), parsed["original_name"].casefold()))
        if parsed.get("_resolved_alternative_id"):
            alternative = db.get(Fragrance, UUID(parsed["_resolved_alternative_id"]))
        else:
            alternative = fragrance_map.get((parsed["alternative_brand"].casefold(), parsed["alternative_name"].casefold()))
        if not original or not alternative:
            raise ReviewDecisionError(f"Zeile {parsed['_row']}: Eine bestätigte Duftreferenz existiert nicht mehr.")
        if original.id == alternative.id:
            raise ReviewDecisionError(f"Zeile {parsed['_row']}: Original und Alternative sind identisch.")

        key = (original.id, alternative.id)
        existing = existing_map.get(key)
        if existing and duplicate_mode == "skip":
            skipped += 1
            continue
        if existing:
            twin = existing
            updated += 1
        else:
            twin = TwinMatch(
                original_id=original.id,
                alternative_id=alternative.id,
                similarity=parsed["similarity"],
            )
            db.add(twin)
            db.flush()
            existing_map[key] = twin
            created += 1

        twin.similarity = parsed["similarity"]
        twin.commonalities = parsed["commonalities"]
        twin.differences = parsed["differences"]
        twin.source_note = parsed["source_note"]
        messages.append({"row": parsed["_row"], "twin_id": str(twin.id)})

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "failed": failed,
        "messages": messages[:100],
    }
