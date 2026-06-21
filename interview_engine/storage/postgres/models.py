"""SQLAlchemy database models for the Nephele technical interview persistence layer."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import ForeignKey, Numeric, String, Text, func, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy database models."""
    pass


class Candidate(Base):
    """Model representing a candidate registered for an interview."""
    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Relationships
    resume: Mapped[Optional[ResumeData]] = relationship(
        "ResumeData", back_populates="candidate", cascade="all, delete-orphan", uselist=False
    )
    sessions: Mapped[List[InterviewSession]] = relationship(
        "InterviewSession", back_populates="candidate", cascade="all, delete-orphan"
    )


class ResumeData(Base):
    """Model representing structured and raw resume information of a candidate."""
    __tablename__ = "resume_data"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    candidate_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("candidates.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    resume_text: Mapped[str] = mapped_column(Text, nullable=False)
    skills: Mapped[Dict[str, Any]] = mapped_column(JSON, server_default="{}", nullable=False)
    education: Mapped[List[Any]] = mapped_column(JSON, server_default="[]", nullable=False)
    projects: Mapped[List[Any]] = mapped_column(JSON, server_default="[]", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Relationships
    candidate: Mapped[Candidate] = relationship("Candidate", back_populates="resume")


class InterviewSession(Base):
    """Model representing an active or finished interview traversal session."""
    __tablename__ = "interview_sessions"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    candidate_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    state: Mapped[str] = mapped_column(String(50), nullable=False)  # CREATED, ACTIVE, PAUSED, COMPLETED, FAILED
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    current_concept: Mapped[str] = mapped_column(String(255), nullable=False)
    visited_concepts: Mapped[List[str]] = mapped_column(JSON, server_default="[]", nullable=False)
    mastery_history: Mapped[List[float]] = mapped_column(JSON, server_default="[]", nullable=False)
    success_streak: Mapped[int] = mapped_column(server_default="0", nullable=False)
    failure_streak: Mapped[int] = mapped_column(server_default="0", nullable=False)
    accelerated: Mapped[bool] = mapped_column(server_default="false", nullable=False)
    terminated: Mapped[bool] = mapped_column(server_default="false", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    candidate: Mapped[Candidate] = relationship("Candidate", back_populates="sessions")
    reports: Mapped[List[InterviewReport]] = relationship(
        "InterviewReport", back_populates="session", cascade="all, delete-orphan"
    )


class ConceptProgress(Base):
    """Model representing decision history for a concept traversed during an interview."""
    __tablename__ = "concept_progress"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    candidate_id: Mapped[str] = mapped_column(String(255), nullable=False)
    concept_id: Mapped[str] = mapped_column(String(255), nullable=False)
    mastery: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    decision: Mapped[str] = mapped_column(String(50), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )


class ConceptEvaluation(Base):
    """Model representing detailed answers and mastery evaluation for a specific concept."""
    __tablename__ = "concept_evaluations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    candidate_id: Mapped[str] = mapped_column(String(255), nullable=False)
    concept_id: Mapped[str] = mapped_column(String(255), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    mastery: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    matched_signals: Mapped[List[str]] = mapped_column(JSON, server_default="[]", nullable=False)
    missing_signals: Mapped[List[str]] = mapped_column(JSON, server_default="[]", nullable=False)
    reasoning: Mapped[List[str]] = mapped_column(JSON, server_default="[]", nullable=False)
    strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    metadata_: Mapped[Dict[str, Any]] = mapped_column(
        "metadata", JSON, server_default="{}", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )


class DomainMastery(Base):
    """Model representing overall mastery score achieved per domain by a candidate."""
    __tablename__ = "domain_mastery"

    candidate_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    domain_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    mastery: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )


class InterviewReport(Base):
    """Model representing the generated final candidate performance evaluation report."""
    __tablename__ = "interview_reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    candidate_id: Mapped[str] = mapped_column(String(255), nullable=False)
    session_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False
    )
    concept_scores: Mapped[Dict[str, float]] = mapped_column(JSON, server_default="{}", nullable=False)
    domain_scores: Mapped[Dict[str, float]] = mapped_column(JSON, server_default="{}", nullable=False)
    strong_concepts: Mapped[List[str]] = mapped_column(JSON, server_default="[]", nullable=False)
    weak_concepts: Mapped[List[str]] = mapped_column(JSON, server_default="[]", nullable=False)
    recommended_topics: Mapped[List[str]] = mapped_column(JSON, server_default="[]", nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Relationships
    session: Mapped[InterviewSession] = relationship("InterviewSession", back_populates="reports")


class GraphStatistics(Base):
    """Model representing structural characteristics and statistics of loaded domain graphs."""
    __tablename__ = "graph_statistics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    domain_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    total_concepts: Mapped[int] = mapped_column(nullable=False)
    total_edges: Mapped[int] = mapped_column(nullable=False)
    max_depth: Mapped[int] = mapped_column(nullable=False)
    density: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )


class EvaluationHistory(Base):
    """Model representing historical evaluations conducted by LLMs and fallbacks."""
    __tablename__ = "evaluation_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    concept_id: Mapped[str] = mapped_column(String(255), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    evaluation_request: Mapped[Dict[str, Any]] = mapped_column(JSON, server_default="{}", nullable=False)
    evaluation_response: Mapped[Dict[str, Any]] = mapped_column(JSON, server_default="{}", nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    latency: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False)  # seconds
    mastery: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )


class ProviderMetrics(Base):
    """Model representing token usage, latency, and cost estimates per provider invocation."""
    __tablename__ = "provider_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(nullable=False)
    completion_tokens: Mapped[int] = mapped_column(nullable=False)
    total_tokens: Mapped[int] = mapped_column(nullable=False)
    latency: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False)
    cost: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )


class QuestionResponseLog(Base):
    """Model representing historical candidate responses and outcomes per question."""
    __tablename__ = "question_responses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    question_id: Mapped[str] = mapped_column(String(255), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    concept_id: Mapped[str] = mapped_column(String(255), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False)
    candidate_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mastery_outcome: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    latency: Mapped[float] = mapped_column(Numeric(6, 3), nullable=False)  # seconds
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )


class QuestionEffectiveness(Base):
    """Model representing tracking metrics and performance effectiveness of interview questions."""
    __tablename__ = "question_effectiveness"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    success_rate: Mapped[float] = mapped_column(Numeric(5, 4), server_default="0.0", nullable=False)
    average_score: Mapped[float] = mapped_column(Numeric(5, 4), server_default="0.0", nullable=False)
    average_latency: Mapped[float] = mapped_column(Numeric(6, 3), server_default="0.0", nullable=False)
    total_responses: Mapped[int] = mapped_column(server_default="0", nullable=False)


class GraphEdgeStatistics(Base):
    """Model representing evolved edge statistics and traversal correlation metrics."""
    __tablename__ = "graph_edge_statistics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_concept: Mapped[str] = mapped_column(String(255), nullable=False)
    target_concept: Mapped[str] = mapped_column(String(255), nullable=False)
    edge_strength: Mapped[float] = mapped_column(Numeric(5, 4), server_default="0.0", nullable=False)
    success_rate: Mapped[float] = mapped_column(Numeric(5, 4), server_default="0.0", nullable=False)
    failure_rate: Mapped[float] = mapped_column(Numeric(5, 4), server_default="0.0", nullable=False)
    traversal_count: Mapped[int] = mapped_column(server_default="0", nullable=False)
    last_updated: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

