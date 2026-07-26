from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import Fragrance, MasterPerfumer
from .perfumer_schemas import PerfumerCreate, PerfumerOut, PerfumerUpdate


router = APIRouter(prefix="/api", tags=["perfumers"])


def _perfumer_id() -> str:
    return f"PER-{uuid4().hex[:12].upper()}"


@router.get("/perfumers", response_model=list[PerfumerOut])
def list_perfumers(db: Session = Depends(get_db)):
    return list(db.scalars(select(MasterPerfumer).order_by(MasterPerfumer.name)))


@router.post("/perfumers", response_model=PerfumerOut, status_code=201)
def create_perfumer(payload: PerfumerCreate, db: Session = Depends(get_db)):
    item = MasterPerfumer(id=payload.id or _perfumer_id(), **payload.model_dump(exclude={"id"}))
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/perfumers/{perfumer_id}", response_model=PerfumerOut)
def update_perfumer(perfumer_id: str, payload: PerfumerUpdate, db: Session = Depends(get_db)):
    item = db.get(MasterPerfumer, perfumer_id)
    if not item:
        raise HTTPException(404, "Parfümeur nicht gefunden")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/perfumers/{perfumer_id}", status_code=204)
def delete_perfumer(perfumer_id: str, db: Session = Depends(get_db)):
    item = db.get(MasterPerfumer, perfumer_id)
    if not item:
        raise HTTPException(404, "Parfümeur nicht gefunden")
    linked = db.scalar(select(Fragrance.id).where(Fragrance.perfumer == item.name).limit(1))
    if linked:
        raise HTTPException(409, "Das Profil kann nicht gelöscht werden, solange Düfte diesen Namen verwenden.")
    db.delete(item)
    db.commit()
    return Response(status_code=204)
