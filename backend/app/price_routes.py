from __future__ import annotations

from datetime import datetime, timedelta
from hashlib import sha256
from typing import Literal
from urllib.parse import urlparse
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from .database import get_db
from .models import Fragrance
from .price_models import FragranceOffer, PriceObservation, Retailer

router = APIRouter(prefix="/api/prices", tags=["prices"])


class RetailerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    base_url: str | None = Field(default=None, max_length=2000)
    active: bool = True


class OfferCheckIn(BaseModel):
    fragrance_id: UUID
    retailer_id: UUID
    product_url: str = Field(min_length=8, max_length=3000)
    product_name: str | None = Field(default=None, max_length=500)
    size_ml: float | None = Field(default=None, gt=0, le=5000)
    product_type: Literal["bottle", "tester", "set", "sample", "refill"] = "bottle"
    price_eur: float = Field(gt=0, le=100000)
    shipping_eur: float = Field(default=0, ge=0, le=10000)
    in_stock: bool = True
    checked_at: datetime | None = None


_CONCENTRATION_ALIASES = {
    "edp": "eau de parfum",
    "e.d.p.": "eau de parfum",
    "eau de parfum spray": "eau de parfum",
    "edt": "eau de toilette",
    "e.d.t.": "eau de toilette",
    "eau de toilette spray": "eau de toilette",
    "edc": "eau de cologne",
    "e.d.c.": "eau de cologne",
    "parfum extract": "extrait de parfum",
    "perfume extract": "extrait de parfum",
}


def _valid_web_url(value: str | None) -> bool:
    if not value:
        return True
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _retailer_out(row: Retailer) -> dict:
    return {
        "id": str(row.id),
        "name": row.name,
        "base_url": row.base_url,
        "active": row.active,
        "created_at": row.created_at,
    }


def _normalized_text(value: str | None) -> str | None:
    normalized = " ".join((value or "").casefold().split()).strip()
    return normalized or None


def _normalized_concentration(value: str | None) -> str | None:
    normalized = _normalized_text(value)
    if not normalized:
        return None
    return _CONCENTRATION_ALIASES.get(normalized, normalized)


def _normalized_size(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 2)


def _variant_identity(row: FragranceOffer) -> dict:
    size_ml = _normalized_size(row.size_ml)
    concentration = _normalized_concentration(row.concentration)
    raw = "|".join((
        row.product_type or "unknown",
        f"{size_ml:.2f}" if size_ml is not None else "unknown",
        concentration or "unknown",
    ))
    variant_key = f"pv-{sha256(raw.encode('utf-8')).hexdigest()[:16]}"
    missing = []
    if size_ml is None:
        missing.append("size_ml")
    if concentration is None:
        missing.append("concentration")
    return {
        "variant_key": variant_key,
        "product_type": row.product_type,
        "size_ml": size_ml,
        "concentration": concentration,
        "variant_complete": not missing,
        "missing_variant_fields": missing,
    }


def _offer_out(row: FragranceOffer) -> dict:
    total = round(row.price_eur + row.shipping_eur, 2)
    variant = _variant_identity(row)
    return {
        "id": str(row.id),
        "offer_source_id": row.offer_source_id,
        "fragrance_id": str(row.fragrance_id),
        "retailer": _retailer_out(row.retailer),
        "product_url": row.product_url,
        "product_name": row.product_name,
        "product_variant": row.product_variant,
        "size_ml": row.size_ml,
        "concentration": row.concentration,
        "product_type": row.product_type,
        "price_eur": round(row.price_eur, 2),
        "shipping_eur": round(row.shipping_eur, 2),
        "total_eur": total,
        "price_per_100ml_eur": round(total / row.size_ml * 100, 2) if row.size_ml else None,
        "currency": row.currency,
        "availability": row.availability,
        "in_stock": row.in_stock,
        "checked_at": row.checked_at,
        "review_status": row.review_status,
        **variant,
    }


def _daily_best_history(rows: list[dict]) -> list[dict]:
    daily: dict[str, dict] = {}
    for row in rows:
        if not row["in_stock"]:
            continue
        day = row["observed_at"].date().isoformat()
        current = daily.get(day)
        if current is None or row["total_eur"] < current["total_eur"]:
            daily[day] = {
                "date": day,
                "observed_at": row["observed_at"],
                "offer_id": row["offer_id"],
                "retailer": row["retailer"],
                "total_eur": row["total_eur"],
            }
    return [daily[key] for key in sorted(daily)]


