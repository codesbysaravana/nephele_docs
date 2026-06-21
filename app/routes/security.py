"""Security validation module including token-bucket rate limiting and candidate session verification."""

from __future__ import annotations

import logging
import time
from typing import Dict, Tuple
from fastapi import Request, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from interview_engine.storage.postgres.service import PostgresService

logger = logging.getLogger(__name__)

# Token bucket storage: { ip: (tokens, last_update_time) }
RATE_LIMIT_BUCKETS: Dict[str, Tuple[float, float]] = {}
LIMIT_CAPACITY = 60.0  # max tokens per client
LIMIT_REFILL_RATE = 1.0  # tokens refilled per second (60 per minute)


def get_db_session():
    """Dependency to retrieve a database session."""
    service = PostgresService()
    with service.session() as session:
        yield session


def rate_limiter(request: Request) -> None:
    """FastAPI dependency enforcing token-bucket rate limiting based on client host IP."""
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()
    
    if client_ip not in RATE_LIMIT_BUCKETS:
        RATE_LIMIT_BUCKETS[client_ip] = (LIMIT_CAPACITY, current_time)
        return

    tokens, last_refill = RATE_LIMIT_BUCKETS[client_ip]
    # Refill tokens since last request
    elapsed = current_time - last_refill
    tokens = min(LIMIT_CAPACITY, tokens + (elapsed * LIMIT_REFILL_RATE))
    
    if tokens < 1.0:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        RATE_LIMIT_BUCKETS[client_ip] = (tokens, current_time)
        raise HTTPException(
            status_code=429,
            detail="Too Many Requests. Please slow down and try again later."
        )
        
    RATE_LIMIT_BUCKETS[client_ip] = (tokens - 1.0, current_time)


def validate_session_active(candidate_id: str, db: Session = Depends(get_db_session)) -> Dict[str, str]:
    """Dependency to verify that a candidate session exists and is ACTIVE."""
    query = text(
        "SELECT state, current_concept, domain FROM interview_sessions WHERE candidate_id = :cid"
    )
    result = db.execute(query, {"cid": candidate_id}).fetchone()
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Interview session for candidate ID '{candidate_id}' not found."
        )
        
    state, current_concept, domain = result
    
    if state == "PAUSED":
        raise HTTPException(
            status_code=400,
            detail="Session is currently paused. Please resume before submitting responses."
        )
    elif state in ("COMPLETED", "FAILED"):
        raise HTTPException(
            status_code=400,
            detail=f"Interview session has already concluded (status: {state})."
        )
        
    return {
        "candidate_id": candidate_id,
        "state": state,
        "current_concept": current_concept,
        "domain": domain
    }
