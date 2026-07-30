from __future__ import annotations

import json
from datetime import datetime
from urllib.parse import urlparse
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .ai_research_import import (
    _collect_ids, _field_preview, _fragrance_map, _is_blank, _normalize,
    _note_preview, _parse_workbook,
)
from .ai_research_price_preview import _price_preview
from .database import get_db
from .models import FragranceNote, ImportQualityRun, Note
from .price_models import FragranceOffer, Retailer

router = APIRouter(prefix="/api/ai-research-import", tags=["ai-research-import"])

DNA_DIMENSIONS = {
    "fresh", "citrus", "green", "aquatic", "floral", "fruity", "sweet",
    "gourmand", "spicy", "woody", "smoky", "earthy", "resinous",
    "leathery", "powdery", "animalic",
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
        raise HTTPException(400, "Duft-DNA enthält nicht unterstützte Felder: " + ", ".join(unknown[:8]))
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
        if f"Noten:{fragrance_id}:{pyramid}:{position}:{note_name.casefold()}" == key:
            return row, UUID(fragrance_id), pyramid, position, note_name
    return None


def _get_or_create_retailer(db: Session, merchant_name: str, product_url: str) -> Retailer:
    retailer = db.query(Retailer).filter(Retailer.name.ilike(merchant_name)).first()
    if retailer:
        return retailer
    parsed = urlparse(product_url)
    retailer = Retailer(
        id=uuid4(), name=merchant_name,
        base_url=f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else None,
        active=False,
    )
    db.add(retailer)
    db.flush()
    return retailer


def _apply_price_source(db: Session, change: dict) -> FragranceOffer:
    value = change["new_value"]
    fragrance_id = UUID(change["fragrance_id"])
    retailer = _get_or_create_retailer(db, value["merchant_name"], value["product_url"])
    source_id = value.get("offer_source_id")

    if source_id:
        offer = db.query(FragranceOffer).filter(FragranceOffer.offer_source_id == source_id).first()
        if not offer:
            raise HTTPException(409, "Die Preisquelle existiert nicht mehr. Bitte Datei erneut prüfen.")
        if offer.fragrance_id != fragrance_id:
            raise HTTPException(409, "Die Preisquelle gehört inzwischen zu einem anderen Duft.")
    else:
        offer = FragranceOffer(
            id=uuid4(), offer_source_id=f"ofs-{uuid4().hex}",
            fragrance_id=fragrance_id, retailer_id=retailer.id,
            product_url=value["product_url"],
            price_eur=float(value.get("current_price") or 0),
            shipping_eur=float(value.get("shipping_cost") or 0),
            in_stock=False, checked_at=datetime.utcnow(),
            scanner_active=False, review_status="PENDING_REVIEW",
        )
        db.add(offer)

    offer.retailer_id = retailer.id
    offer.product_url = value["product_url"]
    offer.product_name = value.get("product_variant") or None
    offer.product_variant = value.get("product_variant") or None
    offer.size_ml = value.get("size_ml")
    offer.concentration = value.get("concentration")
    offer.product_type = value.get("product_kind") or "bottle"
    offer.price_eur = float(value.get("current_price") or 0)
    offer.shipping_eur = float(value.get("shipping_cost") or 0)
    offer.currency = "EUR"
    offer.availability = value.get("availability") or "UNKNOWN"
    offer.in_stock = offer.availability in {"IN_STOCK", "AVAILABLE", "LIMITED"}
    offer.ean_gtin = value.get("ean_gtin")
    offer.merchant_sku = value.get("merchant_sku")
    offer.market_country = value.get("market_country")
    offer.scan_interval = value.get("scan_interval")
    offer.extraction_hint = value.get("extraction_hint")
    offer.trust_status = value.get("trust_status") or "OPEN"
    offer.review_status = "PENDING_REVIEW"
    offer.scanner_active = False
    offer.variant_warning = value.get("variant_warning")
    offer.checked_at = datetime.utcnow()
    offer.updated_at = datetime.utcnow()
    db.flush()
    return offer


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
    if ids - set(fragrances):
        raise HTTPException(400, "Mindestens eine fragrance_id existiert nicht mehr.")

    field_changes, field_errors = _field_preview(parsed, fragrances)
    note_changes, note_errors = _note_preview(parsed, fragrances)
    price_changes, price_errors = _price_preview(parsed, fragrances, db)
    if field_errors + note_errors + price_errors:
        raise HTTPException(400, "Die Datei enthält Prüffehler und kann nicht übernommen werden.")

    applicable = {item["key"]: item for item in field_changes + note_changes + price_changes}
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
    price_sources_applied = 0
    generated_source_ids: list[str] = []
    try:
        for key in selected:
            change = applicable[key]
            if change["sheet"] == "Preisquellen":
                offer = _apply_price_source(db, change)
                applied.append({**change, "saved_offer_source_id": offer.offer_source_id})
                price_sources_applied += 1
                if not change["new_value"].get("offer_source_id"):
                    generated_source_ids.append(offer.offer_source_id)
                continue

            if change["sheet"] == "Noten":
                resolved = _note_row(parsed, key)
                if not resolved:
                    raise HTTPException(409, "Eine ausgewählte Duftnote konnte nicht mehr zugeordnet werden.")
                row, fragrance_id, pyramid, position, note_name = resolved
                note = db.query(Note).filter(Note.name.ilike(note_name)).first()
                if not note:
                    note = Note(
                        id=uuid4(), name=note_name,
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
            "price_sources_applied": price_sources_applied,
            "generated_offer_source_ids": generated_source_ids,
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
        "price_sources_applied": price_sources_applied,
        "generated_offer_source_ids": generated_source_ids,
        "price_sources_activated": False,
    }