def _variant_group_out(
    key: str,
    rows: list[dict],
    history_rows: list[dict],
    all_time_lows: dict[str, float],
) -> dict:
    sample = rows[0]
    available = sorted(
        (row for row in rows if row["in_stock"]),
        key=lambda row: (row["total_eur"], row["price_per_100ml_eur"] or float("inf")),
    )
    unavailable = sorted(
        (row for row in rows if not row["in_stock"]),
        key=lambda row: row["checked_at"],
        reverse=True,
    )
    offer_ids = {row["id"] for row in rows}
    group_history = [row for row in history_rows if row["offer_id"] in offer_ids]
    historic_values = [all_time_lows[row_id] for row_id in offer_ids if row_id in all_time_lows]
    historic_low = min(historic_values) if historic_values else None
    cheapest = available[0] if available else None
    difference = None
    difference_percent = None
    if cheapest and historic_low is not None:
        difference = round(cheapest["total_eur"] - historic_low, 2)
        if historic_low > 0:
            difference_percent = round(difference / historic_low * 100, 1)
    last_checked = max((row["checked_at"] for row in rows), default=None)

    return {
        "variant_key": key,
        "product_type": sample["product_type"],
        "size_ml": sample["size_ml"],
        "concentration": sample["concentration"],
        "variant_complete": sample["variant_complete"],
        "missing_variant_fields": sample["missing_variant_fields"],
        "checked_offers": len(rows),
        "available_offers": len(available),
        "history_observations": len(group_history),
        "last_checked_at": last_checked,
        "cheapest": cheapest,
        "historic_low_total_eur": round(historic_low, 2) if historic_low is not None else None,
        "difference_from_low_eur": difference,
        "difference_from_low_percent": difference_percent,
        "offers": available + unavailable,
        "history": group_history,
        "daily_best_history": _daily_best_history(group_history),
    }


def _variant_sort_key(row: dict) -> tuple:
    type_rank = {
        "bottle": 5,
        "tester": 4,
        "refill": 3,
        "set": 2,
        "sample": 1,
    }.get(row["product_type"], 0)
    cheapest = row["cheapest"]["total_eur"] if row["cheapest"] else float("inf")
    return (
        1 if row["available_offers"] else 0,
        type_rank,
        1 if row["variant_complete"] else 0,
        row["available_offers"],
        row["history_observations"],
        row["size_ml"] or 0,
        -cheapest,
    )


@router.get("/retailers")
def list_retailers(active_only: bool = False, db: Session = Depends(get_db)):
    stmt = select(Retailer)
    if active_only:
        stmt = stmt.where(Retailer.active.is_(True))
    return [_retailer_out(row) for row in db.scalars(stmt.order_by(Retailer.name))]


@router.post("/retailers", status_code=201)
def create_retailer(payload: RetailerCreate, db: Session = Depends(get_db)):
    name = " ".join(payload.name.split())
    if payload.base_url and not _valid_web_url(payload.base_url):
        raise HTTPException(422, "Die Händler-URL muss eine gültige HTTP- oder HTTPS-Adresse sein.")
    row = Retailer(name=name, base_url=payload.base_url, active=payload.active)
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Dieser Händler ist bereits vorhanden.")
    db.refresh(row)
    return _retailer_out(row)


@router.post("/offers/check", status_code=201)
def record_offer_check(payload: OfferCheckIn, db: Session = Depends(get_db)):
    if not _valid_web_url(payload.product_url):
        raise HTTPException(422, "Die Produkt-URL muss eine gültige HTTP- oder HTTPS-Adresse sein.")
    if not db.get(Fragrance, payload.fragrance_id):
        raise HTTPException(404, "Duft nicht gefunden.")
    retailer = db.get(Retailer, payload.retailer_id)
    if not retailer:
        raise HTTPException(404, "Händler nicht gefunden.")
    if not retailer.active:
        raise HTTPException(409, "Für einen deaktivierten Händler können keine neuen Preisprüfungen gespeichert werden.")

    checked_at = payload.checked_at or datetime.utcnow()
    offer = db.scalar(
        select(FragranceOffer)
        .where(
            FragranceOffer.retailer_id == payload.retailer_id,
            FragranceOffer.product_url == payload.product_url,
        )
        .options(joinedload(FragranceOffer.retailer))
    )
    created = offer is None
    if offer is None:
        offer = FragranceOffer(
            fragrance_id=payload.fragrance_id,
            retailer_id=payload.retailer_id,
            product_url=payload.product_url,
        )
        db.add(offer)
    elif offer.fragrance_id != payload.fragrance_id:
        raise HTTPException(409, "Diese Händler-URL ist bereits einem anderen Duft zugeordnet.")

    offer.product_name = payload.product_name
    offer.size_ml = payload.size_ml
    offer.product_type = payload.product_type
    offer.price_eur = payload.price_eur
    offer.shipping_eur = payload.shipping_eur
    offer.in_stock = payload.in_stock
    offer.checked_at = checked_at
    db.flush()

    db.add(PriceObservation(
        offer_id=offer.id,
        price_eur=payload.price_eur,
        shipping_eur=payload.shipping_eur,
        in_stock=payload.in_stock,
        observed_at=checked_at,
    ))
    db.commit()
    return {"created": created, "offer": _offer_out(offer)}


