"""Graph loading and navigation utilities for traversal."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Set

from knowledge_graph.graph_types import GraphDocument, ConceptNode


class GraphNavigator:
    """Navigates concept relationships in a knowledge graph."""

    def __init__(self, graph: GraphDocument) -> None:
        self.graph = graph
        self.concept_by_id = {c.concept_id: c for c in graph.concepts}
        self.concept_by_name = {c.concept_name: c for c in graph.concepts}
        self.successors_map: Dict[str, List[str]] = defaultdict(list)
        self.prerequisites_map: Dict[str, List[str]] = defaultdict(list)

        for edge in graph.edges:
            if edge.relationship_type == "prerequisite":
                self.successors_map[edge.source_id].append(edge.target_id)
                self.prerequisites_map[edge.target_id].append(edge.source_id)
            elif edge.relationship_type == "related" and edge.directionality == "directed":
                self.successors_map[edge.source_id].append(edge.target_id)

    def lookup_concept(self, identifier: str) -> Optional[ConceptNode]:
        """Look up a concept case-insensitively by ID or Name."""
        if not identifier:
            return None

        if identifier in self.concept_by_id:
            return self.concept_by_id[identifier]
        if identifier in self.concept_by_name:
            return self.concept_by_name[identifier]

        # Case insensitive/strip search
        clean_id = identifier.strip().lower()
        for cid, concept in self.concept_by_id.items():
            if cid.lower() == clean_id:
                return concept
        for name, concept in self.concept_by_name.items():
            if name.lower() == clean_id:
                return concept
        return None

    def get_successors(self, concept_id_or_name: str) -> List[str]:
        """Get concept IDs that can be reached from this one, ordered by difficulty (ascending)."""
        concept = self.lookup_concept(concept_id_or_name)
        if not concept:
            return []
        successors = self.successors_map.get(concept.concept_id, [])
        return sorted(successors, key=lambda cid: self.get_concept_difficulty(cid) or 0.0)

    def get_prerequisites(self, concept_id_or_name: str) -> List[str]:
        """Get concept IDs that must be mastered first, ordered by difficulty (descending)."""
        concept = self.lookup_concept(concept_id_or_name)
        if not concept:
            return []
        prerequisites = self.prerequisites_map.get(concept.concept_id, [])
        return sorted(prerequisites, key=lambda cid: self.get_concept_difficulty(cid) or 0.0, reverse=True)

    def get_concept_name(self, concept_id_or_name: str) -> Optional[str]:
        concept = self.lookup_concept(concept_id_or_name)
        return concept.concept_name if concept else None

    def get_concept_difficulty(self, concept_id_or_name: str) -> Optional[float]:
        concept = self.lookup_concept(concept_id_or_name)
        return concept.difficulty if concept else None

    def list_all_concepts(self) -> List[str]:
        return list(self.concept_by_id.keys())
