from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, event, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class ResearchSource(Base):
    __tablename__ = "research_sources"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    adapter_type: Mapped[str] = mapped_column(String(30), nullable=False, default="SINGLE")
    link_pattern: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_pages: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    same_domain_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    interval_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ResearchScanRun(Base):
    __tablename__ = "research_scan_runs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("research_sources.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    found_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pages_scanned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    links_discovered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class ScannerControl(Base):
    __tablename__ = "scanner_control"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    poll_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_cycle_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_cycle_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    last_cycle_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


@event.listens_for(Base.metadata, "after_create")
def ensure_research_adapter_columns(target, connection, **kwargs):
    if connection.dialect.name != "postgresql":
        return
    statements = (
        "ALTER TABLE research_sources ADD COLUMN IF NOT EXISTS adapter_type VARCHAR(30)",
        "ALTER TABLE research_sources ADD COLUMN IF NOT EXISTS link_pattern TEXT",
        "ALTER TABLE research_sources ADD COLUMN IF NOT EXISTS max_pages INTEGER",
        "ALTER TABLE research_sources ADD COLUMN IF NOT EXISTS same_domain_only BOOLEAN",
        "UPDATE research_sources SET adapter_type='SINGLE' WHERE adapter_type IS NULL",
        "UPDATE research_sources SET max_pages=20 WHERE max_pages IS NULL",
        "UPDATE research_sources SET same_domain_only=TRUE WHERE same_domain_only IS NULL",
        "ALTER TABLE research_sources ALTER COLUMN adapter_type SET DEFAULT 'SINGLE'",
        "ALTER TABLE research_sources ALTER COLUMN adapter_type SET NOT NULL",
        "ALTER TABLE research_sources ALTER COLUMN max_pages SET DEFAULT 20",
        "ALTER TABLE research_sources ALTER COLUMN max_pages SET NOT NULL",
        "ALTER TABLE research_sources ALTER COLUMN same_domain_only SET DEFAULT TRUE",
        "ALTER TABLE research_sources ALTER COLUMN same_domain_only SET NOT NULL",
        "ALTER TABLE research_scan_runs ADD COLUMN IF NOT EXISTS pages_scanned INTEGER",
        "ALTER TABLE research_scan_runs ADD COLUMN IF NOT EXISTS links_discovered INTEGER",
        "UPDATE research_scan_runs SET pages_scanned=0 WHERE pages_scanned IS NULL",
        "UPDATE research_scan_runs SET links_discovered=0 WHERE links_discovered IS NULL",
        "ALTER TABLE research_scan_runs ALTER COLUMN pages_scanned SET DEFAULT 0",
        "ALTER TABLE research_scan_runs ALTER COLUMN pages_scanned SET NOT NULL",
        "ALTER TABLE research_scan_runs ALTER COLUMN links_discovered SET DEFAULT 0",
        "ALTER TABLE research_scan_runs ALTER COLUMN links_discovered SET NOT NULL",
        "INSERT INTO scanner_control(id,enabled,poll_seconds) VALUES(1,FALSE,300) ON CONFLICT(id) DO NOTHING",
    )
    for statement in statements:
        connection.execute(text(statement))