@router.get("/fragrances/{fragrance_id}")
def fragrance_prices(
    fragrance_id: UUID,
    days: int = Query(default=90, ge=1, le=1095),
    db: Session = Depends(get_db),
):
    fragrance = db.get(Fragrance, fragrance_id)
    if not fragrance:
        raise HTTPException(404, "Duft nicht gefunden.")

    offers = list(db.scalars(
        select(FragranceOffer)
        .join(Retailer, Retailer.id == FragranceOffer.retailer_id)
        .where(
            FragranceOffer.fragrance_id == fragrance_id,
            FragranceOffer.review_status == "APPROVED",
            Retailer.active.is_(True),
        )
        .options(joinedload(FragranceOffer.retailer))
        .order_by(FragranceOffer.checked_at.desc())
    ).unique())
    offer_rows = [_offer_out(row) for row in offers]
    offer_ids = [row.id for row in offers]

    cutoff = datetime.utcnow() - timedelta(days=days)
    history_rows: list[dict] = []
    all_time_lows: dict[str, float] = {}
    if offer_ids:
        history = list(db.execute(
            select(
                PriceObservation.observed_at,
                PriceObservation.price_eur,
                PriceObservation.shipping_eur,
                PriceObservation.in_stock,
                FragranceOffer.id,
                Retailer.name,
                FragranceOffer.size_ml,
            )
            .join(FragranceOffer, FragranceOffer.id == PriceObservation.offer_id)
            .join(Retailer, Retailer.id == FragranceOffer.retailer_id)
            .where(
                FragranceOffer.id.in_(offer_ids),
                PriceObservation.observed_at >= cutoff,
            )
            .order_by(PriceObservation.observed_at)
        ))
        history_rows = [{
            "observed_at": row.observed_at,
            "offer_id": str(row.id),
            "retailer": row.name,
            "size_ml": row.size_ml,
            "price_eur": round(row.price_eur, 2),
            "shipping_eur": round(row.shipping_eur, 2),
            "total_eur": round(row.price_eur + row.shipping_eur, 2),
            "in_stock": row.in_stock,
        } for row in history]

        lows = db.execute(
            select(
                PriceObservation.offer_id,
                func.min(PriceObservation.price_eur + PriceObservation.shipping_eur),
            )
            .where(
                PriceObservation.offer_id.in_(offer_ids),
                PriceObservation.in_stock.is_(True),
            )
            .group_by(PriceObservation.offer_id)
        ).all()
        all_time_lows = {str(offer_id): float(value) for offer_id, value in lows if value is not None}

    grouped: dict[str, list[dict]] = {}
    for row in offer_rows:
        grouped.setdefault(row["variant_key"], []).append(row)
    variants = [
        _variant_group_out(key, rows, history_rows, all_time_lows)
        for key, rows in grouped.items()
    ]
    variants.sort(key=_variant_sort_key, reverse=True)
    default_variant = variants[0] if variants else None

    return {
        "fragrance_id": str(fragrance_id),
        "currency": "EUR",
        "history_days": days,
        "checked_offers": len(offer_rows),
        "available_offers": sum(1 for row in offer_rows if row["in_stock"]),
        "default_variant_key": default_variant["variant_key"] if default_variant else None,
        "cheapest": default_variant["cheapest"] if default_variant else None,
        "historic_low_total_eur": default_variant["historic_low_total_eur"] if default_variant else None,
        "offers": offer_rows,
        "history": history_rows,
        "variants": variants,
    }
