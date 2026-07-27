from math import ceil
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, exists, func, or_, select
from sqlalchemy.orm import Session, joinedload

from .database import get_db
from .models import Brand, Fragrance, FragranceNote, Note
from .schemas import FragranceOut


router = APIRouter(prefix="/catalog", tags=["catalog"])


def _search_score(query: str):
    needle = query.strip().lower()
    contains = f"%{needle}%"
    starts = f"{needle}%"
    note_match = exists(
        select(1)
        .select_from(FragranceNote)
        .join(Note, Note.id == FragranceNote.note_id)
        .where(
            FragranceNote.fragrance_id == Fragrance.id,
            func.lower(Note.name).like(contains),
        )
    )
    return case(
        (func.lower(Fragrance.name) == needle, 100),
        (func.lower(Fragrance.name).like(starts), 90),
        (func.lower(Brand.name) == needle, 85),
        (func.lower(Brand.name).like(starts), 75),
        (func.lower(Fragrance.name).like(contains), 70),
        (func.lower(Brand.name).like(contains), 65),
        (note_match, 55),
        (func.lower(func.coalesce(Fragrance.accords, "")).like(contains), 45),
        (func.lower(func.coalesce(Fragrance.perfumer, "")).like(contains), 35),
        (func.lower(func.coalesce(Fragrance.description, "")).like(contains), 20),
        else_=0,
    )


def _note_filter(note: str):
    pattern = f"%{note.strip()}%"
    return Fragrance.id.in_(
        select(FragranceNote.fragrance_id)
        .join(Note, Note.id == FragranceNote.note_id)
        .where(Note.name.ilike(pattern))
    )


@router.get("/fragrances")
def catalog_fragrances(
    q: str | None = Query(default=None, max_length=120),
    brand_id: UUID | None = None,
    gender: str | None = Query(default=None, max_length=40),
    concentration: str | None = Query(default=None, max_length=100),
    note: str | None = Query(default=None, max_length=120),
    year_from: int | None = Query(default=None, ge=1500, le=2200),
    year_to: int | None = Query(default=None, ge=1500, le=2200),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    min_longevity: float | None = Query(default=None, ge=0, le=10),
    sort: str = Query(default="relevance", pattern="^(relevance|brand-name|name|price-asc|price-desc|year-desc|longevity-desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=6, le=100),
    db: Session = Depends(get_db),
):
    score = _search_score(q) if q and q.strip() else None
    stmt = select(Fragrance).join(Brand).options(joinedload(Fragrance.brand))

    if score is not None:
        stmt = stmt.where(score > 0)
    if brand_id:
        stmt = stmt.where(Fragrance.brand_id == brand_id)
    if gender:
        stmt = stmt.where(Fragrance.gender == gender)
    if concentration:
        stmt = stmt.where(func.lower(Fragrance.concentration) == concentration.strip().lower())
    if note and note.strip():
        stmt = stmt.where(_note_filter(note))
    if year_from is not None:
        stmt = stmt.where(Fragrance.year >= year_from)
    if year_to is not None:
        stmt = stmt.where(Fragrance.year <= year_to)
    if min_price is not None:
        stmt = stmt.where(Fragrance.price_eur >= min_price)
    if max_price is not None:
        stmt = stmt.where(Fragrance.price_eur <= max_price)
    if min_longevity is not None:
        stmt = stmt.where(Fragrance.longevity >= min_longevity)

    count_stmt = select(func.count()).select_from(stmt.order_by(None).options().subquery())
    total = db.scalar(count_stmt) or 0

    if sort == "name":
        stmt = stmt.order_by(Fragrance.name, Brand.name)
    elif sort == "price-asc":
        stmt = stmt.order_by(Fragrance.price_eur.asc().nullslast(), Brand.name, Fragrance.name)
    elif sort == "price-desc":
        stmt = stmt.order_by(Fragrance.price_eur.desc().nullslast(), Brand.name, Fragrance.name)
    elif sort == "year-desc":
        stmt = stmt.order_by(Fragrance.year.desc().nullslast(), Brand.name, Fragrance.name)
    elif sort == "longevity-desc":
        stmt = stmt.order_by(Fragrance.longevity.desc().nullslast(), Brand.name, Fragrance.name)
    elif sort == "relevance" and score is not None:
        stmt = stmt.order_by(score.desc(), Brand.name, Fragrance.name)
    else:
        stmt = stmt.order_by(Brand.name, Fragrance.name)

    rows = list(db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).unique())
    concentrations = list(db.scalars(
        select(Fragrance.concentration)
        .where(Fragrance.concentration.is_not(None), Fragrance.concentration != "")
        .distinct()
        .order_by(Fragrance.concentration)
    ))
    years = db.execute(select(func.min(Fragrance.year), func.max(Fragrance.year))).one()

    return {
        "items": [FragranceOut.model_validate(row).model_dump(mode="json") for row in rows],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": ceil(total / page_size) if total else 0,
            "has_previous": page > 1,
            "has_next": page * page_size < total,
        },
        "facets": {
            "concentrations": concentrations,
            "year_min": years[0],
            "year_max": years[1],
        },
    }
