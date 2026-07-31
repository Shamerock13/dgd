from . import migrations
from .migrations import Migration


def register_price_alert_migration() -> None:
    if any(item.version == "0018" for item in migrations.MIGRATIONS):
        return
    migrations.MIGRATIONS = (
        *migrations.MIGRATIONS,
        Migration(
            version="0018",
            description="Lokale Preisalarme je Preisvariante ergänzen",
            statements=(
                "CREATE TABLE IF NOT EXISTS price_alerts (id UUID PRIMARY KEY, fragrance_id UUID NOT NULL REFERENCES fragrances(id) ON DELETE CASCADE, variant_key VARCHAR(40) NOT NULL, product_type VARCHAR(30) NOT NULL, size_ml DOUBLE PRECISION, concentration VARCHAR(80), active BOOLEAN NOT NULL DEFAULT TRUE, target_total_eur DOUBLE PRECISION, max_percent_above_low DOUBLE PRECISION, status VARCHAR(30) NOT NULL DEFAULT 'WAITING', current_total_eur DOUBLE PRECISION, historic_low_total_eur DOUBLE PRECISION, last_evaluated_at TIMESTAMP, last_triggered_at TIMESTAMP, trigger_count INTEGER NOT NULL DEFAULT 0, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, CONSTRAINT uq_price_alert_fragrance_variant UNIQUE (fragrance_id, variant_key), CONSTRAINT ck_price_alert_threshold CHECK (target_total_eur IS NOT NULL OR max_percent_above_low IS NOT NULL), CONSTRAINT ck_price_alert_target_positive CHECK (target_total_eur IS NULL OR target_total_eur > 0), CONSTRAINT ck_price_alert_percent_range CHECK (max_percent_above_low IS NULL OR (max_percent_above_low >= 0 AND max_percent_above_low <= 500)))",
                "CREATE INDEX IF NOT EXISTS ix_price_alerts_fragrance ON price_alerts (fragrance_id)",
                "CREATE INDEX IF NOT EXISTS ix_price_alerts_variant ON price_alerts (variant_key)",
                "CREATE INDEX IF NOT EXISTS ix_price_alerts_active ON price_alerts (active)",
                "CREATE INDEX IF NOT EXISTS ix_price_alerts_status ON price_alerts (status)",
            ),
        ),
    )
