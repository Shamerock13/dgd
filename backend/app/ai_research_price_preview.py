from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session, joinedload

from .ai_research_import import (
    _collect_ids,
    _field_preview,
    _fragrance_map,
    _is_blank,
    _note_preview,
    _parse_workbook,
    _serializable,
    _text,
)
from .database import get_db
from .price_models import FragranceOffer, Retailer

router = APIRouter(prefix="/api/ai-research-import", tags=["ai-research-import"])

SOURCE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,63}$")
ALLOWED_PRODUCT_KINDS = {"bottle", "tester", "sample", "set", "refill"}
SEARCH_PATH_PARTS = {"search", "suche", "category", "kategorie", "collections"}


def _number(value: Any, field: str, row_number: int, *, allow_zero: bool = True) -> float | None:
    if _is_blank(value):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} muss eine Zahl sein.") from exc
    if number < 0 or (not allow_zero and number == 0):
        raise ValueError(f"{field} muss größer als 0 sein.")
    return number


def _direct_product_url(value: Any) -> str:
    url = _text(value)
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("product_url muss eine vollständige HTTP(S)-Adresse sein.")
    path_parts = {part.casefold() for part in parsed.path.split("/") if part}
    if path_parts.intersection(SEARCH_PATH_PARTS):
        raise ValueError("product_url wirkt wie eine Such- oder Kategorieseite; benötigt wird eine direkte Produktseite.")
    if len(parsed.path.strip("/")) < 3:
        raise ValueError("product_url ist zu unspezifisch und wirkt nicht wie eine direkte Produktseite.")
    return url


def _offer_snapshot(offer: FragranceOffer | None) -> dict[str, Any] | None:
    if not offer:
        return None
    return {
        "offer_source_id": offer.offer_source_id,
        "merchant_name": offer.retailer.name if offer.retailer else None,
        "product_url": offer.product_url,
        "product_variant": offer.product_variant,
        "size_ml": offer.size_ml,
        "concentration": offer.concentration,
        "product_kind": offer.product_type,
        "current_price": offer.price_eur,
        "shipping_cost": offer.shipping_eur,
        "currency": offer.currency,
        "availability": offer.availability,
        "ean_gtin": offer.ean_gtin,
        "merchant_sku": offer.merchant_sku,
        "market_country": offer.market_country,
        "scan_interval": offer.scan_interval,
        "extraction_hint": offer.extraction_hint,
        "trust_status": offer.trust_status,
        "review_status": offer.review_status,
        "scanner_active": offer.scanner_active,
        "variant_warning": offer.variant_warning,
    }


