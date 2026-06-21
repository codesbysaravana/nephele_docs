"""Interview Orchestrator managing session lifecycle, domain activation, mastery evaluation, and graph traversal."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from domain_activation.activation_engine import DomainActivationEngine
from graph_traversal.traversal_engine import get_next_concept, find_graph_path
from knowledge_graph.graph_loader import load_graph_document
from graph_traversal.graph_navigator import GraphNavigator
from mastery_estimator.estimation_engine import MasteryEstimationEngine
from mastery_estimator.models import EvaluationStrategy

from .database import DatabaseManager
from .chroma_store import ChromaStore
from .question_layer import QuestionLayer
from .report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class InterviewOrchestrator:
    """Manages the full lifecycle and execution of a knowledge-graph guided interview."""

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        chroma_store: Optional[ChromaStore] = None,
        question_layer: Optional[QuestionLayer] = None,
        report_generator: Optional[ReportGenerator] = None
    ) -> None:
        self.db = db_manager or DatabaseManager()
        self.chroma = chroma_store or ChromaStore()
        self.question_layer = question_layer or QuestionLayer()
        self.report_gen = report_generator or ReportGenerator()
        self.mastery_engine = MasteryEstimationEngine()

        # Resolve paths for domain activation
        self.activation_base_dir = Path(__file__).parent.parent / "domain_activation"
        self.activation_engine = DomainActivationEngine(base_dir=self.activation_base_dir)

    def start_interview(
        self,
        candidate_id: str,
        candidate_name: str,
        candidate_email: str,
        resume_json: dict
    ) -> Dict[str, Any]:
        """Initialize the candidate profile, run domain activation, and fetch the entry concept question."""
        logger.info(f"Starting interview session for candidate {candidate_name} ({candidate_id})")

        # 1. Parse resume and extract profile details
        skills = resume_json.get("skills", [])
        # Format skills for CandidateProfile expected dictionary format
        skills_dict = {"technical_skills": skills} if isinstance(skills, list) else skills
        education = resume_json.get("education", [])
        projects = resume_json.get("projects", [])
        resume_text = resume_json.get("resume_text", f"Resume of {candidate_name}. Skills: {', '.join(skills)}")

        # 2. Persist candidate profile
        self.db.persist_candidate(
            candidate_id=candidate_id,
            name=candidate_name,
            email=candidate_email,
            resume_text=resume_text,
            skills=skills_dict,
            education=education,
            projects=projects
        )

        # 3. Activate Domain
        activation_result = self.activation_engine.activate(resume_json)
        if activation_result.active_domains:
            activated_domain = activation_result.active_domains[0].domain
            entry_concepts = activation_result.active_domains[0].entry_concepts
            entry_concept = entry_concepts[0] if entry_concepts else "Supervised Learning"
        else:
            activated_domain = "machine_learning"
            entry_concept = "Supervised Learning"

        logger.info(f"Activated domain: {activated_domain}, Entry concept selected: {entry_concept}")

        # 4. Populate Chroma DB misconceptions from Knowledge Graph
        try:
            graph_path = find_graph_path(activated_domain)
            graph = load_graph_document(graph_path)
            for concept in graph.concepts:
                for mc in concept.common_misconceptions:
                    self.chroma.store_misconception(concept.concept_name, mc)
        except Exception as e:
            logger.error(f"Error seeding misconceptions to Chroma: {e}")

        # 5. Initialize the interview session in Traversal state database
        conn = self.db.get_connection()
        state = {
            "visited_concepts": [entry_concept],
            "mastery_history": [],
            "success_streak": 0,
            "failure_streak": 0
        }
        
        # Save initial session state as CREATED, then immediately activate it
        with conn:
            with conn.cursor() as cur:
                # Store candidate session
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
                        candidate_id,
                        candidate_id,
                        activated_domain,
                        entry_concept,
                        json.dumps([entry_concept]),
                        json.dumps([]),
                    )
                )

        # 6. Fetch the first question from the Question Layer
        question = self.question_layer.get_question(entry_concept, mode="static")
        
        # Store in Chroma Cache
        self.chroma.store_question(question, entry_concept)

        return {
            "session_id": candidate_id,
            "state": "ACTIVE",
            "domain": activated_domain,
            "current_concept": entry_concept,
            "question": question
        }

    def submit_answer(
        self,
        candidate_id: str,
        concept: str,
        question: str,
        answer: str
    ) -> Dict[str, Any]:
        """Process candidate response: estimate mastery, run graph traversal, and determine next concept/question."""
        logger.info(f"[Candidate {candidate_id}] Submitted answer for concept '{concept}'")
        
        # 1. Fetch current session data from PostgreSQL
        conn = self.db.get_connection()
        session_row = None
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT domain, current_concept, visited_concepts, mastery_history, 
                           success_streak, failure_streak, accelerated, terminated, state
                    FROM interview_sessions
                    WHERE candidate_id = %s;
                    """,
                    (candidate_id,)
                )
                session_row = cur.fetchone()

        if not session_row:
            raise ValueError(f"No active session found for candidate {candidate_id}")

        domain, current_concept, visited, mastery_hist, success_streak, failure_streak, accelerated, terminated, session_state = session_row
        
        # Handle parsed json lists if returned as raw strings
        visited = visited if isinstance(visited, list) else json.loads(visited or "[]")
        mastery_hist = mastery_hist if isinstance(mastery_hist, list) else json.loads(mastery_hist or "[]")

        if session_state in ("COMPLETED", "FAILED"):
            return {
                "decision": "end_interview",
                "next_concept": None,
                "question": "The interview has already ended.",
                "state": session_state
            }

        # 2. Store Candidate's Answer in Chroma
        self.chroma.store_answer(answer, concept, question_id=question)

        # 3. Call Mastery Estimator
        eval_result = self.mastery_engine.estimate(
            concept=concept,
            question=question,
            answer=answer,
            strategy=EvaluationStrategy.HYBRID
        )
        
        mastery = eval_result.mastery
        confidence = eval_result.confidence
        reasoning = eval_result.reasoning
        matched = eval_result.evidence.matched_signals
        missing = eval_result.evidence.missing_signals

        # 4. Save Concept Evaluation to PostgreSQL
        self.db.persist_concept_evaluation(
            candidate_id=candidate_id,
            concept_id=concept,
            question=question,
            answer=answer,
            mastery=mastery,
            confidence=confidence,
            matched_signals=matched,
            missing_signals=missing,
            reasoning=reasoning,
            strategy="hybrid",
            metadata=eval_result.metadata
        )

        # 5. Call Graph Traversal Engine
        state = {
            "visited_concepts": visited,
            "mastery_history": mastery_hist,
            "success_streak": success_streak,
            "failure_streak": failure_streak,
            "accelerated": accelerated,
            "terminated": terminated
        }

        traversal_result = get_next_concept(
            domain=domain,
            current_concept=concept,
            mastery=mastery,
            confidence=confidence,
            state=state,
            candidate_id=candidate_id,
            conn=conn
        )

        decision = traversal_result["decision"]
        next_concept = traversal_result.get("next_concept")

        # 6. Check Decision and Update Session Lifecycle State
        new_session_state = "ACTIVE"
        question_text = ""

        if decision == "terminate_branch":
            new_session_state = "FAILED"
            question_text = "Thank you. We have concluded the interview."
            logger.info(f"Interview for candidate {candidate_id} terminated due to failure streak.")
        elif decision == "end_interview" or next_concept is None:
            new_session_state = "COMPLETED"
            question_text = "Thank you. We have completed all concepts in the interview."
            logger.info(f"Interview for candidate {candidate_id} completed successfully.")
        else:
            # Fetch next question
            question_text = self.question_layer.get_question(next_concept, mode="static")
            # Store next question in Chroma
            self.chroma.store_question(question_text, next_concept)

        # 7. Update Session State in PostgreSQL
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
                        new_session_state,
                        next_concept or concept,
                        json.dumps(state["visited_concepts"]),
                        json.dumps(state["mastery_history"]),
                        state["success_streak"],
                        state["failure_streak"],
                        state["accelerated"],
                        state["terminated"],
                        candidate_id
                    )
                )

        # 8. Update Domain Mastery Score
        self.get_domain_mastery(candidate_id, domain)

        # 9. Return Result
        return {
            "decision": decision,
            "next_concept": next_concept,
            "question": question_text,
            "mastery": mastery,
            "confidence": confidence,
            "reasoning": reasoning,
            "state": new_session_state
        }

    def get_next_question(self, candidate_id: str, mode: str = "static") -> Dict[str, Any]:
        """Fetch the next question wording for the current session concept."""
        conn = self.db.get_connection()
        session_row = None
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT current_concept, domain
                    FROM interview_sessions
                    WHERE candidate_id = %s;
                    """,
                    (candidate_id,)
                )
                session_row = cur.fetchone()

        if not session_row:
            raise ValueError(f"No active session found for candidate {candidate_id}")

        concept, domain = session_row
        question = self.question_layer.get_question(concept, mode=mode, chroma_store=self.chroma)
        
        # Cache wording in Chroma
        self.chroma.store_question(question, concept)
        
        return {
            "concept": concept,
            "question": question
        }

    def get_domain_mastery(self, candidate_id: str, domain: str) -> float:
        """Compute the average mastery score for the evaluated concepts in a domain."""
        conn = self.db.get_connection()
        evals = []
        with conn:
            with conn.cursor() as cur:
                # Query all concept evaluations for this candidate
                # Note: We simulate this by checking _CONCEPT_EVALUATIONS if MockConnection,
                # but standard SQL should execute correctly.
                # In MockConnection we directly read _CONCEPT_EVALUATIONS for robustness.
                if hasattr(conn, "cursor_obj"):
                    from .database import _CONCEPT_EVALUATIONS
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

        # Aggregate the latest mastery score for each unique concept evaluated
        latest_concept_scores: Dict[str, float] = {}
        for ev in evals:
            # Overwrite with later evaluations if repeated
            latest_concept_scores[ev["concept_id"]] = ev["mastery"]

        mastery_score = self.report_gen.calculate_domain_mastery(latest_concept_scores)
        self.db.persist_domain_mastery(candidate_id, domain, mastery_score)
        
        return mastery_score

    def generate_report(self, candidate_id: str) -> Dict[str, Any]:
        """Aggregate concept scores and compile the final candidate evaluation report."""
        conn = self.db.get_connection()
        
        # 1. Load Candidate and Session Details
        cand_name = "Candidate"
        domain = "machine_learning"
        session_id = candidate_id
        
        if hasattr(conn, "cursor_obj"):
            from .database import _CANDIDATES, _INTERVIEW_SESSIONS
            cand = _CANDIDATES.get(candidate_id)
            if cand:
                cand_name = cand["name"]
            sess = _INTERVIEW_SESSIONS.get(candidate_id)
            if sess:
                domain = sess["domain"]
                session_id = sess["id"]
        else:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT name FROM candidates WHERE id = %s;", (candidate_id,))
                    row = cur.fetchone()
                    if row:
                        cand_name = row[0]
                    cur.execute("SELECT domain, id FROM interview_sessions WHERE candidate_id = %s;", (candidate_id,))
                    row = cur.fetchone()
                    if row:
                        domain, session_id = row

        # 2. Get all concept masteries evaluated
        evals = []
        if hasattr(conn, "cursor_obj"):
            from .database import _CONCEPT_EVALUATIONS
            evals = [e for e in _CONCEPT_EVALUATIONS if e["candidate_id"] == candidate_id]
        else:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT concept_id, mastery FROM concept_evaluations WHERE candidate_id = %s;",
                        (candidate_id,)
                    )
                    rows = cur.fetchall()
                    evals = [{"concept_id": r[0], "mastery": float(r[1])} for r in rows]

        latest_concept_scores: Dict[str, float] = {}
        for ev in evals:
            latest_concept_scores[ev["concept_id"]] = ev["mastery"]

        # 3. Generate Report
        report = self.report_gen.generate_report(
            candidate_id=candidate_id,
            candidate_name=cand_name,
            domain=domain,
            concept_scores=latest_concept_scores
        )

        # 4. Persist Report to DB
        self.db.persist_report(
            candidate_id=candidate_id,
            session_id=session_id,
            concept_scores=report["concept_scores"],
            domain_scores=report["domain_scores"],
            strong_concepts=report["strong_concepts"],
            weak_concepts=report["weak_concepts"],
            recommended_topics=report["recommended_topics"],
            summary=report["summary"]
        )

        return report

    def pause_interview(self, candidate_id: str) -> Dict[str, Any]:
        """Transition the interview state to PAUSED."""
        conn = self.db.get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE interview_sessions SET state = 'PAUSED', updated_at = CURRENT_TIMESTAMP WHERE candidate_id = %s;",
                    (candidate_id,)
                )
        return {"session_id": candidate_id, "state": "PAUSED"}

    def resume_interview(self, candidate_id: str) -> Dict[str, Any]:
        """Transition the interview state back to ACTIVE."""
        conn = self.db.get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE interview_sessions SET state = 'ACTIVE', updated_at = CURRENT_TIMESTAMP WHERE candidate_id = %s;",
                    (candidate_id,)
                )
        return {"session_id": candidate_id, "state": "ACTIVE"}
