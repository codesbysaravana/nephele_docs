"""
Nephele Interview Engine — Enumerations.

All state, type, and category enumerations used across the orchestrator.
"""

from enum import Enum


class InterviewState(str, Enum):
    """
    Complete interview lifecycle states.

    The interview progresses through these states in order, with the
    orchestrator managing transitions based on candidate interaction
    and internal logic.

    Lifecycle Flow:
        IDLE → GREETING → CANDIDATE_VERIFICATION → RESUME_COLLECTION
        → RESUME_ANALYSIS → ROLE_SELECTION → INTERVIEW_SETUP
        → HR_ROUND → TECHNICAL_ROUND → BEHAVIORAL_ROUND
        → SITUATIONAL_ROUND → MCQ_ROUND → EVALUATION
        → FEEDBACK → REPORT_GENERATION → COMPLETED

    Any active state can branch into:
        → FOLLOW_UP (returns to originating round)
        → PAUSED   (resumes to the state it was paused from)
        → ERROR    (can recover to PAUSED or restart)
    """

    # --- Pre-Interview ---
    IDLE = "idle"
    GREETING = "greeting"
    CANDIDATE_VERIFICATION = "candidate_verification"
    RESUME_COLLECTION = "resume_collection"
    RESUME_ANALYSIS = "resume_analysis"
    ROLE_SELECTION = "role_selection"
    INTERVIEW_SETUP = "interview_setup"

    # --- Interview Rounds ---
    HR_ROUND = "hr_round"
    TECHNICAL_ROUND = "technical_round"
    BEHAVIORAL_ROUND = "behavioral_round"
    SITUATIONAL_ROUND = "situational_round"
    MCQ_ROUND = "mcq_round"

    # --- Follow-Up (branches from any round, returns to it) ---
    FOLLOW_UP = "follow_up"

    # --- Post-Interview ---
    EVALUATION = "evaluation"
    FEEDBACK = "feedback"
    REPORT_GENERATION = "report_generation"
    COMPLETED = "completed"

    # --- Meta States ---
    PAUSED = "paused"
    ERROR = "error"


# States that represent active interview rounds
ROUND_STATES = frozenset({
    InterviewState.HR_ROUND,
    InterviewState.TECHNICAL_ROUND,
    InterviewState.BEHAVIORAL_ROUND,
    InterviewState.SITUATIONAL_ROUND,
    InterviewState.MCQ_ROUND,
})

# States where the system is waiting for candidate speech
LISTENING_STATES = frozenset({
    InterviewState.CANDIDATE_VERIFICATION,
    InterviewState.RESUME_COLLECTION,
    InterviewState.ROLE_SELECTION,
    InterviewState.HR_ROUND,
    InterviewState.TECHNICAL_ROUND,
    InterviewState.BEHAVIORAL_ROUND,
    InterviewState.SITUATIONAL_ROUND,
    InterviewState.MCQ_ROUND,
    InterviewState.FOLLOW_UP,
})

# States where the system is processing internally (no candidate input needed)
PROCESSING_STATES = frozenset({
    InterviewState.RESUME_ANALYSIS,
    InterviewState.INTERVIEW_SETUP,
    InterviewState.EVALUATION,
    InterviewState.FEEDBACK,
    InterviewState.REPORT_GENERATION,
})

# Terminal states
TERMINAL_STATES = frozenset({
    InterviewState.COMPLETED,
})


class Difficulty(str, Enum):
    """Question difficulty levels for adaptive interviewing."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"

    @property
    def numeric(self) -> int:
        """Numeric value for comparison and arithmetic."""
        return {"easy": 1, "medium": 2, "hard": 3, "expert": 4}[self.value]

    def increase(self) -> "Difficulty":
        """Return one level harder, capped at EXPERT."""
        order = [Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD, Difficulty.EXPERT]
        idx = order.index(self)
        return order[min(idx + 1, len(order) - 1)]

    def decrease(self) -> "Difficulty":
        """Return one level easier, capped at EASY."""
        order = [Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD, Difficulty.EXPERT]
        idx = order.index(self)
        return order[max(idx - 1, 0)]


class RoundType(str, Enum):
    """Interview round categories."""

    HR = "hr"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    SITUATIONAL = "situational"
    MCQ = "mcq"

    @property
    def display_name(self) -> str:
        """Human-readable name for prompts and reports."""
        return {
            "hr": "HR / Introductory",
            "technical": "Technical",
            "behavioral": "Behavioral (STAR)",
            "situational": "Situational",
            "mcq": "Multiple Choice",
        }[self.value]

    @property
    def state(self) -> InterviewState:
        """The InterviewState that corresponds to this round."""
        return {
            RoundType.HR: InterviewState.HR_ROUND,
            RoundType.TECHNICAL: InterviewState.TECHNICAL_ROUND,
            RoundType.BEHAVIORAL: InterviewState.BEHAVIORAL_ROUND,
            RoundType.SITUATIONAL: InterviewState.SITUATIONAL_ROUND,
            RoundType.MCQ: InterviewState.MCQ_ROUND,
        }[self]


# Default round order
DEFAULT_ROUND_ORDER = [
    RoundType.HR,
    RoundType.TECHNICAL,
    RoundType.BEHAVIORAL,
    RoundType.SITUATIONAL,
    RoundType.MCQ,
]


class SignalSource(str, Enum):
    """Multi-modal signal input sources."""

    VISION = "vision"
    AUDIO = "audio"
    LANGUAGE = "language"


class ScoreCategory(str, Enum):
    """Evaluation scoring categories for the final report."""

    TECHNICAL_KNOWLEDGE = "technical_knowledge"
    PROBLEM_SOLVING = "problem_solving"
    COMMUNICATION = "communication"
    CONFIDENCE = "confidence"
    EYE_CONTACT = "eye_contact"
    ENGAGEMENT = "engagement"
    PROFESSIONALISM = "professionalism"

    @property
    def display_name(self) -> str:
        return self.value.replace("_", " ").title()

    @property
    def default_weight(self) -> float:
        """Default weight in the final score calculation."""
        return {
            "technical_knowledge": 0.25,
            "problem_solving": 0.20,
            "communication": 0.15,
            "confidence": 0.10,
            "eye_contact": 0.10,
            "engagement": 0.10,
            "professionalism": 0.10,
        }[self.value]
