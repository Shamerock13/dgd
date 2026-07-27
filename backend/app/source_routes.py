from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import String, func, select
from sqlalchemy.orm import Session

from .catalog_routes import router as catalog_router
from .database import get_db
from .models import Brand, Fragrance, MasterSource, TwinMatch
from .source_schemas import SourceCreate, SourceOut, SourceUpdate


router = APIRouter(prefix="/api", tags=["sources"])
router.include_router(catalog_router)


def _source_id() -> str:
    return f"SRC-{uuid4().hex[:12].upper()}"


@router.get("/sources", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db)):
    return list(db.scalars(select(MasterSource).order_by(MasterSource.name)))


@router.post("/sources", response_model=SourceOut, status_code=201)
def create_source(payload: SourceCreate, db: Session = Depends(get_db)):
    item = MasterSource(id=payload.id or _source_id(), **payload.model_dump(exclude={"id"}))
    db.add(item)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(409, "Diese Quellen-ID ist bereits vergeben.")
    db.refresh(item)
    return item


@router.put("/sources/{source_id}", response_model=SourceOut)
def update_source(source_id: str, payload: SourceUpdate, db: Session = Depends(get_db)):
    item = db.get(MasterSource, source_id)
    if not item:
        raise HTTPException(404, "Quelle nicht gefunden")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/sources/{source_id}", status_code=204)
def delete_source(source_id: str, db: Session = Depends(get_db)):
    item = db.get(MasterSource, source_id)
    if not item:
        raise HTTPException(404, "Quelle nicht gefunden")
    db.delete(item)
    db.commit()
    return Response(status_code=204)


@router.get("/verification/summary")
def verification_summary(db: Session = Depends(get_db)):
    source_total = db.scalar(select(func.count(MasterSource.id))) or 0
    trusted = db.scalar(select(func.count(MasterSource.id)).where(MasterSource.trust_status == "TRUSTED")) or 0
    review = db.scalar(select(func.count(MasterSource.id)).where(MasterSource.trust_status == "REVIEW")) or 0
    rejected = db.scalar(select(func.count(MasterSource.id)).where(MasterSource.trust_status == "REJECTED")) or 0
    open_sources = source_total - trusted - review - rejected
    brands_open = db.scalar(select(func.count(Brand.id)).where(Brand.verification_status != "VERIFIED")) or 0
    fragrances_without_source = db.scalar(
        select(func.count(Fragrance.id)).where(
            ~Fragrance.id.cast(String).in_(
                select(MasterSource.object_id).where(MasterSource.object_type == "FRAGRANCE")
            )
        )
    ) or 0
    twins_without_source = db.scalar(
        select(func.count(TwinMatch.id)).where(
            ~TwinMatch.id.cast(String).in_(
                select(MasterSource.object_id).where(MasterSource.object_type == "TWIN")
            )
        )
    ) or 0
    return {
        "sources": source_total,
        "trusted": trusted,
        "review": review,
        "rejected": rejected,
        "open": open_sources,
        "brands_open": brands_open,
        "fragrances_without_source": fragrances_without_source,
        "twins_without_source": twins_without_source,
    }
