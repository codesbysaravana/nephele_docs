"""Routing for report exports (JSON, CSV, and PDF formats)."""

from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Response
from sqlalchemy.orm import Session

from interview_engine.storage.postgres.service import PostgresService
from interview_engine.storage.postgres.models import InterviewReport, Candidate
from graph_evolution.evolution_engine import GraphEvolutionEngine
from app.routes.observability import get_metrics
from app.routes.security import validate_session_active
from app.utils.exporters import (
    export_to_json,
    export_to_csv,
    export_interview_pdf,
    export_evolution_pdf,
    export_analytics_pdf,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/reports", tags=["Report Exports"])


def get_db_session():
    """Dependency to retrieve database session."""
    service = PostgresService()
    with service.session() as session:
        yield session


@router.get("/evolution/export")
def export_evolution_report(
    domain: str = "machine_learning",
    format: str = Query("json", pattern="^(json|csv|pdf)$")
) -> Response:
    """Download system knowledge graph evolution report."""
    try:
        engine = GraphEvolutionEngine()
        report_data = engine.generate_evolution_report(domain)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate evolution report: {str(e)}")

    if format == "json":
        json_str = export_to_json(report_data)
        return Response(
            content=json_str,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=evolution_report_{domain}.json"}
        )
        
    elif format == "csv":
        rows = []
        for rec in report_data.get("existing_edge_recommendations", []):
            rows.append({
                "type": "existing_edge",
                "source": rec.get("source"),
                "target": rec.get("target"),
                "strength": rec.get("strength"),
                "traversal_count": rec.get("traversal_count"),
                "recommendation": rec.get("recommendation")
            })
        for rec in report_data.get("new_relationship_suggestions", []):
            rows.append({
                "type": "new_edge_candidate",
                "source": rec.get("source"),
                "target": rec.get("target"),
                "strength": rec.get("strength"),
                "traversal_count": rec.get("traversal_count"),
                "recommendation": rec.get("recommendation")
            })
        csv_str = export_to_csv(rows, ["type", "source", "target", "strength", "traversal_count", "recommendation"])
        return Response(
            content=csv_str,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=evolution_report_{domain}.csv"}
        )
        
    elif format == "pdf":
        pdf_bytes = export_evolution_pdf(report_data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=evolution_report_{domain}.pdf"}
        )
        
    raise HTTPException(status_code=400, detail="Invalid format specified")


@router.get("/analytics/export")
def export_analytics_report(
    format: str = Query("json", pattern="^(json|csv|pdf)$")
) -> Response:
    """Download system metrics and latency analysis reports."""
    metrics = get_metrics()

    if format == "json":
        json_str = export_to_json(metrics)
        return Response(
            content=json_str,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=system_analytics.json"}
        )
        
    elif format == "csv":
        rows = []
        for stage, stats in metrics.get("latencies", {}).items():
            rows.append({
                "type": "latency",
                "name": stage,
                "average_seconds": stats.get("average_seconds"),
                "invocation_count": stats.get("invocation_count"),
                "cost": ""
            })
        for provider, stats in metrics.get("provider_costs", {}).items():
            rows.append({
                "type": "token_cost",
                "name": provider,
                "average_seconds": "",
                "invocation_count": stats.get("total"),
                "cost": stats.get("cost")
            })
        csv_str = export_to_csv(rows, ["type", "name", "average_seconds", "invocation_count", "cost"])
        return Response(
            content=csv_str,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=system_analytics.csv"}
        )
        
    elif format == "pdf":
        pdf_bytes = export_analytics_pdf(metrics)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=system_analytics.pdf"}
        )
        
    raise HTTPException(status_code=400, detail="Invalid format specified")


@router.get("/{candidate_id}/export")
def export_candidate_report(
    candidate_id: str,
    format: str = Query("json", pattern="^(json|csv|pdf)$"),
    db: Session = Depends(get_db_session)
) -> Response:
    """Download candidate interview report in specified format."""
    report_record = db.query(InterviewReport).filter(
        InterviewReport.candidate_id == candidate_id
    ).order_by(InterviewReport.id.desc()).first()
    
    if not report_record:
        # Check if candidate exists, if so generate report on the fly
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
        try:
            from interview_engine.orchestrator import InterviewOrchestrator
            orchestrator = InterviewOrchestrator()
            report_data = orchestrator.generate_report(candidate_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"No report found or generated for candidate {candidate_id}: {str(e)}")
    else:
        report_data = {
            "candidate_id": report_record.candidate_id,
            "session_id": report_record.session_id,
            "concept_scores": report_record.concept_scores,
            "domain_scores": report_record.domain_scores,
            "strong_concepts": report_record.strong_concepts,
            "weak_concepts": report_record.weak_concepts,
            "recommended_topics": report_record.recommended_topics,
            "summary": report_record.summary,
            "created_at": report_record.created_at,
        }
        # Try to resolve candidate name
        cand = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        report_data["candidate_name"] = cand.name if cand else "Candidate"
        # Determine domain from keys of domain_scores
        report_data["domain"] = list(report_record.domain_scores.keys())[0] if report_record.domain_scores else "machine_learning"

    if format == "json":
        json_str = export_to_json(report_data)
        return Response(
            content=json_str,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=report_{candidate_id}.json"}
        )
        
    elif format == "csv":
        # Convert dictionary metrics into tabular rows
        rows = []
        for concept, score in report_data.get("concept_scores", {}).items():
            rows.append({
                "candidate_id": candidate_id,
                "candidate_name": report_data.get("candidate_name"),
                "domain": report_data.get("domain"),
                "concept": concept,
                "score": score
            })
        csv_str = export_to_csv(rows, ["candidate_id", "candidate_name", "domain", "concept", "score"])
        return Response(
            content=csv_str,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=report_{candidate_id}.csv"}
        )
        
    elif format == "pdf":
        pdf_bytes = export_interview_pdf(report_data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=report_{candidate_id}.pdf"}
        )
        
    raise HTTPException(status_code=400, detail="Invalid format specified")
