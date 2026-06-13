"""
Nephele Interview Engine — Domain Models.

Pure data structures that represent the core interview domain.
These are framework-agnostic dataclasses — no ORM, no Pydantic, no
external dependencies. They are the single source of truth for what
an interview session, question, answer, and candidate look like
throughout the entire backend.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from .enums import Difficulty, InterviewState, RoundType


# ---------------------------------------------------------------------------
# Candidate & Resume
# ---------------------------------------------------------------------------

@dataclass
class CandidateProfile:
    """
    Represents a candidate participating in an interview.

    Built up progressively during the CANDIDATE_VERIFICATION and
    RESUME_ANALYSIS states.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    email: str = ""
    phone: str = ""

    # Populated by resume analysis
    skills: Dict[str, List[str]] = field(default_factory=dict)
    # Example: {"languages": ["Python", "Java"], "frameworks": ["FastAPI"]}

    experience_years: float = 0.0
    education: List[Dict[str, str]] = field(default_factory=list)
    # Example: [{"degree": "B.Tech", "field": "CSE", "institution": "..."}]

    projects: List[Dict[str, str]] = field(default_factory=list)
    resume_raw_text: str = ""
    target_role: str = ""

    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def all_skills_flat(self) -> List[str]:
        """Flatten all skill categories into a single list."""
        result = []
        for category_skills in self.skills.values():
            result.extend(category_skills)
        return result

    def to_context_summary(self) -> str:
        """
        Produce a compact text summary suitable for injecting into
        LLM context.
        """
        parts = [f"Candidate: {self.name}"]
        if self.target_role:
            parts.append(f"Target Role: {self.target_role}")
        if self.experience_years:
            parts.append(f"Experience: {self.experience_years:.1f} years")
        if self.skills:
            for category, items in self.skills.items():
                parts.append(f"  {category}: {', '.join(items)}")
        if self.education:
            for edu in self.education:
                parts.append(
                    f"  Education: {edu.get('degree', '')} in "
                    f"{edu.get('field', '')} from {edu.get('institution', '')}"
                )
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Interview Configuration
# ---------------------------------------------------------------------------

@dataclass
class InterviewConfig:
    """
    Configuration for an interview session.

    Set during INTERVIEW_SETUP and immutable afterwards.
    """

    round_order: List[RoundType] = field(
        default_factory=lambda: [
            RoundType.HR,
            RoundType.TECHNICAL,
            RoundType.BEHAVIORAL,
            RoundType.SITUATIONAL,
            RoundType.MCQ,
        ]
    )
    questions_per_round: Dict[RoundType, int] = field(
        default_factory=lambda: {
            RoundType.HR: 3,
            RoundType.TECHNICAL: 5,
            RoundType.BEHAVIORAL: 3,
            RoundType.SITUATIONAL: 2,
            RoundType.MCQ: 3,
        }
    )
    starting_difficulty: Difficulty = Difficulty.MEDIUM
    max_follow_ups_per_question: int = 2
    answer_timeout_seconds: float = 120.0
    round_timeout_seconds: float = 600.0

    @property
    def total_planned_questions(self) -> int:
        return sum(
            self.questions_per_round.get(r, 0) for r in self.round_order
        )


# ---------------------------------------------------------------------------
# Questions & Answers
# ---------------------------------------------------------------------------

@dataclass
class QuestionRecord:
    """
    A single question asked during the interview.

    Tracks lineage (follow-up chains) via parent_question_id.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    round_type: RoundType = RoundType.HR
    question_text: str = ""
    topic: str = ""
    difficulty: Difficulty = Difficulty.MEDIUM
    sequence_number: int = 0

    # Follow-up tracking
    parent_question_id: Optional[str] = None
    follow_up_depth: int = 0  # 0 = original, 1 = first follow-up, etc.

    asked_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def question_hash(self) -> str:
        """SHA-256 hash for deduplication."""
        normalized = self.question_text.strip().lower()
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    @property
    def is_follow_up(self) -> bool:
        return self.parent_question_id is not None


@dataclass
class AnswerRecord:
    """
    A candidate's response to a question, with multi-modal scoring.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    question_id: str = ""
    session_id: str = ""
    transcript: str = ""
    duration_seconds: float = 0.0

    # Audio-derived metrics
    audio_metrics: AudioSnapshot = field(
        default_factory=lambda: AudioSnapshot()
    )

    # Vision-derived metrics (averaged over answer duration)
    vision_metrics: VisionSnapshot = field(
        default_factory=lambda: VisionSnapshot()
    )

    # LLM-evaluated language scores (each 0.0–10.0)
    language_scores: Dict[str, float] = field(default_factory=dict)
    # Expected keys: "technical_correctness", "communication_quality",
    #                "answer_depth", "relevance"

    # Final fused score for this answer (0.0–100.0)
    answer_score: float = 0.0

    answered_at: datetime = field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Multi-Modal Signal Snapshots
