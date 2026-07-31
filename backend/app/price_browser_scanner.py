from __future__ import annotations

import ipaddress
import socket
from datetime import datetime
from urllib.parse import urljoin, urlparse

import httpx
from sqlalchemy.orm import Session

from .price_models import FragranceOffer, PriceObservation
from .price_scanner import parse_product_json_ld

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/141.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Upgrade-Insecure-Requests": "1",
    "Sec-CH-UA": '"Google Chrome";v="141", "Chromium";v="141", "Not_A Brand";v="24"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
}

_REDIRECT_CODES = {301, 302, 303, 307, 308}
_BLOCK_PAGE_MARKERS = (
    "attention required! | cloudflare",
    "verify you are human",
    "access denied",
    "unusual traffic",
    "datadome",
    "perimeterx",
    "incapsula incident",
    "cf-chl-",
)


def _normalized_host(value: str | None) -> str:
    return (urlparse(value or "").hostname or "").casefold().removeprefix("www.")


def _host_matches(host: str, retailer_host: str) -> bool:
    host = host.casefold().removeprefix("www.")
    retailer_host = retailer_host.casefold().removeprefix("www.")
    return host == retailer_host or host.endswith(f".{retailer_host}")


def _validate_public_target(url: str, retailer_host: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Ungültiges Weiterleitungsziel der Händlerseite")
    if not _host_matches(parsed.hostname, retailer_host):
        raise ValueError("Händlerseite leitet auf eine fremde Domain weiter")

    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, parsed.port or 443)}
    except OSError as exc:
        raise ValueError("Händler-Domain konnte nicht aufgelöst werden") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise ValueError("Interne oder private Netzwerkziele sind nicht erlaubt")


def _raise_for_retailer_status(response: httpx.Response) -> None:
    host = response.url.host or "Händler"
    if response.status_code == 403:
        raise ValueError(
            f"{host} blockiert den serverseitigen Abruf weiterhin (HTTP 403). "
            "Die Quelle wurde nicht verändert; für diesen Shop ist ein echter Browser-Renderer nötig."
        )
    if response.status_code == 429:
        raise ValueError(
            f"{host} begrenzt die Abfragen vorübergehend (HTTP 429). Bitte später erneut testen."
        )
    if response.status_code in {401, 407}:
        raise ValueError(f"{host} verlangt eine Anmeldung oder Proxy-Authentifizierung.")
    response.raise_for_status()


async def _get_document(
    client: httpx.AsyncClient,
    url: str,
    retailer_host: str,
    *,
    referer: str | None = None,
) -> httpx.Response:
    current = url
    for _ in range(6):
        _validate_public_target(current, retailer_host)
        headers = {
            "Sec-Fetch-Site": "same-origin" if referer else "none",
        }
        if referer:
            headers["Referer"] = referer
        response = await client.get(current, headers=headers)
        if response.status_code not in _REDIRECT_CODES:
            _raise_for_retailer_status(response)
            return response
        location = response.headers.get("location")
        if not location:
            raise ValueError("Händlerseite liefert eine Weiterleitung ohne Ziel")
        referer = current
        current = urljoin(current, location)
    raise ValueError("Händlerseite leitet zu häufig weiter")


def _ensure_product_html(response: httpx.Response) -> str:
    content_type = response.headers.get("content-type", "").casefold()
    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
        raise ValueError("Händlerseite liefert kein HTML")

    html = response.text[:5_000_000]
    sample = html[:150_000].casefold()
    if "application/ld+json" not in sample and any(marker in sample for marker in _BLOCK_PAGE_MARKERS):
        raise ValueError(
            "Der Händler liefert eine Schutz- oder CAPTCHA-Seite statt der Produktseite. "
            "Die Quelle wurde nicht verändert."
        )
    return html


async def fetch_product_html(offer: FragranceOffer) -> str:
    if not offer.retailer:
        raise ValueError("Der Preisquelle ist kein Händler zugeordnet")

    product_url = offer.product_url or ""
    base_url = offer.retailer.base_url or ""
    retailer_host = _normalized_host(base_url)
    if not retailer_host:
        raise ValueError("Beim Händler fehlt eine gültige Basis-URL")
    _validate_public_target(product_url, retailer_host)
    _validate_public_target(base_url, retailer_host)

    timeout = httpx.Timeout(30.0, connect=10.0, read=25.0)
    limits = httpx.Limits(max_connections=4, max_keepalive_connections=2)
    async with httpx.AsyncClient(
        follow_redirects=False,
        timeout=timeout,
        limits=limits,
        headers=_BROWSER_HEADERS,
    ) as client:
        # Eine normale Browsersitzung beginnt üblicherweise auf der Händlerseite. Dadurch
        # können Sprach-, Consent- und Session-Cookies gesetzt werden, bevor die Produktseite
        # geladen wird. Fehler beim Vorladen verhindern den eigentlichen Versuch nicht.
        try:
            await _get_document(client, base_url, retailer_host)
        except (httpx.HTTPError, ValueError):
            pass

        response = await _get_document(
            client,
            product_url,
            retailer_host,
            referer=base_url,
        )
        return _ensure_product_html(response)


async def refresh_offer(offer: FragranceOffer, db: Session) -> dict:
    html = await fetch_product_html(offer)
    parsed = parse_product_json_ld(html)

    checked_at = datetime.utcnow()
    offer.price_eur = parsed["price_eur"]
    offer.in_stock = parsed["in_stock"]
    offer.checked_at = checked_at
    if parsed.get("product_name"):
        offer.product_name = parsed["product_name"][:500]
    db.add(PriceObservation(
        offer_id=offer.id,
        price_eur=offer.price_eur,
        shipping_eur=offer.shipping_eur,
        in_stock=offer.in_stock,
        observed_at=checked_at,
    ))
    db.commit()
    return {
        "offer_id": str(offer.id),
        "retailer": offer.retailer.name,
        "status": "SUCCESS",
        "price_eur": offer.price_eur,
        "in_stock": offer.in_stock,
    }
