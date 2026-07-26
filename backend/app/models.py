from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    String, Integer, Float, Text, ForeignKey, DateTime, Date, Boolean, JSON,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    dgd_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    master_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    fragrances: Mapped[list["Fragrance"]] = relationship(back_populates="brand")


class Fragrance(Base):
    __tablename__ = "fragrances"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    dgd_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    brand_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("brands.id"), index=True
    )
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str] = mapped_column(String(40), default="Unisex")
    concentration: Mapped[str | None] = mapped_column(String(80), nullable=True)
    perfumer: Mapped[str | None] = mapped_column(String(160), nullable=True)
    price_eur: Mapped[float | None] = mapped_column(Float, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_source_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    image_source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_usage_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_status: Mapped[str] = mapped_column(String(30), nullable=False, default="OPEN", server_default="OPEN")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Bestehende Freitextfelder bleiben für Kompatibilität und Anzeige erhalten.
    top_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    heart_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    accords: Mapped[str | None] = mapped_column(Text, nullable=True)
    longevity: Mapped[float | None] = mapped_column(Float, nullable=True)
    projection: Mapped[float | None] = mapped_column(Float, nullable=True)
    sweetness: Mapped[float | None] = mapped_column(Float, nullable=True)
    freshness: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    master_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    brand: Mapped["Brand"] = relationship(back_populates="fragrances")
    note_links: Mapped[list["FragranceNote"]] = relationship(
        back_populates="fragrance", cascade="all, delete-orphan"
    )


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    fragrance_links: Mapped[list["FragranceNote"]] = relationship(
        back_populates="note", cascade="all, delete-orphan"
    )


class FragranceNote(Base):
    __tablename__ = "fragrance_notes"
    __table_args__ = (
        UniqueConstraint(
            "fragrance_id", "note_id", "pyramid",
            name="uq_fragrance_note_pyramid"
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    fragrance_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("fragrances.id", ondelete="CASCADE"),
        index=True
    )
    note_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("notes.id", ondelete="CASCADE"),
        index=True
    )
    pyramid: Mapped[str] = mapped_column(String(20), index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)

    fragrance: Mapped["Fragrance"] = relationship(back_populates="note_links")
    note: Mapped["Note"] = relationship(back_populates="fragrance_links")


class TwinMatch(Base):
    __tablename__ = "twin_matches"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    dgd_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    original_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("fragrances.id"), index=True
    )
    alternative_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("fragrances.id"), index=True
    )
    similarity: Mapped[float] = mapped_column(Float)
    differences: Mapped[str | None] = mapped_column(Text, nullable=True)
    commonalities: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    master_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    original: Mapped["Fragrance"] = relationship(foreign_keys=[original_id])
    alternative: Mapped["Fragrance"] = relationship(foreign_keys=[alternative_id])


class MasterPerfumer(Base):
    __tablename__ = "master_perfumers"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(160), nullable=True)
    profile: Mapped[str | None] = mapped_column(Text, nullable=True)
    style: Mapped[str | None] = mapped_column(Text, nullable=True)
    notable_works: Mapped[str | None] = mapped_column(Text, nullable=True)
    article_status: Mapped[str | None] = mapped_column(String(160), nullable=True)
    primary_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    master_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class MasterSource(Base):
    __tablename__ = "master_sources"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    object_type: Mapped[str | None] = mapped_column(String(160), nullable=True)
    object_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_or_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    usage_status: Mapped[str | None] = mapped_column(String(255), nullable=True)
    trust_status: Mapped[str | None] = mapped_column(String(160), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    master_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class MasterImportRun(Base):
    __tablename__ = "master_import_runs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
