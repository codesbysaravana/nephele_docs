"""Example runner for Phase 4 graph traversal engine demonstrating success criteria."""

from __future__ import annotations

import json
from pathlib import Path
from graph_traversal import get_next_concept


def run_examples() -> None:
    print("=== RUNNING PHASE 4 GRAPH TRAVERSAL CASES ===\n")

    # Case 1: Overfitting with 0.90 mastery -> Advance to Regularization
    print("Case 1: Mastery 0.90")
    state_1 = {
        "visited_concepts": ["Overfitting"],
        "mastery_history": [],
        "success_streak": 0,
        "failure_streak": 0
    }
    result_1 = get_next_concept(
        domain="machine_learning",
        current_concept="Overfitting",
        mastery=0.90,
        confidence=0.90,
        state=state_1,
        candidate_id="student_1"
    )
    print(f"INPUT State: {json.dumps(state_1)}")
    print(f"OUTPUT Decision: {json.dumps(result_1, indent=2)}")
    print("-" * 50)

    # Case 2: Overfitting with 0.20 mastery -> Backtrack to Train-Test Split
    print("Case 2: Mastery 0.20")
    state_2 = {
        "visited_concepts": ["Overfitting"],
        "mastery_history": [],
        "success_streak": 0,
        "failure_streak": 0
    }
    result_2 = get_next_concept(
        domain="machine_learning",
        current_concept="Overfitting",
        mastery=0.20,
        confidence=0.90,
        state=state_2,
        candidate_id="student_2"
    )
    print(f"INPUT State: {json.dumps(state_2)}")
    print(f"OUTPUT Decision: {json.dumps(result_2, indent=2)}")
    print("-" * 50)

    # Case 3: Overfitting with 0.60 mastery -> Stay on Overfitting
    print("Case 3: Mastery 0.60")
    state_3 = {
        "visited_concepts": ["Overfitting"],
        "mastery_history": [],
        "success_streak": 0,
        "failure_streak": 0
    }
    result_3 = get_next_concept(
        domain="machine_learning",
        current_concept="Overfitting",
        mastery=0.60,
        confidence=0.90,
        state=state_3,
        candidate_id="student_3"
    )
    print(f"INPUT State: {json.dumps(state_3)}")
    print(f"OUTPUT Decision: {json.dumps(result_3, indent=2)}")
    print("-" * 50)

    # Case 4: 3 consecutive failures -> Terminate branch
    print("Case 4: Three consecutive failures")
    state_4 = {
        "visited_concepts": ["Overfitting"],
        "mastery_history": [],
        "success_streak": 0,
        "failure_streak": 0
    }
    
    # 1st failure (mastery 0.20)
    print("  Triggering failure 1 (mastery=0.20)...")
    res_f1 = get_next_concept(
        domain="machine_learning",
        current_concept="Overfitting",
        mastery=0.20,
        confidence=0.90,
        state=state_4,
        candidate_id="student_4"
    )
    print(f"  Decision: {res_f1['decision']}, Next: {res_f1.get('next_concept')}, Streaks: success={state_4['success_streak']}, failure={state_4['failure_streak']}")

    # 2nd failure (mastery 0.20)
    current_concept_2 = res_f1.get('next_concept', 'Overfitting')
    print(f"  Triggering failure 2 on '{current_concept_2}' (mastery=0.20)...")
    res_f2 = get_next_concept(
        domain="machine_learning",
        current_concept=current_concept_2,
        mastery=0.20,
        confidence=0.90,
        state=state_4,
        candidate_id="student_4"
    )
    print(f"  Decision: {res_f2['decision']}, Next: {res_f2.get('next_concept')}, Streaks: success={state_4['success_streak']}, failure={state_4['failure_streak']}")

    # 3rd failure (mastery 0.20)
    current_concept_3 = res_f2.get('next_concept', 'Train-Test Split')
    print(f"  Triggering failure 3 on '{current_concept_3}' (mastery=0.20)...")
    res_f3 = get_next_concept(
        domain="machine_learning",
        current_concept=current_concept_3,
        mastery=0.20,
        confidence=0.90,
        state=state_4,
        candidate_id="student_4"
    )
    print(f"  Decision: {res_f3['decision']}, Next: {res_f3.get('next_concept')}, Streaks: success={state_4['success_streak']}, failure={state_4['failure_streak']}")
    print(f"\nFinal Case 4 Output:")
    print(json.dumps(res_f3, indent=2))
    print("-" * 50)


if __name__ == "__main__":
    run_examples()
