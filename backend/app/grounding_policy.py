from __future__ import annotations

from urllib.parse import urlparse


FALLBACK_HOSTS = {"google.com", "www.google.com"}


def usable_grounding_sources(sources: list[dict] | None) -> list[dict]:
    """Return concrete HTTP(S) grounding sources, excluding generic fallbacks."""
    result: list[dict] = []
    seen: set[str] = set()
    for source in sources or []:
        url = str(source.get("url") or "").strip()
        parsed = urlparse(url)
        host = (parsed.hostname or "").casefold()
        if parsed.scheme not in {"http", "https"} or not host or host in FALLBACK_HOSTS:
            continue
        if url in seen:
            continue
        seen.add(url)
        result.append(source)
    return result


def grounded_twin_counts(twins: list[dict] | None, sources: list[dict] | None) -> tuple[int, int]:
    """Return (eligible, blocked) twin counts for one Gemini response."""
    count = len(twins or [])
    if not count:
        return 0, 0
    if usable_grounding_sources(sources):
        return count, 0
    return 0, count
