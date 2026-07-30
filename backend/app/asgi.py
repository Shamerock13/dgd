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

from .main import app  # noqa: E402
from .fragrance_dna_routes import router as fragrance_dna_router  # noqa: E402
from .fragrance_dna_proposal_routes import router as fragrance_dna_proposal_router  # noqa: E402
from .performance_research import router as performance_research_router  # noqa: E402
from .ai_research_export_safe import router as ai_research_export_router  # noqa: E402
from .ai_research_import import router as ai_research_import_router  # noqa: E402

app.include_router(fragrance_dna_router)
app.include_router(fragrance_dna_proposal_router)
app.include_router(performance_research_router)
app.include_router(ai_research_export_router)
app.include_router(ai_research_import_router)
_move_spa_fallback_to_end()
