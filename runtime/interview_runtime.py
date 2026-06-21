"""Voice Interview Runtime Integration layer."""

from __future__ import annotations

import json
import logging
import time
import datetime
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from domain_activation.activation_engine import DomainActivationEngine
from graph_traversal.traversal_engine import get_next_concept, find_graph_path
from knowledge_graph.graph_loader import load_graph_document
from graph_traversal.graph_navigator import GraphNavigator
from mastery_estimator.estimation_engine import MasteryEstimationEngine
from mastery_estimator.models import EvaluationStrategy
from interview_engine.database import DatabaseManager
from interview_engine.chroma_store import ChromaStore
from interview_engine.question_layer import QuestionLayer
from interview_engine.report_generator import ReportGenerator
from interview_engine.storage.postgres.models import ConceptEvaluation, InterviewSession

logger = logging.getLogger(__name__)


# ===========================================================================
# STT PROVIDER ABSTRACTION
# ===========================================================================

class STTProvider(ABC):
    """Abstract base class for Speech-To-Text translation."""

    @abstractmethod
    def transcribe(self) -> str:
        """Transcribe speech from microphone or simulated source to text."""
        pass


class AssemblyAISTT(STTProvider):
    """STT Provider using AssemblyAI live websocket streaming."""

    def __init__(self) -> None:
        from app.config import ASSEMBLYAI_API_KEY
        self.api_key = ASSEMBLYAI_API_KEY
        self.enabled = bool(self.api_key and self.api_key != "MOCK_KEY")

    def transcribe(self) -> str:
        """Perform audio capture and transcribe using AssemblyAI websocket service."""
        if not self.enabled:
            logger.warning("AssemblyAI API key missing or set to mock. Returning mock response.")
            return "Mock candidate response due to missing AssemblyAI API key."
        try:
            from app.services.stt_service import speech_to_text
            return speech_to_text()
        except Exception as e:
            logger.error(f"AssemblyAISTT error: {e}", exc_info=True)
            return "Mock transcript after transcription error."


class MockSTT(STTProvider):
    """STT provider to mock/simulate candidate responses during tests."""

    def __init__(self, responses: Optional[List[str]] = None) -> None:
        self.responses = responses or []
        self.index = 0

    def transcribe(self) -> str:
        """Return the next configured mock response."""
        if self.index < len(self.responses):
            res = self.responses[self.index]
            self.index += 1
            return res
        return "Mock candidate response"


# ===========================================================================
# TTS PROVIDER ABSTRACTION
# ===========================================================================

class TTSProvider(ABC):
    """Abstract base class for Text-To-Speech playback."""

    @abstractmethod
    def speak(self, text: str) -> Dict[str, Any]:
        """Convert text question to spoken audio."""
        pass


class PyTTSx3TTS(TTSProvider):
    """TTS Provider using local pyttsx3 playback engine."""

    def __init__(self) -> None:
        self.enabled = True
        try:
            import pyttsx3
            # Attempt to initialize a temporary engine to ensure package works
            engine = pyttsx3.init()
            del engine
        except Exception as e:
            logger.warning(f"Could not initialize local pyttsx3 engine: {e}. PyTTSx3TTS running in mock mode.")
            self.enabled = False

    def speak(self, text: str) -> Dict[str, Any]:
        """Play the question wording using pyttsx3."""
        start_time = time.time()
        if self.enabled:
            try:
                from app.services.tts_service import speak
                speak(text)
            except Exception as e:
                logger.error(f"pyttsx3 playback failed: {e}")
        else:
            logger.info(f"[PyTTSx3TTS Mock Mode] Speaking: '{text}'")

        duration = time.time() - start_time
        return {
            "provider": "pyttsx3" if self.enabled else "pyttsx3_mock",
            "text_length": len(text),
            "playback_duration_seconds": round(duration, 3),
        }


class MockTTS(TTSProvider):
    """TTS provider simulating speech playback without utilizing audio hardware."""

    def speak(self, text: str) -> Dict[str, Any]:
        """Log text and return mocked playback metadata."""
        logger.info(f"[MockTTS] Playback start: '{text}'")
        return {
            "provider": "mock",
            "text_length": len(text),
            "playback_duration_seconds": round(0.05 * len(text.split()), 3),
        }


# ===========================================================================
# CAMERA ANALYTICS ADAPTER
# ===========================================================================

