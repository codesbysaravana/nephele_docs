"""Facade service for concept mastery estimation with database and vector store context integration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from interview_engine.chroma_store import ChromaStore
from interview_engine.database import DatabaseManager

from .embedding_evaluator import EmbeddingEvaluator
from .fallback import FallbackEvaluator
from .hybrid_evaluator import HybridEvaluator
from .models import ConceptEvaluationResult, EvaluationStrategy
from .rubric_loader import RubricLoader

logger = logging.getLogger(__name__)


class MasteryEstimationEngine:
    """High-level API to estimate concept mastery from a QA pair."""

    def __init__(
        self,
        rubric_dir: str | Path | None = None,
        db_manager: Optional[DatabaseManager] = None,
        chroma_store: Optional[ChromaStore] = None,
    ) -> None:
        root = Path(__file__).parent
        self.rubric_loader = RubricLoader(rubric_dir or (root / "rubrics"))
        self.db = db_manager or DatabaseManager()
        self.chroma = chroma_store or ChromaStore()

        fallback_eval = FallbackEvaluator(db_manager=self.db)

        self._evaluators = {
            EvaluationStrategy.LLM: fallback_eval,
            EvaluationStrategy.EMBEDDING: EmbeddingEvaluator(),
            EvaluationStrategy.HYBRID: HybridEvaluator(llm_evaluator=fallback_eval),
        }

    def get_chroma_context(self, concept: str, answer: str) -> str:
        """Query Chroma for context augmentation: misconceptions, reference examples, and similar answers."""
        context_parts = []

        # 1. Retrieve common misconceptions
        try:
            misconceptions = self.chroma.retrieve_misconceptions(concept, limit=2)
            if misconceptions:
                context_parts.append("Known Misconceptions:")
                for m in misconceptions:
                    context_parts.append(f"- {m}")
        except Exception as e:
            logger.warning(f"Error retrieving misconceptions from Chroma: {e}")

        # 2. Retrieve similar past answers
        try:
            similar_answers = self.chroma.retrieve_similar_answers(answer, limit=2)
            if similar_answers:
                context_parts.append("Similar Past Answers:")
                for sa in similar_answers:
                    context_parts.append(f"- {sa}")
        except Exception as e:
            logger.warning(f"Error retrieving similar answers from Chroma: {e}")

        # 3. Retrieve reference examples
        try:
            examples = self.chroma.retrieve_examples(concept, limit=2)
            if examples:
                context_parts.append("Concept Examples:")
                for ex in examples:
                    context_parts.append(f"- {ex}")
        except Exception as e:
            logger.warning(f"Error retrieving examples from Chroma: {e}")

        return "\n".join(context_parts) if context_parts else ""

    def estimate(
        self,
        concept: str,
        question: str,
        answer: str,
        strategy: EvaluationStrategy = EvaluationStrategy.HYBRID,
    ) -> ConceptEvaluationResult:
        """Estimate concept mastery using the configured strategy augmented by Chroma context."""
        rubric = self.rubric_loader.load_concept_rubric(concept)
        context_str = self.get_chroma_context(concept, answer)

        evaluator = self._evaluators[strategy]
        return evaluator.evaluate(
            concept=concept,
            question=question,
            answer=answer,
            rubric=rubric,
            context=context_str if context_str else None,
        )