def _price_preview(parsed, fragrances, db: Session) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    changes: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    rows = parsed.rows.get("Preisquellen", [])

    existing_offers = db.query(FragranceOffer).options(joinedload(FragranceOffer.retailer)).all()
    offers_by_source = {item.offer_source_id: item for item in existing_offers if item.offer_source_id}
    offers_by_url = {(str(item.fragrance_id), item.product_url.strip()): item for item in existing_offers}
    retailers = {item.name.strip().casefold(): item for item in db.query(Retailer).all()}

    seen_source_ids: dict[str, int] = {}
    seen_urls: dict[tuple[str, str], int] = {}

    for row_number, row in enumerate(rows, start=2):
        if _is_blank(row.get("product_url")) and _is_blank(row.get("offer_source_id")):
            continue

        raw_fragrance_id = _text(row.get("fragrance_id"))
        try:
            fragrance_id = UUID(raw_fragrance_id)
        except ValueError:
            errors.append({"sheet": "Preisquellen", "row": row_number, "field": "fragrance_id", "message": "Ungültige fragrance_id."})
            continue
        fragrance = fragrances.get(fragrance_id)
        if not fragrance:
            errors.append({"sheet": "Preisquellen", "row": row_number, "field": "fragrance_id", "message": "fragrance_id existiert nicht."})
            continue

        source_id = _text(row.get("offer_source_id"))
        if source_id:
            if not SOURCE_ID_RE.fullmatch(source_id):
                errors.append({"sheet": "Preisquellen", "row": row_number, "field": "offer_source_id", "message": "offer_source_id hat ein ungültiges Format."})
                continue
            if source_id in seen_source_ids:
                errors.append({"sheet": "Preisquellen", "row": row_number, "field": "offer_source_id", "message": f"offer_source_id ist bereits in Zeile {seen_source_ids[source_id]} enthalten."})
                continue
            seen_source_ids[source_id] = row_number

        try:
            product_url = _direct_product_url(row.get("product_url"))
            size_ml = _number(row.get("size_ml"), "size_ml", row_number, allow_zero=False)
            current_price = _number(row.get("current_price"), "current_price", row_number)
            shipping_cost = _number(row.get("shipping_cost"), "shipping_cost", row_number)
        except ValueError as exc:
            errors.append({"sheet": "Preisquellen", "row": row_number, "message": str(exc)})
            continue

        url_key = (str(fragrance_id), product_url)
        if url_key in seen_urls:
            errors.append({"sheet": "Preisquellen", "row": row_number, "field": "product_url", "message": f"Produktlink ist bereits in Zeile {seen_urls[url_key]} enthalten."})
            continue
        seen_urls[url_key] = row_number

        merchant_name = _text(row.get("merchant_name"))
        if not merchant_name:
            errors.append({"sheet": "Preisquellen", "row": row_number, "field": "merchant_name", "message": "Händlername fehlt."})
            continue

        product_kind = (_text(row.get("product_kind")) or "bottle").casefold()
        if product_kind not in ALLOWED_PRODUCT_KINDS:
            errors.append({"sheet": "Preisquellen", "row": row_number, "field": "product_kind", "message": "Erlaubt sind bottle, tester, sample, set oder refill."})
            continue

        currency = (_text(row.get("currency")) or "EUR").upper()
        if currency != "EUR":
            errors.append({"sheet": "Preisquellen", "row": row_number, "field": "currency", "message": "In Paket 16.7.4 werden nur EUR-Preisquellen übernommen."})
            continue

        market_country = _text(row.get("market_country")).upper()
        if market_country and (len(market_country) != 2 or not market_country.isalpha()):
            errors.append({"sheet": "Preisquellen", "row": row_number, "field": "market_country", "message": "market_country muss ein zweistelliger Ländercode sein."})
            continue

        existing = offers_by_source.get(source_id) if source_id else None
        if source_id and not existing:
            errors.append({"sheet": "Preisquellen", "row": row_number, "field": "offer_source_id", "message": "Unbekannte offer_source_id. Für eine neue Quelle muss das Feld leer bleiben; DGD erzeugt die ID."})
            continue
        if existing and existing.fragrance_id != fragrance_id:
            errors.append({"sheet": "Preisquellen", "row": row_number, "field": "offer_source_id", "message": "offer_source_id gehört zu einem anderen Duft und darf nicht verschoben werden."})
            continue

        url_match = offers_by_url.get(url_key)
        if not source_id and url_match:
            errors.append({"sheet": "Preisquellen", "row": row_number, "field": "product_url", "message": "Diese Produktseite ist bereits als Preisquelle vorhanden; vorhandene offer_source_id verwenden."})
            continue

        warnings: list[str] = []
        concentration = _text(row.get("concentration"))
        product_variant = _text(row.get("product_variant"))
        variant_warning = _text(row.get("variant_warning"))
        if product_kind in {"bottle", "tester", "sample", "refill"} and size_ml is None:
            warnings.append("Größe fehlt; Quelle bleibt bis zur Ergänzung in Prüfung.")
        if not concentration:
            warnings.append("Konzentration fehlt; EDP, EDT, Parfum usw. können nicht sicher getrennt werden.")
        if product_kind != "bottle" and not product_variant:
            warnings.append("Bei Tester, Sample, Set oder Refill sollte die Variante eindeutig beschrieben werden.")
        if variant_warning:
            warnings.append(variant_warning)
        if merchant_name.casefold() not in retailers:
            warnings.append("Händler ist in DGD noch nicht angelegt und wird bei Übernahme zunächst deaktiviert erstellt.")
        if _text(row.get("scanner_active")).casefold() in {"true", "1", "yes", "ja"}:
            warnings.append("scanner_active aus der Datei wird ignoriert; die Quelle bleibt deaktiviert.")

        proposed = {
            "offer_source_id": source_id or None,
            "merchant_name": merchant_name,
            "product_url": product_url,
            "product_variant": product_variant or None,
            "size_ml": size_ml,
            "concentration": concentration or None,
            "product_kind": product_kind,
            "current_price": current_price if current_price is not None else 0,
            "shipping_cost": shipping_cost if shipping_cost is not None else 0,
            "currency": currency,
            "availability": _text(row.get("availability")).upper() or "UNKNOWN",
            "ean_gtin": _text(row.get("ean_gtin")) or None,
            "merchant_sku": _text(row.get("merchant_sku")) or None,
            "market_country": market_country or None,
            "scan_interval": _text(row.get("scan_interval")) or None,
            "extraction_hint": _text(row.get("extraction_hint")) or None,
            "trust_status": _text(row.get("trust_status")).upper() or "OPEN",
            "review_status": "PENDING_REVIEW",
            "scanner_active": False,
            "variant_warning": " ".join(warnings) or None,
        }
        old_value = _offer_snapshot(existing)
        if old_value == proposed:
            continue

        changes.append({
            "key": f"Preisquellen:{source_id or 'NEW'}:{fragrance_id}:{row_number}",
            "sheet": "Preisquellen",
            "row": row_number,
            "fragrance_id": str(fragrance_id),
            "fragrance_name": fragrance.name,
            "brand_name": fragrance.brand.name if fragrance.brand else "",
            "field": "Preisquelle",
            "old_value": _serializable(old_value),
            "new_value": proposed,
            "kind": "conflict" if existing else "new",
            "preview_only": False,
            "warnings": warnings,
        })

    return changes, errors


