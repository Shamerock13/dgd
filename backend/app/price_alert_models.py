from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class PriceAlert(Base):
    __tablename__ = "price_alerts"
    __table_args__ = (
        UniqueConstraint("fragrance_id", "variant_key", name="uq_price_alert_fragrance_variant"),
        CheckConstraint(
            "target_total_eur IS NOT NULL OR max_percent_above_low IS NOT NULL",
            name="ck_price_alert_threshold",
        ),
        CheckConstraint(
            "target_total_eur IS NULL OR target_total_eur > 0",
            name="ck_price_alert_target_positive",
        ),
        CheckConstraint(
            "max_percent_above_low IS NULL OR (max_percent_above_low >= 0 AND max_percent_above_low <= 500)",
            name="ck_price_alert_percent_range",
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    fragrance_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("fragrances.id", ondelete="CASCADE"), nullable=False, index=True
    )
    variant_key: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    product_type: Mapped[str] = mapped_column(String(30), nullable=False)
    size_ml: Mapped[float | None] = mapped_column(Float, nullable=True)
    concentration: Mapped[str | None] = mapped_column(String(80), nullable=True)

    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true", index=True)
    target_total_eur: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_percent_above_low: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="WAITING", server_default="WAITING", index=True)
    current_total_eur: Mapped[float | None] = mapped_column(Float, nullable=True)
    historic_low_total_eur: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_evaluated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    trigger_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
