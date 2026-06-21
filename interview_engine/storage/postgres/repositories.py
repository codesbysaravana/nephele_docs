"""Repository layer for encapsulating PostgreSQL database operations."""

from __future__ import annotations

from typing import List, Optional
from sqlalchemy.orm import Session

from .models import (
    Candidate,
    ResumeData,
    InterviewSession,
    ConceptProgress,
    ConceptEvaluation,
    DomainMastery,
    InterviewReport,
    GraphStatistics,
    EvaluationHistory,
    ProviderMetrics,
    QuestionResponseLog,
    QuestionEffectiveness,
    GraphEdgeStatistics,
)


class CandidateRepository:
    """Repository handling persistence for Candidates and ResumeData."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, candidate: Candidate) -> Candidate:
        """Upsert a candidate record."""
        db_candidate = self.session.query(Candidate).filter(Candidate.id == candidate.id).first()
        if db_candidate:
            db_candidate.name = candidate.name
            db_candidate.email = candidate.email
            return db_candidate
        else:
            self.session.add(candidate)
            return candidate

    def get_by_id(self, candidate_id: str) -> Optional[Candidate]:
        """Fetch candidate by primary key."""
        return self.session.query(Candidate).filter(Candidate.id == candidate_id).first()

    def save_resume(self, resume: ResumeData) -> ResumeData:
        """Upsert a candidate's resume data."""
        db_resume = self.session.query(ResumeData).filter(ResumeData.candidate_id == resume.candidate_id).first()
        if db_resume:
            db_resume.resume_text = resume.resume_text
            db_resume.skills = resume.skills
            db_resume.education = resume.education
            db_resume.projects = resume.projects
            return db_resume
        else:
            self.session.add(resume)
            return resume

    def get_resume(self, candidate_id: str) -> Optional[ResumeData]:
        """Fetch resume data for a candidate."""
        return self.session.query(ResumeData).filter(ResumeData.candidate_id == candidate_id).first()


class InterviewRepository:
    """Repository handling persistence for InterviewSessions, ConceptProgress, and ConceptEvaluations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save_session(self, interview_session: InterviewSession) -> InterviewSession:
        """Upsert an interview session record."""
        db_session = self.session.query(InterviewSession).filter(InterviewSession.id == interview_session.id).first()
        if db_session:
            db_session.state = interview_session.state
            db_session.domain = interview_session.domain
            db_session.current_concept = interview_session.current_concept
            db_session.visited_concepts = interview_session.visited_concepts
            db_session.mastery_history = interview_session.mastery_history
            db_session.success_streak = interview_session.success_streak
            db_session.failure_streak = interview_session.failure_streak
            db_session.accelerated = interview_session.accelerated
            db_session.terminated = interview_session.terminated
            return db_session
        else:
            self.session.add(interview_session)
            return interview_session

    def get_session(self, session_id: str) -> Optional[InterviewSession]:
        """Fetch an interview session by ID."""
        return self.session.query(InterviewSession).filter(InterviewSession.id == session_id).first()

    def get_session_by_candidate(self, candidate_id: str) -> Optional[InterviewSession]:
        """Fetch an interview session by candidate ID."""
        return self.session.query(InterviewSession).filter(InterviewSession.candidate_id == candidate_id).first()

    def add_concept_progress(self, progress: ConceptProgress) -> ConceptProgress:
        """Add a traversal progress record."""
        self.session.add(progress)
        return progress

    def add_concept_evaluation(self, evaluation: ConceptEvaluation) -> ConceptEvaluation:
        """Add a concept evaluation record."""
        self.session.add(evaluation)
        return evaluation

    def get_evaluations(self, candidate_id: str) -> List[ConceptEvaluation]:
        """Fetch all concept evaluations for a candidate."""
        return self.session.query(ConceptEvaluation).filter(ConceptEvaluation.candidate_id == candidate_id).all()


class MasteryRepository:
    """Repository handling persistence for DomainMastery."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save_domain_mastery(self, domain_mastery: DomainMastery) -> DomainMastery:
        """Upsert a domain mastery score."""
        db_mastery = self.session.query(DomainMastery).filter(
            DomainMastery.candidate_id == domain_mastery.candidate_id,
            DomainMastery.domain_id == domain_mastery.domain_id
        ).first()
        if db_mastery:
            db_mastery.mastery = domain_mastery.mastery
            return db_mastery
        else:
            self.session.add(domain_mastery)
            return domain_mastery

    def get_domain_mastery(self, candidate_id: str, domain_id: str) -> Optional[DomainMastery]:
        """Fetch a specific domain mastery score for a candidate."""
        return self.session.query(DomainMastery).filter(
            DomainMastery.candidate_id == candidate_id,
            DomainMastery.domain_id == domain_id
        ).first()

    def get_all_mastery(self, candidate_id: str) -> List[DomainMastery]:
        """Fetch all domain mastery scores for a candidate."""
        return self.session.query(DomainMastery).filter(DomainMastery.candidate_id == candidate_id).all()


