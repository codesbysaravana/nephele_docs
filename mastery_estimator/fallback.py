"""Fallback execution chain and token/cost persistence logic for concept evaluators."""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from interview_engine.database import DatabaseManager

from .base import BaseEvaluator
from .llm_evaluator import LLMEvaluator
from .models import ConceptEvaluationResult, ConceptRubric, EvaluationStrategy
from .providers import GeminiEvaluator, GroqEvaluator, OpenAIEvaluator

logger = logging.getLogger(__name__)


class FallbackEvaluator(BaseEvaluator):
    """Manages sequential evaluator execution chain: Groq -> Gemini -> OpenAI -> Rubric."""

    strategy = EvaluationStrategy.LLM

    def __init__(self, db_manager: Optional[DatabaseManager] = None) -> None:
        self.db = db_manager or DatabaseManager()

    def evaluate(
        self,
        concept: str,
        question: str,
        answer: str,
        rubric: ConceptRubric,
        context: Optional[str] = None,
    ) -> ConceptEvaluationResult:
        """Run the fallback execution chain for concept evaluation."""
        providers = [
            ("groq", GroqEvaluator),
            ("gemini", GeminiEvaluator),
            ("openai", OpenAIEvaluator),
        ]

        for provider_name, evaluator_cls in providers:
            try:
                # 1. Attempt to instantiate the evaluator.
                # If API keys are missing, this throws a ValueError.
                evaluator = evaluator_cls()
                
                # 2. Attempt to evaluate using the provider.
                logger.info(f"Attempting mastery evaluation using provider: {provider_name}")
                start_time = time.time()
                result = evaluator.evaluate(concept, question, answer, rubric, context)
                latency = time.time() - start_time
                
                # 3. Persist metrics and evaluation history.
                meta = result.metadata
                prompt_tokens = meta.get("prompt_tokens", 0)
                completion_tokens = meta.get("completion_tokens", 0)
                total_tokens = meta.get("total_tokens", 0)
                cost = meta.get("cost_usd", 0.0)
                raw_request = meta.get("raw_request", "")
                raw_response = meta.get("raw_response", "")

                try:
                    self.db.persist_provider_metrics(
                        provider=provider_name,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        latency=latency,
                        cost=cost,
                    )
                except Exception as db_err:
                    logger.error(f"Failed to persist provider metrics to DB: {db_err}")

                try:
                    self.db.persist_evaluation_history(
                        concept_id=concept,
                        question=question,
                        answer=answer,
                        evaluation_request={"prompt": raw_request},
                        evaluation_response={
                            "response": raw_response,
                            "result": result.to_dict()
                        },
                        provider=provider_name,
                        latency=latency,
                        mastery=result.mastery,
                        confidence=result.confidence,
                    )
                except Exception as db_err:
                    logger.error(f"Failed to persist evaluation history to DB: {db_err}")

                logger.info(f"Mastery evaluation succeeded with provider {provider_name} (mastery={result.mastery})")
                return result

            except Exception as e:
                logger.warning(
                    f"Provider {provider_name} failed during evaluation: {e}. Skipping to next provider."
                )

        # 4. Fallback to local rule-backed Rubric Evaluator (LLMEvaluator wrapper)
        logger.warning("All LLM providers failed or were skipped. Falling back to local Rubric Evaluator.")
        start_time = time.time()
        rubric_evaluator = LLMEvaluator()
        result = rubric_evaluator.evaluate(concept, question, answer, rubric, context)
        latency = time.time() - start_time

        try:
            self.db.persist_evaluation_history(
                concept_id=concept,
                question=question,
                answer=answer,
                evaluation_request={"fallback": "rubric"},
                evaluation_response={"result": result.to_dict()},
                provider="rubric",
                latency=latency,
                mastery=result.mastery,
                confidence=result.confidence,
            )
        except Exception as db_err:
            logger.error(f"Failed to persist fallback evaluation history to DB: {db_err}")

        return result
