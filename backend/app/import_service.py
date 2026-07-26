from __future__ import annotations

import csv
import io
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import UUID
from xml.etree import ElementTree as ET

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from .models import Brand, Fragrance, FragranceNote, Note, TwinMatch


FRAGRANCE_ALIASES = {
    "marke": "brand",
    "brand": "brand",
    "duft": "name",
    "duftname": "name",
    "name": "name",
    "jahr": "year",
    "geschlecht": "gender",
    "zielgruppe": "gender",
    "konzentration": "concentration",
    "parfümeur": "perfumer",
    "parfumeur": "perfumer",
    "preis": "price_eur",
    "preis eur": "price_eur",
    "preis (€)": "price_eur",
    "preis euro": "price_eur",
    "bild url": "image_url",
    "bild-url": "image_url",
    "bildquelle": "image_source_name",
    "bildquelle name": "image_source_name",
    "bildquelle url": "image_source_url",
    "bild-quellen-url": "image_source_url",
    "bild nutzungshinweis": "image_usage_note",
    "bildrechte": "image_usage_note",
    "bildstatus": "image_status",
    "beschreibung": "description",
    "kopfnoten": "top_notes",
    "kopfnote": "top_notes",
    "herznoten": "heart_notes",
    "herznote": "heart_notes",
    "basisnoten": "base_notes",
    "basisnote": "base_notes",
    "akkorde": "accords",
    "haltbarkeit": "longevity",
    "projektion": "projection",
    "süße": "sweetness",
    "suesse": "sweetness",
    "frische": "freshness",
}

TWIN_ALIASES = {
    "original marke": "original_brand",
    "original duft": "original_name",
    "alternative marke": "alternative_brand",
    "alternative duft": "alternative_name",
    "ähnlichkeit": "similarity",
    "ähnlichkeit %": "similarity",
    "aehnlichkeit": "similarity",
    "gemeinsamkeiten": "commonalities",
    "unterschiede": "differences",
    "quellenhinweis": "source_note",
    "quelle": "source_note",
}


def clean_header(value: Any) -> str:
    text = str(value or "").strip().casefold()
    text = re.sub(r"\s+", " ", text)
    return text


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def parse_float(value: Any) -> float | None:
    text = clean_text(value)
    if text is None:
        return None
    text = text.replace("€", "").replace("%", "").replace(" ", "")
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    else:
        text = text.replace(",", ".")
    return float(text)


def parse_int(value: Any) -> int | None:
    number = parse_float(value)
    return int(number) if number is not None else None


def normalize_image_status(value: Any) -> str:
    folded = str(value or "OPEN").strip().casefold()
    aliases = {
        "open": "OPEN", "offen": "OPEN",
        "verified": "VERIFIED", "geprüft": "VERIFIED", "geprueft": "VERIFIED",
        "broken": "BROKEN", "fehlerhaft": "BROKEN", "defekt": "BROKEN",
    }
    return aliases.get(folded, "OPEN")


def valid_image_location(value: str | None) -> bool:
    if not value:
        return True
    if value.startswith("/"):
        return True
    return urlparse(value).scheme in {"http", "https"}


def split_notes(value: Any) -> list[str]:
    text = clean_text(value)
    if not text:
        return []
    values = re.split(r"[,|\n]+", text)
    result = []
    seen = set()
    for raw in values:
        name = " ".join(raw.strip().split())
        key = name.casefold()
        if name and key not in seen:
            result.append(name)
            seen.add(key)
    return result