@router.post("/preview")
async def preview_ai_research_import_with_prices(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    filename = file.filename or ""
    if not filename.lower().endswith(".xlsx"):
        raise HTTPException(400, "Bitte eine XLSX-Datei auswählen.")
    content = await file.read()
    if not content or len(content) > 25 * 1024 * 1024:
        raise HTTPException(400, "Die Datei ist leer oder größer als 25 MB.")

    parsed = _parse_workbook(content)
    ids = _collect_ids(parsed)
    fragrances = _fragrance_map(db, ids)
    unknown_ids = sorted(str(item) for item in ids - set(fragrances))
    if unknown_ids:
        raise HTTPException(400, f"Unbekannte fragrance_id: {', '.join(unknown_ids[:5])}")

    field_changes, field_errors = _field_preview(parsed, fragrances)
    note_changes, note_errors = _note_preview(parsed, fragrances)
    price_changes, price_errors = _price_preview(parsed, fragrances, db)
    changes = field_changes + note_changes + price_changes
    errors = field_errors + note_errors + price_errors

    summary = {
        "fragrances": len(ids),
        "changes": len(changes),
        "new_values": sum(1 for item in changes if item["kind"] == "new"),
        "conflicts": sum(1 for item in changes if item["kind"] == "conflict"),
        "preview_only": sum(1 for item in changes if item.get("preview_only")),
        "errors": len(errors),
        "price_sources": len(price_changes),
        "price_source_errors": len(price_errors),
    }
    return {
        "filename": filename,
        "export_id": parsed.export_id,
        "schema_version": parsed.schema_version,
        "summary": summary,
        "changes": changes,
        "errors": errors,
        "database_changed": False,
        "price_sources_scanner_active": False,
    }
