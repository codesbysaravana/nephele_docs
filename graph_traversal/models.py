"""Core models for graph traversal and decision making."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TraversalDecision(str, Enum):
    """Traversal decision from graph navigation."""

    ADVANCE = "advance"
    BACKTRACK = "backtrack"
    STAY = "stay"
    ACCELERATE = "accelerate"
    TERMINATE_BRANCH = "terminate_branch"
    END_INTERVIEW = "end_interview"


@dataclass
class TraversalState:
    """Session-level traversal state across concepts."""

    candidate_id: str
    domain: str
    current_concept: str
    visited_concepts: List[str] = field(default_factory=list)
    mastery_history: List[float] = field(default_factory=list)
    success_streak: int = 0
    failure_streak: int = 0
    accelerated: bool = False
    terminated: bool = False

    def __post_init__(self) -> None:
        if self.current_concept and self.current_concept not in self.visited_concepts:
            self.visited_concepts.append(self.current_concept)

    def update_after_decision(self, next_concept: Optional[str], mastery: float) -> None:
        """Update state after a traversal decision."""
        self.mastery_history.append(mastery)
        if next_concept:
            if next_concept not in self.visited_concepts:
                self.visited_concepts.append(next_concept)
            self.current_concept = next_concept

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state exactly as required by the Traversal State format."""
        return {
            "visited_concepts": self.visited_concepts,
            "mastery_history": self.mastery_history,
            "success_streak": self.success_streak,
            "failure_streak": self.failure_streak,
        }

    @classmethod
    def from_dict(
        cls,
        candidate_id: str,
        domain: str,
        current_concept: str,
        d: Dict[str, Any],
        accelerated: bool = False,
        terminated: bool = False
    ) -> TraversalState:
        """Load state from dictionary."""
        visited = d.get("visited_concepts", [])
        if not visited and current_concept:
            visited = [current_concept]
        return cls(
            candidate_id=candidate_id,
            domain=domain,
            current_concept=current_concept,
            visited_concepts=visited,
            mastery_history=d.get("mastery_history", []),
            success_streak=d.get("success_streak", 0),
            failure_streak=d.get("failure_streak", 0),
            accelerated=accelerated,
            terminated=terminated,
        )


@dataclass
class TraversalResult:
    """Result of a traversal decision."""

    decision: TraversalDecision
    next_concept: Optional[str]
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to serializable dict, omitting next_concept if not applicable."""
        res: Dict[str, Any] = {
            "decision": self.decision.value,
        }
        if self.decision not in (TraversalDecision.TERMINATE_BRANCH, TraversalDecision.END_INTERVIEW):
            if self.next_concept is not None:
                res["next_concept"] = self.next_concept
        if self.reason:
            res["reason"] = self.reason
        return res
