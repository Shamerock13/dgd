from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .fragrance_dna import FragranceDNAValues


ProposalStatus = Literal["OPEN", "APPROVED", "REJECTED"]
ProposalSource = Literal["RESEARCH", "AI_ASSISTED", "RULE_BASED", "MANUAL"]


class FragranceDNAProposalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fragrance_id: UUID
    values: FragranceDNAValues
    source: ProposalSource
    source_label: str | None = Field(default=None, max_length=255)
    source_url: str | None = None
    rationale: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class FragranceDNAProposalReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["APPROVE", "REJECT"]
    accepted_values: FragranceDNAValues | None = None
    review_note: str | None = None


class FragranceDNAProposalOut(BaseModel):
    id: UUID
    fragrance_id: UUID
    values: dict[str, float]
    source: ProposalSource
    source_label: str | None
    source_url: str | None
    rationale: str | None
    confidence: float | None
    status: ProposalStatus
    created_at: datetime
    reviewed_at: datetime | None
    review_note: str | None
