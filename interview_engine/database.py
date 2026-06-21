"""Database manager implementing database operations delegated to SQLAlchemy and PostgreSQL."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from .storage.postgres.service import PostgresService
from .storage.postgres.models import (
    Candidate,
    ResumeData,
    InterviewSession,
    ConceptProgress,
    ConceptEvaluation,
    DomainMastery,
    InterviewReport,
    EvaluationHistory,
    ProviderMetrics,
    QuestionResponseLog,
    QuestionEffectiveness,
    GraphEdgeStatistics,
)
from .storage.postgres.repositories import (
    CandidateRepository,
    InterviewRepository,
    MasteryRepository,
    ReportRepository,
    EvaluationRepository,
    QuestionRepository,
    GraphEdgeStatsRepository,
)

logger = logging.getLogger(__name__)


def reset_mock_db() -> None:
    """Clear and recreate all database tables to ensure test isolation."""
    logger.info("Resetting persistence database tables...")
    pg = PostgresService()
    # Drop existing tables
    pg.drop_tables()
    # Create tables
    pg.create_tables()
    # Create the reports view to support legacy queries referencing 'reports'
    try:
        with pg.engine.begin() as conn:
            conn.execute(text("DROP VIEW IF EXISTS reports;"))
            conn.execute(text("CREATE VIEW reports AS SELECT id, candidate_id, session_id, concept_scores, domain_scores, strong_concepts, weak_concepts, recommended_topics, summary, created_at FROM interview_reports;"))
            logger.info("Database reset complete (tables created and reports view initialized).")
    except Exception as e:
        logger.error(f"Error initializing database reports view: {e}")


class CursorWrapper:
    """Wraps raw DBAPI cursors to support the context manager protocol and translate PG queries to SQLite."""

    def __init__(self, raw_cursor: Any, is_sqlite: bool = False) -> None:
        self.raw_cursor = raw_cursor
        self.is_sqlite = is_sqlite

    def execute(self, query: str, params: tuple = ()) -> Any:
        if self.is_sqlite:
            # Convert PostgreSQL query parameter syntax (%s) to SQLite syntax (?)
            query = query.replace("%s", "?")
            # Remove PostgreSQL JSONB cast syntax which causes SQLite errors
            query = query.replace("::jsonb", "").replace("::json", "")
        return self.raw_cursor.execute(query, params)

    def fetchone(self) -> Any:
        return self.raw_cursor.fetchone()

    def fetchall(self) -> Any:
        return self.raw_cursor.fetchall()

    def close(self) -> None:
        try:
            self.raw_cursor.close()
        except Exception:
            pass

    def __enter__(self) -> CursorWrapper:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()


class ConnectionWrapper:
    """Wraps raw DBAPI connections to support the context manager protocol across different databases."""

    def __init__(self, raw_conn: Any, is_sqlite: bool = False) -> None:
        self.raw_conn = raw_conn
        self.is_sqlite = is_sqlite

    def cursor(self) -> CursorWrapper:
        return CursorWrapper(self.raw_conn.cursor(), is_sqlite=self.is_sqlite)

    def commit(self) -> None:
        self.raw_conn.commit()

    def rollback(self) -> None:
        self.raw_conn.rollback()

    def close(self) -> None:
        self.raw_conn.close()

    def __enter__(self) -> ConnectionWrapper:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            try:
                self.rollback()
            except Exception:
                pass
        else:
            try:
                self.commit()
            except Exception:
                pass


class DatabaseManager:
    """Interface layer delegating database operations to SQLAlchemy repositories."""

    def __init__(self, connection_provider: Optional[Any] = None) -> None:
        # Provide a default PostgresService
        self.service = PostgresService()

    def get_connection(self) -> Any:
        """Get an active DBAPI-compliant database connection (useful for legacy raw query executions)."""
        # For legacy raw SQL execution, we return a wrapped raw DBAPI connection.
        is_sqlite = "sqlite" in self.service.database_url
        return ConnectionWrapper(self.service.engine.raw_connection(), is_sqlite=is_sqlite)

    def persist_candidate(
        self,
        candidate_id: str,
        name: str,
        email: str,
        resume_text: str,
        skills: dict,
        education: list,
        projects: list
    ) -> None:
        """Insert or update a candidate and their resume data."""
        with self.service.session() as session:
            repo = CandidateRepository(session)
            
            # 1. Upsert candidate
            cand = Candidate(id=candidate_id, name=name, email=email)
            repo.save(cand)
            
            # 2. Upsert resume data
            resume = ResumeData(
                candidate_id=candidate_id,
                resume_text=resume_text,
                skills=skills,
                education=education,
                projects=projects
            )
            repo.save_resume(resume)

    def persist_concept_evaluation(
        self,
        candidate_id: str,
        concept_id: str,
        question: str,
        answer: str,
        mastery: float,
        confidence: float,
        matched_signals: List[str],
        missing_signals: List[str],
        reasoning: List[str],
        strategy: str,
        metadata: dict
    ) -> None:
        """Insert a concept evaluation record."""
        with self.service.session() as session:
            repo = InterviewRepository(session)
            evaluation = ConceptEvaluation(
                candidate_id=candidate_id,
                concept_id=concept_id,
                question=question,
                answer=answer,
                mastery=mastery,
                confidence=confidence,
                matched_signals=matched_signals,
                missing_signals=missing_signals,
                reasoning=reasoning,
                strategy=strategy,
                metadata_=metadata
            )
            repo.add_concept_evaluation(evaluation)

    def persist_domain_mastery(self, candidate_id: str, domain_id: str, mastery: float) -> None:
        """Upsert a domain-level mastery score."""
        with self.service.session() as session:
            repo = MasteryRepository(session)
            dm = DomainMastery(
                candidate_id=candidate_id,
                domain_id=domain_id,
                mastery=mastery
            )
            repo.save_domain_mastery(dm)

    def persist_report(
        self,
        candidate_id: str,
        session_id: str,
        concept_scores: dict,
        domain_scores: dict,
        strong_concepts: List[str],
        weak_concepts: List[str],
        recommended_topics: List[str],
        summary: str
    ) -> None:
        """Insert or update a final interview evaluation report."""
        with self.service.session() as session:
            repo = ReportRepository(session)
            report = InterviewReport(
                candidate_id=candidate_id,
                session_id=session_id,
                concept_scores=concept_scores,
                domain_scores=domain_scores,
                strong_concepts=strong_concepts,
                weak_concepts=weak_concepts,
                recommended_topics=recommended_topics,
                summary=summary
            )
            repo.save_report(report)

    def persist_evaluation_history(
        self,
        concept_id: str,
        question: str,
        answer: str,
        evaluation_request: dict,
        evaluation_response: dict,
        provider: str,
        latency: float,
        mastery: float,
        confidence: float
    ) -> None:
        """Insert an evaluation history record."""
        with self.service.session() as session:
            repo = EvaluationRepository(session)
            history = EvaluationHistory(
                concept_id=concept_id,
                question=question,
                answer=answer,
                evaluation_request=evaluation_request,
                evaluation_response=evaluation_response,
                provider=provider,
                latency=latency,
                mastery=mastery,
                confidence=confidence
            )
            repo.add_evaluation_history(history)

    def persist_provider_metrics(
        self,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        latency: float,
        cost: float
    ) -> None:
        """Insert a provider metrics record."""
        with self.service.session() as session:
            repo = EvaluationRepository(session)
            metrics = ProviderMetrics(
                provider=provider,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                latency=latency,
                cost=cost
            )
            repo.add_provider_metrics(metrics)

    def persist_question_response(
        self,
        session_id: str,
        question_id: str,
        question_text: str,
        concept_id: str,
        difficulty: str,
        candidate_answer: Optional[str],
        mastery_outcome: float,
        latency: float
    ) -> None:
        """Insert a question response log and update its aggregate effectiveness metrics."""
        with self.service.session() as session:
            repo = QuestionRepository(session)
            log = QuestionResponseLog(
                session_id=session_id,
                question_id=question_id,
                question_text=question_text,
                concept_id=concept_id,
                difficulty=difficulty,
                candidate_answer=candidate_answer,
                mastery_outcome=mastery_outcome,
                latency=latency
            )
            repo.add_response_log(log)
            # Flush to database so the new log is visible to the update query
            session.flush()
            repo.update_question_effectiveness(question_id)

    def get_session_question_logs(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve all question response logs for a session as detached-safe dictionaries."""
        with self.service.session() as session:
            repo = QuestionRepository(session)
            logs = repo.get_session_logs(session_id)
            return [
                {
                    "question_id": log.question_id,
                    "question_text": log.question_text,
                    "concept_id": log.concept_id,
                    "difficulty": log.difficulty,
                    "mastery_outcome": float(log.mastery_outcome) if log.mastery_outcome is not None else 0.0,
                    "latency": float(log.latency) if log.latency is not None else 0.0
                }
                for log in logs
            ]


    def get_question_effectiveness(self, question_id: str) -> Optional[QuestionEffectiveness]:
        """Retrieve aggregate effectiveness metrics for a question ID."""
        with self.service.session() as session:
            repo = QuestionRepository(session)
            return repo.get_question_effectiveness(question_id)

    def persist_edge_statistics(
        self,
        source_concept: str,
        target_concept: str,
        edge_strength: float,
        success_rate: float,
        failure_rate: float,
        traversal_count: int
    ) -> None:
        """Insert or update graph edge statistics in the database."""
        with self.service.session() as session:
            repo = GraphEdgeStatsRepository(session)
            stats = GraphEdgeStatistics(
                source_concept=source_concept,
                target_concept=target_concept,
                edge_strength=edge_strength,
                success_rate=success_rate,
                failure_rate=failure_rate,
                traversal_count=traversal_count
            )
            repo.save_edge_stats(stats)

    def get_all_edge_statistics(self) -> List[Dict[str, Any]]:
        """Retrieve all persisted graph edge statistics as detached dictionaries."""
        with self.service.session() as session:
            repo = GraphEdgeStatsRepository(session)
            rows = repo.get_all_edge_stats()
            return [
                {
                    "source_concept": r.source_concept,
                    "target_concept": r.target_concept,
                    "edge_strength": float(r.edge_strength),
                    "success_rate": float(r.success_rate),
                    "failure_rate": float(r.failure_rate),
                    "traversal_count": r.traversal_count
                }
                for r in rows
            ]


