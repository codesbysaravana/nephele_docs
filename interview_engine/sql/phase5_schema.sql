-- PostgreSQL schema for storing candidates, interview sessions, concept evaluations, domain mastery and reports.

-- 1. candidates table
CREATE TABLE IF NOT EXISTS candidates (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    resume_text TEXT NOT NULL,
    skills JSONB NOT NULL DEFAULT '{}'::jsonb,
    education JSONB NOT NULL DEFAULT '[]'::jsonb,
    projects JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. interview_sessions table
CREATE TABLE IF NOT EXISTS interview_sessions (
    id VARCHAR(255) PRIMARY KEY,
    candidate_id VARCHAR(255) NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    state VARCHAR(50) NOT NULL, -- CREATED, ACTIVE, PAUSED, COMPLETED, FAILED
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

-- 3. concept_progress table
CREATE TABLE IF NOT EXISTS concept_progress (
    id SERIAL PRIMARY KEY,
    candidate_id VARCHAR(255) NOT NULL,
    concept_id VARCHAR(255) NOT NULL,
    mastery NUMERIC(5,4) NOT NULL,
    decision VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 4. concept_evaluations table
CREATE TABLE IF NOT EXISTS concept_evaluations (
    id SERIAL PRIMARY KEY,
    candidate_id VARCHAR(255) NOT NULL,
    concept_id VARCHAR(255) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    mastery NUMERIC(5,4) NOT NULL,
    confidence NUMERIC(5,4) NOT NULL,
    matched_signals JSONB NOT NULL DEFAULT '[]'::jsonb,
    missing_signals JSONB NOT NULL DEFAULT '[]'::jsonb,
    reasoning JSONB NOT NULL DEFAULT '[]'::jsonb,
    strategy VARCHAR(50) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 5. domain_mastery table
CREATE TABLE IF NOT EXISTS domain_mastery (
    candidate_id VARCHAR(255) NOT NULL,
    domain_id VARCHAR(255) NOT NULL,
    mastery NUMERIC(5,4) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (candidate_id, domain_id)
);

-- 6. reports table
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    candidate_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    concept_scores JSONB NOT NULL DEFAULT '{}'::jsonb,
    domain_scores JSONB NOT NULL DEFAULT '{}'::jsonb,
    strong_concepts JSONB NOT NULL DEFAULT '[]'::jsonb,
    weak_concepts JSONB NOT NULL DEFAULT '[]'::jsonb,
    recommended_topics JSONB NOT NULL DEFAULT '[]'::jsonb,
    summary TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_interview_sessions_candidate ON interview_sessions (candidate_id);
CREATE INDEX IF NOT EXISTS idx_concept_progress_candidate ON concept_progress (candidate_id);
CREATE INDEX IF NOT EXISTS idx_concept_evaluations_candidate ON concept_evaluations (candidate_id);
CREATE INDEX IF NOT EXISTS idx_domain_mastery_candidate ON domain_mastery (candidate_id);
CREATE INDEX IF NOT EXISTS idx_reports_candidate ON reports (candidate_id);
