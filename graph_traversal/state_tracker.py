"""State tracker for persisting and retrieving traversal session state."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
from .models import TraversalState


class StateTracker:
    """Tracks session state in-memory and handles PostgreSQL persistence."""

    def __init__(self) -> None:
        self.in_memory_sessions: Dict[str, TraversalState] = {}

    def get_session(self, candidate_id: str, conn: Optional[Any] = None) -> Optional[TraversalState]:
        """Retrieve the active session state for a candidate."""
        if conn is not None:
            return self.load_from_db(candidate_id, conn)
        return self.in_memory_sessions.get(candidate_id)

    def save_session(
        self,
        state: TraversalState,
        conn: Optional[Any] = None,
        last_decision: Optional[str] = None,
        last_mastery: Optional[float] = None,
        concept_id: Optional[str] = None
    ) -> None:
        """Save the traversal state and optionally log progress to database."""
        self.in_memory_sessions[state.candidate_id] = state

        if conn is not None:
            self.save_to_db(state, conn)
            if last_decision is not None and last_mastery is not None:
                self.add_progress_record(
                    candidate_id=state.candidate_id,
                    concept_id=concept_id or state.current_concept,
                    mastery=last_mastery,
                    decision=last_decision,
                    conn=conn
                )

    def load_from_db(self, candidate_id: str, conn: Any) -> Optional[TraversalState]:
        """Load session state from PostgreSQL database."""
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT domain, current_concept, visited_concepts, mastery_history, 
                           success_streak, failure_streak, accelerated, terminated
                    FROM interview_sessions
                    WHERE candidate_id = %s
                    ORDER BY updated_at DESC
                    LIMIT 1;
                    """,
                    (candidate_id,)
                )
                row = cur.fetchone()
                if not row:
                    return None

                domain, current_concept, visited_json, mastery_json, success_streak, failure_streak, accelerated, terminated = row
                
                # Handled if it's already list or string representation
                visited_concepts = visited_json if isinstance(visited_json, list) else json.loads(visited_json or "[]")
                mastery_history = mastery_json if isinstance(mastery_json, list) else json.loads(mastery_json or "[]")

                state = TraversalState(
                    candidate_id=candidate_id,
                    domain=domain,
                    current_concept=current_concept,
                    visited_concepts=visited_concepts,
                    mastery_history=mastery_history,
                    success_streak=success_streak,
                    failure_streak=failure_streak,
                    accelerated=accelerated,
                    terminated=terminated
                )
                self.in_memory_sessions[candidate_id] = state
                return state
        except Exception as e:
            print(f"Error loading state from database: {e}")
            return self.in_memory_sessions.get(candidate_id)

    def save_to_db(self, state: TraversalState, conn: Any) -> None:
        """Upsert session state to PostgreSQL database."""
        try:
            visited_json = json.dumps(state.visited_concepts)
            mastery_json = json.dumps(state.mastery_history)

            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO interview_sessions (
                        id, candidate_id, domain, current_concept, visited_concepts, 
                        mastery_history, success_streak, failure_streak, accelerated, terminated, updated_at, state
                    )
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s, CURRENT_TIMESTAMP, 'ACTIVE')
                    ON CONFLICT (id) 
                    DO UPDATE SET
                        domain = EXCLUDED.domain,
                        current_concept = EXCLUDED.current_concept,
                        visited_concepts = EXCLUDED.visited_concepts,
                        mastery_history = EXCLUDED.mastery_history,
                        success_streak = EXCLUDED.success_streak,
                        failure_streak = EXCLUDED.failure_streak,
                        accelerated = EXCLUDED.accelerated,
                        terminated = EXCLUDED.terminated,
                        updated_at = CURRENT_TIMESTAMP;
                    """,
                    (
                        state.candidate_id,  # id
                        state.candidate_id,  # candidate_id
                        state.domain,
                        state.current_concept,
                        visited_json,
                        mastery_json,
                        state.success_streak,
                        state.failure_streak,
                        state.accelerated,
                        state.terminated
                    )
                )
        except Exception as e:
            print(f"Error saving state to database: {e}")

    def add_progress_record(
        self,
        candidate_id: str,
        concept_id: str,
        mastery: float,
        decision: str,
        conn: Any
    ) -> None:
        """Log a traversal step to the concept_progress table."""
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO concept_progress (candidate_id, concept_id, mastery, decision, timestamp)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP);
                    """,
                    (candidate_id, concept_id, mastery, decision)
                )
        except Exception as e:
            print(f"Error saving progress record: {e}")
