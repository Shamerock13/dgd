from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


USAGE_STATUS_ALIASES = {
    "open": "OPEN",
    "offen": "OPEN",
    "allowed": "ALLOWED",
    "nutzbar": "ALLOWED",
    "freigegeben": "ALLOWED",
    "restricted": "RESTRICTED",
    "eingeschränkt": "RESTRICTED",
    "eingeschraenkt": "RESTRICTED",
    "privat / vor veröffentlichung prüfen": "RESTRICTED",
    "privat / vor veroeffentlichung pruefen": "RESTRICTED",
    "internal": "INTERNAL",
    "intern": "INTERNAL",
    "projektintern": "INTERNAL",
    "nur intern": "INTERNAL",
}

TRUST_STATUS_ALIASES = {
    "open": "OPEN",
    "offen": "OPEN",
    "ungeprüft": "OPEN",
    "ungeprueft": "OPEN",
    "review": "REVIEW",
    "in prüfung": "REVIEW",
    "in pruefung": "REVIEW",
    "mittel": "REVIEW",
    "mittel bis hoch": "REVIEW",
    "trusted": "TRUSTED",
    "vertrauenswürdig": "TRUSTED",
    "vertrauenswuerdig": "TRUSTED",
    "hoch": "TRUSTED",
    "rejected": "REJECTED",
    "verworfen": "REJECTED",
    "abgelehnt": "REJECTED",
}


def _normalize_status(value: str | None, aliases: dict[str, str], fallback: str) -> str:
    if value is None:
        return fallback
    raw = str(value).strip()
    if not raw:
        return fallback
    upper = raw.upper()
    if upper in set(aliases.values()):
        return upper
    return aliases.get(raw.casefold(), fallback)


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

    @field_validator("usage_status", mode="before")
    @classmethod
    def normalize_usage_status(cls, value):
        return _normalize_status(value, USAGE_STATUS_ALIASES, "OPEN")

    @field_validator("trust_status", mode="before")
    @classmethod
    def normalize_trust_status(cls, value):
        return _normalize_status(value, TRUST_STATUS_ALIASES, "OPEN")


class SourceCreate(SourceBase):
    id: str | None = Field(default=None, max_length=32)


class SourceUpdate(SourceBase):
    pass


class SourceOut(SourceBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
