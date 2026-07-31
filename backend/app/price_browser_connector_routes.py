from __future__ import annotations

from datetime import datetime
from html import escape
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from uuid import uuid4
import zipfile

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .database import get_db
from .price_models import FragranceOffer, PriceObservation, Retailer
from .price_scan_capability import BROWSER_REQUIRED_TRUST_STATUS
from .price_scanner import parse_product_json_ld
from .price_source_review_models import PriceSourceReviewEvent

router = APIRouter(prefix="/api/prices/browser-connector", tags=["price-browser-connector"])

_CONNECTOR_HEADER = "browser-extension-v1"
_EXTENSION_VERSION = "0.1.0"
_EXTENSION_DIR = Path(__file__).with_name("browser_extension")
_MAX_EVIDENCE_BYTES = 1_500_000
_TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "msclkid",
    "ref",
    "referrer",
    "source",
}


class BrowserPageEvidence(BaseModel):
    url: str = Field(min_length=8, max_length=4000)
    title: str | None = Field(default=None, max_length=1000)
    json_ld: list[str] = Field(default_factory=list, max_length=40)
    meta: dict[str, str] = Field(default_factory=dict)
    visible_text: str | None = Field(default=None, max_length=400_000)
    extension_version: str | None = Field(default=None, max_length=40)

    @field_validator("json_ld")
    @classmethod
    def validate_json_ld(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        total = 0
        for value in values:
            text = str(value or "").strip()
            if not text:
                continue
            if len(text) > 250_000:
                raise ValueError("Ein JSON-LD-Block ist zu groß.")
            total += len(text.encode("utf-8"))
            if total > 900_000:
                raise ValueError("Die strukturierten Produktdaten sind zu groß.")
            cleaned.append(text)
        return cleaned

    @field_validator("meta")
    @classmethod
    def validate_meta(cls, value: dict[str, str]) -> dict[str, str]:
        if len(value) > 80:
            raise ValueError("Zu viele Meta-Angaben.")
        return {
            str(key)[:120]: str(item)[:4000]
            for key, item in value.items()
            if str(key).strip() and str(item).strip()
        }


def _host(value: str | None) -> str:
    return (urlparse(value or "").hostname or "").casefold().removeprefix("www.")


def _host_matches(host: str, expected: str) -> bool:
    host = host.casefold().removeprefix("www.")
    expected = expected.casefold().removeprefix("www.")
    return host == expected or host.endswith(f".{expected}")


def _canonical_product_url(value: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(422, "Die Browserseite besitzt keine gültige HTTP-/HTTPS-URL.")

    host = parsed.hostname.casefold().removeprefix("www.")
    port = parsed.port
    netloc = host
    if port and not ((parsed.scheme == "http" and port == 80) or (parsed.scheme == "https" and port == 443)):
        netloc = f"{host}:{port}"

    query = []
    for key, item in parse_qsl(parsed.query, keep_blank_values=True):
        normalized_key = key.casefold()
        if normalized_key.startswith("utm_") or normalized_key in _TRACKING_QUERY_KEYS:
            continue
        query.append((key, item))
    query.sort(key=lambda pair: (pair[0].casefold(), pair[1]))

    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return urlunparse((parsed.scheme.casefold(), netloc, path, "", urlencode(query, doseq=True), ""))


def _build_evidence_html(payload: BrowserPageEvidence) -> str:
    parts = ["<!doctype html><html><head>"]
    for block in payload.json_ld:
        parts.append('<script type="application/ld+json">')
        parts.append(block.replace("</script", "<\\/script"))
        parts.append("</script>")
    for key, value in payload.meta.items():
        parts.append(
            f'<meta property="{escape(key, quote=True)}" content="{escape(value, quote=True)}">'
        )
    if payload.title:
        parts.append(f"<title>{escape(payload.title)}</title>")
    parts.append("</head><body>")
    if payload.visible_text:
        parts.append(escape(payload.visible_text))
    parts.append("</body></html>")
    html = "".join(parts)
    if len(html.encode("utf-8")) > _MAX_EVIDENCE_BYTES:
        raise HTTPException(413, "Die Browserdaten sind zu groß.")
    return html


def _find_offer(db: Session, page_url: str) -> FragranceOffer:
    canonical_page = _canonical_product_url(page_url)
    page_host = _host(page_url)
    candidates = list(db.scalars(
        select(FragranceOffer)
        .join(Retailer, Retailer.id == FragranceOffer.retailer_id)
        .where(
            FragranceOffer.review_status == "APPROVED",
            FragranceOffer.trust_status == BROWSER_REQUIRED_TRUST_STATUS,
        )
        .options(joinedload(FragranceOffer.retailer))
        .order_by(FragranceOffer.updated_at.desc())
        .limit(1000)
    ).unique())

    matches: list[FragranceOffer] = []
    for offer in candidates:
        retailer_host = _host(offer.retailer.base_url if offer.retailer else None)
        if not retailer_host or not _host_matches(page_host, retailer_host):
            continue
        try:
            if _canonical_product_url(offer.product_url) == canonical_page:
                matches.append(offer)
        except HTTPException:
            continue

    if not matches:
        raise HTTPException(
            404,
            "Für diese Produktseite wurde keine freigegebene Preisquelle mit Status „Browser erforderlich“ gefunden.",
        )
    if len(matches) > 1:
        raise HTTPException(409, "Die Produktseite ist mehreren Preisquellen zugeordnet.")
    return matches[0]


def _validate_request_origin(request: Request, connector_header: str | None) -> None:
    if connector_header != _CONNECTOR_HEADER:
        raise HTTPException(403, "Ungültige Browser-Connector-Anfrage.")
    origin = (request.headers.get("origin") or "").casefold()
    if origin and not origin.startswith(("chrome-extension://", "moz-extension://")):
        raise HTTPException(403, "Der Preisimport ist ausschließlich über die Browser-Erweiterung erlaubt.")


def _availability_value(in_stock: bool) -> str:
    return "IN_STOCK" if in_stock else "OUT_OF_STOCK"


@router.get("/health")
def browser_connector_health():
    return {
        "status": "ok",
        "protocol": _CONNECTOR_HEADER,
        "extension_version": _EXTENSION_VERSION,
    }


@router.get("/extension.zip")
def download_browser_extension():
    if not _EXTENSION_DIR.is_dir():
        raise HTTPException(503, "Das Browser-Connector-Paket ist in dieser Installation nicht vorhanden.")

    files = [item for item in sorted(_EXTENSION_DIR.iterdir()) if item.is_file() and not item.name.startswith(".")]
    if not files:
        raise HTTPException(503, "Das Browser-Connector-Paket ist leer.")

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in files:
            archive.write(item, arcname=f"dgd-preis-connector/{item.name}")
        archive.writestr(
            "dgd-preis-connector/VERSION.txt",
            f"DGD Preis-Connector {_EXTENSION_VERSION}\nProtokoll: {_CONNECTOR_HEADER}\n",
        )
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": (
                f'attachment; filename="dgd-preis-connector-{_EXTENSION_VERSION}.zip"'
            ),
            "Cache-Control": "no-store",
        },
    )


