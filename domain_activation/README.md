# Domain Activation Layer (Phase 2)

This module activates knowledge graph domains from structured resume JSON.

## Scope

Implemented:
- Domain registry mapping (skills/projects/technologies to domains)
- Alias mapping (ML, Data Science, etc. -> machine_learning)
- Domain confidence scoring
- Entry concept selection from graph domain files
- Domain prioritization for interview ordering

Not implemented:
- Graph traversal
- Mastery estimation
- Interview orchestration
- Embeddings/semantic matching

## Architecture

1. `registry.py`
- Loads `aliases.json` and `registry.json`
- Normalizes resume tokens
- Resolves token -> canonical domain and weight

2. `confidence_engine.py`
- Aggregates evidence by source (`skills`, `domains`, `project_technologies`, `project_names`)
- Computes confidence and priority score

3. `activation_engine.py`
- Consumes resume JSON
- Builds domain evidence buckets
- Produces sorted active domains with confidence and entry concepts

4. `models.py`
- Defines `ActiveDomain` and `ActivationResult`

## Confidence Design

Confidence is computed from weighted evidence and clipped to [0.0, 0.99].

- Alias hit base weight: `0.60`
- Registry hit base weight: from `registry.json`
- Source multipliers:
  - skills: `1.00`
  - domains: `1.10`
  - project_technologies: `1.15`
  - project_names: `0.80`
- Diversity bonus: `0.03` per additional non-empty evidence source beyond the first

## Prioritization

Domains are ordered by:
1. priority score (`confidence + evidence_density_bonus`)
2. confidence
3. total evidence count

## Entry Concept Selection

Entry concepts are read from:
- `knowledge_graph/domains/*.json`

No traversal is performed.

## Example

Input resume:

```json
{
  "skills": ["Python", "Machine Learning", "TensorFlow", "SQL"]
}
```

Output (`ActivationResult.to_dict()`):

```json
{
  "active_domains": [
    {
      "domain": "machine_learning",
      "confidence": 0.92,
      "entry_concepts": ["Supervised Learning", "Train-Test Split"]
    },
    {
      "domain": "python",
      "confidence": 0.75,
      "entry_concepts": ["Python Basics", "Data Types", "Control Flow"]
    },
    {
      "domain": "sql",
      "confidence": 0.60,
      "entry_concepts": ["SQL Fundamentals", "SELECT and WHERE", "JOIN Basics"]
    }
  ]
}
```

## Extensibility Hooks

Future upgrades can extend:
- `registry.json` with embedding vectors or semantic tags
- `aliases.json` with ontology expansions
- `activation_engine.py` with semantic token matching and retrieval
