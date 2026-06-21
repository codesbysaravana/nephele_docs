"""Hybrid mastery evaluator combining LLM and embedding outputs."""

from __future__ import annotations

from typing import Optional
from .base import BaseEvaluator, clamp, low_mastery_result
from .embedding_evaluator import EmbeddingEvaluator
from .llm_evaluator import LLMEvaluator
from .models import ConceptEvaluationResult, ConceptRubric, EvaluationEvidence, EvaluationStrategy


class HybridEvaluator(BaseEvaluator):
    """Blend LLM and embedding estimates with agreement-based confidence."""

    strategy = EvaluationStrategy.HYBRID

    def __init__(
        self,
        llm_weight: float = 0.7,
        embedding_weight: float = 0.3,
        llm_evaluator: Optional[BaseEvaluator] = None,
    ) -> None:
        total = llm_weight + embedding_weight
        self.llm_weight = llm_weight / total
        self.embedding_weight = embedding_weight / total
        self.llm = llm_evaluator or LLMEvaluator()
        self.embedding = EmbeddingEvaluator()

    def evaluate(self, concept: str, question: str, answer: str, rubric: ConceptRubric, context: str | None = None) -> ConceptEvaluationResult:
        llm_result = self.llm.evaluate(concept, question, answer, rubric, context)
        emb_result = self.embedding.evaluate(concept, question, answer, rubric, context)

        if llm_result.metadata.get("classification") == "unknown_answer":
            return low_mastery_result(concept, self.strategy, rubric)

        mastery = clamp(
            (self.llm_weight * llm_result.mastery)
            + (self.embedding_weight * emb_result.mastery)
        )

        agreement = 1.0 - abs(llm_result.mastery - emb_result.mastery)
        confidence = clamp(
            (self.llm_weight * llm_result.confidence)
            + (self.embedding_weight * emb_result.confidence)
            + (0.08 * agreement)
        )

        matched = sorted(
            set(llm_result.evidence.matched_signals).union(emb_result.evidence.matched_signals)
        )
        missing = sorted({signal.signal_id for signal in rubric.required_signals}.difference(matched))

        reasoning = [
            "Hybrid evaluation combined rubric-semantic and embedding-similarity evidence.",
            f"LLM mastery={llm_result.mastery:.2f}, embedding mastery={emb_result.mastery:.2f}.",
        ]
        reasoning.extend(llm_result.reasoning[:2])
        reasoning.extend(emb_result.reasoning[:2])

        return ConceptEvaluationResult(
            concept=concept,
            mastery=mastery,
            confidence=confidence,
            reasoning=reasoning,
            evidence=EvaluationEvidence(
                matched_signals=matched,
                missing_signals=missing,
            ),
            strategy=self.strategy,
            metadata={
                "llm": llm_result.to_dict(),
                "embedding": emb_result.to_dict(),
                "agreement": round(agreement, 4),
                "weights": {
                    "llm": round(self.llm_weight, 4),
                    "embedding": round(self.embedding_weight, 4),
                },
            },
        )
