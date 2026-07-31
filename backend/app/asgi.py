from __future__ import annotations

from . import migrations
from .migrations import Migration
from .price_source_review_migration import register_price_source_review_migration
from .price_alert_migration import register_price_alert_migration


def _register_fragrance_dna_migration() -> None:
    if any(item.version == "0013" for item in migrations.MIGRATIONS):
        return
    migrations.MIGRATIONS = (
        *migrations.MIGRATIONS,
        Migration(
            version="0013",
            description="Strukturierte Duft-DNA und persönliche DNA ergänzen",
            statements=(
                "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS fragrance_dna JSONB",
                "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS fragrance_dna_source VARCHAR(30)",
                "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS fragrance_dna_status VARCHAR(30)",
                "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS fragrance_dna_source_count INTEGER",
                "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS fragrance_dna_confidence DOUBLE PRECISION",
                "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS fragrance_dna_disagreement DOUBLE PRECISION",
                "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS fragrance_dna_researched_at TIMESTAMP",
                "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS personal_fragrance_dna JSONB",
                "UPDATE fragrances SET fragrance_dna_status = 'OPEN' WHERE fragrance_dna_status IS NULL OR btrim(fragrance_dna_status) = ''",
                "ALTER TABLE fragrances ALTER COLUMN fragrance_dna_status SET DEFAULT 'OPEN'",
                "ALTER TABLE fragrances ALTER COLUMN fragrance_dna_status SET NOT NULL",
                "CREATE INDEX IF NOT EXISTS ix_fragrances_dna_status ON fragrances (fragrance_dna_status)",
            ),
        ),
    )


def _register_fragrance_dna_proposal_migration() -> None:
    if any(item.version == "0014" for item in migrations.MIGRATIONS):
        return
    migrations.MIGRATIONS = (
        *migrations.MIGRATIONS,
        Migration(
            version="0014",
            description="Kontrollierte Duft-DNA-Recherchevorschläge ergänzen",
            statements=(
                "CREATE TABLE IF NOT EXISTS fragrance_dna_proposals (id UUID PRIMARY KEY, fragrance_id UUID NOT NULL REFERENCES fragrances(id) ON DELETE CASCADE, values JSONB NOT NULL, source VARCHAR(30) NOT NULL, source_label VARCHAR(255), source_url TEXT, rationale TEXT, confidence DOUBLE PRECISION, status VARCHAR(30) NOT NULL DEFAULT 'OPEN', created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, reviewed_at TIMESTAMP, review_note TEXT)",
                "CREATE INDEX IF NOT EXISTS ix_fragrance_dna_proposals_fragrance ON fragrance_dna_proposals (fragrance_id)",
                "CREATE INDEX IF NOT EXISTS ix_fragrance_dna_proposals_status ON fragrance_dna_proposals (status)",
            ),
        ),
    )


def _register_performance_research_migration() -> None:
    if any(item.version == "0015" for item in migrations.MIGRATIONS):
        return
    migrations.MIGRATIONS = (
        *migrations.MIGRATIONS,
        Migration(
            version="0015",
            description="Kontrollierte KI-Vorschläge für strukturierte Performance-Daten",
            statements=(
                "CREATE TABLE IF NOT EXISTS performance_research_proposals (id UUID PRIMARY KEY, fragrance_id UUID NOT NULL REFERENCES fragrances(id) ON DELETE CASCADE, values JSONB NOT NULL, accepted_values JSONB, source_label VARCHAR(255), source_url TEXT, sources JSONB, rationale TEXT, confidence DOUBLE PRECISION, status VARCHAR(30) NOT NULL DEFAULT 'OPEN', created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, reviewed_at TIMESTAMP, review_note TEXT)",
                "CREATE INDEX IF NOT EXISTS ix_performance_research_fragrance ON performance_research_proposals (fragrance_id)",
                "CREATE INDEX IF NOT EXISTS ix_performance_research_status ON performance_research_proposals (status)",
            ),
        ),
    )


def _register_price_source_migration() -> None:
    if any(item.version == "0016" for item in migrations.MIGRATIONS):
        return
    migrations.MIGRATIONS = (
        *migrations.MIGRATIONS,
        Migration(
            version="0016",
            description="Geprüfte Preisquellen und sichere Scanner-Freigabe ergänzen",
            statements=(
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
            ),
        ),
    )


def _move_spa_fallback_to_end() -> None:
    fallback_routes = [route for route in app.router.routes if getattr(route, "path", None) == "/{full_path:path}"]
    if not fallback_routes:
        return
    for route in fallback_routes:
        app.router.routes.remove(route)
        app.router.routes.append(route)


_register_fragrance_dna_migration()
_register_fragrance_dna_proposal_migration()
_register_performance_research_migration()
_register_price_source_migration()
register_price_source_review_migration()
register_price_alert_migration()

from .main import app  # noqa: E402
from .fragrance_dna_routes import router as fragrance_dna_router  # noqa: E402
from .fragrance_dna_proposal_routes import router as fragrance_dna_proposal_router  # noqa: E402
from .performance_research import router as performance_research_router  # noqa: E402
from .ai_research_export_safe import router as ai_research_export_router  # noqa: E402
from .ai_research_price_preview import router as ai_research_price_preview_router  # noqa: E402
from . import ai_research_price_aliases  # noqa: E402,F401
from .ai_research_import import router as ai_research_import_router  # noqa: E402
from .ai_research_import_apply import router as ai_research_import_apply_router  # noqa: E402
from .price_browser_connector_routes import router as price_browser_connector_router  # noqa: E402
from .price_browser_queue_routes import router as price_browser_queue_router  # noqa: E402

app.include_router(fragrance_dna_router)
app.include_router(fragrance_dna_proposal_router)
app.include_router(performance_research_router)
app.include_router(ai_research_export_router)
# Muss vor dem bisherigen Import-Router registriert werden, weil beide denselben
# Vorschaupfad anbieten. Der erweiterte Router übernimmt den vollständigen Ablauf.
app.include_router(ai_research_price_preview_router)
app.include_router(ai_research_import_router)
app.include_router(ai_research_import_apply_router)
app.include_router(price_browser_connector_router)
app.include_router(price_browser_queue_router)
_move_spa_fallback_to_end()
