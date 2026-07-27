from __future__ import annotations

import json
import re
from html import unescape

FIELD_LIMITS = {
    "brand_name": 160,
    "fragrance_name": 200,
    "concentration": 80,
    "perfumer": 160,
    "description": 350,
    "brand_description": 600,
    "perfumer_profile": 800,
    "comparison_reason": 240,
    "source_excerpt": 500,
    "source_name": 300,
    "url": 2000,
    "note": 80,
}


LIST_PREFIX_RE = re.compile(
    r"^\s*(?:kopf(?:note|noten)?|top\s*notes?|herz(?:note|noten)?|middle\s*notes?|heart\s*notes?|basis(?:note|noten)?|base\s*notes?|akkorde?|accords?|main\s*accords?)\s*[:\-–]\s*",
    re.I,
)


def compact_text(value, limit: int, *, sentence_boundary: bool = True) -> str:
    text_value = unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
    text_value = text_value.strip("{}[]() \t\r\n\"'`")
    text_value = re.sub(r"\s+", " ", text_value).strip(" ,;:")
    if len(text_value) <= limit:
        return text_value
    candidate = text_value[:limit].rstrip()
    if sentence_boundary:
        sentence_end = max(candidate.rfind(". "), candidate.rfind("! "), candidate.rfind("? "))
        if sentence_end >= max(40, limit // 2):
            return candidate[: sentence_end + 1].strip()
    word_end = candidate.rfind(" ")
    if word_end >= max(20, limit // 2):
        candidate = candidate[:word_end]
    return candidate.rstrip(" ,;:-")


def compact_name(value, field: str) -> str:
    return compact_text(value, FIELD_LIMITS[field], sentence_boundary=False)


def _list_values(value) -> list[object]:
    if value in (None, ""):
        return []
    if isinstance(value, (list, tuple, set)):
        result: list[object] = []
        for item in value:
            result.extend(_list_values(item))
        return result
    if not isinstance(value, str):
        return [value]

    text_value = unescape(value).strip()
    text_value = LIST_PREFIX_RE.sub("", text_value)
    if text_value[:1] in "[{" and text_value[-1:] in "]}":
        try:
            parsed = json.loads(text_value.replace("'", '"'))
            if parsed != value:
                return _list_values(parsed)
        except (TypeError, ValueError, json.JSONDecodeError):
            pass

    text_value = re.sub(r"[\[\]{}()]", " ", text_value)
    text_value = text_value.replace("\u201c", '"').replace("\u201d", '"').replace("\u201e", '"')
    return re.split(r"[,;|\n]+", text_value)


def compact_list(value, *, max_items: int, item_limit: int = 80) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in _list_values(value):
        cleaned = compact_text(item, item_limit, sentence_boundary=False)
        cleaned = LIST_PREFIX_RE.sub("", cleaned)
        cleaned = cleaned.strip("{}[]() \t\r\n\"'`").strip(" ,;:|-")
        cleaned = re.sub(r"^(?:and|und)\s+", "", cleaned, flags=re.I)
        fingerprint = cleaned.casefold()
        if cleaned and fingerprint not in seen:
            seen.add(fingerprint)
            result.append(cleaned)
        if len(result) >= max_items:
            break
    return result


def split_brand_fragrance(value: str) -> tuple[str, str]:
    cleaned = compact_text(value, 300, sentence_boundary=False)
    for separator in (" – ", " — ", " - ", ": ", " by "):
        if separator in cleaned:
            brand, fragrance = cleaned.split(separator, 1)
            if brand.strip() and fragrance.strip():
                return compact_name(brand, "brand_name"), compact_name(fragrance, "fragrance_name")
    return "", compact_name(cleaned, "fragrance_name")


def normalize_candidate(row: dict) -> dict:
    return {
        **row,
        "brand_name": compact_name(row.get("brand_name") or "Unbekannte Marke", "brand_name"),
        "fragrance_name": compact_name(row.get("fragrance_name"), "fragrance_name"),
        "concentration": compact_name(row.get("concentration"), "concentration") or None,
        "description": compact_text(row.get("description"), FIELD_LIMITS["description"]) or None,
        "image_url": compact_text(row.get("image_url"), FIELD_LIMITS["url"], sentence_boundary=False) or None,
    }
