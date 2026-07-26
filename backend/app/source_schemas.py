from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class SourceBase(BaseModel):
    name: str = Field(min_length=1, max_length=500)
    object_type: str | None = Field(default=None, max_length=160)
    object_id: str | None = Field(default=None, max_length=255)
    source_type: str | None = Field(default=None, max_length=255)
    file_or_url: str | None = None
    source_date: datetime | None = None
    usage_status: str = Field(default="OPEN", pattern="^(OPEN|ALLOWED|RESTRICTED|INTERNAL)$")
    trust_status: str = Field(default="OPEN", pattern="^(OPEN|REVIEW|TRUSTED|REJECTED)$")
    note: str | None = None


class SourceCreate(SourceBase):
    id: str | None = Field(default=None, max_length=32)


class SourceUpdate(SourceBase):
    pass


class SourceOut(SourceBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
