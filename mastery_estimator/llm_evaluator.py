"""Mock LLM evaluator for concept-centric mastery estimation."""

from __future__ import annotations

from typing import List

from .base import BaseEvaluator, clamp, contains_phrase, is_unknown_answer, low_mastery_result
from .models import ConceptEvaluationResult, ConceptRubric, EvaluationEvidence, EvaluationStrategy


class LLMEvaluator(BaseEvaluator):
    """Rule-backed mock of LLM semantic concept evaluation."""

    strategy = EvaluationStrategy.LLM

    def evaluate(self, concept: str, question: str, answer: str, rubric: ConceptRubric, context: str | None = None) -> ConceptEvaluationResult:
        if is_unknown_answer(answer):
            return low_mastery_result(concept, self.strategy, rubric)

        matched_ids: List[str] = []
        missing_ids: List[str] = []
        reasoning: List[str] = []

        total_weight = rubric.total_required_weight or 1.0
        covered_weight = 0.0

        for signal in rubric.required_signals:
            if _signal_matches(answer, signal.keywords):
                matched_ids.append(signal.signal_id)
                covered_weight += max(0.0, signal.weight)
                reasoning.append(f"Candidate correctly addressed: {signal.description}")
            else:
                missing_ids.append(signal.signal_id)

        coverage = covered_weight / total_weight

        # Optional signals nudge mastery slightly but do not dominate required coverage.
        optional_hits = 0
        for signal in rubric.optional_signals:
            if _signal_matches(answer, signal.keywords):
                optional_hits += 1

        optional_bonus = min(0.05, optional_hits * 0.02)
        mastery = clamp(coverage + optional_bonus)

        # Confidence reflects clarity of detected concept evidence.
        confidence = clamp(0.72 + (coverage * 0.24) + (0.01 * optional_hits), 0.0, 0.98)

        evidence = EvaluationEvidence(
            matched_signals=matched_ids,
            missing_signals=missing_ids,
        )

        if not reasoning:
            reasoning = ["No core concept signals were found in the answer."]

        return ConceptEvaluationResult(
            concept=concept,
            mastery=mastery,
            confidence=confidence,
            reasoning=reasoning,
            evidence=evidence,
            strategy=self.strategy,
            metadata={
                "coverage": round(coverage, 4),
                "optional_hits": optional_hits,
                "model": "mock-llm-rubric-evaluator",
            },
        )


def _signal_matches(answer: str, keywords: List[str]) -> bool:
    for keyword in keywords:
        if contains_phrase(answer, keyword):
            return True
    return False
