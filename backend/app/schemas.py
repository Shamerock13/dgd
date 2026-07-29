from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BrandBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    country: str | None = None
    founded_year: int | None = Field(default=None, ge=1500, le=2200)
    website_url: str | None = None
    verification_status: str = Field(default="OPEN", pattern="^(OPEN|VERIFIED|REVIEW)$")
    description: str | None = None


class BrandCreate(BrandBase):
    pass


class BrandUpdate(BrandBase):
    pass


class BrandOut(BrandBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class FragranceBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    brand_id: UUID
    year: int | None = None
    gender: str = "Unisex"
    concentration: str | None = None
    perfumer: str | None = None
    price_eur: float | None = None
    image_url: str | None = None
    image_source_name: str | None = Field(default=None, max_length=200)
    image_source_url: str | None = None
    image_usage_note: str | None = None
    image_status: str = Field(default="OPEN", pattern="^(OPEN|VERIFIED|BROKEN)$")
    description: str | None = None
    top_notes: str | None = None
    heart_notes: str | None = None
    base_notes: str | None = None
    accords: str | None = None

    longevity: float | None = Field(default=None, ge=0, le=10)
    projection: float | None = Field(default=None, ge=0, le=10)
    sweetness: float | None = Field(default=None, ge=0, le=10)
    freshness: float | None = Field(default=None, ge=0, le=10)

    longevity_min_hours: float | None = Field(default=None, ge=0, le=72)
    longevity_max_hours: float | None = Field(default=None, ge=0, le=72)
    longevity_score: float | None = Field(default=None, ge=0, le=10)
    sillage: float | None = Field(default=None, ge=0, le=10)
    performance_score: float | None = Field(default=None, ge=0, le=10)
    projection_first_hour: float | None = Field(default=None, ge=0, le=10)
    projection_after_three_hours: float | None = Field(default=None, ge=0, le=10)
    drydown_strength: float | None = Field(default=None, ge=0, le=10)
    performance_source_count: int | None = Field(default=None, ge=0)
    performance_confidence: float | None = Field(default=None, ge=0, le=100)
    performance_disagreement: float | None = Field(default=None, ge=0, le=100)
    performance_status: str = Field(default="OPEN", pattern="^(OPEN|VERIFIED|REVIEW_REQUIRED)$")
    performance_researched_at: datetime | None = None
    performance_version: str | None = Field(default=None, max_length=120)
    performance_production_period: str | None = Field(default=None, max_length=120)

    personal_longevity_hours: float | None = Field(default=None, ge=0, le=72)
    personal_projection: float | None = Field(default=None, ge=0, le=10)
    personal_sillage: float | None = Field(default=None, ge=0, le=10)
    personal_performance_score: float | None = Field(default=None, ge=0, le=10)

    fragrance_dna: dict[str, float | None] | None = None
    fragrance_dna_source: str | None = Field(default=None, pattern="^(MANUAL|RESEARCH|RULE_BASED)$")
    fragrance_dna_status: str = Field(default="OPEN", pattern="^(OPEN|VERIFIED|REVIEW_REQUIRED)$")
    fragrance_dna_source_count: int | None = Field(default=None, ge=0)
    fragrance_dna_confidence: float | None = Field(default=None, ge=0, le=1)
    fragrance_dna_disagreement: float | None = Field(default=None, ge=0, le=1)
    fragrance_dna_researched_at: datetime | None = None
    personal_fragrance_dna: dict[str, float | None] | None = None

    @model_validator(mode="after")
    def validate_performance_range(self):
        if (
            self.longevity_min_hours is not None
            and self.longevity_max_hours is not None
            and self.longevity_min_hours > self.longevity_max_hours
        ):
            raise ValueError("longevity_min_hours darf nicht größer als longevity_max_hours sein")
        return self


class FragranceCreate(FragranceBase):
    pass


class FragranceUpdate(FragranceBase):
    pass


class FragranceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    brand: BrandOut
    year: int | None = None
    gender: str
    concentration: str | None = None
    perfumer: str | None = None
    price_eur: float | None = None
    image_url: str | None = None
    image_source_name: str | None = None
    image_source_url: str | None = None
    image_usage_note: str | None = None
    image_status: str = "OPEN"
    description: str | None = None
    top_notes: str | None = None
    heart_notes: str | None = None
    base_notes: str | None = None
    accords: str | None = None
    longevity: float | None = None
    projection: float | None = None
    sweetness: float | None = None
    freshness: float | None = None
    longevity_min_hours: float | None = None
    longevity_max_hours: float | None = None
    longevity_score: float | None = None
    sillage: float | None = None
    performance_score: float | None = None
    projection_first_hour: float | None = None
    projection_after_three_hours: float | None = None
    drydown_strength: float | None = None
    performance_source_count: int | None = None
    performance_confidence: float | None = None
    performance_disagreement: float | None = None
    performance_status: str = "OPEN"
    performance_researched_at: datetime | None = None
    performance_version: str | None = None
    performance_production_period: str | None = None
    personal_longevity_hours: float | None = None
    personal_projection: float | None = None
    personal_sillage: float | None = None
    personal_performance_score: float | None = None
    fragrance_dna: dict[str, float | None] | None = None
    fragrance_dna_source: str | None = None
    fragrance_dna_status: str = "OPEN"
    fragrance_dna_source_count: int | None = None
    fragrance_dna_confidence: float | None = None
    fragrance_dna_disagreement: float | None = None
    fragrance_dna_researched_at: datetime | None = None
    personal_fragrance_dna: dict[str, float | None] | None = None


class TwinCreate(BaseModel):
    original_id: UUID
    alternative_id: UUID
    similarity: float = Field(ge=0, le=100)
    differences: str | None = None
    commonalities: str | None = None
    source_note: str | None = None


class TwinOut(BaseModel):
    id: UUID
    original: FragranceOut
    alternative: FragranceOut
    similarity: float
    differences: str | None = None
    commonalities: str | None = None
    source_note: str | None = None


class NoteBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str | None = None
    description: str | None = None


class NoteCreate(NoteBase):
    pass


class NoteUpdate(NoteBase):
    pass


class NoteOut(NoteBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class FragranceNoteAssignment(BaseModel):
    note_id: UUID
    pyramid: str = Field(pattern="^(top|heart|base)$")
    position: int = Field(default=0, ge=0)


class FragranceNoteOut(BaseModel):
    id: UUID
    pyramid: str
    position: int
    note: NoteOut