def read_csv_bytes(data: bytes) -> list[dict[str, Any]]:
    decoded = None
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            decoded = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if decoded is None:
        raise ValueError("Die CSV-Datei konnte nicht gelesen werden.")

    sample = decoded[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
    except csv.Error:
        dialect = csv.excel
        dialect.delimiter = ";"

    reader = csv.DictReader(io.StringIO(decoded), dialect=dialect)
    return [dict(row) for row in reader if any(clean_text(v) for v in row.values())]


def column_index(reference: str) -> int:
    letters = re.match(r"[A-Z]+", reference or "")
    if not letters:
        return 0
    value = 0
    for char in letters.group(0):
        value = value * 26 + ord(char) - 64
    return value - 1


def read_xlsx_bytes(data: bytes, preferred_sheet: str) -> list[dict[str, Any]]:
    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    rel_ns = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
    office_rel = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"

    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for si in root.findall("a:si", ns):
                shared_strings.append("".join(t.text or "" for t in si.iterfind(".//a:t", ns)))

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rel_map = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in relationships.findall("r:Relationship", rel_ns)
        }

        sheets = []
        for sheet in workbook.findall("a:sheets/a:sheet", ns):
            name = sheet.attrib["name"]
            target = rel_map[sheet.attrib[office_rel]]
            if not target.startswith("/"):
                target = "xl/" + target.lstrip("/")
            else:
                target = target.lstrip("/")
            sheets.append((name, target))

        selected = next((s for s in sheets if s[0].casefold() == preferred_sheet.casefold()), None)
        if selected is None:
            selected = sheets[0] if sheets else None
        if selected is None:
            raise ValueError("Die Excel-Datei enthält kein Tabellenblatt.")

        sheet_xml = ET.fromstring(archive.read(selected[1]))
        rows: list[list[Any]] = []
        for row in sheet_xml.findall(".//a:sheetData/a:row", ns):
            values: list[Any] = []
            for cell in row.findall("a:c", ns):
                idx = column_index(cell.attrib.get("r", ""))
                while len(values) <= idx:
                    values.append(None)

                cell_type = cell.attrib.get("t")
                value_node = cell.find("a:v", ns)
                inline_node = cell.find("a:is", ns)

                value: Any = None
                if cell_type == "inlineStr" and inline_node is not None:
                    value = "".join(t.text or "" for t in inline_node.iterfind(".//a:t", ns))
                elif value_node is not None:
                    raw = value_node.text or ""
                    if cell_type == "s":
                        value = shared_strings[int(raw)]
                    elif cell_type == "b":
                        value = raw == "1"
                    else:
                        value = raw
                values[idx] = value
            rows.append(values)

    nonempty = [row for row in rows if any(clean_text(v) for v in row)]
    if not nonempty:
        return []
    headers = [str(v or "").strip() for v in nonempty[0]]
    result = []
    for row in nonempty[1:]:
        padded = row + [None] * (len(headers) - len(row))
        item = {headers[i]: padded[i] for i in range(len(headers)) if headers[i]}
        if any(clean_text(v) for v in item.values()):
            result.append(item)
    return result


def parse_file(filename: str, data: bytes, import_type: str) -> list[dict[str, Any]]:
    suffix = Path(filename or "").suffix.casefold()
    if suffix == ".csv":
        return read_csv_bytes(data)
    if suffix == ".xlsx":
        preferred = "Düfte Import" if import_type == "fragrances" else "Duftzwillinge Import"
        return read_xlsx_bytes(data, preferred)
    raise ValueError("Unterstützt werden CSV- und XLSX-Dateien.")


def map_rows(rows: list[dict[str, Any]], import_type: str) -> list[dict[str, Any]]:
    aliases = FRAGRANCE_ALIASES if import_type == "fragrances" else TWIN_ALIASES
    mapped = []
    for index, row in enumerate(rows, start=2):
        item: dict[str, Any] = {"_row": index}
        for header, value in row.items():
            key = aliases.get(clean_header(header))
            if key:
                item[key] = value
        mapped.append(item)
    return mapped


