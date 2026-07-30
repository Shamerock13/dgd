from __future__ import annotations

from . import ai_research_price_preview as price_preview


PRODUCT_KIND_ALIASES = {
    "reguläre ware": "bottle",
    "regulaere ware": "bottle",
    "normalware": "bottle",
    "flakon": "bottle",
    "flasche": "bottle",
    "bottle": "bottle",
    "tester": "tester",
    "testerware": "tester",
    "probe": "sample",
    "sample": "sample",
    "abfüllung": "sample",
    "abfuellung": "sample",
    "set": "set",
    "geschenkset": "set",
    "duftset": "set",
    "refill": "refill",
    "nachfüllung": "refill",
    "nachfuellung": "refill",
}

_original_price_preview = price_preview._price_preview


def _price_preview_with_aliases(parsed, fragrances, db):
    """Translate user-facing product-kind labels to DGD's stable internal codes."""
    changed_rows: list[tuple[dict, object]] = []
    for row in parsed.rows.get("Preisquellen", []):
        raw = row.get("product_kind")
        if raw is None:
            continue
        normalized = str(raw).strip().casefold()
        mapped = PRODUCT_KIND_ALIASES.get(normalized)
        if mapped and mapped != raw:
            changed_rows.append((row, raw))
            row["product_kind"] = mapped
    try:
        return _original_price_preview(parsed, fragrances, db)
    finally:
        for row, original in changed_rows:
            row["product_kind"] = original


price_preview._price_preview = _price_preview_with_aliases
