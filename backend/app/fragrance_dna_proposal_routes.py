from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .database import get_db
from .fragrance_dna_proposal_service import (
    create_proposal,
    list_proposals,
    review_proposal,
)
from .fragrance_dna_proposals import (
    FragranceDNAProposalCreate,
    FragranceDNAProposalOut,
    FragranceDNAProposalReview,
    ProposalStatus,
)


router = APIRouter(prefix="/api/fragrance-dna/proposals", tags=["fragrance-dna-proposals"])


@router.post("", response_model=FragranceDNAProposalOut)
def post_proposal(payload: FragranceDNAProposalCreate, db: Session = Depends(get_db)):
    try:
        return create_proposal(db, payload)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("", response_model=list[FragranceDNAProposalOut])
def get_proposals(
    status: ProposalStatus | None = Query(default=None),
    fragrance_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return list_proposals(db, status=status, fragrance_id=fragrance_id)


@router.post("/{proposal_id}/review", response_model=FragranceDNAProposalOut)
def post_proposal_review(
    proposal_id: UUID,
    payload: FragranceDNAProposalReview,
    db: Session = Depends(get_db),
):
    try:
        return review_proposal(db, proposal_id, payload)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
