"""Health checks routing for Nephele database, Chroma, providers, and voice runtime."""

from __future__ import annotations

import os
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from interview_engine.storage.postgres.service import PostgresService
from interview_engine.chroma_store import ChromaStore

router = APIRouter(prefix="/api/health", tags=["Health"])


def get_db_session():
    """Dependency to get a SQLAlchemy database session."""
    service = PostgresService()
    with service.session() as session:
        yield session


@router.get("")
@router.get("/health")
def health() -> Dict[str, str]:
    """Base system health check."""
    return {"status": "healthy", "service": "Nephele Technical Interview Engine"}


@router.get("/database")
def database_health(db: Session = Depends(get_db_session)) -> Dict[str, Any]:
    """Check database connectivity and pool health."""
    try:
        # Execute basic select query to verify connection
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "PostgreSQL" if "postgresql" in PostgresService().database_url else "SQLite",
            "connection": "up"
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={"status": "unhealthy", "database": "unreachable", "error": str(e)}
        )


@router.get("/chroma")
def chroma_health() -> Dict[str, Any]:
    """Check ChromaDB service status and collections."""
    try:
        store = ChromaStore()
        # Ping client heartbeat
        heartbeat = store.service.client.heartbeat()
        return {
            "status": "healthy",
            "heartbeat": heartbeat,
            "collections": ["questions", "answers", "misconceptions", "concept_examples", "interview_memory"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={"status": "unhealthy", "chromadb": "unreachable", "error": str(e)}
        )


@router.get("/provider")
def provider_health() -> Dict[str, Any]:
    """Check configuration and presence of third-party AI provider keys."""
    providers = {
        "Gemini": bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")),
        "Groq": bool(os.environ.get("GROQ_API_KEY")),
        "OpenAI": bool(os.environ.get("OPENAI_API_KEY")),
        "AssemblyAI": bool(os.environ.get("ASSEMBLYAI_API_KEY")),
        "Deepgram": bool(os.environ.get("DEEPGRAM_API_KEY")),
    }
    
    # Check if we are running in dry-run/mock mode
    all_keys_missing = not any(providers.values())
    mode = "mock/offline" if all_keys_missing else "production"

    return {
        "status": "healthy",
        "mode": mode,
        "providers_configured": providers
    }


@router.get("/runtime")
def runtime_health(db: Session = Depends(get_db_session)) -> Dict[str, Any]:
    """Count active and total interview sessions stored in PostgreSQL."""
    try:
        # Query total active sessions count
        active_count = db.execute(
            text("SELECT COUNT(*) FROM interview_sessions WHERE state = 'ACTIVE'")
        ).scalar()
        
        total_count = db.execute(
            text("SELECT COUNT(*) FROM interview_sessions")
        ).scalar()

        paused_count = db.execute(
            text("SELECT COUNT(*) FROM interview_sessions WHERE state = 'PAUSED'")
        ).scalar()

        completed_count = db.execute(
            text("SELECT COUNT(*) FROM interview_sessions WHERE state = 'COMPLETED'")
        ).scalar()

        failed_count = db.execute(
            text("SELECT COUNT(*) FROM interview_sessions WHERE state = 'FAILED'")
        ).scalar()

        return {
            "status": "healthy",
            "active_sessions": active_count,
            "paused_sessions": paused_count,
            "completed_sessions": completed_count,
            "failed_sessions": failed_count,
            "total_sessions": total_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": "Failed to inspect session tables", "error": str(e)}
        )
