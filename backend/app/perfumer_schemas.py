from pydantic import BaseModel, ConfigDict, Field


class PerfumerBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    birth_year: int | None = Field(default=None, ge=1800, le=2200)
    nationality: str | None = Field(default=None, max_length=160)
    profile: str | None = None
    style: str | None = None
    notable_works: str | None = None
    article_status: str = Field(default="OPEN", pattern="^(OPEN|REVIEW|VERIFIED)$")
    primary_source: str | None = None
    note: str | None = None


class PerfumerCreate(PerfumerBase):
    id: str | None = Field(default=None, max_length=32)


class PerfumerUpdate(PerfumerBase):
    pass


class PerfumerOut(PerfumerBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
