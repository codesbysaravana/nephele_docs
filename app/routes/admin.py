"""Routing and computation for the Admin Dashboard backend API."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from interview_engine.storage.postgres.service import PostgresService
from interview_engine.storage.postgres.models import (
    Candidate,
    InterviewSession,
    ConceptEvaluation,
    DomainMastery,
    GraphStatistics,
    InterviewReport
)
from graph_evolution.evolution_engine import GraphEvolutionEngine
from knowledge_graph.graph_loader import load_graph_document
from graph_traversal.traversal_engine import find_graph_path

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["Admin"])


def get_db_session():
    """Dependency to retrieve database session."""
    service = PostgresService()
    with service.session() as session:
        yield session


@router.get("/overview")
def get_admin_overview(db: Session = Depends(get_db_session)) -> Dict[str, Any]:
    """Retrieve high-level status aggregates of all candidate sessions and system mastery metrics."""
    total_candidates = db.query(Candidate).count()
    total_sessions = db.query(InterviewSession).count()
    completed_sessions = db.query(InterviewSession).filter(
        InterviewSession.state == "COMPLETED"
    ).count()
    active_sessions = db.query(InterviewSession).filter(
        InterviewSession.state == "ACTIVE"
    ).count()

    # Average mastery across all domain masteries
    avg_mastery = db.query(func.avg(DomainMastery.mastery)).scalar()
    avg_mastery_val = float(avg_mastery) if avg_mastery is not None else 0.0

    return {
        "total_candidates": total_candidates,
        "total_sessions": total_sessions,
        "active_sessions": active_sessions,
        "completed_sessions": completed_sessions,
        "average_system_mastery": round(avg_mastery_val, 3),
        "system_status": "ONLINE"
    }


@router.get("/candidates")
def search_candidates(
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """Search registered candidates and retrieve their current interview progress and final score reports."""
    query = db.query(Candidate)
    if q:
        query = query.filter(
            Candidate.name.ilike(f"%{q}%") |
            Candidate.email.ilike(f"%{q}%") |
            Candidate.id.ilike(f"%{q}%")
        )
    candidates = query.all()

    results = []
    for cand in candidates:
        # Find latest session
        sess = db.query(InterviewSession).filter(
            InterviewSession.candidate_id == cand.id
        ).order_by(InterviewSession.updated_at.desc()).first()
        
        # Find latest report
        report = db.query(InterviewReport).filter(
            InterviewReport.candidate_id == cand.id
        ).order_by(InterviewReport.id.desc()).first()

        results.append({
            "id": cand.id,
            "name": cand.name,
            "email": cand.email,
            "registered_at": cand.created_at.isoformat(),
            "session": {
                "session_id": sess.id,
                "state": sess.state,
                "domain": sess.domain,
                "current_concept": sess.current_concept,
                "visited_count": len(sess.visited_concepts) if sess.visited_concepts else 0,
                "last_active": sess.updated_at.isoformat()
            } if sess else None,
            "has_report": report is not None,
            "report_summary": report.summary if report else None
        })
    return results


@router.get("/concept-analytics")
def get_concept_analytics(db: Session = Depends(get_db_session)) -> List[Dict[str, Any]]:
    """Fetch average mastery scores and response count data for all traversed concepts."""
    rows = db.query(
        ConceptEvaluation.concept_id,
        func.avg(ConceptEvaluation.mastery),
        func.avg(ConceptEvaluation.confidence),
        func.count(ConceptEvaluation.id)
    ).group_by(ConceptEvaluation.concept_id).all()

    return [
        {
            "concept_id": row[0],
            "average_mastery": round(float(row[1]), 3) if row[1] is not None else 0.0,
            "average_confidence": round(float(row[2]), 3) if row[2] is not None else 0.0,
            "total_evaluations": row[3]
        }
        for row in rows
    ]


@router.get("/graph-analytics")
def get_graph_analytics(db: Session = Depends(get_db_session)) -> List[Dict[str, Any]]:
    """Read structural parameters of domain graphs from database or calculate them from local JSON files."""
    db_stats = db.query(GraphStatistics).all()
    if db_stats:
        return [
            {
                "domain": s.domain_id,
                "total_concepts": s.total_concepts,
                "total_edges": s.total_edges,
                "max_depth": s.max_depth,
                "density": float(s.density),
                "last_updated": s.updated_at.isoformat()
            }
            for s in db_stats
        ]

    # Dynamic fallback loading JSON documents if graph_statistics table is empty
    domains = ["machine_learning", "python", "sql", "dsa"]
    fallback_stats = []
    for dom in domains:
        try:
            path = find_graph_path(dom)
            graph = load_graph_document(path)
            num_concepts = len(graph.concepts)
            num_edges = len(graph.edges)
            density = num_edges / (num_concepts * (num_concepts - 1)) if num_concepts > 1 else 0.0
            fallback_stats.append({
                "domain": dom,
                "total_concepts": num_concepts,
                "total_edges": num_edges,
                "max_depth": 3,  # estimate
                "density": round(density, 4),
                "last_updated": "dynamic_fallback"
            })
        except Exception:
            pass
    return fallback_stats


@router.get("/evolution-reports")
def get_admin_evolution_reports(
    domain: str = Query("machine_learning")
) -> Dict[str, Any]:
    """Retrieve data-driven structure suggestions from the Evolution Engine for human-in-the-loop review."""
    try:
        engine = GraphEvolutionEngine()
        return engine.generate_evolution_report(domain)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate evolution recommendations: {str(e)}"
        )


@router.get("/system-health")
def get_system_health(db: Session = Depends(get_db_session)) -> Dict[str, Any]:
    """Compile aggregated health indicators across DB connectivity, Chroma status, and AI providers."""
    from app.routes.health import database_health, chroma_health, provider_health
    
    db_status = "healthy"
    try:
        database_health(db)
    except Exception:
        db_status = "unhealthy"

    chroma_status = "healthy"
    try:
        chroma_health()
    except Exception:
        chroma_status = "unhealthy"

    providers = provider_health()

    return {
        "overall_status": "healthy" if db_status == "healthy" and chroma_status == "healthy" else "degraded",
        "database": db_status,
        "chromadb": chroma_status,
        "providers": providers.get("providers_configured", {}),
        "execution_mode": providers.get("mode")
    }
