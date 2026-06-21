# Graph Traversal Engine (Phase 4)

This module navigates the knowledge graph based on mastery estimates.

## Scope

Implemented:
- Forward traversal (high mastery → successor)
- Backward traversal (low mastery → prerequisite)
- Stay rule (medium mastery → stay on concept)
- Branch termination (3+ failures)
- Acceleration (3+ successes)
- Traversal state tracking
- PostgreSQL schema

Not implemented:
- Question generation
- Answer evaluation
- LLM calls
- Interview orchestration

## Core APIs

- `GraphTraversalEngine.start_traversal()`: Initialize a candidate session
- `GraphTraversalEngine.decide_next()`: Get next concept based on mastery

## Decision Rules

- Mastery >= 0.80: ADVANCE
- Mastery <= 0.40: BACKTRACK
- 0.40 < Mastery < 0.80: STAY
- 3+ failures: TERMINATE_BRANCH
- 3+ successes: ACCELERATE