class ReportRepository:
    """Repository handling persistence for InterviewReports."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save_report(self, report: InterviewReport) -> InterviewReport:
        """Upsert a candidate evaluation report."""
        db_report = self.session.query(InterviewReport).filter(
            InterviewReport.session_id == report.session_id
        ).first()
        if db_report:
            db_report.concept_scores = report.concept_scores
            db_report.domain_scores = report.domain_scores
            db_report.strong_concepts = report.strong_concepts
            db_report.weak_concepts = report.weak_concepts
            db_report.recommended_topics = report.recommended_topics
            db_report.summary = report.summary
            return db_report
        else:
            self.session.add(report)
            return report

    def get_report(self, session_id: str) -> Optional[InterviewReport]:
        """Fetch evaluation report by session ID."""
        return self.session.query(InterviewReport).filter(InterviewReport.session_id == session_id).first()

    def get_reports_by_candidate(self, candidate_id: str) -> List[InterviewReport]:
        """Fetch all evaluation reports for a candidate."""
        return self.session.query(InterviewReport).filter(InterviewReport.candidate_id == candidate_id).all()


class GraphStatsRepository:
    """Repository handling persistence for GraphStatistics."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save_stats(self, stats: GraphStatistics) -> GraphStatistics:
        """Upsert graph statistics for a domain."""
        db_stats = self.session.query(GraphStatistics).filter(
            GraphStatistics.domain_id == stats.domain_id
        ).first()
        if db_stats:
            db_stats.total_concepts = stats.total_concepts
            db_stats.total_edges = stats.total_edges
            db_stats.max_depth = stats.max_depth
            db_stats.density = stats.density
            return db_stats
        else:
            self.session.add(stats)
            return stats

    def get_stats(self, domain_id: str) -> Optional[GraphStatistics]:
        """Fetch graph statistics for a domain."""
        return self.session.query(GraphStatistics).filter(GraphStatistics.domain_id == domain_id).first()


class EvaluationRepository:
    """Repository handling persistence for EvaluationHistory and ProviderMetrics."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add_evaluation_history(self, history: EvaluationHistory) -> EvaluationHistory:
        """Add an evaluation history record."""
        self.session.add(history)
        return history

    def get_evaluation_history(self, concept_id: Optional[str] = None) -> List[EvaluationHistory]:
        """Fetch evaluation history, optionally filtered by concept_id."""
        query = self.session.query(EvaluationHistory)
        if concept_id:
            query = query.filter(EvaluationHistory.concept_id == concept_id)
        return query.all()

    def add_provider_metrics(self, metrics: ProviderMetrics) -> ProviderMetrics:
        """Add a provider invocation metrics record."""
        self.session.add(metrics)
        return metrics

    def get_provider_metrics(self, provider: Optional[str] = None) -> List[ProviderMetrics]:
        """Fetch provider metrics, optionally filtered by provider."""
        query = self.session.query(ProviderMetrics)
        if provider:
            query = query.filter(ProviderMetrics.provider == provider)
        return query.all()


class QuestionRepository:
    """Repository handling persistence for QuestionResponseLog and QuestionEffectiveness."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add_response_log(self, log: QuestionResponseLog) -> QuestionResponseLog:
        """Add a question response log."""
        self.session.add(log)
        return log

    def get_session_logs(self, session_id: str) -> List[QuestionResponseLog]:
        """Fetch all response logs for a given session."""
        return self.session.query(QuestionResponseLog).filter(QuestionResponseLog.session_id == session_id).all()

    def get_question_effectiveness(self, question_id: str) -> Optional[QuestionEffectiveness]:
        """Fetch effectiveness metrics for a question."""
        return self.session.query(QuestionEffectiveness).filter(QuestionEffectiveness.question_id == question_id).first()

    def update_question_effectiveness(self, question_id: str) -> Optional[QuestionEffectiveness]:
        """Recalculate and update effectiveness metrics for a question based on logs."""
        logs = self.session.query(QuestionResponseLog).filter(QuestionResponseLog.question_id == question_id).all()
        total_responses = len(logs)
        if total_responses == 0:
            return None

        # Success rate defined as percentage of responses with mastery score >= 0.5
        successful_responses = sum(1 for log in logs if float(log.mastery_outcome) >= 0.5)
        success_rate = successful_responses / total_responses

        average_score = sum(float(log.mastery_outcome) for log in logs) / total_responses
        average_latency = sum(float(log.latency) for log in logs) / total_responses

        eff = self.session.query(QuestionEffectiveness).filter(QuestionEffectiveness.question_id == question_id).first()
        if not eff:
            eff = QuestionEffectiveness(
                question_id=question_id,
                success_rate=success_rate,
                average_score=average_score,
                average_latency=average_latency,
                total_responses=total_responses
            )
            self.session.add(eff)
        else:
            eff.success_rate = success_rate
            eff.average_score = average_score
            eff.average_latency = average_latency
            eff.total_responses = total_responses

        return eff


class GraphEdgeStatsRepository:
    """Repository handling persistence for GraphEdgeStatistics."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save_edge_stats(self, stats: GraphEdgeStatistics) -> GraphEdgeStatistics:
        """Upsert graph edge statistics."""
        db_stats = self.session.query(GraphEdgeStatistics).filter(
            GraphEdgeStatistics.source_concept == stats.source_concept,
            GraphEdgeStatistics.target_concept == stats.target_concept
        ).first()
        if db_stats:
            db_stats.edge_strength = stats.edge_strength
            db_stats.success_rate = stats.success_rate
            db_stats.failure_rate = stats.failure_rate
            db_stats.traversal_count = stats.traversal_count
            return db_stats
        else:
            self.session.add(stats)
            return stats

    def get_edge_stats(self, source: str, target: str) -> Optional[GraphEdgeStatistics]:
        """Fetch statistics for a specific concept-to-concept relationship edge."""
        return self.session.query(GraphEdgeStatistics).filter(
            GraphEdgeStatistics.source_concept == source,
            GraphEdgeStatistics.target_concept == target
        ).first()

    def get_all_edge_stats(self) -> List[GraphEdgeStatistics]:
        """Fetch all calculated edge statistics records."""
        return self.session.query(GraphEdgeStatistics).all()



