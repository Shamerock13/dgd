from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

DNA_DIMENSIONS = (
    "fresh",
    "citrus",
    "green",
    "aquatic",
    "floral",
    "fruity",
    "sweet",
    "gourmand",
    "spicy",
    "woody",
    "smoky",
    "earthy",
    "resinous",
    "leathery",
    "powdery",
    "animalic",
)


class FragranceDNAValues(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fresh: float | None = Field(default=None, ge=0, le=10)
    citrus: float | None = Field(default=None, ge=0, le=10)
    green: float | None = Field(default=None, ge=0, le=10)
    aquatic: float | None = Field(default=None, ge=0, le=10)
    floral: float | None = Field(default=None, ge=0, le=10)
    fruity: float | None = Field(default=None, ge=0, le=10)
    sweet: float | None = Field(default=None, ge=0, le=10)
    gourmand: float | None = Field(default=None, ge=0, le=10)
    spicy: float | None = Field(default=None, ge=0, le=10)
    woody: float | None = Field(default=None, ge=0, le=10)
    smoky: float | None = Field(default=None, ge=0, le=10)
    earthy: float | None = Field(default=None, ge=0, le=10)
    resinous: float | None = Field(default=None, ge=0, le=10)
    leathery: float | None = Field(default=None, ge=0, le=10)
    powdery: float | None = Field(default=None, ge=0, le=10)
    animalic: float | None = Field(default=None, ge=0, le=10)

    @model_validator(mode="after")
    def reject_empty_payload(self):
        if not any(getattr(self, key) is not None for key in DNA_DIMENSIONS):
            raise ValueError("Mindestens eine Duft-DNA-Dimension muss gesetzt sein")
        return self


class FragranceDNAMetadata(BaseModel):
    source: Literal["MANUAL", "RESEARCH", "RULE_BASED"]
    status: Literal["OPEN", "VERIFIED", "REVIEW_REQUIRED"] = "OPEN"
    source_count: int | None = Field(default=None, ge=0)
    confidence: float | None = Field(default=None, ge=0, le=1)
    disagreement: float | None = Field(default=None, ge=0, le=1)
    researched_at: datetime | None = None


class FragranceDNAProfile(BaseModel):
    values: FragranceDNAValues
    metadata: FragranceDNAMetadata


class FragranceDNAOut(FragranceDNAProfile):
    model_config = ConfigDict(from_attributes=True)