# ---------------------------------------------------------------------------

@dataclass
class VisionSnapshot:
    """
    Aggregated vision metrics for a time window (typically one answer).

    Values are rolling averages computed from the vision pipeline
    frames received during the candidate's response.
    """

    eye_contact_score: float = 0.0      # 0–100
    engagement_score: float = 0.0       # 0–100
    head_yaw: float = 0.0              # degrees
    head_pitch: float = 0.0            # degrees
    head_roll: float = 0.0             # degrees
    face_visible_ratio: float = 0.0    # 0.0–1.0 (fraction of time face seen)
    sample_count: int = 0              # number of frames averaged

    def update_from_frame(
        self,
        eye_contact: float,
        engagement: float,
        yaw: float,
        pitch: float,
        roll: float,
        face_visible: bool,
    ) -> None:
        """
        Incrementally update the rolling average with a new vision frame.

        Uses the online mean formula:
            new_mean = old_mean + (new_value - old_mean) / n
        """
        self.sample_count += 1
        n = self.sample_count

        self.eye_contact_score += (eye_contact - self.eye_contact_score) / n
        self.engagement_score += (engagement - self.engagement_score) / n
        self.head_yaw += (yaw - self.head_yaw) / n
        self.head_pitch += (pitch - self.head_pitch) / n
        self.head_roll += (roll - self.head_roll) / n

        visible_val = 1.0 if face_visible else 0.0
        self.face_visible_ratio += (visible_val - self.face_visible_ratio) / n

    def reset(self) -> None:
        """Clear all accumulated data for the next answer window."""
        self.eye_contact_score = 0.0
        self.engagement_score = 0.0
        self.head_yaw = 0.0
        self.head_pitch = 0.0
        self.head_roll = 0.0
        self.face_visible_ratio = 0.0
        self.sample_count = 0


@dataclass
class AudioSnapshot:
    """
    Audio-derived metrics for a single answer.

    Populated by the STT service or audio analysis layer.
    """

    words_per_minute: float = 0.0
    silence_ratio: float = 0.0         # 0.0–1.0 (fraction of silence)
    filler_word_count: int = 0
    total_word_count: int = 0
    speech_duration_seconds: float = 0.0


@dataclass
class MultiModalSignals:
    """
    Fused multi-modal signals for the current answer window.

    This is the unified signal object that the orchestrator consults
    when making decisions about difficulty adaptation, follow-ups,
    and scoring.
    """

    vision: VisionSnapshot = field(default_factory=VisionSnapshot)
    audio: AudioSnapshot = field(default_factory=AudioSnapshot)

    # Language scores from LLM evaluation (each 0.0–10.0)
    language_technical: float = 0.0
    language_communication: float = 0.0
    language_depth: float = 0.0
    language_relevance: float = 0.0

    @property
    def language_average(self) -> float:
        """Average of all language sub-scores."""
        scores = [
            self.language_technical,
            self.language_communication,
            self.language_depth,
            self.language_relevance,
        ]
        return sum(scores) / len(scores) if scores else 0.0

    @property
    def overall_confidence(self) -> float:
        """
        Fused confidence score combining all modalities.

        Formula:
            0.75 × language_avg_normalized +
            0.15 × vision_engagement_normalized +
            0.10 × audio_confidence

        Returns 0.0–100.0
        """
        language_norm = self.language_average * 10.0  # 0-10 → 0-100
        vision_norm = self.vision.engagement_score     # already 0-100
        audio_conf = self._compute_audio_confidence()  # 0-100

        return (
            0.75 * language_norm
            + 0.15 * vision_norm
            + 0.10 * audio_conf
        )

    def _compute_audio_confidence(self) -> float:
        """
        Derive a confidence score from audio metrics.

        High confidence indicators:
          - WPM in 120-180 range (natural speech pace)
          - Low silence ratio (< 0.3)
          - Few filler words relative to total words
        """
        # WPM scoring: peak at 150 WPM, drops off either side
        wpm = self.audio.words_per_minute
        if wpm <= 0:
            wpm_score = 0.0
        else:
            deviation = abs(wpm - 150) / 100.0
            wpm_score = max(0.0, 1.0 - deviation) * 100.0

        # Silence penalty: 0% silence = 100, 100% silence = 0
        silence_score = max(0.0, (1.0 - self.audio.silence_ratio)) * 100.0

        # Filler word penalty
        if self.audio.total_word_count > 0:
            filler_ratio = self.audio.filler_word_count / self.audio.total_word_count
            filler_score = max(0.0, (1.0 - filler_ratio * 5.0)) * 100.0
        else:
            filler_score = 0.0

        return 0.40 * wpm_score + 0.30 * silence_score + 0.30 * filler_score

    def reset_for_next_answer(self) -> None:
        """Clear all signals for the next answer window."""
        self.vision.reset()
        self.audio = AudioSnapshot()
        self.language_technical = 0.0
        self.language_communication = 0.0
        self.language_depth = 0.0
        self.language_relevance = 0.0


