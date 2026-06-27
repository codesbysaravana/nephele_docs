"""Core coding-round engine — question generation and answer evaluation.

Wraps the Groq async client to call ``llama-3.1-8b-instant`` in JSON
mode, validates responses with Pydantic, and provides sensible
fallbacks on error.
"""

import json
import logging
from typing import List

import groq

from app.config import GROQ_API_KEY
from app.models.coding_models import (
    CodingDifficulty,
    CodingEvaluation,
    CodingQuestion,
    CodingTopic,
)
from app.prompts.coding_evaluation import get_coding_evaluation_prompt
from app.prompts.coding_questions import get_coding_question_prompt

logger = logging.getLogger(__name__)

_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


class CodingEngine:
    """Async engine for generating coding questions and evaluating answers.

    Uses the Groq cloud API with ``llama-3.1-8b-instant`` in
    ``response_format={"type": "json_object"}`` mode so every response
    is guaranteed to be parseable JSON.
    """

    def __init__(self) -> None:
        if not GROQ_API_KEY:
            logger.warning(
                "GROQ_API_KEY is not set — CodingEngine will fail on API calls."
            )
        self._client = groq.AsyncGroq(api_key=GROQ_API_KEY)
        logger.info("CodingEngine initialised (model=%s)", _MODEL)

    # ── Question generation ──────────────────────────────────────────

    async def generate_question(
        self,
        topic: CodingTopic,
        difficulty: CodingDifficulty,
        candidate_skills: List[str],
    ) -> CodingQuestion:
        """Generate a single coding interview question via LLM.

        Parameters
        ----------
        topic:
            The target data-structure / algorithm topic.
        difficulty:
            The desired difficulty tier.
        candidate_skills:
            The candidate's self-declared skills.

        Returns
        -------
        CodingQuestion
            A validated Pydantic model instance.
        """

        prompt = get_coding_question_prompt(
            topic=topic.value,
            difficulty=difficulty.value,
            candidate_skills=candidate_skills,
        )

        try:
            response = await self._client.chat.completions.create(
                model=_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that responds only in valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=1024,
            )

            raw = response.choices[0].message.content
            logger.debug("Raw question JSON: %s", raw)

            data = json.loads(raw)  # type: ignore[arg-type]
            question = CodingQuestion.model_validate(data)
            logger.info("Generated question: %s [%s/%s]", question.title, topic.value, difficulty.value)
            return question

        except json.JSONDecodeError as exc:
            logger.error("Failed to parse question JSON from LLM response: %s", exc)
        except Exception as exc:  # noqa: BLE001
            logger.error("Question generation failed: %s", exc, exc_info=True)

        # Fallback question so callers always receive a valid object.
        logger.warning("Returning fallback coding question")
        return CodingQuestion(
            title="Two Sum",
            difficulty=difficulty,
            topic=topic,
            description=(
                "Given an array of integers nums and an integer target, "
                "return the indices of the two numbers that add up to target."
            ),
            sample_input="nums = [2, 7, 11, 15], target = 9",
            sample_output="[0, 1]",
            constraints="2 <= nums.length <= 10^4, -10^9 <= nums[i] <= 10^9",
            hints=[
                "Think about what value you need to find for each element.",
                "A hash map can reduce the time complexity.",
                "You can solve this in a single pass through the array.",
            ],
        )

    # ── Answer evaluation ────────────────────────────────────────────

    async def evaluate_answer(
        self,
        question: CodingQuestion,
        candidate_explanation: str,
    ) -> CodingEvaluation:
        """Evaluate the candidate's verbal explanation of their solution.

        Parameters
        ----------
        question:
            The ``CodingQuestion`` that was posed.
        candidate_explanation:
            The candidate's spoken / typed explanation.

        Returns
        -------
        CodingEvaluation
            A validated Pydantic model instance with scores and feedback.
        """

        prompt = get_coding_evaluation_prompt(question, candidate_explanation)

        try:
            response = await self._client.chat.completions.create(
                model=_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that responds only in valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=512,
            )

            raw = response.choices[0].message.content
            logger.debug("Raw evaluation JSON: %s", raw)

            data = json.loads(raw)  # type: ignore[arg-type]
            evaluation = CodingEvaluation.model_validate(data)
            logger.info("Evaluation complete — overall=%.1f", evaluation.overall)
            return evaluation

        except json.JSONDecodeError as exc:
            logger.error("Failed to parse evaluation JSON from LLM response: %s", exc)
        except Exception as exc:  # noqa: BLE001
            logger.error("Answer evaluation failed: %s", exc, exc_info=True)

        # Fallback evaluation so callers always receive a valid object.
        logger.warning("Returning fallback coding evaluation")
        return CodingEvaluation(
            understanding=0.0,
            logic=0.0,
            time_complexity=0.0,
            space_complexity=0.0,
            communication=0.0,
            overall=0.0,
            feedback="Evaluation could not be completed due to a system error. Please try again.",
        )
