"""Routing and computation for the Analytics Dashboard backend API."""

from __future__ import annotations

import logging
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from interview_engine.storage.postgres.service import PostgresService
from interview_engine.storage.postgres.models import (
    DomainMastery,
    InterviewSession,
    QuestionEffectiveness,
    GraphEdgeStatistics,
    Candidate
)
from graph_evolution.evolution_engine import GraphEvolutionEngine
from graph_evolution.edge_updater import EdgeUpdater

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


def get_db_session():
    """Dependency to retrieve database session."""
    service = PostgresService()
    with service.session() as session:
        yield session


@router.get("")
def get_analytics_dashboard_data(
    domain: str = Query("machine_learning"),
    db: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """Compile and return all analytics metrics required for the Analytics Dashboard."""
    logger.info(f"Compiling analytics dashboard metrics for domain: '{domain}'")
    
    # 1. Fetch data from Graph Evolution Engine
    evolution_report = {}
    try:
        evolution_engine = GraphEvolutionEngine(db_manager=None)
        evolution_report = evolution_engine.generate_evolution_report(domain)
    except Exception as e:
        logger.error(f"Failed to generate evolution stats for analytics: {e}")

    # 2. Average Domain Mastery
    avg_mastery = db.query(func.avg(DomainMastery.mastery)).filter(
        DomainMastery.domain_id == domain
    ).scalar()
    avg_mastery_val = float(avg_mastery) if avg_mastery is not None else 0.0

    # 3. Average Interview Duration (for COMPLETED or FAILED sessions)
    sessions = db.query(InterviewSession).filter(
        InterviewSession.state.in_(["COMPLETED", "FAILED"])
    ).all()
    durations = [(s.updated_at - s.created_at).total_seconds() for s in sessions]
    avg_duration_seconds = sum(durations) / len(durations) if durations else 0.0

    # 4. Relationship Strength Rankings
    edge_stats = db.query(GraphEdgeStatistics).order_by(
        GraphEdgeStatistics.edge_strength.desc()
    ).all()
    relationship_strengths = [
        {
            "source": edge.source_concept,
            "target": edge.target_concept,
            "strength": float(edge.edge_strength),
            "traversal_count": edge.traversal_count
        }
        for edge in edge_stats
    ]

    # 5. Candidate Improvement Trends (Aggregated summary of student trajectories)
    updater = EdgeUpdater(db_manager=None)
    candidates = db.query(Candidate).all()
    improving_count = 0
    declining_count = 0
    misunderstood_count = 0
    total_candidates = len(candidates)
    
    candidate_details = []
    for cand in candidates:
        try:
            trend = updater.analyze_candidate_trends(cand.id)
            improving_count += len(trend.get("improving_concepts", []))
            declining_count += len(trend.get("declining_concepts", []))
            misunderstood_count += len(trend.get("misunderstood_concepts", []))
            candidate_details.append({
                "candidate_id": cand.id,
                "name": cand.name,
                "improving": trend.get("improving_concepts", []),
                "declining": trend.get("declining_concepts", []),
                "misunderstood": trend.get("misunderstood_concepts", [])
            })
        except Exception:
            pass

    # 6. Question Effectiveness Rankings
    q_effect = db.query(QuestionEffectiveness).order_by(
        QuestionEffectiveness.success_rate.desc()
    ).all()
    question_rankings = [
        {
            "question_id": qe.question_id,
            "success_rate": float(qe.success_rate),
            "average_score": float(qe.average_score),
            "average_latency": float(qe.average_latency),
            "total_responses": qe.total_responses
        }
        for qe in q_effect
    ]

    # Extrapolate most failed/successful concept arrays from the evolution engine
    most_failed = evolution_report.get("most_failed_concepts", [])
    most_successful = evolution_report.get("most_successful_concepts", [])
    most_common_misconceptions = evolution_report.get("mined_misconceptions", [])
    concept_difficulty = evolution_report.get("concept_difficulty_rankings", [])

    return {
        "domain": domain,
        "most_failed_concepts": most_failed,
        "most_successful_concepts": most_successful,
        "most_common_misconceptions": most_common_misconceptions,
        "average_domain_mastery": round(avg_mastery_val, 3),
        "average_interview_duration_seconds": round(avg_duration_seconds, 1),
        "concept_difficulty_rankings": concept_difficulty,
        "relationship_strength_rankings": relationship_strengths,
        "candidate_trends_summary": {
            "total_candidates": total_candidates,
            "total_improving_concepts": improving_count,
            "total_declining_concepts": declining_count,
            "total_misunderstood_concepts": misunderstood_count,
            "candidate_details": candidate_details
        },
        "question_effectiveness_rankings": question_rankings
    }
