ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS fragrance_dna JSONB;
ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS fragrance_dna_source VARCHAR(30);
ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS fragrance_dna_status VARCHAR(30);
ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS fragrance_dna_source_count INTEGER;
ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS fragrance_dna_confidence DOUBLE PRECISION;
ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS fragrance_dna_disagreement DOUBLE PRECISION;
ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS fragrance_dna_researched_at TIMESTAMP;
ALTER TABLE fragrances ADD COLUMN IF NOT EXISTS personal_fragrance_dna JSONB;

UPDATE fragrances
SET fragrance_dna_status = 'OPEN'
WHERE fragrance_dna_status IS NULL OR btrim(fragrance_dna_status) = '';

ALTER TABLE fragrances ALTER COLUMN fragrance_dna_status SET DEFAULT 'OPEN';
ALTER TABLE fragrances ALTER COLUMN fragrance_dna_status SET NOT NULL;

CREATE INDEX IF NOT EXISTS ix_fragrances_dna_status
    ON fragrances (fragrance_dna_status);

COMMENT ON COLUMN fragrances.fragrance_dna IS
    'Strukturierte aggregierte Duft-DNA. Fehlende Dimensionen bleiben nicht gesetzt.';
COMMENT ON COLUMN fragrances.personal_fragrance_dna IS
    'Persönliche Duft-DNA, strikt getrennt von aggregierten Recherchewerten.';
