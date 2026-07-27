from __future__ import annotations

import json
from collections import defaultdict

from sqlalchemy import text
from sqlalchemy.orm import Session


def canonical_value(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def known_finding_values(db: Session, fragrance_id, fields: set[str]) -> dict[str, set[str]]:
    if not fields:
        return {}
    rows = db.execute(text("""
        SELECT field_name, proposed_value
        FROM enrichment_findings
        WHERE fragrance_id=:fragrance_id
          AND field_name = ANY(:fields)
          AND status IN ('PENDING','APPROVED','REJECTED','CONFLICT')
        ORDER BY updated_at DESC
        LIMIT 200
    """), {"fragrance_id": fragrance_id, "fields": list(fields)}).mappings()
    result: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        result[row["field_name"]].add(canonical_value(row["proposed_value"]))
    return dict(result)


def known_value_count(values: dict[str, set[str]]) -> int:
    return sum(len(items) for items in values.values())


def is_known_value(field: str, value: object, known: dict[str, set[str]]) -> bool:
    return canonical_value(value) in known.get(field, set())


def exclusion_prompt(values: dict[str, set[str]]) -> str:
    if not values:
        return ""
    lines = ["\nBereits gefundene oder geprüfte Feldwerte – nicht erneut ausgeben:"]
    for field in sorted(values):
        for raw in list(sorted(values[field]))[:8]:
            try:
                display = json.loads(raw)
            except json.JSONDecodeError:
                display = raw
            text_value = json.dumps(display, ensure_ascii=False)
            lines.append(f"- {field}: {text_value[:240]}")
    return "\n".join(lines)
