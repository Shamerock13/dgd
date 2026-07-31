from __future__ import annotations

BROWSER_REQUIRED_TRUST_STATUS = "BROWSER_REQUIRED"

_BROWSER_REQUIRED_MARKERS = (
    "blockiert auch den chromium-renderer",
    "schutz- oder captcha-seite",
    "browser-renderer nötig",
    "browser-connector erforderlich",
)


def requires_browser_connector(error: BaseException | str) -> bool:
    """Erkennt dauerhafte serverseitige Händlerblockaden ohne Schutzmechanismen zu umgehen."""
    text = str(error).casefold()
    return any(marker in text for marker in _BROWSER_REQUIRED_MARKERS)


def browser_connector_required(trust_status: str | None) -> bool:
    return (trust_status or "").strip().upper() == BROWSER_REQUIRED_TRUST_STATUS
