from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser
from urllib.parse import quote_plus, urljoin, urlparse

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Fragrance
from .price_models import Retailer
from .price_scanner import _host_matches, parse_product_json_ld

SEARCH_URLS = {
    "douglas.de": "https://www.douglas.de/de/search?q={query}",
    "flaconi.de": "https://www.flaconi.de/search/?q={query}",
    "notino.de": "https://www.notino.de/search.asp?exps={query}",
    "parfumdreams.de": "https://www.parfumdreams.de/Suche?query={query}",
    "easycosmetic.de": "https://www.easycosmetic.de/search.aspx?q={query}",
    "sephora.de": "https://www.sephora.de/search?q={query}",
}


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.casefold() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self._href = href
            self._text = []

    def handle_data(self, data):
        if self._href:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.casefold() == "a" and self._href:
            text = " ".join(" ".join(self._text).split())
            self.links.append({"href": self._href, "text": unescape(text)})
            self._href = None
            self._text = []


def _tokens(value: str) -> list[str]:
    return [part for part in re.findall(r"[a-z0-9]+", value.casefold()) if len(part) > 1]


def _score(title: str, brand: str, fragrance: str) -> int:
    haystack = set(_tokens(title))
    brand_tokens = _tokens(brand)
    fragrance_tokens = _tokens(fragrance)
    score = sum(18 for token in brand_tokens if token in haystack)
    score += sum(14 for token in fragrance_tokens if token in haystack)
    normalized = " ".join(_tokens(title))
    if " ".join(brand_tokens) in normalized:
        score += 20
    if " ".join(fragrance_tokens) in normalized:
        score += 25
    for penalty in ("set", "geschenkset", "sample", "probe", "refill", "duschgel", "deodorant", "bodylotion"):
        if penalty in haystack:
            score -= 8
    return max(0, min(score, 100))


def _retailer_host(retailer: Retailer) -> str:
    return (urlparse(retailer.base_url or "").hostname or "").casefold().removeprefix("www.")


def _candidate_links(html: str, base_url: str, brand: str, fragrance: str) -> list[dict]:
    parser = _LinkParser()
    parser.feed(html[:4_000_000])
    host = (urlparse(base_url).hostname or "").casefold().removeprefix("www.")
    seen: set[str] = set()
    rows: list[dict] = []
    for entry in parser.links:
        title = entry["text"].strip()
        if len(title) < 4:
            continue
        url = urljoin(base_url, entry["href"])
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or not _host_matches(parsed.hostname, host):
            continue
        clean_url = parsed._replace(fragment="").geturl()
        if clean_url in seen:
            continue
        score = _score(title, brand, fragrance)
        if score < 35:
            continue
        seen.add(clean_url)
        rows.append({"product_url": clean_url, "title": title[:500], "score": score})
    rows.sort(key=lambda row: (-row["score"], len(row["title"])))
    return rows[:8]


async def discover_products(fragrance: Fragrance, retailer: Retailer) -> dict:
    host = _retailer_host(retailer)
    template = SEARCH_URLS.get(host)
    if not template:
        return {"retailer_id": str(retailer.id), "retailer": retailer.name, "status": "UNSUPPORTED", "candidates": []}
    query = quote_plus(f"{fragrance.brand.name} {fragrance.name}")
    search_url = template.format(query=query)
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; DGD-PriceDiscovery/1.0; +private-catalog)",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.5",
    }
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20, headers=headers) as client:
            response = await client.get(search_url)
            response.raise_for_status()
            candidates = _candidate_links(response.text, str(response.url), fragrance.brand.name, fragrance.name)
        return {
            "retailer_id": str(retailer.id),
            "retailer": retailer.name,
            "status": "SUCCESS",
            "search_url": search_url,
            "candidates": candidates,
        }
    except Exception as exc:
        return {
            "retailer_id": str(retailer.id),
            "retailer": retailer.name,
            "status": "FAILED",
            "error": f"{type(exc).__name__}: {exc}"[:500],
            "candidates": [],
        }


async def verify_candidate(url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; DGD-PriceDiscovery/1.0; +private-catalog)",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.5",
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=20, headers=headers) as client:
        response = await client.get(url)
        response.raise_for_status()
        parsed = parse_product_json_ld(response.text[:3_000_000])
    return {**parsed, "product_url": str(response.url)}


def active_retailers(db: Session, retailer_ids=None) -> list[Retailer]:
    stmt = select(Retailer).where(Retailer.active.is_(True)).order_by(Retailer.name)
    if retailer_ids:
        stmt = stmt.where(Retailer.id.in_(retailer_ids))
    return list(db.scalars(stmt))
