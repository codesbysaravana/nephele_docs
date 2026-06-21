"""Base evaluator interfaces and utilities."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Iterable, List, Set, Optional

from .models import ConceptEvaluationResult, ConceptRubric, EvaluationEvidence, EvaluationStrategy


UNKNOWN_PATTERNS = [
    r"\bi\s+don'?t\s+know\b",
    r"\bno\s+idea\b",
    r"\bnot\s+sure\b",
    r"\bdon'?t\s+remember\b",
]


class BaseEvaluator(ABC):
    """Abstract interface for mastery evaluators."""

    strategy: EvaluationStrategy

    @abstractmethod
    def evaluate(
        self,
        concept: str,
        question: str,
        answer: str,
        rubric: ConceptRubric,
        context: Optional[str] = None,
    ) -> ConceptEvaluationResult:
        """Estimate concept mastery from a question-answer pair."""


def is_unknown_answer(answer: str) -> bool:
    """Detect explicit non-answers with high certainty."""
    normalized = answer.strip().lower()
    if not normalized:
        return True
    for pattern in UNKNOWN_PATTERNS:
        if re.search(pattern, normalized):
            return True
    return False


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


def contains_phrase(text: str, phrase: str) -> bool:
    return normalize_text(phrase) in normalize_text(text)


def tokenize(value: str) -> Set[str]:
    tokens = re.findall(r"[a-z0-9]+", value.lower())
    return set(tokens)


def jaccard_similarity(a: Iterable[str], b: Iterable[str]) -> float:
    set_a = set(a)
    set_b = set(b)
    if not set_a or not set_b:
        return 0.0
    intersection = set_a.intersection(set_b)
    union = set_a.union(set_b)
    return len(intersection) / len(union)


def low_mastery_result(concept: str, strategy: EvaluationStrategy, rubric: ConceptRubric) -> ConceptEvaluationResult:
    missing = [signal.signal_id for signal in rubric.required_signals]
    evidence = EvaluationEvidence(matched_signals=[], missing_signals=missing)
    return ConceptEvaluationResult(
        concept=concept,
        mastery=0.1,
        confidence=0.95,
        reasoning=["Candidate provided no concept evidence."],
        evidence=evidence,
        strategy=strategy,
        metadata={"classification": "unknown_answer"},
    )


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))
