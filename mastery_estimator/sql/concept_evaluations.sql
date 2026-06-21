-- PostgreSQL schema for storing concept-level mastery evaluations.

CREATE TABLE IF NOT EXISTS concept_evaluations (
    id BIGSERIAL PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    concept_id TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    mastery NUMERIC(5,4) NOT NULL CHECK (mastery >= 0 AND mastery <= 1),
    confidence NUMERIC(5,4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    matched_signals JSONB NOT NULL DEFAULT '[]'::jsonb,
    missing_signals JSONB NOT NULL DEFAULT '[]'::jsonb,
    reasoning JSONB NOT NULL DEFAULT '[]'::jsonb,
    strategy TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_concept_evaluations_candidate
    ON concept_evaluations (candidate_id);

CREATE INDEX IF NOT EXISTS idx_concept_evaluations_concept
    ON concept_evaluations (concept_id);

CREATE INDEX IF NOT EXISTS idx_concept_evaluations_created_at
    ON concept_evaluations (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_concept_evaluations_matched_signals
    ON concept_evaluations USING GIN (matched_signals);

CREATE INDEX IF NOT EXISTS idx_concept_evaluations_missing_signals
    ON concept_evaluations USING GIN (missing_signals);
