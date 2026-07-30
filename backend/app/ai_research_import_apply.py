from __future__ import annotations

import json
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .ai_research_import import (
    _collect_ids,
    _field_preview,
    _fragrance_map,
    _is_blank,
    _normalize,
    _note_preview,
    _parse_workbook,
)
from .database import get_db
from .models import FragranceNote, ImportQualityRun, Note

router = APIRouter(prefix="/api/ai-research-import", tags=["ai-research-import"])

DNA_DIMENSIONS = {
    "fresh", "citrus", "green", "aquatic", "floral", "fruity",
    "sweet", "gourmand", "spicy", "woody", "smoky", "earthy",
    "resinous", "leathery", "powdery", "animalic",
}


def _selected_keys(raw: str) -> set[str]:
    try:
        values = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(400, "Die Auswahl ist kein gültiges JSON.") from exc
    if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
        raise HTTPException(400, "Die Auswahl muss eine Liste technischer Änderungsschlüssel sein.")
    if len(values) > 5000:
        raise HTTPException(400, "Es wurden zu viele Änderungen ausgewählt.")
    return set(values)


def _validate_dna(value):
    if not isinstance(value, dict):
        raise HTTPException(400, "Duft-DNA muss ein JSON-Objekt sein.")
    unknown = sorted(set(value) - DNA_DIMENSIONS)
    if unknown:
        raise HTTPException(
            400,
            "Duft-DNA enthält nicht unterstützte Felder: " + ", ".join(unknown[:8]),
        )
    normalized: dict[str, float] = {}
    for key, raw in value.items():
        if raw is None:
            continue
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise HTTPException(400, f"Duft-DNA-Feld {key} muss eine Zahl von 0 bis 10 sein.")
        number = float(raw)
        if number < 0 or number > 10:
            raise HTTPException(400, f"Duft-DNA-Feld {key} liegt außerhalb von 0 bis 10.")
        normalized[key] = number
    if not normalized:
        raise HTTPException(400, "Duft-DNA enthält keine gültigen numerischen Dimensionen.")
    return normalized


def _note_row(parsed, key: str):
    for row in parsed.rows.get("Noten", []):
        fragrance_id = str(row.get("fragrance_id") or "").strip()
        pyramid = str(row.get("pyramid") or "").strip().upper()
        note_name = str(row.get("note_name") or "").strip()
        try:
            position = int(float(row.get("position") or 0))
        except (TypeError, ValueError):
            continue
        candidate = f"Noten:{fragrance_id}:{pyramid}:{position}:{note_name.casefold()}"
        if candidate == key:
            return row, UUID(fragrance_id), pyramid, position, note_name
    return None


@router.post("/apply")
async def apply_ai_research_import(
    file: UploadFile = File(...),
    selected_keys: str = Form(...),
    confirm_conflicts: bool = Form(False),
    db: Session = Depends(get_db),
):
    filename = file.filename or ""
    if not filename.lower().endswith(".xlsx"):
        raise HTTPException(400, "Bitte eine XLSX-Datei auswählen.")
    content = await file.read()
    if not content or len(content) > 25 * 1024 * 1024:
        raise HTTPException(400, "Die Datei ist leer oder größer als 25 MB.")

    selected = _selected_keys(selected_keys)
    if not selected:
        raise HTTPException(400, "Es wurde keine Änderung ausgewählt.")

    parsed = _parse_workbook(content)
    ids = _collect_ids(parsed)
    fragrances = _fragrance_map(db, ids)
    unknown_ids = ids - set(fragrances)
    if unknown_ids:
        raise HTTPException(400, "Mindestens eine fragrance_id existiert nicht mehr.")

    field_changes, field_errors = _field_preview(parsed, fragrances)
    note_changes, note_errors = _note_preview(parsed, fragrances)
    errors = field_errors + note_errors
    if errors:
        raise HTTPException(400, "Die Datei enthält Prüffehler und kann nicht übernommen werden.")

    applicable = {item["key"]: item for item in field_changes + note_changes}
    unavailable = sorted(selected - set(applicable))
    if unavailable:
        raise HTTPException(
            409,
            "Die Vorschau ist nicht mehr aktuell. Bitte Datei erneut prüfen. "
            f"Nicht verfügbare Änderungen: {', '.join(unavailable[:3])}",
        )

    conflicts = [applicable[key] for key in selected if applicable[key].get("kind") == "conflict"]
    if conflicts and not confirm_conflicts:
        raise HTTPException(409, "Ausgewählte Konflikte müssen ausdrücklich bestätigt werden.")

    applied: list[dict] = []
    try:
        for key in selected:
            change = applicable[key]
            if change["sheet"] == "Noten":
                resolved = _note_row(parsed, key)
                if not resolved:
                    raise HTTPException(409, "Eine ausgewählte Duftnote konnte nicht mehr zugeordnet werden.")
                row, fragrance_id, pyramid, position, note_name = resolved
                note = db.query(Note).filter(Note.name.ilike(note_name)).first()
                if not note:
                    note = Note(
                        id=uuid4(),
                        name=note_name,
                        category=str(row.get("note_category") or "").strip() or None,
                        description=str(row.get("note_description") or "").strip() or None,
                    )
                    db.add(note)
                    db.flush()
                exists = db.query(FragranceNote).filter(
                    FragranceNote.fragrance_id == fragrance_id,
                    FragranceNote.note_id == note.id,
                    FragranceNote.pyramid == pyramid,
                ).first()
                if not exists:
                    db.add(FragranceNote(
                        id=uuid4(), fragrance_id=fragrance_id, note_id=note.id,
                        pyramid=pyramid, position=position,
                    ))
                applied.append(change)
                continue

            fragrance = fragrances[UUID(change["fragrance_id"])]
            field = change["field"]
            model_field = "fragrance_dna" if field == "fragrance_dna_json" else field
            if model_field.startswith("personal_") or not hasattr(fragrance, model_field):
                raise HTTPException(400, f"Feld {field} darf nicht übernommen werden.")
            value = _normalize(field, change["new_value"])
            if field == "fragrance_dna_json":
                value = _validate_dna(value)
            if _is_blank(value):
                raise HTTPException(400, f"Leere Werte dürfen nicht als Löschung übernommen werden: {field}")
            setattr(fragrance, model_field, value)
            applied.append(change)

        report = {
            "export_id": parsed.export_id,
            "schema_version": parsed.schema_version,
            "selected_count": len(selected),
            "applied_count": len(applied),
            "conflicts_confirmed": bool(conflicts),
            "applied": applied,
            "price_sources_activated": False,
        }
        run = ImportQualityRun(
            id=uuid4(), filename=filename, import_type="ai_research",
            duplicate_mode="selective", status="APPLIED", report=report,
        )
        db.add(run)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(500, "Die ausgewählten Änderungen konnten nicht gespeichert werden.") from exc

    return {
        "status": "APPLIED",
        "run_id": str(run.id),
        "export_id": parsed.export_id,
        "applied_count": len(applied),
        "conflicts_applied": len(conflicts),
        "price_sources_activated": False,
    }
