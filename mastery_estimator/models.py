"""Core models for mastery estimation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class EvaluationStrategy(str, Enum):
    """Supported evaluation strategies."""

    LLM = "llm"
    EMBEDDING = "embedding"
    HYBRID = "hybrid"


@dataclass(slots=True)
class RubricSignal:
    """A concept signal that indicates concept understanding."""

    signal_id: str
    description: str
    keywords: List[str]
    weight: float = 1.0


@dataclass(slots=True)
class ConceptRubric:
    """Rubric used to assess mastery for one concept."""

    concept: str
    required_signals: List[RubricSignal] = field(default_factory=list)
    optional_signals: List[RubricSignal] = field(default_factory=list)
    reference_answer: str = ""

    @property
    def total_required_weight(self) -> float:
        return sum(max(0.0, signal.weight) for signal in self.required_signals)


@dataclass(slots=True)
class EvaluationEvidence:
    """Evidence extracted by an evaluator."""

    matched_signals: List[str] = field(default_factory=list)
    missing_signals: List[str] = field(default_factory=list)


@dataclass(slots=True)
class ConceptEvaluationResult:
    """Output of concept-centric mastery estimation."""

    concept: str
    mastery: float
    confidence: float
    reasoning: List[str] = field(default_factory=list)
    evidence: EvaluationEvidence = field(default_factory=EvaluationEvidence)
    strategy: EvaluationStrategy = EvaluationStrategy.HYBRID
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "concept": self.concept,
            "mastery": round(self.mastery, 3),
            "confidence": round(self.confidence, 3),
            "reasoning": self.reasoning,
            "matched_signals": self.evidence.matched_signals,
            "missing_signals": self.evidence.missing_signals,
            "strategy": self.strategy.value,
            "metadata": self.metadata,
        }
