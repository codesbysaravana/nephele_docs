"""Validation helpers for Nephele's knowledge graph."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, List, Set

from .graph_types import GraphDocument


ALLOWED_RELATIONSHIP_TYPES = {"prerequisite", "related", "cross_domain"}
ALLOWED_DIRECTIONALITY = {"directed", "undirected"}


def validate_graph_document(graph: GraphDocument) -> List[str]:
    """Return a list of validation errors for a graph document."""
    errors: List[str] = []

    domain_ids = {domain.domain_id for domain in graph.domains}
    concept_ids = {concept.concept_id for concept in graph.concepts}

    if len(domain_ids) != len(graph.domains):
        errors.append("Duplicate domain_id values found.")

    if len(concept_ids) != len(graph.concepts):
        errors.append("Duplicate concept_id values found.")

    concept_by_id = {concept.concept_id: concept for concept in graph.concepts}

    for concept in graph.concepts:
        if concept.domain_id not in domain_ids:
            errors.append(f"Concept {concept.concept_id} references unknown domain_id {concept.domain_id}.")

        if not 0.0 <= concept.difficulty <= 1.0:
            errors.append(f"Concept {concept.concept_id} difficulty must be between 0.0 and 1.0.")

        if not 0.0 <= concept.importance_weight <= 1.0:
            errors.append(f"Concept {concept.concept_id} importance_weight must be between 0.0 and 1.0.")

        if concept.estimated_question_count < 0:
            errors.append(f"Concept {concept.concept_id} estimated_question_count must be non-negative.")

        for ref in concept.question_ids:
            if not ref:
                errors.append(f"Concept {concept.concept_id} contains an empty question_id reference.")

    for edge in graph.edges:
        if edge.relationship_type not in ALLOWED_RELATIONSHIP_TYPES:
            errors.append(f"Edge {edge.edge_id} has invalid relationship_type {edge.relationship_type}.")

        if edge.directionality not in ALLOWED_DIRECTIONALITY:
            errors.append(f"Edge {edge.edge_id} has invalid directionality {edge.directionality}.")

        if edge.source_id not in concept_ids:
            errors.append(f"Edge {edge.edge_id} references unknown source concept {edge.source_id}.")

        if edge.target_id not in concept_ids:
            errors.append(f"Edge {edge.edge_id} references unknown target concept {edge.target_id}.")

        if edge.relationship_type in {"prerequisite"} and edge.source_id == edge.target_id:
            errors.append(f"Edge {edge.edge_id} cannot be a self-loop prerequisite.")

        if edge.relationship_type == "cross_domain":
            source_domain = concept_by_id[edge.source_id].domain_id
            target_domain = concept_by_id[edge.target_id].domain_id
            if source_domain == target_domain:
                errors.append(f"Edge {edge.edge_id} is cross_domain but stays inside the same domain.")

    errors.extend(_detect_dependency_cycles(graph))
    return errors


def _detect_dependency_cycles(graph: GraphDocument) -> List[str]:
    """Detect cycles in prerequisite relationships only."""
    adjacency = defaultdict(list)
    for edge in graph.edges:
        if edge.relationship_type == "prerequisite":
            adjacency[edge.source_id].append(edge.target_id)

    visiting: Set[str] = set()
    visited: Set[str] = set()
    errors: List[str] = []

    def visit(node_id: str, path: List[str]) -> None:
        if node_id in visiting:
            cycle_start = path.index(node_id)
            cycle = path[cycle_start:] + [node_id]
            errors.append("Prerequisite cycle detected: " + " -> ".join(cycle))
            return
        if node_id in visited:
            return

        visiting.add(node_id)
        path.append(node_id)
        for child_id in adjacency.get(node_id, []):
            visit(child_id, path)
        path.pop()
        visiting.remove(node_id)
        visited.add(node_id)

    for concept in graph.concepts:
        if concept.concept_id not in visited:
            visit(concept.concept_id, [])

    return errors
