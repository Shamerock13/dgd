CREATE TABLE IF NOT EXISTS fragrance_dna_proposals (
    id UUID PRIMARY KEY,
    fragrance_id UUID NOT NULL REFERENCES fragrances(id) ON DELETE CASCADE,
    values JSONB NOT NULL,
    source VARCHAR(30) NOT NULL,
    source_label VARCHAR(255),
    source_url TEXT,
    rationale TEXT,
    confidence DOUBLE PRECISION,
    status VARCHAR(30) NOT NULL DEFAULT 'OPEN',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    review_note TEXT
);

CREATE INDEX IF NOT EXISTS ix_fragrance_dna_proposals_fragrance
    ON fragrance_dna_proposals (fragrance_id);

CREATE INDEX IF NOT EXISTS ix_fragrance_dna_proposals_status
    ON fragrance_dna_proposals (status);

COMMENT ON TABLE fragrance_dna_proposals IS
    'Kontrollierte Duft-DNA-Recherchevorschläge. OPEN-Vorschläge verändern veröffentlichte DNA-Werte nicht.';
