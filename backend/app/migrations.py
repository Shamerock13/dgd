from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import Engine, text


logger = logging.getLogger("dgd.migrations")


@dataclass(frozen=True)
class Migration:
    version: str
    description: str
    statements: tuple[str, ...]


MIGRATIONS: tuple[Migration, ...] = (
    Migration(
        version="0001",
        description="Bestehende DGD-Tabellen auf das Anwendungsschema 0.8 bringen",
        statements=(
            # Marken
            "ALTER TABLE brands ADD COLUMN IF NOT EXISTS country VARCHAR(100)",
            "ALTER TABLE brands ADD COLUMN IF NOT EXISTS description TEXT",

            # Düfte: alle aktuell von SQLAlchemy erwarteten Felder ergänzen.
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS year INTEGER",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS gender VARCHAR(40)",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS concentration VARCHAR(80)",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS perfumer VARCHAR(160)",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS price_eur DOUBLE PRECISION",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS image_url TEXT",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS description TEXT",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS top_notes TEXT",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS heart_notes TEXT",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS base_notes TEXT",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS accords TEXT",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS longevity DOUBLE PRECISION",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS projection DOUBLE PRECISION",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS sweetness DOUBLE PRECISION",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS freshness DOUBLE PRECISION",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS created_at TIMESTAMP",

            # Sichere Standardwerte für bereits vorhandene Datensätze.
            "UPDATE fragrances SET gender = 'Unisex' WHERE gender IS NULL OR btrim(gender) = ''",
            "ALTER TABLE fragrances ALTER COLUMN gender SET DEFAULT 'Unisex'",
            "ALTER TABLE fragrances ALTER COLUMN gender SET NOT NULL",
            "UPDATE fragrances SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL",
            "ALTER TABLE fragrances ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE fragrances ALTER COLUMN created_at SET NOT NULL",

            # Duftzwillinge
            "ALTER TABLE twin_matches ADD COLUMN IF NOT EXISTS differences TEXT",
            "ALTER TABLE twin_matches ADD COLUMN IF NOT EXISTS commonalities TEXT",
            "ALTER TABLE twin_matches ADD COLUMN IF NOT EXISTS source_note TEXT",

            # Duftnoten-Tabellen können aus 0.6/0.7 bereits vorhanden sein.
            "ALTER TABLE notes ADD COLUMN IF NOT EXISTS category VARCHAR(80)",
            "ALTER TABLE notes ADD COLUMN IF NOT EXISTS description TEXT",
            "ALTER TABLE fragrance_notes ADD COLUMN IF NOT EXISTS position INTEGER",
            "UPDATE fragrance_notes SET position = 0 WHERE position IS NULL",
            "ALTER TABLE fragrance_notes ALTER COLUMN position SET DEFAULT 0",
            "ALTER TABLE fragrance_notes ALTER COLUMN position SET NOT NULL",

            # Indizes – idempotent und ohne Verlust vorhandener Daten.
            "CREATE INDEX IF NOT EXISTS ix_fragrances_name ON fragrances (name)",
            "CREATE INDEX IF NOT EXISTS ix_fragrances_brand_id ON fragrances (brand_id)",
            "CREATE INDEX IF NOT EXISTS ix_twin_matches_original_id ON twin_matches (original_id)",
            "CREATE INDEX IF NOT EXISTS ix_twin_matches_alternative_id ON twin_matches (alternative_id)",
            "CREATE INDEX IF NOT EXISTS ix_notes_name ON notes (name)",
            "CREATE INDEX IF NOT EXISTS ix_notes_category ON notes (category)",
            "CREATE INDEX IF NOT EXISTS ix_fragrance_notes_fragrance_id ON fragrance_notes (fragrance_id)",
            "CREATE INDEX IF NOT EXISTS ix_fragrance_notes_note_id ON fragrance_notes (note_id)",
            "CREATE INDEX IF NOT EXISTS ix_fragrance_notes_pyramid ON fragrance_notes (pyramid)",
        ),
    ),

Migration(
    version="0002",
    description="Legacy-Spalten dgd_id für neue Datensätze optional machen",
    statements=(
        """
        DO $$
        DECLARE
            current_table TEXT;
        BEGIN
            FOREACH current_table IN ARRAY ARRAY[
                'brands',
                'fragrances',
                'notes',
                'twin_matches',
                'fragrance_notes'
            ]
            LOOP
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns AS cols
                    WHERE cols.table_schema = 'public'
                      AND cols.table_name = current_table
                      AND cols.column_name = 'dgd_id'
                ) THEN
                    EXECUTE format(
                        'ALTER TABLE %I ALTER COLUMN dgd_id DROP NOT NULL',
                        current_table
                    );
                END IF;
            END LOOP;
        END
        $$;
        """,
    ),
),
    Migration(
        version="0003",
        description="Master-Datenbank v2 direkt in DGD importierbar machen",
        statements=(
            "ALTER TABLE brands ADD COLUMN IF NOT EXISTS dgd_id VARCHAR(32)",
            "ALTER TABLE brands ADD COLUMN IF NOT EXISTS master_data JSONB",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS dgd_id VARCHAR(32)",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS master_data JSONB",
            "ALTER TABLE twin_matches ADD COLUMN IF NOT EXISTS dgd_id VARCHAR(32)",
            "ALTER TABLE twin_matches ADD COLUMN IF NOT EXISTS master_data JSONB",
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_brands_dgd_id ON brands (dgd_id) WHERE dgd_id IS NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_fragrances_dgd_id ON fragrances (dgd_id) WHERE dgd_id IS NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_twin_matches_dgd_id ON twin_matches (dgd_id) WHERE dgd_id IS NOT NULL",
            """
            CREATE TABLE IF NOT EXISTS master_sources (
                id VARCHAR(32) PRIMARY KEY,
                name VARCHAR(500) NOT NULL,
                object_type VARCHAR(160),
                object_id VARCHAR(255),
                source_type VARCHAR(255),
                file_or_url TEXT,
                source_date TIMESTAMP,
                usage_status VARCHAR(255),
                trust_status VARCHAR(160),
                note TEXT,
                master_data JSONB
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS master_import_runs (
                id UUID PRIMARY KEY,
                filename VARCHAR(500) NOT NULL,
                file_version VARCHAR(50),
                status VARCHAR(30) NOT NULL,
                report JSONB,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
        ),
    ),
    Migration(
        version="0004",
        description="Pflichtfeld brands.active für Master-Import absichern",
        statements=(
            "ALTER TABLE brands ADD COLUMN IF NOT EXISTS active BOOLEAN",
            "UPDATE brands SET active = TRUE WHERE active IS NULL",
            "ALTER TABLE brands ALTER COLUMN active SET DEFAULT TRUE",
            "ALTER TABLE brands ALTER COLUMN active SET NOT NULL",
        ),
    ),
    Migration(
        version="0005",
        description="Legacy-Pflichtfelder für Master-Import vollständig absichern",
        statements=(
            # Felder bei komplett neuen Datenbanken zuerst anlegen.
            "ALTER TABLE brands ADD COLUMN IF NOT EXISTS verification_status VARCHAR(40)",
            "ALTER TABLE brands ADD COLUMN IF NOT EXISTS created_at TIMESTAMP",
            "ALTER TABLE brands ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS status VARCHAR(40)",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS heritage BOOLEAN",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS verification_status VARCHAR(40)",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS created_at TIMESTAMP",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP",

            # Marken aus dem ursprünglichen DGD-Core-Schema.
            "UPDATE brands SET verification_status = 'OPEN' WHERE verification_status IS NULL",
            "ALTER TABLE brands ALTER COLUMN verification_status SET DEFAULT 'OPEN'",
            "UPDATE brands SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL",
            "ALTER TABLE brands ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP",
            "UPDATE brands SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL",
            "ALTER TABLE brands ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP",

            # Düfte besitzen im ursprünglichen Schema weitere NOT-NULL-Felder,
            # die der Master-Importer nicht explizit schreiben muss.
            "UPDATE fragrances SET status = 'UNKNOWN' WHERE status IS NULL",
            "ALTER TABLE fragrances ALTER COLUMN status SET DEFAULT 'UNKNOWN'",
            "UPDATE fragrances SET heritage = FALSE WHERE heritage IS NULL",
            "ALTER TABLE fragrances ALTER COLUMN heritage SET DEFAULT FALSE",
            "UPDATE fragrances SET verification_status = 'OPEN' WHERE verification_status IS NULL",
            "ALTER TABLE fragrances ALTER COLUMN verification_status SET DEFAULT 'OPEN'",
            "UPDATE fragrances SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL",
            "ALTER TABLE fragrances ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP",
            "UPDATE fragrances SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL",
            "ALTER TABLE fragrances ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP",
        ),
    ),
    Migration(
        version="0006",
        description="Parfümeure und Importhistorie für Master Database v2 vervollständigen",
        statements=(
            """
            CREATE TABLE IF NOT EXISTS master_perfumers (
                id VARCHAR(32) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                birth_year INTEGER,
                nationality VARCHAR(160),
                profile TEXT,
                style TEXT,
                notable_works TEXT,
                article_status VARCHAR(160),
                primary_source TEXT,
                note TEXT,
                master_data JSONB
            )
            """,
            "CREATE INDEX IF NOT EXISTS ix_master_perfumers_name ON master_perfumers (name)",
            "CREATE INDEX IF NOT EXISTS ix_master_import_runs_created_at ON master_import_runs (created_at DESC)",
        ),
    ),
    Migration(
        version="0007",
        description="Bildquellen, Nutzungsstatus und robuste Bildverwaltung ergänzen",
        statements=(
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS image_source_name VARCHAR(200)",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS image_source_url TEXT",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS image_usage_note TEXT",
            "ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS image_status VARCHAR(30)",
            "UPDATE fragrances SET image_status = 'OPEN' WHERE image_status IS NULL OR btrim(image_status) = ''",
            "ALTER TABLE fragrances ALTER COLUMN image_status SET DEFAULT 'OPEN'",
            "ALTER TABLE fragrances ALTER COLUMN image_status SET NOT NULL",
            "CREATE INDEX IF NOT EXISTS ix_fragrances_image_status ON fragrances (image_status)",
        ),
    ),
    Migration(
        version="0008",
        description="Markenprofile um Gründungsjahr, Website und Verifizierungsstatus ergänzen",
        statements=(
            "ALTER TABLE brands ADD COLUMN IF NOT EXISTS founded_year INTEGER",
            "ALTER TABLE brands ADD COLUMN IF NOT EXISTS website_url TEXT",
            "ALTER TABLE brands ADD COLUMN IF NOT EXISTS verification_status VARCHAR(40)",
            "UPDATE brands SET verification_status = 'OPEN' WHERE verification_status IS NULL OR btrim(verification_status) = ''",
            "ALTER TABLE brands ALTER COLUMN verification_status SET DEFAULT 'OPEN'",
            "ALTER TABLE brands ALTER COLUMN verification_status SET NOT NULL",
            "CREATE INDEX IF NOT EXISTS ix_brands_verification_status ON brands (verification_status)",
        ),
    ),
    Migration(
        version="0009",
        description="Quellenregister und Verifizierungsstatus für die App absichern",
        statements=(
            "UPDATE master_sources SET trust_status = 'OPEN' WHERE trust_status IS NULL OR btrim(trust_status) = ''",
            "UPDATE master_sources SET usage_status = 'OPEN' WHERE usage_status IS NULL OR btrim(usage_status) = ''",
            "ALTER TABLE master_sources ALTER COLUMN trust_status SET DEFAULT 'OPEN'",
            "ALTER TABLE master_sources ALTER COLUMN usage_status SET DEFAULT 'OPEN'",
            "CREATE INDEX IF NOT EXISTS ix_master_sources_object ON master_sources (object_type, object_id)",
            "CREATE INDEX IF NOT EXISTS ix_master_sources_trust_status ON master_sources (trust_status)",
            "CREATE INDEX IF NOT EXISTS ix_master_sources_usage_status ON master_sources (usage_status)",
        ),
    ),

    Migration(
        version="0010",
        description="Parfümeurprofile und Artikelstatus absichern",
        statements=(
            "UPDATE master_perfumers SET article_status = 'OPEN' WHERE article_status IS NULL OR btrim(article_status) = ''",
            "CREATE INDEX IF NOT EXISTS ix_master_perfumers_article_status ON master_perfumers (article_status)",
        ),
    ),

)


def _ensure_migration_table(connection) -> None:
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS dgd_schema_migrations (
            version VARCHAR(40) PRIMARY KEY,
            description TEXT NOT NULL,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """))


def run_migrations(engine: Engine) -> list[str]:
    """Apply every missing migration in a single PostgreSQL transaction."""
    applied_now: list[str] = []

    with engine.begin() as connection:
        # Prevent two app instances from migrating the same database simultaneously.
        connection.execute(
            text("SELECT pg_advisory_xact_lock(hashtext('dgd-schema-migrations'))")
        )
        _ensure_migration_table(connection)

        applied = set(
            connection.execute(
                text("SELECT version FROM dgd_schema_migrations")
            ).scalars()
        )

        for migration in MIGRATIONS:
            if migration.version in applied:
                logger.info(
                    "Datenbankmigration %s bereits vorhanden: %s",
                    migration.version,
                    migration.description,
                )
                continue

            logger.info(
                "Wende Datenbankmigration %s an: %s",
                migration.version,
                migration.description,
            )
            for statement in migration.statements:
                connection.execute(text(statement))

            connection.execute(
                text("""
                    INSERT INTO dgd_schema_migrations (version, description)
                    VALUES (:version, :description)
                """),
                {
                    "version": migration.version,
                    "description": migration.description,
                },
            )
            applied_now.append(migration.version)

    return applied_now


def current_schema_version(engine: Engine) -> str:
    with engine.connect() as connection:
        exists = connection.execute(text("""
            SELECT to_regclass('public.dgd_schema_migrations') IS NOT NULL
        """)).scalar_one()
        if not exists:
            return "nicht initialisiert"

        version = connection.execute(text("""
            SELECT version
            FROM dgd_schema_migrations
            ORDER BY applied_at DESC, version DESC
            LIMIT 1
        """)).scalar_one_or_none()
        return version or "0"


def migration_history(engine: Engine) -> list[dict[str, str]]:
    with engine.connect() as connection:
        exists = connection.execute(text("""
            SELECT to_regclass('public.dgd_schema_migrations') IS NOT NULL
        """)).scalar_one()
        if not exists:
            return []

        rows = connection.execute(text("""
            SELECT version, description, applied_at
            FROM dgd_schema_migrations
            ORDER BY applied_at, version
        """)).mappings()

        return [
            {
                "version": row["version"],
                "description": row["description"],
                "applied_at": row["applied_at"].isoformat(),
            }
            for row in rows
        ]
