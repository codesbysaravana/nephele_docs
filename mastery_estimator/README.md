# Mastery Estimation Layer (Phase 3)

This module estimates concept mastery from a question-answer pair.

## Scope

Implemented:
- Concept-centric rubric evaluation
- Evidence extraction (`matched_signals`, `missing_signals`)
- Mastery and confidence outputs
- Three strategies: LLM, Embedding, Hybrid
- PostgreSQL schema for concept evaluations

Not implemented:
- Graph traversal
- Interview progression logic
- Next-concept decisions

## Folder Structure

- `models.py`: Rubric and evaluation models
- `rubric_loader.py`: Rubric loading from JSON
- `llm_evaluator.py`: Mock LLM-based concept evaluator
- `embedding_evaluator.py`: Mock embedding-similarity evaluator
- `hybrid_evaluator.py`: Combines LLM + embedding estimates
- `estimation_engine.py`: Facade service
- `rubrics/`: Concept rubrics
- `sql/concept_evaluations.sql`: PostgreSQL table

## Extensibility

Designed to support:
- future fine-tuned evaluator models
- future knowledge tracing
- future adaptive scoring calibration
- future semantic/embedding retrieval systems
