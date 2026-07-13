import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import asdict
from enum import Enum
import threading

from app.models.domain import InterviewSession, CandidateProfile, InterviewConfig, QuestionRecord, AnswerRecord, VisionSnapshot, AudioSnapshot, MultiModalSignals, RoundResult
from app.models.enums import InterviewState, RoundType, Difficulty

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Enum):
            return o.value
        if isinstance(o, set):
            return list(o)
        return super().default(o)

def _deserialize_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    return datetime.fromisoformat(dt_str)

def _deserialize_dict(data: dict) -> InterviewSession:
    """Manually reconstruct the deeply nested InterviewSession from a dict."""
    
    # 1. CandidateProfile
    cand_data = data.get("candidate", {})
    candidate = CandidateProfile(
        id=cand_data.get("id", ""),
        name=cand_data.get("name", ""),
        email=cand_data.get("email", ""),
        phone=cand_data.get("phone", ""),
        skills=cand_data.get("skills", {}),
        experience_years=cand_data.get("experience_years", 0.0),
        education=cand_data.get("education", []),
        projects=cand_data.get("projects", []),
        resume_raw_text=cand_data.get("resume_raw_text", ""),
        target_role=cand_data.get("target_role", ""),
        created_at=_deserialize_datetime(cand_data.get("created_at")) or datetime.utcnow()
    )

    # 2. InterviewConfig
    conf_data = data.get("config", {})
    config = InterviewConfig(
        round_order=[RoundType(r) for r in conf_data.get("round_order", [])],
        questions_per_round={RoundType(k): v for k, v in conf_data.get("questions_per_round", {}).items()},
        starting_difficulty=Difficulty(conf_data.get("starting_difficulty", "MEDIUM")),
        max_follow_ups_per_question=conf_data.get("max_follow_ups_per_question", 2),
        answer_timeout_seconds=conf_data.get("answer_timeout_seconds", 120.0),
        round_timeout_seconds=conf_data.get("round_timeout_seconds", 600.0)
    )

    # 3. Questions
    questions = []
    for q_data in data.get("questions", []):
        questions.append(QuestionRecord(
            id=q_data.get("id", ""),
            session_id=q_data.get("session_id", ""),
            round_type=RoundType(q_data.get("round_type", "HR")),
            question_text=q_data.get("question_text", ""),
            topic=q_data.get("topic", ""),
            difficulty=Difficulty(q_data.get("difficulty", "MEDIUM")),
            sequence_number=q_data.get("sequence_number", 0),
            parent_question_id=q_data.get("parent_question_id"),
            follow_up_depth=q_data.get("follow_up_depth", 0),
            asked_at=_deserialize_datetime(q_data.get("asked_at")) or datetime.utcnow()
        ))

    # 4. Answers
    answers = []
    for a_data in data.get("answers", []):
        v_data = a_data.get("vision_metrics", {})
        vision = VisionSnapshot(
            eye_contact_score=v_data.get("eye_contact_score", 0.0),
            engagement_score=v_data.get("engagement_score", 0.0),
            head_yaw=v_data.get("head_yaw", 0.0),
            head_pitch=v_data.get("head_pitch", 0.0),
            head_roll=v_data.get("head_roll", 0.0),
            face_visible_ratio=v_data.get("face_visible_ratio", 0.0),
            sample_count=v_data.get("sample_count", 0)
        )
        au_data = a_data.get("audio_metrics", {})
        audio = AudioSnapshot(
            words_per_minute=au_data.get("words_per_minute", 0.0),
            silence_ratio=au_data.get("silence_ratio", 0.0),
            filler_word_count=au_data.get("filler_word_count", 0),
            total_word_count=au_data.get("total_word_count", 0),
            speech_duration_seconds=au_data.get("speech_duration_seconds", 0.0)
        )
        answers.append(AnswerRecord(
            id=a_data.get("id", ""),
            question_id=a_data.get("question_id", ""),
            session_id=a_data.get("session_id", ""),
            transcript=a_data.get("transcript", ""),
            duration_seconds=a_data.get("duration_seconds", 0.0),
            audio_metrics=audio,
            vision_metrics=vision,
            language_scores=a_data.get("language_scores", {}),
            answer_score=a_data.get("answer_score", 0.0),
            answered_at=_deserialize_datetime(a_data.get("answered_at")) or datetime.utcnow()
        ))

    # 5. Current Signals
    sig_data = data.get("current_signals", {})
    sig_v_data = sig_data.get("vision", {})
    sig_vision = VisionSnapshot(**sig_v_data) if sig_v_data else VisionSnapshot()
    sig_a_data = sig_data.get("audio", {})
    sig_audio = AudioSnapshot(**sig_a_data) if sig_a_data else AudioSnapshot()
    signals = MultiModalSignals(
        vision=sig_vision,
        audio=sig_audio,
        language_technical=sig_data.get("language_technical", 0.0),
        language_communication=sig_data.get("language_communication", 0.0),
        language_depth=sig_data.get("language_depth", 0.0),
        language_relevance=sig_data.get("language_relevance", 0.0)
    )

    # 6. Session itself
    current_round_type_val = data.get("current_round_type")
    
    session = InterviewSession(
        id=data.get("id", ""),
        candidate=candidate,
        config=config,
        current_state=InterviewState(data.get("current_state", "IDLE")),
        previous_state=InterviewState(data.get("previous_state")) if data.get("previous_state") else None,
        current_round_type=RoundType(current_round_type_val) if current_round_type_val else None,
        current_round_index=data.get("current_round_index", 0),
        current_difficulty=Difficulty(data.get("current_difficulty", "MEDIUM")),
        questions=questions,
        answers=answers,
        asked_question_hashes=set(data.get("asked_question_hashes", [])),
        round_results={}, # Complex to serialize/deserialize, leaving empty for now
        current_signals=signals,
        category_scores=data.get("category_scores", {}),
        final_score=data.get("final_score", 0.0),
        grade=data.get("grade", ""),
        conversation_history=data.get("conversation_history", []),
        created_at=_deserialize_datetime(data.get("created_at")) or datetime.utcnow(),
        started_at=_deserialize_datetime(data.get("started_at")),
        ended_at=_deserialize_datetime(data.get("ended_at")),
        last_error=data.get("last_error", ""),
        error_count=data.get("error_count", 0)
    )
    return session


class SQLiteStateStore:
    """
    A thread-safe SQLite backed document store for InterviewSessions.
    Uses JSON serialization to store the nested dataclass.
    """
    def __init__(self, db_path: str = "nephele_state.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        return self._conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

    def save_session(self, session: InterviewSession) -> None:
        data_json = json.dumps(asdict(session), cls=EnhancedJSONEncoder)
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO sessions (id, data, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (session.id, data_json)
            )
            self._conn.commit()

    def get_session(self, session_id: str) -> Optional[InterviewSession]:
        with self._lock:
            cursor = self._conn.execute("SELECT data FROM sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
        if row:
            data = json.loads(row["data"])
            try:
                return _deserialize_dict(data)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to deserialize session {session_id}: {e}")
                return None
        return None

    def delete_session(self, session_id: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            self._conn.commit()

    def get_all_session_ids(self) -> list[str]:
        with self._lock:
            cursor = self._conn.execute("SELECT id FROM sessions")
            return [row["id"] for row in cursor.fetchall()]

# Global Singleton
state_store = SQLiteStateStore()
