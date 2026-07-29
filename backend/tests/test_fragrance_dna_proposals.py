from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.fragrance_dna_proposals import (
    FragranceDNAProposalCreate,
    FragranceDNAProposalReview,
)


def test_proposal_accepts_partial_values():
    proposal = FragranceDNAProposalCreate(
        fragrance_id=uuid4(),
        values={"fresh": 7.5, "woody": 4.0},
        source="RESEARCH",
        confidence=0.82,
    )
    assert proposal.values.fresh == 7.5
    assert proposal.values.citrus is None


def test_proposal_rejects_unknown_dimension():
    with pytest.raises(ValidationError):
        FragranceDNAProposalCreate(
            fragrance_id=uuid4(),
            values={"fresh": 5, "metallic": 8},
            source="RESEARCH",
        )


def test_proposal_rejects_confidence_over_one():
    with pytest.raises(ValidationError):
        FragranceDNAProposalCreate(
            fragrance_id=uuid4(),
            values={"fresh": 5},
            source="AI_ASSISTED",
            confidence=1.1,
        )


def test_review_accepts_rejection_without_values():
    review = FragranceDNAProposalReview(decision="REJECT", review_note="Quelle nicht belastbar")
    assert review.accepted_values is None


def test_review_accepts_partial_confirmation():
    review = FragranceDNAProposalReview(
        decision="APPROVE",
        accepted_values={"woody": 8.0},
    )
    assert review.accepted_values.woody == 8.0
    assert review.accepted_values.fresh is None


def test_review_rejects_invalid_decision():
    with pytest.raises(ValidationError):
        FragranceDNAProposalReview(decision="PUBLISH")