# ---------------------------------------------------------------------------
# Round & Session Aggregates
# ---------------------------------------------------------------------------

@dataclass
class RoundResult:
    """Aggregated results for a completed interview round."""

    round_type: RoundType = RoundType.HR
    questions_asked: int = 0
    questions_answered: int = 0
    average_score: float = 0.0
    difficulty_progression: List[Difficulty] = field(default_factory=list)
    topics_covered: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None


@dataclass
class InterviewSession:
    """
    The root aggregate for an entire interview session.

    This is the top-level object that the orchestrator manages.
    It holds references to the candidate, configuration, all questions
    and answers, current state, and accumulated results.

    Designed for serialization to the database for persistence and
    crash recovery.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    candidate: CandidateProfile = field(default_factory=CandidateProfile)
    config: InterviewConfig = field(default_factory=InterviewConfig)

    # Current state
    current_state: InterviewState = InterviewState.IDLE
    previous_state: Optional[InterviewState] = None  # for pause/resume
    current_round_type: Optional[RoundType] = None
    current_round_index: int = 0  # index into config.round_order
    current_difficulty: Difficulty = Difficulty.MEDIUM

    # Question tracking
    questions: List[QuestionRecord] = field(default_factory=list)
    answers: List[AnswerRecord] = field(default_factory=list)
    asked_question_hashes: Set[str] = field(default_factory=set)

    # Round results
    round_results: Dict[str, RoundResult] = field(default_factory=dict)

    # Live multi-modal signals (current answer window)
    current_signals: MultiModalSignals = field(
        default_factory=MultiModalSignals
    )

    # Session-level scores (populated during EVALUATION)
    category_scores: Dict[str, float] = field(default_factory=dict)
    final_score: float = 0.0
    grade: str = ""

    # Conversation history for LLM context
    conversation_history: List[Dict[str, str]] = field(default_factory=list)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    # Error tracking
    last_error: str = ""
    error_count: int = 0

    # --- Convenience Properties ---

    @property
    def is_active(self) -> bool:
        return self.current_state not in {
            InterviewState.COMPLETED,
            InterviewState.IDLE,
            InterviewState.ERROR,
        }

    @property
    def is_in_round(self) -> bool:
        from .enums import ROUND_STATES
        return self.current_state in ROUND_STATES

    @property
    def current_round_config_limit(self) -> int:
        """Max questions configured for the current round."""
        if self.current_round_type:
            return self.config.questions_per_round.get(
                self.current_round_type, 3
            )
        return 0

    @property
    def current_round_question_count(self) -> int:
        """Number of non-follow-up questions asked in the current round."""
        if not self.current_round_type:
            return 0
        return sum(
            1 for q in self.questions
            if q.round_type == self.current_round_type and not q.is_follow_up
        )

    @property
    def last_question(self) -> Optional[QuestionRecord]:
        return self.questions[-1] if self.questions else None

    @property
    def last_answer(self) -> Optional[AnswerRecord]:
        return self.answers[-1] if self.answers else None

    @property
    def total_duration_seconds(self) -> float:
        if not self.started_at:
            return 0.0
        end = self.ended_at or datetime.utcnow()
        return (end - self.started_at).total_seconds()

    def get_questions_for_round(self, round_type: RoundType) -> List[QuestionRecord]:
        return [q for q in self.questions if q.round_type == round_type]

    def get_answers_for_round(self, round_type: RoundType) -> List[AnswerRecord]:
        round_q_ids = {q.id for q in self.get_questions_for_round(round_type)}
        return [a for a in self.answers if a.question_id in round_q_ids]

    def add_to_history(self, role: str, content: str) -> None:
        """Append a message to the conversation history."""
        self.conversation_history.append({"role": role, "content": content})
