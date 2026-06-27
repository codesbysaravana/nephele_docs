"""Pydantic v2 data models for the Nephele coding-round engine.

Defines the canonical schemas for coding questions and evaluations,
along with enumerations for difficulty levels and topic categories.
"""

from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class CodingDifficulty(str, Enum):
    """Difficulty tiers used for adaptive question selection."""

    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class CodingTopic(str, Enum):
    """Data-structure / algorithm topic categories."""

    ARRAYS = "Arrays"
    STRINGS = "Strings"
    LINKED_LISTS = "Linked Lists"
    STACKS = "Stacks"
    QUEUES = "Queues"
    HASH_MAPS = "Hash Maps"
    TREES = "Trees"
    BST = "BST"
    GRAPHS = "Graphs"
    HEAPS = "Heaps"
    GREEDY = "Greedy"
    DYNAMIC_PROGRAMMING = "Dynamic Programming"


class CodingQuestion(BaseModel):
    """Schema returned by the LLM when generating a coding question."""

    title: str = ""
    difficulty: CodingDifficulty = CodingDifficulty.EASY
    topic: CodingTopic = CodingTopic.ARRAYS
    description: str = ""
    sample_input: str = ""
    sample_output: str = ""
    constraints: str = ""
    hints: List[str] = Field(default_factory=list)


class CodingEvaluation(BaseModel):
    """Schema returned by the LLM when evaluating a candidate's explanation."""

    understanding: float = Field(0.0, ge=0, le=10, description="Did the candidate grasp the problem?")
    logic: float = Field(0.0, ge=0, le=10, description="Is the proposed approach logically correct?")
    time_complexity: float = Field(0.0, ge=0, le=10, description="Quality of time-complexity analysis")
    space_complexity: float = Field(0.0, ge=0, le=10, description="Quality of space-complexity analysis")
    communication: float = Field(0.0, ge=0, le=10, description="Clarity of verbal explanation")
    overall: float = Field(0.0, ge=0, le=10, description="Holistic score")
    feedback: str = Field("", description="Free-text feedback for the candidate")
