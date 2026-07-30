from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Retailer(Base):
    __tablename__ = "price_retailers"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(180), nullable=False, unique=True, index=True)
    base_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    offers: Mapped[list["FragranceOffer"]] = relationship(back_populates="retailer")


class FragranceOffer(Base):
    __tablename__ = "fragrance_offers"
    __table_args__ = (
        UniqueConstraint("retailer_id", "product_url", name="uq_offer_retailer_product_url"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    offer_source_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)
    fragrance_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("fragrances.id", ondelete="CASCADE"), nullable=False, index=True
    )
    retailer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("price_retailers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_url: Mapped[str] = mapped_column(Text, nullable=False)
    product_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    product_variant: Mapped[str | None] = mapped_column(String(240), nullable=True)
    size_ml: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    concentration: Mapped[str | None] = mapped_column(String(80), nullable=True)
    product_type: Mapped[str] = mapped_column(String(30), nullable=False, default="bottle", server_default="bottle")
    price_eur: Mapped[float] = mapped_column(Float, nullable=False)
    shipping_eur: Mapped[float] = mapped_column(Float, nullable=False, default=0, server_default="0")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR", server_default="EUR")
    availability: Mapped[str] = mapped_column(String(40), nullable=False, default="UNKNOWN", server_default="UNKNOWN")
    in_stock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true", index=True)
    ean_gtin: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    merchant_sku: Mapped[str | None] = mapped_column(String(160), nullable=True)
    market_country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    scan_interval: Mapped[str | None] = mapped_column(String(40), nullable=True)
    extraction_hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    trust_status: Mapped[str] = mapped_column(String(30), nullable=False, default="OPEN", server_default="OPEN")
    review_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="PENDING_REVIEW", server_default="PENDING_REVIEW", index=True
    )
    scanner_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false", index=True
    )
    variant_warning: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    retailer: Mapped[Retailer] = relationship(back_populates="offers")
    observations: Mapped[list["PriceObservation"]] = relationship(
        back_populates="offer", cascade="all, delete-orphan"
    )


class PriceObservation(Base):
    __tablename__ = "price_observations"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    offer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("fragrance_offers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    price_eur: Mapped[float] = mapped_column(Float, nullable=False)
    shipping_eur: Mapped[float] = mapped_column(Float, nullable=False, default=0, server_default="0")
    in_stock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    observed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    offer: Mapped[FragranceOffer] = relationship(back_populates="observations")
