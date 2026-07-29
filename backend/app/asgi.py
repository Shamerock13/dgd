from __future__ import annotations

from . import migrations
from .migrations import Migration


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


def _move_spa_fallback_to_end() -> None:
    fallback_routes = [
        route for route in app.router.routes
        if getattr(route, "path", None) == "/{full_path:path}"
    ]
    if not fallback_routes:
        return
    for route in fallback_routes:
        app.router.routes.remove(route)
        app.router.routes.append(route)


_register_fragrance_dna_migration()

from .main import app  # noqa: E402
from .fragrance_dna_routes import router as fragrance_dna_router  # noqa: E402

app.include_router(fragrance_dna_router)
_move_spa_fallback_to_end()
