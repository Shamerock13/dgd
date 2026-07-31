from . import migrations
from .migrations import Migration


def register_price_source_review_migration() -> None:
    if any(item.version == "0017" for item in migrations.MIGRATIONS):
        return
    migrations.MIGRATIONS = (
        *migrations.MIGRATIONS,
        Migration(
            version="0017",
            description="Auditprotokoll für Preisquellen-Prüfung ergänzen",
            statements=(
                "CREATE TABLE IF NOT EXISTS price_source_review_events (id UUID PRIMARY KEY, offer_id UUID NOT NULL REFERENCES fragrance_offers(id) ON DELETE CASCADE, action VARCHAR(40) NOT NULL, previous_status VARCHAR(30), new_status VARCHAR(30), scanner_active BOOLEAN NOT NULL DEFAULT FALSE, retailer_activated BOOLEAN NOT NULL DEFAULT FALSE, note TEXT, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)",
                "CREATE INDEX IF NOT EXISTS ix_price_source_review_events_offer ON price_source_review_events (offer_id)",
                "CREATE INDEX IF NOT EXISTS ix_price_source_review_events_action ON price_source_review_events (action)",
                "CREATE INDEX IF NOT EXISTS ix_price_source_review_events_created ON price_source_review_events (created_at DESC)",
            ),
        ),
    )
