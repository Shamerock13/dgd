from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from .price_browser_scanner import fetch_product_html
from .price_models import FragranceOffer, PriceObservation
from .price_playwright_renderer import render_product_html
from .price_scanner import parse_product_json_ld


def _requires_chromium(exc: Exception) -> bool:
    message = str(exc).casefold()
    return any(
        marker in message
        for marker in (
            "http 403",
            "schutz- oder captcha-seite",
            "echter browser-renderer nötig",
            "serverseitigen abruf weiterhin",
        )
    )


async def refresh_offer(offer: FragranceOffer, db: Session) -> dict:
    renderer = "http"
    try:
        html = await fetch_product_html(offer)
    except Exception as exc:
        if not _requires_chromium(exc):
            raise
        if not offer.retailer:
            raise ValueError("Der Preisquelle ist kein Händler zugeordnet") from exc
        html = await render_product_html(
            offer.product_url,
            offer.retailer.base_url or "",
        )
        renderer = "chromium"

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
        "retailer": offer.retailer.name if offer.retailer else "Unbekannt",
        "status": "SUCCESS",
        "renderer": renderer,
        "price_eur": offer.price_eur,
        "in_stock": offer.in_stock,
    }
