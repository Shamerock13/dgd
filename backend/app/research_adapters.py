import re
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlparse

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .research_routes import ScanRequest, _public_url, scan_page


class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(href.strip())


async def _read_html(url: str) -> str:
    checked = _public_url(url)
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=15,
            headers={"User-Agent": "DGD-Research/1.1"},
        ) as client:
            response = await client.get(checked)
            response.raise_for_status()
            if "text/html" not in response.headers.get("content-type", ""):
                raise HTTPException(415, "Die Quelle liefert keine HTML-Seite.")
            return response.text[:2_000_000]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Quellseite konnte nicht gelesen werden: {exc}") from exc


def discover_product_links(source_url: str, html: str, link_pattern: str | None, max_pages: int, same_domain_only: bool) -> list[str]:
    collector = LinkCollector()
    collector.feed(html)
    source_host = (urlparse(source_url).hostname or "").casefold()
    pattern = re.compile(link_pattern, re.I) if link_pattern else None
    result: list[str] = []
    seen: set[str] = set()

    for href in collector.links:
        absolute, _ = urldefrag(urljoin(source_url, href))
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            continue
        if same_domain_only and parsed.hostname.casefold() != source_host:
            continue
        if pattern and not pattern.search(absolute):
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        result.append(absolute)
        if len(result) >= max_pages:
            break
    return result


async def scan_source_adapter(row, db: Session) -> dict:
    adapter = str(row.get("adapter_type") or "SINGLE").upper()
    if adapter == "SINGLE":
        result = await scan_page(ScanRequest(url=row["url"], source_name=row["name"]), db)
        return {**result, "pages_scanned": 1, "links_discovered": 1}
    if adapter != "LIST":
        raise HTTPException(400, f"Unbekannter Quellenadapter: {adapter}")

    html = await _read_html(row["url"])
    links = discover_product_links(
        row["url"],
        html,
        row.get("link_pattern"),
        max(1, min(int(row.get("max_pages") or 20), 100)),
        bool(row.get("same_domain_only", True)),
    )
    totals = {"found": 0, "created": 0, "possible_duplicates": 0}
    errors: list[str] = []
    scanned = 0
    for link in links:
        try:
            result = await scan_page(ScanRequest(url=link, source_name=row["name"]), db)
            scanned += 1
            totals["found"] += result["found"]
            totals["created"] += result["created"]
            totals["possible_duplicates"] += result["possible_duplicates"]
        except Exception as exc:
            errors.append(f"{link}: {getattr(exc, 'detail', exc)}")
    return {
        **totals,
        "pages_scanned": scanned,
        "links_discovered": len(links),
        "page_errors": errors[:10],
    }
