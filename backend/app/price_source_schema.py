from __future__ import annotations

from sqlalchemy import event, text

from .database import Base


PRICE_SOURCE_SCHEMA_VERSION = "0016-price-sources"


STATEMENTS = (
    "ALTER TABLE fragrance_offers ADD COLUMN IF NOT EXISTS offer_source_id VARCHAR(64)",
    "ALTER TABLE fragrance_offers ADD COLUMN IF NOT EXISTS product_variant VARCHAR(240)",
    "ALTER TABLE fragrance_offers ADD COLUMN IF NOT EXISTS concentration VARCHAR(80)",
    "ALTER TABLE fragrance_offers ADD COLUMN IF NOT EXISTS currency VARCHAR(3)",
    "ALTER TABLE fragrance_offers ADD COLUMN IF NOT EXISTS availability VARCHAR(40)",
    "ALTER TABLE fragrance_offers ADD COLUMN IF NOT EXISTS ean_gtin VARCHAR(32)",
    "ALTER TABLE fragrance_offers ADD COLUMN IF NOT EXISTS merchant_sku VARCHAR(160)",
    "ALTER TABLE fragrance_offers ADD COLUMN IF NOT EXISTS market_country VARCHAR(2)",
    "ALTER TABLE fragrance_offers ADD COLUMN IF NOT EXISTS scan_interval VARCHAR(40)",
    "ALTER TABLE fragrance_offers ADD COLUMN IF NOT EXISTS extraction_hint TEXT",
    "ALTER TABLE fragrance_offers ADD COLUMN IF NOT EXISTS trust_status VARCHAR(30)",
    "ALTER TABLE fragrance_offers ADD COLUMN IF NOT EXISTS review_status VARCHAR(30)",
    "ALTER TABLE fragrance_offers ADD COLUMN IF NOT EXISTS scanner_active BOOLEAN",
    "ALTER TABLE fragrance_offers ADD COLUMN IF NOT EXISTS variant_warning TEXT",
    "ALTER TABLE fragrance_offers ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP",
    "UPDATE fragrance_offers SET currency = 'EUR' WHERE currency IS NULL OR btrim(currency) = ''",
    "UPDATE fragrance_offers SET availability = CASE WHEN in_stock THEN 'IN_STOCK' ELSE 'OUT_OF_STOCK' END WHERE availability IS NULL OR btrim(availability) = ''",
    "UPDATE fragrance_offers SET trust_status = 'OPEN' WHERE trust_status IS NULL OR btrim(trust_status) = ''",
    "UPDATE fragrance_offers SET review_status = 'PENDING_REVIEW' WHERE review_status IS NULL OR btrim(review_status) = ''",
    "UPDATE fragrance_offers SET scanner_active = FALSE WHERE scanner_active IS NULL",
    "UPDATE fragrance_offers SET updated_at = COALESCE(checked_at, created_at, CURRENT_TIMESTAMP) WHERE updated_at IS NULL",
    "ALTER TABLE fragrance_offers ALTER COLUMN currency SET DEFAULT 'EUR'",
    "ALTER TABLE fragrance_offers ALTER COLUMN availability SET DEFAULT 'UNKNOWN'",
    "ALTER TABLE fragrance_offers ALTER COLUMN trust_status SET DEFAULT 'OPEN'",
    "ALTER TABLE fragrance_offers ALTER COLUMN review_status SET DEFAULT 'PENDING_REVIEW'",
    "ALTER TABLE fragrance_offers ALTER COLUMN scanner_active SET DEFAULT FALSE",
    "ALTER TABLE fragrance_offers ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP",
    "ALTER TABLE fragrance_offers ALTER COLUMN currency SET NOT NULL",
    "ALTER TABLE fragrance_offers ALTER COLUMN availability SET NOT NULL",
    "ALTER TABLE fragrance_offers ALTER COLUMN trust_status SET NOT NULL",
    "ALTER TABLE fragrance_offers ALTER COLUMN review_status SET NOT NULL",
    "ALTER TABLE fragrance_offers ALTER COLUMN scanner_active SET NOT NULL",
    "ALTER TABLE fragrance_offers ALTER COLUMN updated_at SET NOT NULL",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_fragrance_offers_offer_source_id ON fragrance_offers (offer_source_id) WHERE offer_source_id IS NOT NULL",
    "CREATE INDEX IF NOT EXISTS ix_fragrance_offers_review_status ON fragrance_offers (review_status)",
    "CREATE INDEX IF NOT EXISTS ix_fragrance_offers_scanner_active ON fragrance_offers (scanner_active)",
    "CREATE INDEX IF NOT EXISTS ix_fragrance_offers_ean_gtin ON fragrance_offers (ean_gtin)",
)


@event.listens_for(Base.metadata, "after_create")
def ensure_price_source_schema(_metadata, connection, **_kwargs) -> None:
    """Extend existing price tables after the normal metadata create step.

    Every statement is idempotent. This hook runs before the application starts
    serving requests and keeps existing installations compatible while package
    16.7.4 is developed on its feature branch.
    """
    table_exists = connection.execute(
        text("SELECT to_regclass('public.fragrance_offers') IS NOT NULL")
    ).scalar_one()
    if not table_exists:
        return
    for statement in STATEMENTS:
        connection.execute(text(statement))
