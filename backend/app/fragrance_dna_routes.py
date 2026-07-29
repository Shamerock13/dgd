from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .fragrance_dna import FragranceDNAProfile, FragranceDNAValues
from .fragrance_dna_service import (
    read_fragrance_dna,
    write_fragrance_dna,
    write_personal_fragrance_dna,
)

router = APIRouter(prefix="/api/fragrances", tags=["fragrance-dna"])


@router.get("/{fragrance_id}/dna")
def get_fragrance_dna(fragrance_id: UUID, db: Session = Depends(get_db)):
    try:
        return read_fragrance_dna(db, fragrance_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.put("/{fragrance_id}/dna")
def put_fragrance_dna(
    fragrance_id: UUID,
    payload: FragranceDNAProfile,
    db: Session = Depends(get_db),
):
    try:
        return write_fragrance_dna(db, fragrance_id, payload)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.put("/{fragrance_id}/dna/personal")
def put_personal_fragrance_dna(
    fragrance_id: UUID,
    payload: FragranceDNAValues,
    db: Session = Depends(get_db),
):
    try:
        return write_personal_fragrance_dna(db, fragrance_id, payload)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
