"""Graph traversal engine for interview progression."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

from knowledge_graph.graph_loader import load_graph_document
from .decision_rules import decide_traversal, select_next_concept
from .graph_navigator import GraphNavigator
from .models import TraversalDecision, TraversalResult, TraversalState
from .exceptions import TraversalLoopDetected
from .state_tracker import StateTracker

logger = logging.getLogger(__name__)

# In-memory loop tracker for fallback/testing when no database connection is present
_IN_MEMORY_LOOP_TRACKER = {}


def find_graph_path(domain: str) -> Path:
    """Resolve graph file path based on the domain name."""
    base_dir = Path(__file__).parent.parent / "knowledge_graph"
    candidates = [
        base_dir / "examples" / f"{domain}_graph.json",
        base_dir / "examples" / f"{domain}.json",
        base_dir / f"{domain}.json",
    ]
    for cand in candidates:
        if cand.exists():
            return cand
    
    # Raise error if no matching graph file is found
    raise FileNotFoundError(f"Knowledge graph document for domain '{domain}' not found.")


# Module-level tracker instance for module-level functions
_tracker = StateTracker()


def get_next_concept(
    domain: str,
    current_concept: str,
    mastery: float,
    confidence: float,
    state: Optional[dict] = None,
    candidate_id: str = "default_candidate",
    conn: Optional[Any] = None
) -> dict:
    """Decide next concept, updating streaks and state, and return the decision dictionary."""
    graph_path = find_graph_path(domain)
    graph = load_graph_document(graph_path)
    navigator = GraphNavigator(graph)

    # Check if current concept exists in active graph
    if not navigator.lookup_concept(current_concept):
        from .exceptions import GraphConceptNotFound
        raise GraphConceptNotFound(f"Concept '{current_concept}' not found in domain '{domain}' graph.")

    # 1. Resolve State
    if state is not None:
        t_state = TraversalState.from_dict(
            candidate_id=candidate_id,
            domain=domain,
            current_concept=current_concept,
            d=state
        )
    else:
        t_state = _tracker.get_session(candidate_id, conn)
        if not t_state:
            t_state = TraversalState(
                candidate_id=candidate_id,
                domain=domain,
                current_concept=current_concept,
                visited_concepts=[current_concept],
            )

    # 2. Check if already terminated
    if t_state.terminated:
        res = terminate_branch()
        if state is not None:
            state.update(t_state.to_dict())
        return res

    # 3. Decide traversal action
    decision = decide_traversal(t_state, mastery)

    # 4. Handle decision to find next concept
    next_concept = None
    reason = ""

    if decision == TraversalDecision.ADVANCE:
        next_concept = advance(t_state.current_concept, navigator, set(t_state.visited_concepts))
        reason = "High mastery"
    elif decision == TraversalDecision.BACKTRACK:
        next_concept = backtrack(t_state.current_concept, navigator, set(t_state.visited_concepts))
        reason = "Low mastery"
    elif decision == TraversalDecision.STAY:
        next_concept = t_state.current_concept
        reason = "Medium mastery"
    elif decision == TraversalDecision.ACCELERATE:
        next_concept = accelerate(t_state.current_concept, navigator, set(t_state.visited_concepts))
        reason = "High mastery"
    elif decision == TraversalDecision.TERMINATE_BRANCH:
        res = terminate_branch()
        if state is not None:
            state.update(t_state.to_dict())
            state["terminated"] = True
        return res

    # 5. Update state
    evaluated_concept = t_state.current_concept
    t_state.update_after_decision(next_concept, mastery)

    # If state was passed as dict, sync it back
    if state is not None:
        state.update(t_state.to_dict())
        state["accelerated"] = t_state.accelerated
        state["terminated"] = t_state.terminated

    # Loop detection check
    resolved_next = next_concept or t_state.current_concept
    if resolved_next == evaluated_concept:
        consecutive_count = 1
        db_queried = False
        if conn and candidate_id:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT concept_id FROM concept_evaluations WHERE candidate_id = %s ORDER BY id DESC LIMIT 5;",
                        (candidate_id,)
                    )
                    rows = cur.fetchall()
                    consecutive_count = 0
                    for row in rows:
                        if row[0] == evaluated_concept:
                            consecutive_count += 1
                        else:
                            break
                    db_queried = True
            except Exception as e:
                logger.error(f"Error querying loop detection stats: {e}")
        
        if not db_queried:
            key = (candidate_id, evaluated_concept)
            consecutive_count = _IN_MEMORY_LOOP_TRACKER.get(key, 0) + 1
            _IN_MEMORY_LOOP_TRACKER[key] = consecutive_count
            
        if consecutive_count >= 3:
            raise TraversalLoopDetected(f"Infinite traversal loop detected on concept '{evaluated_concept}' for candidate '{candidate_id}'.")
    else:
        if candidate_id:
            for k in list(_IN_MEMORY_LOOP_TRACKER.keys()):
                if k[0] == candidate_id:
                    _IN_MEMORY_LOOP_TRACKER.pop(k, None)

    # 6. Save using StateTracker
    _tracker.save_session(t_state, conn, decision.value, mastery, concept_id=evaluated_concept)

    # 7. Format output
    result_dict = {
        "decision": decision.value,
        "next_concept": next_concept
    }
    if reason:
        result_dict["reason"] = reason

    return result_dict


def advance(concept: str, navigator: GraphNavigator, visited: Set[str]) -> Optional[str]:
    """Determine the next concept during forward traversal."""
    return select_next_concept(TraversalDecision.ADVANCE, concept, navigator, visited)


def backtrack(concept: str, navigator: GraphNavigator, visited: Set[str]) -> Optional[str]:
    """Determine the next concept during backward traversal."""
    return select_next_concept(TraversalDecision.BACKTRACK, concept, navigator, visited)


def terminate_branch(reason: str = "Insufficient foundation") -> dict:
    """Return a branch termination decision."""
    return {
        "decision": TraversalDecision.TERMINATE_BRANCH.value,
        "reason": reason
    }


def accelerate(concept: str, navigator: GraphNavigator, visited: Set[str]) -> Optional[str]:
    """Determine the next concept during acceleration."""
    return select_next_concept(TraversalDecision.ACCELERATE, concept, navigator, visited)


class GraphTraversalEngine:
    """Navigates the knowledge graph based on mastery estimates."""

    def __init__(self, graph_path: str | Path) -> None:
        self.graph = load_graph_document(graph_path)
        self.navigator = GraphNavigator(self.graph)
        self.tracker = StateTracker()

    def start_traversal(self, candidate_id: str, domain: str, entry_concept: str) -> TraversalState:
        """Initialize a new traversal session."""
        concept_node = self.navigator.lookup_concept(entry_concept)
        concept_name = concept_node.concept_name if concept_node else entry_concept
        
        state = TraversalState(
            candidate_id=candidate_id,
            domain=domain,
            current_concept=concept_name,
            visited_concepts=[concept_name],
        )
        self.tracker.save_session(state)
        return state

    def decide_next(
        self,
        candidate_id: str,
        mastery: float,
        confidence: float = 1.0,
        conn: Optional[Any] = None
    ) -> TraversalResult:
        """Decide the next concept based on current mastery and update session state."""
        state = self.tracker.get_session(candidate_id, conn)
        if not state:
            raise ValueError(f"No traversal session for candidate {candidate_id}")

        if state.terminated:
            return TraversalResult(
                decision=TraversalDecision.TERMINATE_BRANCH,
                next_concept=None,
                reason="Branch terminated due to insufficient foundation."
            )

        # Decide traversal and next concept
        decision = decide_traversal(state, mastery)
        
        next_concept = None
        if decision == TraversalDecision.ADVANCE:
            next_concept = self.advance(state.current_concept, set(state.visited_concepts))
            reason = f"High mastery ({mastery:.2f}), advancing to next concept."
        elif decision == TraversalDecision.BACKTRACK:
            next_concept = self.backtrack(state.current_concept, set(state.visited_concepts))
            reason = f"Low mastery ({mastery:.2f}), reviewing prerequisite concept."
        elif decision == TraversalDecision.STAY:
            next_concept = state.current_concept
            reason = f"Medium mastery ({mastery:.2f}), staying on current concept."
        elif decision == TraversalDecision.ACCELERATE:
            next_concept = self.accelerate(state.current_concept, set(state.visited_concepts))
            reason = "Accelerating: Strong consecutive mastery demonstrated."
        elif decision == TraversalDecision.TERMINATE_BRANCH:
            next_concept = None
            reason = "Terminating branch: Too many consecutive failures indicate insufficient foundation."
        else:
            next_concept = None
            reason = "Interview ended."

        # Update and persist state
        evaluated_concept = state.current_concept
        state.update_after_decision(next_concept, mastery)
        self.tracker.save_session(state, conn, decision.value, mastery, concept_id=evaluated_concept)

        return TraversalResult(
            decision=decision,
            next_concept=next_concept,
            reason=reason,
            metadata={
                "success_streak": state.success_streak,
                "failure_streak": state.failure_streak,
                "accelerated": state.accelerated,
                "terminated": state.terminated
            }
        )

    def advance(self, concept: str, visited: Set[str]) -> Optional[str]:
        return advance(concept, self.navigator, visited)

    def backtrack(self, concept: str, visited: Set[str]) -> Optional[str]:
        return backtrack(concept, self.navigator, visited)

    def terminate_branch(self, reason: str = "Insufficient foundation") -> dict:
        return terminate_branch(reason)

    def accelerate(self, concept: str, visited: Set[str]) -> Optional[str]:
        return accelerate(concept, self.navigator, visited)
