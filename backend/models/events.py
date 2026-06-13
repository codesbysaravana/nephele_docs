"""
Nephele Interview Engine — Event Definitions.

Lightweight event objects emitted by the state machine and orchestrator.
These are consumed by the WebSocket manager to push real-time updates
to connected frontends, and by the session manager for persistence.

All events inherit from a common ``Event`` base and carry a timestamp,
session ID, and typed payload.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from .enums import Difficulty, InterviewState, RoundType, ScoreCategory


@dataclass
class Event:
    """Base event that all interview events inherit from."""

    event_type: str = ""
    session_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-safe dictionary for WebSocket transmission."""
        return {
            "event": self.event_type,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self._payload(),
        }

    def _payload(self) -> Dict[str, Any]:
        """Override in subclasses to provide event-specific data."""
        return {}


@dataclass
class StateChangedEvent(Event):
    """Emitted whenever the state machine transitions to a new state."""

    event_type: str = field(default="state_changed", init=False)
    from_state: InterviewState = InterviewState.IDLE
    to_state: InterviewState = InterviewState.IDLE
    trigger: str = ""  # The trigger name that caused the transition

    def _payload(self) -> Dict[str, Any]:
        return {
            "from": self.from_state.value,
            "to": self.to_state.value,
            "trigger": self.trigger,
        }


@dataclass
class QuestionAskedEvent(Event):
    """Emitted when a new question is presented to the candidate."""

    event_type: str = field(default="question_asked", init=False)
    question_id: str = ""
    question_text: str = ""
    round_type: RoundType = RoundType.HR
    difficulty: Difficulty = Difficulty.MEDIUM
    sequence_number: int = 0
    is_follow_up: bool = False

    def _payload(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "text": self.question_text,
            "round": self.round_type.value,
            "difficulty": self.difficulty.value,
            "sequence": self.sequence_number,
            "is_follow_up": self.is_follow_up,
        }


@dataclass
class AnswerReceivedEvent(Event):
    """Emitted when a candidate's answer has been transcribed and recorded."""

    event_type: str = field(default="answer_received", init=False)
    answer_id: str = ""
    question_id: str = ""
    transcript_preview: str = ""  # First 200 chars
    duration_seconds: float = 0.0
    answer_score: float = 0.0

    def _payload(self) -> Dict[str, Any]:
        return {
            "answer_id": self.answer_id,
            "question_id": self.question_id,
            "preview": self.transcript_preview[:200],
            "duration": round(self.duration_seconds, 1),
            "score": round(self.answer_score, 1),
        }


@dataclass
class VisionUpdateEvent(Event):
    """Emitted periodically with the latest vision metrics."""

    event_type: str = field(default="vision_update", init=False)
    eye_contact_score: float = 0.0
    engagement_score: float = 0.0
    face_visible: bool = False
    head_yaw: float = 0.0
    head_pitch: float = 0.0

    def _payload(self) -> Dict[str, Any]:
        return {
            "eye_contact_score": round(self.eye_contact_score, 1),
            "engagement_score": round(self.engagement_score, 1),
            "face_visible": self.face_visible,
            "head_yaw": round(self.head_yaw, 1),
            "head_pitch": round(self.head_pitch, 1),
        }


@dataclass
class ScoreUpdateEvent(Event):
    """Emitted when a scoring category is updated."""

    event_type: str = field(default="score_update", init=False)
    category: str = ""
    value: float = 0.0

    def _payload(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "value": round(self.value, 1),
        }


@dataclass
class RoundCompleteEvent(Event):
    """Emitted when an interview round finishes."""

    event_type: str = field(default="round_complete", init=False)
    round_type: RoundType = RoundType.HR
    questions_asked: int = 0
    average_score: float = 0.0
    duration_seconds: float = 0.0

    def _payload(self) -> Dict[str, Any]:
        return {
            "round": self.round_type.value,
            "round_name": self.round_type.display_name,
            "questions_asked": self.questions_asked,
            "average_score": round(self.average_score, 1),
            "duration": round(self.duration_seconds, 1),
        }


@dataclass
class InterviewCompleteEvent(Event):
    """Emitted when the entire interview is finished."""

    event_type: str = field(default="interview_complete", init=False)
    final_score: float = 0.0
    grade: str = ""
    total_questions: int = 0
    duration_seconds: float = 0.0

    def _payload(self) -> Dict[str, Any]:
        return {
            "final_score": round(self.final_score, 1),
            "grade": self.grade,
            "total_questions": self.total_questions,
            "duration": round(self.duration_seconds, 1),
        }


@dataclass
class ErrorEvent(Event):
    """Emitted when an error occurs in the pipeline."""

    event_type: str = field(default="error", init=False)
    error_message: str = ""
    error_source: str = ""  # e.g. "stt", "tts", "llm", "vision"
    recoverable: bool = True

    def _payload(self) -> Dict[str, Any]:
        return {
            "message": self.error_message,
            "source": self.error_source,
            "recoverable": self.recoverable,
        }
