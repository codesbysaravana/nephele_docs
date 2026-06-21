"""Decision rules for graph traversal based on mastery."""

from __future__ import annotations

from typing import Optional, Set
from .models import TraversalDecision, TraversalState
from .graph_navigator import GraphNavigator


def decide_traversal(
    state: TraversalState,
    mastery: float,
) -> TraversalDecision:
    """Apply decision rules to determine next action based on updated streaks."""
    # 1. Update success/failure streaks
    if mastery >= 0.80:
        state.success_streak += 1
        state.failure_streak = 0
    elif mastery <= 0.40:
        state.failure_streak += 1
        state.success_streak = 0
    else:
        # Medium mastery resets streaks because it's a stay
        state.success_streak = 0
        state.failure_streak = 0

    # 2. Rule: Check for branch termination (3+ failures)
    if state.failure_streak >= 3:
        state.terminated = True
        return TraversalDecision.TERMINATE_BRANCH

    # 3. Rule: Check for acceleration (3+ successes)
    if state.success_streak >= 3:
        state.accelerated = True
        # Reset success streak after accelerating to avoid double acceleration
        state.success_streak = 0
        return TraversalDecision.ACCELERATE

    # 4. Forward traversal (mastery >= 0.80)
    if mastery >= 0.80:
        return TraversalDecision.ADVANCE

    # 5. Backward traversal (mastery <= 0.40)
    if mastery <= 0.40:
        return TraversalDecision.BACKTRACK

    # 6. Stay rule (medium mastery)
    return TraversalDecision.STAY


def select_next_concept(
    decision: TraversalDecision,
    current_concept_id_or_name: str,
    navigator: GraphNavigator,
    visited: Set[str],
) -> Optional[str]:
    """Select the next concept based on the traversal decision and cycle protection."""
    current_concept = navigator.lookup_concept(current_concept_id_or_name)
    if not current_concept:
        from .exceptions import GraphConceptNotFound
        raise GraphConceptNotFound(f"Concept '{current_concept_id_or_name}' not found in the active knowledge graph.")

    current_id = current_concept.concept_id

    # If staying, keep the current concept name
    if decision == TraversalDecision.STAY:
        return current_concept.concept_name

    # Helper to convert concept IDs to concept names
    def get_display_name(cid: str) -> str:
        name = navigator.get_concept_name(cid)
        return name if name else cid

    # 1. Handle ADVANCE
    if decision == TraversalDecision.ADVANCE:
        successors = navigator.get_successors(current_id)
        # Find first unvisited successor
        for s in successors:
            s_name = get_display_name(s)
            if s_name not in visited and s not in visited:
                return s_name
        
        # Cycle Protection: All successors are visited.
        # Find the next unvisited concept in the entire domain sorted by difficulty
        all_concepts = navigator.graph.concepts
        unvisited = [
            c for c in all_concepts
            if c.concept_name not in visited and c.concept_id not in visited
        ]
        if unvisited:
            # Sort by difficulty, pick the one closest to current difficulty
            unvisited_sorted = sorted(unvisited, key=lambda c: abs(c.difficulty - current_concept.difficulty))
            return unvisited_sorted[0].concept_name
        return None

    # 2. Handle BACKTRACK
    elif decision == TraversalDecision.BACKTRACK:
        prerequisites = navigator.get_prerequisites(current_id)
        # Find first unvisited prerequisite
        for p in prerequisites:
            p_name = get_display_name(p)
            if p_name not in visited and p not in visited:
                return p_name
        
        # If all prerequisites are visited, fallback to the most relevant (difficult) prerequisite
        if prerequisites:
            return get_display_name(prerequisites[0])

        # Cycle Protection: All prerequisites are visited and no prerequisites exist.
        # Find the closest unvisited concept by difficulty
        all_concepts = navigator.graph.concepts
        unvisited = [
            c for c in all_concepts
            if c.concept_name not in visited and c.concept_id not in visited
        ]
        if unvisited:
            # Pick the easiest unvisited concept
            unvisited_sorted = sorted(unvisited, key=lambda c: c.difficulty)
            return unvisited_sorted[0].concept_name
        return None

    # 3. Handle ACCELERATE
    elif decision == TraversalDecision.ACCELERATE:
        # Get successors of current concept
        successors = navigator.get_successors(current_id)
        
        # We want to skip to advanced concepts (grand-successors)
        grand_successors = []
        for s in successors:
            for gs in navigator.get_successors(s):
                if gs != current_id:
                    grand_successors.append(gs)

        # Remove duplicates while keeping order
        seen_gs = set()
        unique_gs = []
        for gs in grand_successors:
            if gs not in seen_gs:
                seen_gs.add(gs)
                unique_gs.append(gs)

        # Sort grand successors by difficulty ascending
        unique_gs = sorted(unique_gs, key=lambda cid: navigator.get_concept_difficulty(cid) or 0.0)

        # Find first unvisited grand successor
        for gs in unique_gs:
            gs_name = get_display_name(gs)
            if gs_name not in visited and gs not in visited:
                return gs_name

        # Fallback to unvisited immediate successors
        for s in successors:
            s_name = get_display_name(s)
            if s_name not in visited and s not in visited:
                return s_name

        # Fallback to closest unvisited concept in entire domain with higher difficulty
        all_concepts = navigator.graph.concepts
        unvisited_higher = [
            c for c in all_concepts
            if c.concept_name not in visited and c.concept_id not in visited and c.difficulty > current_concept.difficulty
        ]
        if unvisited_higher:
            unvisited_higher_sorted = sorted(unvisited_higher, key=lambda c: c.difficulty)
            return unvisited_higher_sorted[0].concept_name

        # Fallback to any unvisited concept
        unvisited = [
            c for c in all_concepts
            if c.concept_name not in visited and c.concept_id not in visited
        ]
        if unvisited:
            unvisited_sorted = sorted(unvisited, key=lambda c: c.difficulty)
            return unvisited_sorted[0].concept_name

        return None

    return get_display_name(current_id)
