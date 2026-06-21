"""Graph document loading helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .graph_types import (
    ConceptNode,
    DomainNode,
    FutureConceptState,
    FutureEdgeMetadata,
    GraphDocument,
    RelationshipEdge,
)


def load_graph_document(path: str | Path) -> GraphDocument:
    """Load a graph document from JSON."""
    graph_path = Path(path)
    payload = json.loads(graph_path.read_text(encoding="utf-8"))
    return graph_document_from_dict(payload)


def graph_document_from_dict(payload: Dict[str, Any]) -> GraphDocument:
    """Build a typed graph document from a dictionary payload."""
    domains = [DomainNode(**domain) for domain in payload.get("domains", [])]

    concepts = []
    for concept in payload.get("concepts", []):
        future_state_payload = concept.get("future_state", {}) or {}
        concept = dict(concept)
        concept["future_state"] = FutureConceptState(**future_state_payload)
        concepts.append(ConceptNode(**concept))

    edges = []
    for edge in payload.get("edges", []):
        metadata_payload = edge.get("metadata", {}) or {}
        edge = dict(edge)
        edge["metadata"] = FutureEdgeMetadata(**metadata_payload)
        edges.append(RelationshipEdge(**edge))

    return GraphDocument(
        graph_id=payload["graph_id"],
        version=payload["version"],
        domains=domains,
        concepts=concepts,
        edges=edges,
        metadata=payload.get("metadata", {}),
    )
