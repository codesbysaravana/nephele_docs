# Nephele Interview Engine Storage Architecture (Phase 6A)

This document describes the production-ready storage architecture implemented for the Nephele technical interview traversal engine, transitioning from mock/in-memory storage to a combined PostgreSQL and ChromaDB backend.

## PostgreSQL Database Schema

We use SQLAlchemy 2.x to define tables and relationships. Migrations are managed by Alembic.

### Tables

1. **`candidates`**:
   - `id` (VARCHAR(255) Primary Key): Unique candidate identifier.
   - `name` (VARCHAR(255)): Full candidate name.
   - `email` (VARCHAR(255)): Contact email.
   - `created_at` (TIMESTAMPTZ): Record creation timestamp.

2. **`resume_data`**:
   - `id` (SERIAL Primary Key)
   - `candidate_id` (VARCHAR(255) ForeignKey to `candidates.id` ON DELETE CASCADE, Unique): Link to candidate.
   - `resume_text` (TEXT): Raw text representation.
   - `skills` (JSONB): Parsed skills JSON object.
   - `education` (JSONB): List of degrees/institutions.
   - `projects` (JSONB): List of technical projects.
   - `created_at` (TIMESTAMPTZ)

3. **`interview_sessions`**:
   - `id` (VARCHAR(255) Primary Key): Unique session ID.
   - `candidate_id` (VARCHAR(255) ForeignKey to `candidates.id` ON DELETE CASCADE)
   - `state` (VARCHAR(50)): Lifecycle state (`CREATED`, `ACTIVE`, `PAUSED`, `COMPLETED`, `FAILED`).
   - `domain` (VARCHAR(255)): Activated domain (e.g. `machine_learning`).
   - `current_concept` (VARCHAR(255)): Current traversal concept.
   - `visited_concepts` (JSONB): Array of visited concept names.
   - `mastery_history` (JSONB): Historical mastery scores corresponding to visited concepts.
   - `success_streak` (INTEGER)
   - `failure_streak` (INTEGER)
   - `accelerated` (BOOLEAN)
   - `terminated` (BOOLEAN)
   - `created_at` (TIMESTAMPTZ)
   - `updated_at` (TIMESTAMPTZ)

4. **`concept_progress`**:
   - `id` (SERIAL Primary Key)
   - `candidate_id` (VARCHAR(255))
   - `concept_id` (VARCHAR(255))
   - `mastery` (NUMERIC(5,4))
   - `decision` (VARCHAR(50))
   - `timestamp` (TIMESTAMPTZ)

5. **`concept_evaluations`**:
   - `id` (SERIAL Primary Key)
   - `candidate_id` (VARCHAR(255))
   - `concept_id` (VARCHAR(255))
   - `question` (TEXT)
   - `answer` (TEXT)
   - `mastery` (NUMERIC(5,4))
   - `confidence` (NUMERIC(5,4))
   - `matched_signals` (JSONB)
   - `missing_signals` (JSONB)
   - `reasoning` (JSONB)
   - `strategy` (VARCHAR(50))
   - `metadata` (JSONB)
   - `created_at` (TIMESTAMPTZ)

6. **`domain_mastery`**:
   - `candidate_id` (VARCHAR(255))
   - `domain_id` (VARCHAR(255))
   - `mastery` (NUMERIC(5,4))
   - `created_at` (TIMESTAMPTZ)
   - Primary Key: `(candidate_id, domain_id)`

7. **`interview_reports`**:
   - `id` (SERIAL Primary Key)
   - `candidate_id` (VARCHAR(255))
   - `session_id` (VARCHAR(255) ForeignKey to `interview_sessions.id` ON DELETE CASCADE)
   - `concept_scores` (JSONB)
   - `domain_scores` (JSONB)
   - `strong_concepts` (JSONB)
   - `weak_concepts` (JSONB)
   - `recommended_topics` (JSONB)
   - `summary` (TEXT)
   - `created_at` (TIMESTAMPTZ)

8. **`graph_statistics`**:
   - `id` (SERIAL Primary Key)
   - `domain_id` (VARCHAR(255) Unique)
   - `total_concepts` (INTEGER)
   - `total_edges` (INTEGER)
   - `max_depth` (INTEGER)
   - `density` (NUMERIC(5,4))
   - `updated_at` (TIMESTAMPTZ)

---

## ChromaDB Vector Collections

We partition the vector storage space into 5 specialized collections, facilitating fast semantic searches and caching:

1. **`questions`**: Stores generated/selected question formulations mapped to concepts for caching and semantic lookup.
2. **`answers`**: Stores candidate answers. Allows semantic similarity comparisons to historical candidate responses.
3. **`misconceptions`**: Seeded with known misconceptions from the knowledge graphs to enable semantic matching during evaluations.
4. **`concept_examples`**: Stores typical reference question-answer pairs for context loading.
5. **`interview_memory`**: Stores visual and behavioral signal observations (e.g. eye contact trends, gaze shifts) mapped by candidate ID and timestamp.

---

## Repository Layer

PostgreSQL operations are encapsulated inside repositories bound to active SQLAlchemy Sessions:

- **`CandidateRepository`**: CRUD for candidate profiling and resume text/metadata.
- **`InterviewRepository`**: CRUD for managing session states, progress logging, and detailed evaluative metrics.
- **`MasteryRepository`**: CRUD for tracking candidate mastery scores at the domain level.
- **`ReportRepository`**: CRUD for storing and fetching generated evaluation reports.
- **`GraphStatsRepository`**: Handles metrics corresponding to domain graph topologies.

---

## Services

- **`PostgresService`**: Initializes connection pool (`pool_size=10`, `max_overflow=20`), sets up sessionmakers, and provides transaction context managers (`session()`) supporting automated commit and rollback.
- **`ChromaService`**: Wraps the Chroma client, initializes collections, and translates document text into vectors via embeddings.
- **`PersistenceService`**: A unified coordinator binding database transactions across repositories and writing semantic events to Chroma.
