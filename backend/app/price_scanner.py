from __future__ import annotations

import ipaddress
import json
import re
import socket
from datetime import datetime, timedelta
from html import unescape
from urllib.parse import urlparse

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .price_models import FragranceOffer, PriceObservation, Retailer

SUPPORTED_RETAILER_HOSTS = {
    "douglas.de",
    "flaconi.de",
    "notino.de",
    "parfumdreams.de",
    "easycosmetic.de",
    "sephora.de",
}


def _host_matches(host: str, expected_host: str) -> bool:
    host = host.casefold().removeprefix("www.")
    expected_host = expected_host.casefold().removeprefix("www.")
    return host == expected_host or host.endswith(f".{expected_host}")


def _validate_offer_url(offer: FragranceOffer) -> str:
    parsed = urlparse(offer.product_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Ungültige Produkt-URL")
    retailer_host = urlparse(offer.retailer.base_url or "").hostname
    if not retailer_host or not _host_matches(parsed.hostname, retailer_host):
        raise ValueError("Produkt-URL gehört nicht zur Händler-Domain")
    normalized_host = retailer_host.casefold().removeprefix("www.")
    if normalized_host not in SUPPORTED_RETAILER_HOSTS:
        raise ValueError("Für diesen Händler ist noch kein automatischer Adapter freigegeben")
    addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, parsed.port or 443)}
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise ValueError("Interne oder private Netzwerkziele sind nicht erlaubt")
    return offer.product_url


def _numbers(value) -> list[float]:
    if value is None:
        return []
    if isinstance(value, (int, float)):
        return [float(value)]
    if isinstance(value, dict):
        values = []
        for key in ("price", "lowPrice", "highPrice"):
            values.extend(_numbers(value.get(key)))
        return values
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_numbers(item))
        return values
    text = str(value).strip().replace("€", "").replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(",", ".")
    try:
        return [float(text)]
    except ValueError:
        return []


def _availability(value) -> bool | None:
    if value is None:
        return None
    text = str(value).casefold()
    if any(word in text for word in ("instock", "in_stock", "lieferbar", "available", "preorder")):
        return True
    if any(word in text for word in ("outofstock", "out_of_stock", "ausverkauft", "unavailable", "soldout")):
        return False
    return None


def _product_entries(payload):
    stack = payload if isinstance(payload, list) else [payload]
    while stack:
        entry = stack.pop()
        if not isinstance(entry, dict):
            continue
        graph = entry.get("@graph")
        if isinstance(graph, list):
            stack.extend(graph)
        kind = entry.get("@type")
        kinds = set(kind if isinstance(kind, list) else [kind])
        if kinds.intersection({"Product", "IndividualProduct", "ProductGroup"}):
            yield entry


def parse_product_json_ld(html: str) -> dict:
    blocks = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.I | re.S,
    )
    candidates = []
    for block in blocks:
        try:
            payload = json.loads(unescape(block.strip()))
        except Exception:
            continue
        for product in _product_entries(payload):
            offers = product.get("offers")
            offer_list = offers if isinstance(offers, list) else [offers]
            for offer in offer_list:
                if not isinstance(offer, dict):
                    continue
                prices = _numbers(offer)
                currency = str(offer.get("priceCurrency") or "EUR").upper()
                if prices and currency == "EUR":
                    candidates.append({
                        "price_eur": min(prices),
                        "in_stock": _availability(offer.get("availability")),
                        "product_name": str(product.get("name") or "").strip() or None,
                    })
    if not candidates:
        raise ValueError("Auf der Produktseite wurde kein verwertbarer EUR-Preis gefunden")
    candidates.sort(key=lambda row: row["price_eur"])
    result = candidates[0]
    if result["in_stock"] is None:
        result["in_stock"] = True
    return result


async def refresh_offer(offer: FragranceOffer, db: Session) -> dict:
    url = _validate_offer_url(offer)
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; DGD-PriceBot/1.0; +private-catalog)",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.5",
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=20, headers=headers) as client:
        response = await client.get(url)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type:
            raise ValueError("Händlerseite liefert kein HTML")
        parsed = parse_product_json_ld(response.text[:3_000_000])

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


async def refresh_due_offers(db: Session, interval_hours: int = 24, limit: int = 100) -> dict:
    cutoff = datetime.utcnow() - timedelta(hours=max(1, min(interval_hours, 720)))
    offers = list(db.scalars(
        select(FragranceOffer)
        .join(Retailer, Retailer.id == FragranceOffer.retailer_id)
        .where(
            Retailer.active.is_(True),
            FragranceOffer.checked_at <= cutoff,
        )
        .options(joinedload(FragranceOffer.retailer))
        .order_by(FragranceOffer.checked_at)
        .limit(max(1, min(limit, 500)))
    ).unique())

    results = []
    for offer in offers:
        try:
            results.append(await refresh_offer(offer, db))
        except Exception as exc:
            db.rollback()
            results.append({
                "offer_id": str(offer.id),
                "retailer": offer.retailer.name,
                "status": "FAILED",
                "error": f"{type(exc).__name__}: {exc}"[:600],
            })
    successful = sum(row["status"] == "SUCCESS" for row in results)
    return {
        "due": len(offers),
        "successful": successful,
        "failed": len(results) - successful,
        "results": results,
    }
