"""Unified persistence service orchestrating database transactions and vector storage operations."""

from __future__ import annotations

from typing import Tuple
from sqlalchemy.orm import Session

from .postgres.service import PostgresService
from .postgres.repositories import (
    CandidateRepository,
    InterviewRepository,
    MasteryRepository,
    ReportRepository,
    GraphStatsRepository,
    EvaluationRepository,
    QuestionRepository,
    GraphEdgeStatsRepository,
)
from .chroma.service import ChromaService


class PersistenceService:
    """Orchestrates high-level database operations by wrapping PostgreSQL and Chroma services."""

    def __init__(self, postgres_service: PostgresService, chroma_service: ChromaService) -> None:
        self.postgres = postgres_service
        self.chroma = chroma_service

    def get_repositories(
        self, session: Session
    ) -> Tuple[
        CandidateRepository,
        InterviewRepository,
        MasteryRepository,
        ReportRepository,
        GraphStatsRepository,
    ]:
        """Get all repository wrappers initialized with the given session."""
        return (
            CandidateRepository(session),
            InterviewRepository(session),
            MasteryRepository(session),
            ReportRepository(session),
            GraphStatsRepository(session),
        )

    def get_evaluation_repository(self, session: Session) -> EvaluationRepository:
        """Get evaluation history and provider metrics repository wrapper."""
        return EvaluationRepository(session)

    def get_question_repository(self, session: Session) -> QuestionRepository:
        """Get question history and effectiveness metrics repository wrapper."""
        return QuestionRepository(session)

    def get_edge_stats_repository(self, session: Session) -> GraphEdgeStatsRepository:
        """Get graph edge statistics repository wrapper."""
        return GraphEdgeStatsRepository(session)