class CameraAdapter:
    """Consumes real-time camera engagement/attention snapshots and aggregates them."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        """Clear the accumulated frame buffers."""
        self._eye_contact_scores: List[float] = []
        self._engagement_scores: List[float] = []
        self._attention_scores: List[float] = []

    def consume_frame_metrics(
        self,
        eye_contact_score: float,
        engagement_score: float,
        attention_score: Optional[float] = None,
        pitch: float = 0.0,
        yaw: float = 0.0,
    ) -> None:
        """Record frame vision metrics, estimating attention from head pose if needed."""
        self._eye_contact_scores.append(eye_contact_score)
        self._engagement_scores.append(engagement_score)

        if attention_score is not None:
            self._attention_scores.append(attention_score)
        else:
            # Derived attention: look center if head pitch/yaw deviations are minor
            derived_attention = max(0.0, 100.0 - (abs(pitch) + abs(yaw)) * 2.0)
            self._attention_scores.append(derived_attention)

    def get_average_metrics(self) -> Dict[str, float]:
        """Compute average metrics during the current evaluation block."""
        def avg(lst: List[float]) -> float:
            return sum(lst) / len(lst) if lst else 0.0

        return {
            "eye_contact_score": round(avg(self._eye_contact_scores), 2),
            "engagement_score": round(avg(self._engagement_scores), 2),
            "attention_score": round(avg(self._attention_scores), 2),
        }


# ===========================================================================
# RUNTIME SESSION MANAGER
# ===========================================================================

class InterviewRuntimeManager:
    """Coordinates the live technical interview execution guiding traversal, persistence, speech, and vision layers."""

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        chroma_store: Optional[ChromaStore] = None,
        question_layer: Optional[QuestionLayer] = None,
        stt_provider: Optional[STTProvider] = None,
        tts_provider: Optional[TTSProvider] = None,
        camera_adapter: Optional[CameraAdapter] = None,
    ) -> None:
        self.db = db_manager or DatabaseManager()
        self.chroma = chroma_store or ChromaStore()
        self.question_layer = question_layer or QuestionLayer(db_manager=self.db, chroma_store=self.chroma)

        # Core engines
        self.mastery_engine = MasteryEstimationEngine(db_manager=self.db, chroma_store=self.chroma)
        self.activation_base_dir = Path(__file__).parent.parent / "domain_activation"
        self.activation_engine = DomainActivationEngine(base_dir=self.activation_base_dir)
        self.report_gen = ReportGenerator()

        # Communication/Sensor Adapters
        self.stt_provider = stt_provider or MockSTT()
        self.tts_provider = tts_provider or MockTTS()
        self.camera_adapter = camera_adapter or CameraAdapter()

        # Live State Parameters
        self.candidate_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.domain: Optional[str] = None
        self.current_concept: Optional[str] = None
        self.visited_concepts: List[str] = []
        self.mastery_history: List[float] = []
        self.success_streak: int = 0
        self.failure_streak: int = 0
        self.accelerated: bool = False
        self.terminated: bool = False
        self.session_state: str = "IDLE"  # IDLE, ACTIVE, PAUSED, COMPLETED, FAILED

        # Histories
        self.transcript_history: List[Dict[str, Any]] = []
        self.question_history: List[Dict[str, Any]] = []

    def start_runtime(
        self,
        candidate_id: str,
        candidate_name: str,
        candidate_email: str,
        resume_json: dict
    ) -> Dict[str, Any]:
        """Initialize candidate entry, determine domain, select entry concept, and fetch first question."""
        logger.info(f"Initializing live voice runtime for candidate {candidate_name} ({candidate_id})")

        self.candidate_id = candidate_id
        self.session_id = candidate_id
        self.session_state = "ACTIVE"

        # 1. Parse and persist candidate profile details
        skills = resume_json.get("skills", [])
        skills_dict = {"technical_skills": skills} if isinstance(skills, list) else skills
        education = resume_json.get("education", [])
        projects = resume_json.get("projects", [])
        resume_text = resume_json.get("resume_text", f"Resume of {candidate_name}. Skills: {', '.join(skills)}")

        self.db.persist_candidate(
            candidate_id=candidate_id,
            name=candidate_name,
            email=candidate_email,
            resume_text=resume_text,
            skills=skills_dict,
            education=education,
            projects=projects
        )

        # 2. Run domain activation
        activation_result = self.activation_engine.activate(resume_json)
        if activation_result.active_domains:
            self.domain = activation_result.active_domains[0].domain
            entry_concepts = activation_result.active_domains[0].entry_concepts
            self.current_concept = entry_concepts[0] if entry_concepts else "Supervised Learning"
        else:
            self.domain = "machine_learning"
            self.current_concept = "Supervised Learning"

        self.visited_concepts = [self.current_concept]
        self.mastery_history = []
        self.success_streak = 0
        self.failure_streak = 0
        self.accelerated = False
        self.terminated = False

        # Seed misconceptions to Chroma
        try:
            graph_path = find_graph_path(self.domain)
            graph = load_graph_document(graph_path)
            for concept in graph.concepts:
                for mc in concept.common_misconceptions:
                    self.chroma.store_misconception(concept.concept_name, mc)
        except Exception as e:
            logger.error(f"Error seeding misconceptions to Chroma: {e}")

        # 3. Create interview session in PostgreSQL
        conn = self.db.get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO interview_sessions (
                        id, candidate_id, state, domain, current_concept, visited_concepts, 
                        mastery_history, success_streak, failure_streak, accelerated, terminated, updated_at
                    )
                    VALUES (%s, %s, 'ACTIVE', %s, %s, %s::jsonb, %s::jsonb, 0, 0, FALSE, FALSE, CURRENT_TIMESTAMP)
                    ON CONFLICT (id) DO UPDATE SET
                        state = 'ACTIVE',
                        domain = EXCLUDED.domain,
                        current_concept = EXCLUDED.current_concept,
                        visited_concepts = EXCLUDED.visited_concepts,
                        mastery_history = EXCLUDED.mastery_history,
                        updated_at = CURRENT_TIMESTAMP;
                    """,
                    (
                        self.session_id,
                        candidate_id,
                        self.domain,
                        self.current_concept,
                        json.dumps(self.visited_concepts),
                        json.dumps([]),
                    )
                )

        # 4. Generate first question wording (default to static strategy)
        question_data = self.question_layer.generate_question(
            concept=self.current_concept,
            mastery=0.5,  # initial mastery
            session_id=candidate_id,
            strategy="static"
        )
        question_text = question_data["question_text"]

        self.chroma.store_question(question_text, self.current_concept)

        # Record histories
        self.question_history.append({
            "question_id": question_data["question_id"],
            "question_text": question_text,
            "concept": self.current_concept,
            "difficulty": question_data["difficulty"],
            "source": question_data.get("source", "static")
        })
        self.transcript_history.append({
            "role": "interviewer",
            "text": question_text,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })

        self.camera_adapter.reset()

        return {
            "session_id": self.session_id,
            "state": self.session_state,
            "domain": self.domain,
            "current_concept": self.current_concept,
            "question": question_text
        }

    def generate_audio_question(self, question_text: str) -> Dict[str, Any]:
        """Convert the current text question to spoken voice output."""
        return self.tts_provider.speak(question_text)

    def receive_transcript(self) -> str:
        """Trigger live mic recording to transcribe the candidate's spoken response."""
        return self.stt_provider.transcribe()

    def submit_answer(
        self,
        candidate_id: str,
        concept: str,
        question: str,
        answer: str,
        latency: float = 0.0
    ) -> Dict[str, Any]:
        """Grade response, step graph traversal engine, store metrics/outcomes, and select next concept."""
        logger.info(f"Submitting candidate answer for concept '{concept}'")

        if self.session_state in ("COMPLETED", "FAILED"):
            return {
                "decision": "end_interview",
                "next_concept": None,
                "question": "The interview has concluded.",
                "state": self.session_state
            }

        # 1. Update transcript logs
        self.transcript_history.append({
            "role": "candidate",
            "text": answer,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })

        # 2. Extract and reset camera metrics for this question period
        avg_camera_metrics = self.camera_adapter.get_average_metrics()
        self.camera_adapter.reset()

        # 3. Cache answer text in Chroma
        last_q_id = self.question_history[-1].get("question_id") if self.question_history else f"{concept}_basic_static_0"
        self.chroma.store_answer(answer, concept, question_id=last_q_id)

        # 4. Evaluate concept mastery via hybrid estimation
        eval_result = self.mastery_engine.estimate(
            concept=concept,
            question=question,
            answer=answer,
            strategy=EvaluationStrategy.HYBRID
        )
        mastery = eval_result.mastery
        confidence = eval_result.confidence

        # Save camera engagement metrics inside concept evaluation metadata
        eval_result.metadata["engagement_metrics"] = avg_camera_metrics

        # 5. Persist detailed concept evaluation log to SQL
        self.db.persist_concept_evaluation(
            candidate_id=candidate_id,
            concept_id=concept,
            question=question,
            answer=answer,
            mastery=mastery,
            confidence=confidence,
            matched_signals=eval_result.evidence.matched_signals,
            missing_signals=eval_result.evidence.missing_signals,
            reasoning=eval_result.reasoning,
            strategy="hybrid",
            metadata=eval_result.metadata
        )

        # 6. Prepare traversal state and call traversal engine
        state_dict = {
            "visited_concepts": self.visited_concepts,
            "mastery_history": self.mastery_history,
            "success_streak": self.success_streak,
            "failure_streak": self.failure_streak,
            "accelerated": self.accelerated,
            "terminated": self.terminated
        }

        conn = self.db.get_connection()
        with conn:
            traversal_result = get_next_concept(
                domain=self.domain,
                current_concept=concept,
                mastery=mastery,
                confidence=confidence,
                state=state_dict,
                candidate_id=candidate_id,
                conn=conn
            )

        # Sync updated state back to manager
        self.visited_concepts = state_dict["visited_concepts"]
        self.mastery_history = state_dict["mastery_history"]
        self.success_streak = state_dict["success_streak"]
        self.failure_streak = state_dict["failure_streak"]
        self.accelerated = state_dict.get("accelerated", False)
        self.terminated = state_dict.get("terminated", False)

        decision = traversal_result["decision"]
        next_concept = traversal_result.get("next_concept")

        # 7. Persist question outcome & updates effectiveness stats
        self.question_layer.store_question_outcome(
            question_id=last_q_id,
            question_text=question,
            concept=concept,
            difficulty=self.question_layer.map_difficulty(mastery),
            candidate_answer=answer,
            mastery_outcome=mastery,
            latency=latency,
            session_id=candidate_id
        )

        # 8. Compute and persist overall domain-level mastery score
        self.get_domain_mastery(candidate_id, self.domain)

        # 9. Handle next concept selection or termination
        next_question_text = ""
        if decision == "terminate_branch":
            self.session_state = "FAILED"
            next_question_text = "Thank you. We have concluded the interview."
        elif decision == "end_interview" or next_concept is None:
            self.session_state = "COMPLETED"
            next_question_text = "Thank you. We have completed all concepts in the interview."
        else:
            self.current_concept = next_concept
            # Generate next adaptive question using hybrid question bank strategy
            next_q_data = self.question_layer.generate_question(
                concept=self.current_concept,
                mastery=mastery,
                session_id=candidate_id,
                strategy="hybrid"
            )
            next_question_text = next_q_data["question_text"]

            self.chroma.store_question(next_question_text, self.current_concept)

            # Record histories
            self.question_history.append({
                "question_id": next_q_data["question_id"],
                "question_text": next_question_text,
                "concept": self.current_concept,
                "difficulty": next_q_data["difficulty"],
                "source": next_q_data.get("source", "hybrid")
            })
            self.transcript_history.append({
                "role": "interviewer",
                "text": next_question_text,
                "timestamp": datetime.datetime.utcnow().isoformat()
            })

        # Update database interview session record
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE interview_sessions
                    SET state = %s,
                        current_concept = %s,
                        visited_concepts = %s::jsonb,
                        mastery_history = %s::jsonb,
                        success_streak = %s,
                        failure_streak = %s,
                        accelerated = %s,
                        terminated = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE candidate_id = %s;
                    """,
                    (
                        self.session_state,
                        self.current_concept or concept,
                        json.dumps(self.visited_concepts),
                        json.dumps(self.mastery_history),
                        self.success_streak,
                        self.failure_streak,
                        self.accelerated,
                        self.terminated,
                        candidate_id
                    )
                )

        return {
            "decision": decision,
            "next_concept": next_concept,
            "question": next_question_text,
            "mastery": mastery,
            "confidence": confidence,
            "state": self.session_state
        }

    def pause_interview(self, candidate_id: str) -> Dict[str, Any]:
        """Pause the current interview session in both memory and database."""
        logger.info(f"Pausing session for candidate {candidate_id}")
        self.session_state = "PAUSED"
        conn = self.db.get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE interview_sessions SET state = 'PAUSED', updated_at = CURRENT_TIMESTAMP WHERE candidate_id = %s;",
                    (candidate_id,)
                )
        return {"session_id": candidate_id, "state": "PAUSED"}

    def resume_interview(self, candidate_id: str) -> Dict[str, Any]:
        """Resume a paused interview session in both memory and database."""
        logger.info(f"Resuming session for candidate {candidate_id}")
        self.session_state = "ACTIVE"
        conn = self.db.get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE interview_sessions SET state = 'ACTIVE', updated_at = CURRENT_TIMESTAMP WHERE candidate_id = %s;",
                    (candidate_id,)
                )
        return {"session_id": candidate_id, "state": "ACTIVE"}

    def stop_interview(self, candidate_id: str) -> Dict[str, Any]:
        """Conclude the interview, calculate final scores, persist report, and update state."""
        logger.info(f"Stopping/Concluding interview for candidate {candidate_id}")
        
        if self.terminated:
            self.session_state = "FAILED"
        else:
            self.session_state = "COMPLETED"

        conn = self.db.get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE interview_sessions SET state = %s, updated_at = CURRENT_TIMESTAMP WHERE candidate_id = %s;",
                    (self.session_state, candidate_id)
                )

        # 1. Get overall domain mastery score
        domain_mastery = self.get_domain_mastery(candidate_id, self.domain or "machine_learning")

        # 2. Retrieve all concept scores for reporting
        evals = []
        with conn:
            with conn.cursor() as cur:
                if hasattr(conn, "cursor_obj"):
                    from interview_engine.database import _CONCEPT_EVALUATIONS
                    evals = [e for e in _CONCEPT_EVALUATIONS if e["candidate_id"] == candidate_id]
                else:
                    cur.execute(
                        "SELECT concept_id, mastery FROM concept_evaluations WHERE candidate_id = %s;",
                        (candidate_id,)
                    )
                    rows = cur.fetchall()
                    evals = [{"concept_id": r[0], "mastery": float(r[1])} for r in rows]

        latest_concept_scores = {}
        for ev in evals:
            latest_concept_scores[ev["concept_id"]] = ev["mastery"]

        # Retrieve candidate name
        cand_name = "Candidate"
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM candidates WHERE id = %s;", (candidate_id,))
                row = cur.fetchone()
                if row:
                    cand_name = row[0]

        # 3. Generate final report and persist to PostgreSQL
        report = self.report_gen.generate_report(
            candidate_id=candidate_id,
            candidate_name=cand_name,
            domain=self.domain or "machine_learning",
            concept_scores=latest_concept_scores
        )

        self.db.persist_report(
            candidate_id=candidate_id,
            session_id=self.session_id or candidate_id,
            concept_scores=report["concept_scores"],
            domain_scores=report["domain_scores"],
            strong_concepts=report["strong_concepts"],
            weak_concepts=report["weak_concepts"],
            recommended_topics=report["recommended_topics"],
            summary=report["summary"]
        )

        return {
            "session_id": self.session_id,
            "state": self.session_state,
            "domain_mastery": domain_mastery,
            "report": report
        }

    def get_domain_mastery(self, candidate_id: str, domain: str) -> float:
        """Compute the average mastery score for evaluated concepts in a domain."""
        conn = self.db.get_connection()
        evals = []
        with conn:
            with conn.cursor() as cur:
                if hasattr(conn, "cursor_obj"):
                    from interview_engine.database import _CONCEPT_EVALUATIONS
                    evals = [e for e in _CONCEPT_EVALUATIONS if e["candidate_id"] == candidate_id]
                else:
                    cur.execute(
                        """
                        SELECT concept_id, mastery
                        FROM concept_evaluations
                        WHERE candidate_id = %s;
                        """,
                        (candidate_id,)
                    )
                    rows = cur.fetchall()
                    evals = [{"concept_id": r[0], "mastery": float(r[1])} for r in rows]

        latest_concept_scores: Dict[str, float] = {}
        for ev in evals:
            latest_concept_scores[ev["concept_id"]] = ev["mastery"]

        mastery_score = self.report_gen.calculate_domain_mastery(latest_concept_scores)
        self.db.persist_domain_mastery(candidate_id, domain, mastery_score)
        return mastery_score

    def recover_session(self, candidate_id: str) -> bool:
        """Load and recover a candidate's session state and transcript logs from persistence."""
        conn = self.db.get_connection()
        row = None
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, domain, current_concept, visited_concepts, mastery_history, 
                           success_streak, failure_streak, accelerated, terminated, state
                    FROM interview_sessions
                    WHERE candidate_id = %s
                    ORDER BY updated_at DESC
                    LIMIT 1;
                    """,
                    (candidate_id,)
                )
                row = cur.fetchone()

        if not row:
            logger.warning(f"No database session record to recover for candidate {candidate_id}")
            return False

        sess_id, domain, current_concept, visited_json, mastery_json, success_streak, failure_streak, accelerated, terminated, state = row

        self.candidate_id = candidate_id
        self.session_id = sess_id
        self.domain = domain
        self.current_concept = current_concept
        self.visited_concepts = visited_json if isinstance(visited_json, list) else json.loads(visited_json or "[]")
        self.mastery_history = mastery_json if isinstance(mastery_json, list) else json.loads(mastery_json or "[]")
        self.success_streak = success_streak
        self.failure_streak = failure_streak
        self.accelerated = bool(accelerated)
        self.terminated = bool(terminated)
        self.session_state = state

        # Reset rolling metrics and histories
        self.camera_adapter.reset()
        self.transcript_history = []
        self.question_history = []

        # Query past evaluations to restore question history and transcript
        evals = []
        with conn:
            with conn.cursor() as cur:
                if hasattr(conn, "cursor_obj"):
                    from interview_engine.database import _CONCEPT_EVALUATIONS
                    evals_raw = [e for e in _CONCEPT_EVALUATIONS if e["candidate_id"] == candidate_id]
                    for ev in evals_raw:
                        evals.append({
                            "concept_id": ev["concept_id"],
                            "question": ev["question"],
                            "answer": ev["answer"],
                            "mastery": float(ev["mastery"]),
                            "confidence": float(ev["confidence"]),
                            "created_at": datetime.datetime.utcnow(),
                            "metadata": ev.get("metadata", {})
                        })
                else:
                    cur.execute(
                        """
                        SELECT concept_id, question, answer, mastery, confidence, created_at, metadata
                        FROM concept_evaluations
                        WHERE candidate_id = %s
                        ORDER BY id ASC;
                        """,
                        (candidate_id,)
                    )
                    rows = cur.fetchall()
                    for r in rows:
                        meta_dict = {}
                        if r[6]:
                            try:
                                meta_dict = json.loads(r[6]) if isinstance(r[6], str) else r[6]
                            except Exception:
                                pass
                        evals.append({
                            "concept_id": r[0],
                            "question": r[1],
                            "answer": r[2],
                            "mastery": float(r[3]),
                            "confidence": float(r[4]),
                            "created_at": r[5],
                            "metadata": meta_dict
                        })

        for ev in evals:
            # Reconstruct transcript turns
            self.transcript_history.append({
                "role": "interviewer",
                "text": ev["question"],
                "timestamp": str(ev["created_at"])
            })
            self.transcript_history.append({
                "role": "candidate",
                "text": ev["answer"],
                "timestamp": str(ev["created_at"])
            })

            # Reconstruct question history entries
            diff = self.question_layer.map_difficulty(ev["mastery"])
            self.question_history.append({
                "question_id": f"{ev['concept_id']}_{diff}_recovered",
                "question_text": ev["question"],
                "concept": ev["concept_id"],
                "difficulty": diff,
                "mastery_outcome": ev["mastery"]
            })

        # Re-inject current question to transcript / question history if session is active
        if self.session_state not in ("COMPLETED", "FAILED"):
            try:
                # Use current concept wording
                q_text = self.question_layer.get_question(self.current_concept, mode="static")
                self.question_history.append({
                    "question_id": f"{self.current_concept}_recovered_active",
                    "question_text": q_text,
                    "concept": self.current_concept,
                    "difficulty": self.question_layer.map_difficulty(0.5)
                })
                self.transcript_history.append({
                    "role": "interviewer",
                    "text": q_text,
                    "timestamp": datetime.datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"Failed to restore current active question on recovery: {e}")

        logger.info(f"Successfully recovered state for candidate {candidate_id}")
        return True
