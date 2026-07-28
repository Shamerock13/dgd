from __future__ import annotations

import json
import re
from html import unescape
from html.parser import HTMLParser
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlparse

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

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.5",
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
}

MEDIA_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".avif", ".ico",
    ".bmp", ".tif", ".tiff", ".mp4", ".webm", ".pdf", ".css", ".js",
    ".woff", ".woff2", ".ttf", ".eot", ".xml", ".json",
}

MEDIA_PATH_PARTS = (
    "/images/", "/image/", "/img/", "/media/", "/assets/", "/static/",
    "/cdn/", "/icons/", "/icon/", "/logos/", "/logo/", "/thumbnails/",
    "/thumbnail/", "/banners/", "/banner/", "/fonts/", "/sprites/",
)


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
    if brand_tokens and " ".join(brand_tokens) in normalized:
        score += 20
    if fragrance_tokens and " ".join(fragrance_tokens) in normalized:
        score += 25
    for penalty in (
        "set", "geschenkset", "sample", "probe", "refill", "nachfüllung",
        "duschgel", "deodorant", "bodylotion", "aftershave", "rasiergel",
    ):
        if penalty in haystack:
            score -= 10
    return max(0, min(score, 100))


def _retailer_host(retailer: Retailer) -> str:
    return (urlparse(retailer.base_url or "").hostname or "").casefold().removeprefix("www.")


def _normalize_candidate_url(raw_url: str, base_url: str, expected_host: str) -> str | None:
    raw_url = unescape(raw_url).replace("\\/", "/").strip('"\' ')
    if raw_url.startswith("//"):
        raw_url = f"https:{raw_url}"
    url = urljoin(base_url, raw_url)
    parsed = urlparse(url)
    if parsed.hostname and parsed.hostname.endswith("duckduckgo.com"):
        redirected = parse_qs(parsed.query).get("uddg")
        if redirected:
            url = unquote(redirected[0])
            parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    if not _host_matches(parsed.hostname, expected_host):
        return None
    return parsed._replace(fragment="").geturl()


def _looks_like_product_url(url: str) -> bool:
    parsed = urlparse(url)
    path = unquote(parsed.path).casefold()
    filename = path.rsplit("/", 1)[-1]

    if any(filename.endswith(extension) for extension in MEDIA_EXTENSIONS):
        return False
    if any(part in path for part in MEDIA_PATH_PARTS):
        return False

    blocked = (
        "/search", "/suche", "/login", "/cart", "/warenkorb", "/category",
        "/marken/", "/brand/", "/account", "/checkout", "/wishlist",
        "/service/", "/hilfe/", "/privacy", "/datenschutz", "/impressum",
    )
    if any(part in path for part in blocked):
        return False

    query_keys = {key.casefold() for key in parse_qs(parsed.query)}
    if query_keys.intersection({"width", "height", "format", "quality", "crop", "fit", "w", "h"}):
        return False

    useful = ("/p/", "/parfum/", "/produkt", "/product", ".html", ".htm")
    return any(part in path for part in useful) or len([part for part in path.split("/") if part]) >= 3


def _candidate_links(html: str, base_url: str, brand: str, fragrance: str) -> list[dict]:
    expected_host = (urlparse(base_url).hostname or "").casefold().removeprefix("www.")
    parser = _LinkParser()
    parser.feed(html[:5_000_000])
    raw_entries = list(parser.links)

    # Modern shops often keep product links only in embedded JSON/state data.
    patterns = (
        r'"(?:url|href|canonicalUrl|productUrl)"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"',
        r'https?:\\?/\\?/[^"\'<>\s]+',
        r'href=["\']([^"\']+)["\']',
    )
    for pattern in patterns:
        for match in re.findall(pattern, html[:5_000_000], re.I):
            value = match if isinstance(match, str) else match[0]
            raw_entries.append({"href": value, "text": ""})

    seen: set[str] = set()
    rows: list[dict] = []
    for entry in raw_entries:
        clean_url = _normalize_candidate_url(entry["href"], base_url, expected_host)
        if not clean_url or clean_url in seen or not _looks_like_product_url(clean_url):
            continue
        url_label = unquote(urlparse(clean_url).path.replace("-", " ").replace("_", " "))
        title = " ".join(part for part in (entry.get("text", "").strip(), url_label) if part)
        score = _score(title, brand, fragrance)
        if score < 28:
            continue
        seen.add(clean_url)
        rows.append({"product_url": clean_url, "title": (entry.get("text") or url_label)[:500], "score": score})
    rows.sort(key=lambda row: (-row["score"], len(row["title"])))
    return rows[:8]


async def _domain_search_candidates(client: httpx.AsyncClient, host: str, brand: str, fragrance: str) -> list[dict]:
    query = quote_plus(f'site:{host} "{brand}" "{fragrance}" parfum')
    response = await client.get(f"https://html.duckduckgo.com/html/?q={query}")
    response.raise_for_status()
    return _candidate_links(response.text, f"https://{host}/", brand, fragrance)


async def discover_products(fragrance: Fragrance, retailer: Retailer) -> dict:
    host = _retailer_host(retailer)
    template = SEARCH_URLS.get(host)
    if not template:
        return {"retailer_id": str(retailer.id), "retailer": retailer.name, "status": "UNSUPPORTED", "candidates": []}
    query = quote_plus(f"{fragrance.brand.name} {fragrance.name}")
    search_url = template.format(query=query)
    attempts: list[str] = []
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=25, headers=REQUEST_HEADERS) as client:
            response = await client.get(search_url)
            response.raise_for_status()
            attempts.append("retailer_search")
            candidates = _candidate_links(response.text, str(response.url), fragrance.brand.name, fragrance.name)
            if not candidates:
                attempts.append("domain_fallback")
                candidates = await _domain_search_candidates(
                    client, host, fragrance.brand.name, fragrance.name
                )
        return {
            "retailer_id": str(retailer.id),
            "retailer": retailer.name,
            "status": "SUCCESS" if candidates else "NO_MATCH",
            "search_url": search_url,
            "strategy": attempts[-1] if attempts else None,
            "candidates": candidates,
        }
    except Exception as exc:
        return {
            "retailer_id": str(retailer.id),
            "retailer": retailer.name,
            "status": "FAILED",
            "error": f"{type(exc).__name__}: {exc}"[:500],
            "strategy": attempts[-1] if attempts else None,
            "candidates": [],
        }


async def verify_candidate(url: str) -> dict:
    async with httpx.AsyncClient(follow_redirects=True, timeout=25, headers=REQUEST_HEADERS) as client:
        response = await client.get(url)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").casefold()
        if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
            raise ValueError("Der Treffer ist keine HTML-Produktseite")
        if not _looks_like_product_url(str(response.url)):
            raise ValueError("Der Treffer ist keine gültige Produktseite")
        parsed = parse_product_json_ld(response.text[:3_000_000])
    return {**parsed, "product_url": str(response.url)}


def active_retailers(db: Session, retailer_ids=None) -> list[Retailer]:
    stmt = select(Retailer).where(Retailer.active.is_(True)).order_by(Retailer.name)
    if retailer_ids:
        stmt = stmt.where(Retailer.id.in_(retailer_ids))
    return list(db.scalars(stmt))
