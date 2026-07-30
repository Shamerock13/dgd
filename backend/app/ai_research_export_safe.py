from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

from . import ai_research_export as base


def _safe_excel_value(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return ILLEGAL_CHARACTERS_RE.sub("", value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (dict, list, tuple, set)):
        return base._json(value)
    return value


def _safe_append(ws, headers: list[str], values: dict) -> None:
    ws.append([_safe_excel_value(values.get(header, "")) for header in headers])


# The route function resolves _append from its source module at runtime. Replacing
# it here keeps the export implementation centralized while protecting XLSX XML
# from invalid control characters and unsupported cell value types.
base._append = _safe_append
router = base.router
