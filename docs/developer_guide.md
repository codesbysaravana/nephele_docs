# Nephele Developer Guide

This document assists developers on boarding the codebase, running tests, customizing templates, and adding features.

---

## 1. Directory Structure

```
Nephele/
│
├── admin/                     # Admin Dashboard Frontend Static Assets
├── analytics/                 # Analytics Dashboard Frontend Static Assets
├── app/
│   ├── agents/                # LLM agent definitions
│   ├── routes/                # FastAPI Routers (interview, health, observability, etc.)
│   ├── services/              # Base system services (stt, tts)
│   ├── utils/                 # Utilities (exporters)
│   └── main.py                # App entrypoint
│
├── domain_activation/         # Skill parsers and domain matcher engines
├── graph_evolution/           # Edges updater and misconception collectors
├── graph_traversal/           # Dynamic graph traversal routines
├── interview_engine/          # Orchestrators and persistence layers
│   ├── storage/
│   │   ├── chroma/            # ChromaDB collection wrappers
│   │   └── postgres/          # SQLAlchemy Models & Repositories
│   └── database.py            # Database manager layer
│
├── knowledge_graph/           # Graph loader and JSON domain definition documents
├── mastery_estimator/         # Evaluation engines and LLM provider interfaces
├── runtime/                   # Speech/Sensors integrations and runtime orchestrator
└── tests/                     # Verification test suites
```

---

## 2. Running Backend Tests

Tests are managed using `pytest`. The system contains extensive test coverages for all phases.

### Execute All Standard Tests
To run all tests (ignoring the integration tests that require a local camera / GUI):
```bash
pytest --ignore=tests/vision/test_integration.py
```

### Validate Specific Phases
To execute verification tests for database migrations or engine segments:
- **Phase 6D Runtime**: `pytest tests/test_phase6d.py`
- **Phase 6E Evolution**: `pytest tests/test_phase6e.py`
- **Phase 6F Deployments**: `pytest tests/test_phase6f.py`

---

## 3. Creating New Domains & Customizing Rubrics

### Adding a Domain Knowledge Graph
1. Create a new graph definition file under `knowledge_graph/domains/` named `your_domain.json`.
2. Format the JSON following the established schema structure:
   ```json
   {
     "domain_id": "your_domain",
     "concepts": [
       {
         "concept_id": "concept_name_id",
         "concept_name": "Human-Readable Concept Name",
         "difficulty": "basic",
         "rubrics": [
           "Rubric signal points 1",
           "Rubric signal points 2"
         ],
         "common_misconceptions": [
           "Common wrong idea"
         ]
       }
     ],
     "edges": [
       {
         "source_id": "prerequisite_concept_id",
         "target_id": "concept_name_id",
         "edge_type": "prerequisite"
       }
     ]
   }
   ```
3. Map the domain name in `domain_activation/activation_engine.py` to support automatic activation via resume keyword mappings.
