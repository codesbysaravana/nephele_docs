-- PostgreSQL schema for storing interview sessions and candidate concept progress.

CREATE TABLE IF NOT EXISTS interview_sessions (
    id SERIAL PRIMARY KEY,
    candidate_id VARCHAR(255) UNIQUE NOT NULL,
    domain VARCHAR(255) NOT NULL,
    current_concept VARCHAR(255) NOT NULL,
    visited_concepts JSONB NOT NULL DEFAULT '[]'::jsonb,
    mastery_history JSONB NOT NULL DEFAULT '[]'::jsonb,
    success_streak INTEGER NOT NULL DEFAULT 0,
    failure_streak INTEGER NOT NULL DEFAULT 0,
    accelerated BOOLEAN NOT NULL DEFAULT FALSE,
    terminated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS concept_progress (
    id SERIAL PRIMARY KEY,
    candidate_id VARCHAR(255) NOT NULL,
    concept_id VARCHAR(255) NOT NULL,
    mastery NUMERIC(5,4) NOT NULL,
    decision VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_interview_sessions_candidate ON interview_sessions (candidate_id);
CREATE INDEX IF NOT EXISTS idx_concept_progress_candidate ON concept_progress (candidate_id);
CREATE INDEX IF NOT EXISTS idx_concept_progress_concept ON concept_progress (concept_id);
