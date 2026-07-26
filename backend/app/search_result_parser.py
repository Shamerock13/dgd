from __future__ import annotations

import re
from html import unescape
from urllib.parse import parse_qs, urlparse


def clean_text(value: object, limit: int = 2000) -> str:
    if value is None:
        return ""
    value = unescape(re.sub(r"<[^>]+>", " ", str(value)))
    return re.sub(r"\s+", " ", value).strip()[:limit]


def unwrap_search_url(href: str) -> str:
    href = unescape(href or "").strip()
    parsed = urlparse(href)
    query = parse_qs(parsed.query)
    target = query.get("uddg", [href])[0]
    return unescape(target)


def parse_search_results(html: str, limit: int = 8) -> list[dict]:
    """Parse DuckDuckGo HTML and Lite layouts without relying on one class name."""
    rows: list[dict] = []
    seen: set[str] = set()
    patterns = (
        r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        r'<a[^>]+class="[^"]*result-link[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        r'<h2[^>]*class="[^"]*result[^"]*"[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        r'<a[^>]+href="([^"]*uddg=[^"]+)"[^>]*>(.*?)</a>',
    )
    snippets = [
        clean_text(value, 1500)
        for value in re.findall(
            r'<(?:a|div|td)[^>]+class="[^"]*(?:result__snippet|result-snippet)[^"]*"[^>]*>(.*?)</(?:a|div|td)>',
            html,
            re.I | re.S,
        )
    ]
    candidates: list[tuple[str, str]] = []
    for pattern in patterns:
        candidates.extend(re.findall(pattern, html, re.I | re.S))
    for index, (href, title_html) in enumerate(candidates):
        target = unwrap_search_url(href)
        if not target.startswith(("http://", "https://")) or target in seen:
            continue
        title = clean_text(title_html, 500)
        if not title:
            continue
        seen.add(target)
        rows.append({
            "url": target,
            "title": title,
            "snippet": snippets[index] if index < len(snippets) else "",
        })
        if len(rows) >= limit:
            break
    return rows
