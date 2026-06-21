# Rubric Format

Each rubric file defines one concept.

Required fields:
- `concept`
- `required_signals[]`
  - `signal_id`
  - `description`
  - `keywords[]`
  - `weight`

Optional fields:
- `optional_signals[]`
- `reference_answer`

The estimator scores concept understanding by signal coverage, not language quality.
