"""Typed graph structures for Nephele's knowledge graph."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class FutureConceptState:
    """Reserved future per-concept learning state."""

    mastery_score: Optional[float] = None
    confidence: Optional[float] = None
    attempt_count: Optional[int] = None
    interview_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class FutureEdgeMetadata:
    """Reserved future edge analytics metadata."""

    relationship_strength: Optional[float] = None
    traversal_frequency: Optional[int] = None
    success_rate: Optional[float] = None
    failure_rate: Optional[float] = None


@dataclass(slots=True)
class DomainNode:
    """Domain-level grouping and entry points."""

    domain_id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    entry_concepts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ConceptNode:
    """Concept metadata only. Relationships live on edges."""

    concept_id: str
    concept_name: str
    domain_id: str
    difficulty: float
    description: str
    tags: List[str] = field(default_factory=list)
    importance_weight: float = 1.0
    estimated_question_count: int = 1
    question_ids: List[str] = field(default_factory=list)
    common_failures: List[str] = field(default_factory=list)
    common_misconceptions: List[str] = field(default_factory=list)
    future_state: FutureConceptState = field(default_factory=FutureConceptState)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RelationshipEdge:
    """Directed or undirected concept relationship."""

    edge_id: str
    source_id: str
    target_id: str
    relationship_type: str
    label: str = ""
    directionality: str = "directed"
    metadata: FutureEdgeMetadata = field(default_factory=FutureEdgeMetadata)


@dataclass(slots=True)
class GraphDocument:
    """Portable graph document that can be stored in JSON or mapped later."""

    graph_id: str
    version: str
    domains: List[DomainNode] = field(default_factory=list)
    concepts: List[ConceptNode] = field(default_factory=list)
    edges: List[RelationshipEdge] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the graph document to JSON-safe primitives."""
        return asdict(self)
