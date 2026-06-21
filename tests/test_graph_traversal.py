"""Unit tests for Graph Traversal Engine (Phase 4)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

from graph_traversal import (
    GraphTraversalEngine,
    get_next_concept,
    TraversalDecision,
    TraversalState,
)


class TestGraphTraversal(unittest.TestCase):
    def setUp(self) -> None:
        # Load the example ML graph
        self.graph_path = Path(__file__).parent.parent / "knowledge_graph" / "examples" / "machine_learning_graph.json"
        self.engine = GraphTraversalEngine(graph_path=self.graph_path)
        self.candidate_id = "test_student"

    def test_case_1_advance(self) -> None:
        """Case 1: Current concept: Overfitting, mastery: 0.90 -> decision: advance, next_concept: Regularization"""
        state = self.engine.start_traversal(
            candidate_id=self.candidate_id,
            domain="machine_learning",
            entry_concept="Overfitting",
        )
        result = self.engine.decide_next(candidate_id=self.candidate_id, mastery=0.90)
        res_dict = result.to_dict()

        self.assertEqual(res_dict["decision"], "advance")
        self.assertEqual(res_dict["next_concept"], "Regularization")

    def test_case_2_backtrack(self) -> None:
        """Case 2: Current concept: Overfitting, mastery: 0.20 -> decision: backtrack, next_concept: Train-Test Split"""
        state = self.engine.start_traversal(
            candidate_id=self.candidate_id,
            domain="machine_learning",
            entry_concept="Overfitting",
        )
        result = self.engine.decide_next(candidate_id=self.candidate_id, mastery=0.20)
        res_dict = result.to_dict()

        self.assertEqual(res_dict["decision"], "backtrack")
        self.assertEqual(res_dict["next_concept"], "Train-Test Split")

    def test_case_3_stay(self) -> None:
        """Case 3: Current concept: Overfitting, mastery: 0.60 -> decision: stay, next_concept: Overfitting"""
        state = self.engine.start_traversal(
            candidate_id=self.candidate_id,
            domain="machine_learning",
            entry_concept="Overfitting",
        )
        result = self.engine.decide_next(candidate_id=self.candidate_id, mastery=0.60)
        res_dict = result.to_dict()

        self.assertEqual(res_dict["decision"], "stay")
        self.assertEqual(res_dict["next_concept"], "Overfitting")

    def test_case_4_terminate_branch(self) -> None:
        """Case 4: 3 consecutive failures -> decision: terminate_branch"""
        state = self.engine.start_traversal(
            candidate_id=self.candidate_id,
            domain="machine_learning",
            entry_concept="Overfitting",
        )
        # 1st failure
        result = self.engine.decide_next(candidate_id=self.candidate_id, mastery=0.20)
        self.assertEqual(result.decision, TraversalDecision.BACKTRACK)

        # 2nd failure
        result = self.engine.decide_next(candidate_id=self.candidate_id, mastery=0.20)
        self.assertEqual(result.decision, TraversalDecision.BACKTRACK)

        # 3rd failure
        result = self.engine.decide_next(candidate_id=self.candidate_id, mastery=0.20)
        res_dict = result.to_dict()
        self.assertEqual(res_dict["decision"], "terminate_branch")
        self.assertEqual(res_dict["reason"], "Terminating branch: Too many consecutive failures indicate insufficient foundation.")

    def test_acceleration_rule(self) -> None:
        """Test acceleration rule: 3 consecutive successes -> decision: accelerate"""
        state = self.engine.start_traversal(
            candidate_id=self.candidate_id,
            domain="machine_learning",
            entry_concept="Overfitting",
        )
        # 1st success
        result = self.engine.decide_next(candidate_id=self.candidate_id, mastery=0.90)
        self.assertEqual(result.decision, TraversalDecision.ADVANCE)
        self.assertEqual(result.next_concept, "Regularization")

        # 2nd success
        result = self.engine.decide_next(candidate_id=self.candidate_id, mastery=0.90)
        self.assertEqual(result.decision, TraversalDecision.ADVANCE)
        self.assertEqual(result.next_concept, "L1 Regularization")

        # 3rd success -> Should accelerate
        result = self.engine.decide_next(candidate_id=self.candidate_id, mastery=0.90)
        res_dict = result.to_dict()
        self.assertEqual(res_dict["decision"], "accelerate")
        self.assertIsNotNone(res_dict["next_concept"])

    def test_cycle_protection(self) -> None:
        """Test cycle protection: ensure it doesn't get stuck in visited loops."""
        # Initialize session
        state = self.engine.start_traversal(
            candidate_id=self.candidate_id,
            domain="machine_learning",
            entry_concept="Overfitting",
        )
        # Mark Regularization and Bias-Variance Tradeoff as visited manually
        state.visited_concepts.extend(["Regularization", "Bias Variance Tradeoff"])

        # Advance should skip visited successors and pick the closest unvisited by difficulty
        result = self.engine.decide_next(candidate_id=self.candidate_id, mastery=0.95)
        res_dict = result.to_dict()

        self.assertEqual(res_dict["decision"], "advance")
        # Overfitting is 0.35, next unvisited should be Model Evaluation Metrics (0.35)
        self.assertEqual(res_dict["next_concept"], "Model Evaluation Metrics")

    def test_get_next_concept_api(self) -> None:
        """Test the get_next_concept module-level function."""
        # Define state dict matching traversal state format
        state = {
            "visited_concepts": ["Overfitting"],
            "mastery_history": [],
            "success_streak": 0,
            "failure_streak": 0
        }

        # Call get_next_concept
        res = get_next_concept(
            domain="machine_learning",
            current_concept="Overfitting",
            mastery=0.85,
            confidence=0.90,
            state=state,
            candidate_id="api_student"
        )

        self.assertEqual(res["decision"], "advance")
        self.assertEqual(res["next_concept"], "Regularization")
        self.assertEqual(state["success_streak"], 1)
        self.assertIn("Regularization", state["visited_concepts"])

    def test_db_persistence(self) -> None:
        """Test PostgreSQL state tracker with a mock connection."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock load from DB returning empty
        mock_cursor.fetchone.return_value = None

        # Call get_next_concept with mock db conn
        res = get_next_concept(
            domain="machine_learning",
            current_concept="Overfitting",
            mastery=0.20,
            confidence=0.90,
            candidate_id="db_student",
            conn=mock_conn
        )

        # Assert insert statements were executed
        self.assertTrue(mock_cursor.execute.called)
        
        # Verify first call logged correctly
        self.assertEqual(res["decision"], "backtrack")
        self.assertEqual(res["next_concept"], "Train-Test Split")


if __name__ == "__main__":
    unittest.main()