def validate_fragrance_row(row: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors = []
    brand = clean_text(row.get("brand"))
    name = clean_text(row.get("name"))
    if not brand:
        errors.append("Marke fehlt")
    if not name:
        errors.append("Duftname fehlt")

    parsed = {
        "_row": row["_row"],
        "brand": brand,
        "name": name,
        "year": None,
        "gender": clean_text(row.get("gender")) or "Unisex",
        "concentration": clean_text(row.get("concentration")),
        "perfumer": clean_text(row.get("perfumer")),
        "price_eur": None,
        "image_url": clean_text(row.get("image_url")),
        "image_source_name": clean_text(row.get("image_source_name")),
        "image_source_url": clean_text(row.get("image_source_url")),
        "image_usage_note": clean_text(row.get("image_usage_note")),
        "image_status": normalize_image_status(row.get("image_status")),
        "description": clean_text(row.get("description")),
        "top_notes": split_notes(row.get("top_notes")),
        "heart_notes": split_notes(row.get("heart_notes")),
        "base_notes": split_notes(row.get("base_notes")),
        "accords": clean_text(row.get("accords")),
        "longevity": None,
        "projection": None,
        "sweetness": None,
        "freshness": None,
    }

    try:
        parsed["year"] = parse_int(row.get("year"))
    except ValueError:
        errors.append("Jahr ist ungültig")

    for key, label in [
        ("price_eur", "Preis"),
        ("longevity", "Haltbarkeit"),
        ("projection", "Projektion"),
        ("sweetness", "Süße"),
        ("freshness", "Frische"),
    ]:
        try:
            parsed[key] = parse_float(row.get(key))
        except ValueError:
            errors.append(f"{label} ist ungültig")

    for key, label in [
        ("longevity", "Haltbarkeit"),
        ("projection", "Projektion"),
        ("sweetness", "Süße"),
        ("freshness", "Frische"),
    ]:
        value = parsed[key]
        if value is not None and not 0 <= value <= 10:
            errors.append(f"{label} muss zwischen 0 und 10 liegen")

    if parsed["year"] is not None and not 1700 <= parsed["year"] <= 2200:
        errors.append("Jahr liegt außerhalb des gültigen Bereichs")
    if not valid_image_location(parsed["image_url"]):
        errors.append("Bild-URL muss mit http://, https:// oder / beginnen")
    if not valid_image_location(parsed["image_source_url"]):
        errors.append("Bildquellen-URL muss mit http://, https:// oder / beginnen")

    return parsed, errors


def validate_twin_row(row: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    parsed = {
        "_row": row["_row"],
        "original_brand": clean_text(row.get("original_brand")),
        "original_name": clean_text(row.get("original_name")),
        "alternative_brand": clean_text(row.get("alternative_brand")),
        "alternative_name": clean_text(row.get("alternative_name")),
        "similarity": None,
        "commonalities": clean_text(row.get("commonalities")),
        "differences": clean_text(row.get("differences")),
        "source_note": clean_text(row.get("source_note")),
    }
    errors = []
    for key, label in [
        ("original_brand", "Original-Marke"),
        ("original_name", "Original-Duft"),
        ("alternative_brand", "Alternative-Marke"),
        ("alternative_name", "Alternative-Duft"),
    ]:
        if not parsed[key]:
            errors.append(f"{label} fehlt")
    try:
        parsed["similarity"] = parse_float(row.get("similarity"))
    except ValueError:
        errors.append("Ähnlichkeit ist ungültig")
    if parsed["similarity"] is None:
        errors.append("Ähnlichkeit fehlt")
    elif not 0 <= parsed["similarity"] <= 100:
        errors.append("Ähnlichkeit muss zwischen 0 und 100 liegen")
    return parsed, errors


def get_database_maps(db: Session):
    brands = list(db.scalars(select(Brand)).all())
    notes = list(db.scalars(select(Note)).all())
    fragrances = list(
        db.scalars(select(Fragrance).join(Brand)).all()
    )
    brand_map = {b.name.casefold(): b for b in brands}
    note_map = {n.name.casefold(): n for n in notes}
    fragrance_map = {
        (f.brand.name.casefold(), f.name.casefold()): f
        for f in fragrances
    }
    return brand_map, note_map, fragrance_map


def preview_import(db: Session, rows: list[dict[str, Any]], import_type: str) -> dict[str, Any]:
    mapped = map_rows(rows, import_type)
    brand_map, note_map, fragrance_map = get_database_maps(db)
    preview_rows = []
    errors_total = 0
    duplicate_count = 0
    new_brands = set()
    new_notes = set()
    missing_fragrances = 0

    if import_type == "fragrances":
        seen_file = set()
        for raw in mapped:
            parsed, errors = validate_fragrance_row(raw)
            key = (
                (parsed["brand"] or "").casefold(),
                (parsed["name"] or "").casefold(),
            )
            duplicate = bool(parsed["brand"] and parsed["name"] and key in fragrance_map)
            duplicate_in_file = key in seen_file and all(key)
            if all(key):
                seen_file.add(key)
            if duplicate:
                duplicate_count += 1
            if duplicate_in_file:
                errors.append("Dubletten-Zeile innerhalb der Importdatei")
            if parsed["brand"] and parsed["brand"].casefold() not in brand_map:
                new_brands.add(parsed["brand"])
            for pyramid in ("top_notes", "heart_notes", "base_notes"):
                for note in parsed[pyramid]:
                    if note.casefold() not in note_map:
                        new_notes.add(note)
            errors_total += len(errors)
            preview_rows.append({
                "row": parsed["_row"],
                "brand": parsed["brand"],
                "name": parsed["name"],
                "year": parsed["year"],
                "price_eur": parsed["price_eur"],
                "status": "Fehler" if errors else ("Dublettenfund" if duplicate else "Neu"),
                "errors": errors,
            })
    else:
        existing_twins = {
            (t.original_id, t.alternative_id)
            for t in db.scalars(select(TwinMatch)).all()
        }
        for raw in mapped:
            parsed, errors = validate_twin_row(raw)
            original = fragrance_map.get((
                (parsed["original_brand"] or "").casefold(),
                (parsed["original_name"] or "").casefold(),
            ))
            alternative = fragrance_map.get((
                (parsed["alternative_brand"] or "").casefold(),
                (parsed["alternative_name"] or "").casefold(),
            ))
            if parsed["original_brand"] and parsed["original_name"] and not original:
                errors.append("Original-Duft nicht in DGD gefunden")
                missing_fragrances += 1
            if parsed["alternative_brand"] and parsed["alternative_name"] and not alternative:
                errors.append("Alternative nicht in DGD gefunden")
                missing_fragrances += 1
            duplicate = bool(original and alternative and (original.id, alternative.id) in existing_twins)
            if duplicate:
                duplicate_count += 1
            errors_total += len(errors)
            preview_rows.append({
                "row": parsed["_row"],
                "original": f'{parsed["original_brand"] or ""} – {parsed["original_name"] or ""}',
                "alternative": f'{parsed["alternative_brand"] or ""} – {parsed["alternative_name"] or ""}',
                "similarity": parsed["similarity"],
                "status": "Fehler" if errors else ("Dublettenfund" if duplicate else "Neu"),
                "errors": errors,
            })

    return {
        "import_type": import_type,
        "total_rows": len(mapped),
        "valid_rows": sum(1 for r in preview_rows if not r["errors"]),
        "error_count": errors_total,
        "duplicate_count": duplicate_count,
        "new_brand_count": len(new_brands),
        "new_note_count": len(new_notes),
        "missing_fragrance_count": missing_fragrances,
        "new_brands": sorted(new_brands),
        "new_notes": sorted(new_notes),
        "rows": preview_rows[:250],
        "rows_truncated": len(preview_rows) > 250,
    }


def get_or_create_brand(db: Session, brand_map: dict[str, Brand], name: str) -> Brand:
    key = name.casefold()
    brand = brand_map.get(key)
    if not brand:
        brand = Brand(name=name)
        db.add(brand)
        db.flush()
        brand_map[key] = brand
    return brand


def get_or_create_note(db: Session, note_map: dict[str, Note], name: str) -> Note:
    key = name.casefold()
    note = note_map.get(key)
    if not note:
        note = Note(name=name, category="Nicht kategorisiert")
        db.add(note)
        db.flush()
        note_map[key] = note
    return note


def replace_notes(
    db: Session,
    fragrance: Fragrance,
    parsed: dict[str, Any],
    note_map: dict[str, Note],
) -> None:
    db.execute(
        delete(FragranceNote).where(FragranceNote.fragrance_id == fragrance.id)
    )
    groups = [
        ("top", parsed["top_notes"]),
        ("heart", parsed["heart_notes"]),
        ("base", parsed["base_notes"]),
    ]
    for pyramid, names in groups:
        for position, name in enumerate(names):
            note = get_or_create_note(db, note_map, name)
            db.add(FragranceNote(
                fragrance_id=fragrance.id,
                note_id=note.id,
                pyramid=pyramid,
                position=position,
            ))
    fragrance.top_notes = ", ".join(parsed["top_notes"]) or None
    fragrance.heart_notes = ", ".join(parsed["heart_notes"]) or None
    fragrance.base_notes = ", ".join(parsed["base_notes"]) or None


def commit_import(
    db: Session,
    rows: list[dict[str, Any]],
    import_type: str,
    duplicate_mode: str,
) -> dict[str, Any]:
    if duplicate_mode not in {"skip", "update"}:
        raise ValueError("Ungültiger Dublettenmodus.")

    mapped = map_rows(rows, import_type)
    brand_map, note_map, fragrance_map = get_database_maps(db)
    created = updated = skipped = failed = 0
    messages = []

    try:
        if import_type == "fragrances":
            seen_file = set()
            for raw in mapped:
                parsed, errors = validate_fragrance_row(raw)
                key = (
                    (parsed["brand"] or "").casefold(),
                    (parsed["name"] or "").casefold(),
                )
                if key in seen_file and all(key):
                    errors.append("Dubletten-Zeile innerhalb der Importdatei")
                seen_file.add(key)
                if errors:
                    failed += 1
                    messages.append({"row": parsed["_row"], "errors": errors})
                    continue

                existing = fragrance_map.get(key)
                if existing and duplicate_mode == "skip":
                    skipped += 1
                    continue

                brand = get_or_create_brand(db, brand_map, parsed["brand"])
                if existing:
                    fragrance = existing
                    updated += 1
                else:
                    fragrance = Fragrance(
                        name=parsed["name"],
                        brand_id=brand.id,
                        gender=parsed["gender"],
                    )
                    db.add(fragrance)
                    db.flush()
                    fragrance.brand = brand
                    fragrance_map[key] = fragrance
                    created += 1

                scalar_fields = [
                    "year", "gender", "concentration", "perfumer", "price_eur",
                    "image_url", "image_source_name", "image_source_url",
                    "image_usage_note", "image_status", "description", "accords",
                    "longevity", "projection", "sweetness", "freshness",
                ]
                for field in scalar_fields:
                    value = parsed[field]
                    if value is not None:
                        setattr(fragrance, field, value)

                replace_notes(db, fragrance, parsed, note_map)

        else:
            existing_map = {
                (t.original_id, t.alternative_id): t
                for t in db.scalars(select(TwinMatch)).all()
            }
            for raw in mapped:
                parsed, errors = validate_twin_row(raw)
                original = fragrance_map.get((
                    (parsed["original_brand"] or "").casefold(),
                    (parsed["original_name"] or "").casefold(),
                ))
                alternative = fragrance_map.get((
                    (parsed["alternative_brand"] or "").casefold(),
                    (parsed["alternative_name"] or "").casefold(),
                ))
                if not original:
                    errors.append("Original-Duft nicht in DGD gefunden")
                if not alternative:
                    errors.append("Alternative nicht in DGD gefunden")
                if errors:
                    failed += 1
                    messages.append({"row": parsed["_row"], "errors": errors})
                    continue

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

        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "failed": failed,
        "messages": messages[:100],
    }