@router.post("/import")
def import_browser_price(
    payload: BrowserPageEvidence,
    request: Request,
    x_dgd_connector: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    _validate_request_origin(request, x_dgd_connector)
    offer = _find_offer(db, payload.url)
    if not offer.retailer:
        raise HTTPException(409, "Der Preisquelle ist kein Händler zugeordnet.")
    if offer.review_status != "APPROVED":
        raise HTTPException(409, "Die Preisquelle ist nicht freigegeben.")
    if offer.trust_status != BROWSER_REQUIRED_TRUST_STATUS:
        raise HTTPException(409, "Diese Preisquelle ist nicht für den Browser-Connector vorgemerkt.")

    html = _build_evidence_html(payload)
    try:
        parsed: dict[str, Any] = parse_product_json_ld(html)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

    price = round(float(parsed.get("price_eur") or 0), 2)
    if not 0.5 <= price <= 10_000:
        raise HTTPException(422, "Der erkannte EUR-Preis liegt außerhalb des zulässigen Bereichs.")
    in_stock = bool(parsed.get("in_stock"))
    checked_at = datetime.utcnow()

    previous_price = round(float(offer.price_eur or 0), 2)
    offer.price_eur = price
    offer.in_stock = in_stock
    offer.availability = _availability_value(in_stock)
    offer.checked_at = checked_at
    offer.updated_at = checked_at
    offer.scanner_active = False
    if parsed.get("product_name"):
        offer.product_name = str(parsed["product_name"])[:500]
    elif payload.title:
        offer.product_name = payload.title[:500]

    db.add(PriceObservation(
        offer_id=offer.id,
        price_eur=price,
        shipping_eur=offer.shipping_eur,
        in_stock=in_stock,
        observed_at=checked_at,
    ))
    note = (
        f"{previous_price:.2f} → {price:.2f} EUR · "
        f"{'lieferbar' if in_stock else 'nicht lieferbar'} · "
        f"Browser-Connector {payload.extension_version or 'unbekannt'}"
    )
    db.add(PriceSourceReviewEvent(
        id=uuid4(),
        offer_id=offer.id,
        action="BROWSER_IMPORT_SUCCESS",
        previous_status=offer.review_status,
        new_status=offer.review_status,
        scanner_active=False,
        retailer_activated=False,
        note=note,
    ))
    db.commit()

    return {
        "status": "SUCCESS",
        "offer_id": str(offer.id),
        "offer_source_id": offer.offer_source_id,
        "retailer": offer.retailer.name,
        "price_eur": price,
        "previous_price_eur": previous_price,
        "in_stock": in_stock,
        "checked_at": checked_at,
    }
