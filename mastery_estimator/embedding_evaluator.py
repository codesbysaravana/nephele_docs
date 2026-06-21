"""Mock embedding-based evaluator using lexical similarity proxies."""

from __future__ import annotations

from typing import Dict, List

from .base import BaseEvaluator, clamp, is_unknown_answer, jaccard_similarity, low_mastery_result, tokenize
from .models import ConceptEvaluationResult, ConceptRubric, EvaluationEvidence, EvaluationStrategy


class EmbeddingEvaluator(BaseEvaluator):
    """Approximate embedding evaluator via signal-keyword similarity."""

    strategy = EvaluationStrategy.EMBEDDING

    def __init__(self, similarity_threshold: float = 0.2) -> None:
        self.similarity_threshold = similarity_threshold

    def evaluate(self, concept: str, question: str, answer: str, rubric: ConceptRubric, context: str | None = None) -> ConceptEvaluationResult:
        if is_unknown_answer(answer):
            return low_mastery_result(concept, self.strategy, rubric)

        answer_tokens = tokenize(answer)

        matched: List[str] = []
        missing: List[str] = []
        reasoning: List[str] = []

        total_weight = rubric.total_required_weight or 1.0
        covered_weight = 0.0
        similarities: Dict[str, float] = {}

        for signal in rubric.required_signals:
            signal_similarity = _max_signal_similarity(answer_tokens, signal.keywords)
            similarities[signal.signal_id] = signal_similarity

            if signal_similarity >= self.similarity_threshold:
                matched.append(signal.signal_id)
                covered_weight += max(0.0, signal.weight)
                reasoning.append(
                    f"Semantic similarity supports signal '{signal.description}' ({signal_similarity:.2f})."
                )
            else:
                missing.append(signal.signal_id)

        coverage = covered_weight / total_weight

        avg_similarity = 0.0
        if similarities:
            avg_similarity = sum(similarities.values()) / len(similarities)

        mastery = clamp((0.75 * coverage) + (0.25 * avg_similarity))
        confidence = clamp(0.68 + (0.24 * avg_similarity) + (0.08 * coverage), 0.0, 0.97)

        evidence = EvaluationEvidence(matched_signals=matched, missing_signals=missing)

        if not reasoning:
            reasoning = ["Embedding similarity did not meet signal thresholds."]

        return ConceptEvaluationResult(
            concept=concept,
            mastery=mastery,
            confidence=confidence,
            reasoning=reasoning,
            evidence=evidence,
            strategy=self.strategy,
            metadata={
                "avg_similarity": round(avg_similarity, 4),
                "similarities": {k: round(v, 4) for k, v in similarities.items()},
                "model": "mock-embedding-similarity",
            },
        )


def _max_signal_similarity(answer_tokens: set[str], keywords: List[str]) -> float:
    best = 0.0
    for keyword in keywords:
        sim = jaccard_similarity(answer_tokens, tokenize(keyword))
        if sim > best:
            best = sim
    return best
