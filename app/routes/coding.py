"""FastAPI routes for the Nephele coding-round engine.

Provides endpoints for generating coding questions and evaluating
candidate explanations.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.coding.coding_engine import CodingEngine
from app.models.coding_models import (
    CodingDifficulty,
    CodingEvaluation,
    CodingQuestion,
    CodingTopic,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/coding", tags=["Coding"])

# A module-level engine instance (re-used across requests).
_engine = CodingEngine()


# ── Request / response bodies ────────────────────────────────────────


class EvaluateRequest(BaseModel):
    """Request body for ``POST /coding/evaluate``."""

    question: CodingQuestion = Field(..., description="The coding question that was posed.")
    explanation: str = Field(..., min_length=1, description="Candidate's verbal explanation of their approach.")


# ── Endpoints ────────────────────────────────────────────────────────


@router.get(
    "/question",
    response_model=CodingQuestion,
    summary="Generate a coding question",
    description="Returns a single LLM-generated coding question. "
    "Optionally specify topic and difficulty; otherwise defaults are used.",
)
async def get_question(
    topic: Optional[CodingTopic] = Query(
        default=None,
        description="Data-structure / algorithm topic. Defaults to Arrays.",
    ),
    difficulty: Optional[CodingDifficulty] = Query(
        default=None,
        description="Difficulty tier. Defaults to Easy.",
    ),
    skills: Optional[List[str]] = Query(
        default=None,
        description="Candidate skills (can be repeated).",
    ),
) -> CodingQuestion:
    """Generate a coding interview question.

    Query Parameters
    ----------------
    topic : CodingTopic, optional
        Defaults to ``Arrays``.
    difficulty : CodingDifficulty, optional
        Defaults to ``Easy``.
    skills : list[str], optional
        Candidate skill keywords used to personalise the question.
    """

    resolved_topic = topic or CodingTopic.ARRAYS
    resolved_difficulty = difficulty or CodingDifficulty.EASY
    resolved_skills: List[str] = skills or []

    try:
        question = await _engine.generate_question(
            topic=resolved_topic,
            difficulty=resolved_difficulty,
            candidate_skills=resolved_skills,
        )
        return question
    except Exception as exc:
        logger.error("GET /coding/question failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate coding question. Please try again later.",
        ) from exc


@router.post(
    "/evaluate",
    response_model=CodingEvaluation,
    summary="Evaluate a candidate's explanation",
    description="Accepts the original question and the candidate's verbal "
    "explanation, then returns a scored evaluation.",
)
async def evaluate_answer(body: EvaluateRequest) -> CodingEvaluation:
    """Evaluate a candidate's verbal explanation of their coding solution.

    Request Body
    ------------
    question : CodingQuestion
        The question that was posed to the candidate.
    explanation : str
        The candidate's explanation of their approach.
    """

    try:
        evaluation = await _engine.evaluate_answer(
            question=body.question,
            candidate_explanation=body.explanation,
        )
        return evaluation
    except Exception as exc:
        logger.error("POST /coding/evaluate failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to evaluate the candidate's answer. Please try again later.",
        ) from exc
