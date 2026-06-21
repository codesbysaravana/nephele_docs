"""Integration regression tests for Phase 6F: Blocker Fixes for Python/SQL Graph Traversal and Loop Detection."""

import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

import chromadb

from interview_engine.chroma_store import ChromaStore
from interview_engine.database import DatabaseManager
from interview_engine.orchestrator import InterviewOrchestrator
from interview_engine.storage.postgres.service import PostgresService
from graph_traversal.traversal_engine import find_graph_path, get_next_concept
from graph_traversal.exceptions import TraversalLoopDetected, GraphConceptNotFound


class TestInterviewFlowRegression(unittest.TestCase):
    def setUp(self) -> None:
        # Isolated SQLite DB for testing
        self.pg_service = PostgresService(database_url="sqlite:///test_nephele_regression.db")
        self.pg_service.drop_tables()
        self.pg_service.create_tables()

        self.db_manager = DatabaseManager()
        self.db_manager.service = self.pg_service

        self.chroma_client = chromadb.EphemeralClient()
        self.chroma_store = ChromaStore(client=self.chroma_client)

        self.orchestrator = InterviewOrchestrator(
            db_manager=self.db_manager,
            chroma_store=self.chroma_store
        )
        self.candidate_id = "candidate_regression_test"
        
        # Clear loop tracker state
        from graph_traversal.traversal_engine import _IN_MEMORY_LOOP_TRACKER
        _IN_MEMORY_LOOP_TRACKER.clear()

    def tearDown(self) -> None:
        self.pg_service.drop_tables()

    def test_python_and_sql_domain_activation(self) -> None:
        """Verify that Python and SQL skills activate their correct domains and start at Basics."""
        # 1. Test Python activation
        resume_py = {
            "skills": ["Python"],
            "education": [],
            "projects": []
        }
        res_py = self.orchestrator.start_interview(
            candidate_id="python_cand",
            candidate_name="Py Candidate",
            candidate_email="py@example.com",
            resume_json=resume_py
        )
        self.assertEqual(res_py["domain"], "python")
        self.assertEqual(res_py["current_concept"], "Python Basics")

        # 2. Test SQL activation
        resume_sql = {
            "skills": ["SQL"],
            "education": [],
            "projects": []
        }
        res_sql = self.orchestrator.start_interview(
            candidate_id="sql_cand",
            candidate_name="SQL Candidate",
            candidate_email="sql@example.com",
            resume_json=resume_sql
        )
        self.assertEqual(res_sql["domain"], "sql")
        self.assertEqual(res_sql["current_concept"], "SQL Basics")

    def test_strict_graph_loading_missing_file(self) -> None:
        """Verify that find_graph_path raises FileNotFoundError for missing domain graph."""
        with self.assertRaises(FileNotFoundError):
            find_graph_path("non_existent_domain_graph")

    def test_unmapped_concept_raises_exception(self) -> None:
        """Verify that get_next_concept raises GraphConceptNotFound for unmapped/invalid concepts."""
        with self.assertRaises(GraphConceptNotFound):
            get_next_concept(
                domain="python",
                current_concept="Invalid Concept Name That Does Not Exist In Graph",
                mastery=0.8,
                confidence=1.0,
                candidate_id=self.candidate_id
            )

    def test_loop_detection_raises_traversal_loop_detected(self) -> None:
        """Verify that TraversalLoopDetected is raised if concept stays the same for 3 consecutive turns."""
        state = {
            "visited_concepts": ["Python Basics"],
            "mastery_history": [0.5, 0.5],
            "success_streak": 0,
            "failure_streak": 0,
            "accelerated": False,
            "terminated": False
        }
        
        # Turn 1
        res1 = get_next_concept(
            domain="python",
            current_concept="Python Basics",
            mastery=0.5, # Medium mastery -> STAY decision
            confidence=1.0,
            state=state,
            candidate_id=self.candidate_id
        )
        self.assertEqual(res1["next_concept"], "Python Basics")

        # Turn 2
        res2 = get_next_concept(
            domain="python",
            current_concept="Python Basics",
            mastery=0.5, # Medium mastery -> STAY decision
            confidence=1.0,
            state=state,
            candidate_id=self.candidate_id
        )
        self.assertEqual(res2["next_concept"], "Python Basics")

        # Turn 3 -> Loop should be detected and raise TraversalLoopDetected
        with self.assertRaises(TraversalLoopDetected):
            get_next_concept(
                domain="python",
                current_concept="Python Basics",
                mastery=0.5,
                confidence=1.0,
                state=state,
                candidate_id=self.candidate_id
            )

    def test_loop_detection_caught_by_orchestrator(self) -> None:
        """Verify that TraversalLoopDetected is caught by InterviewOrchestrator and session is failed safely."""
        # 1. Start python interview
        resume_py = {"skills": ["Python"]}
        start_res = self.orchestrator.start_interview(
            candidate_id=self.candidate_id,
            candidate_name="Py Candidate",
            candidate_email="py@example.com",
            resume_json=resume_py
        )
        q1 = start_res["question"]

        # Turn 1 (STAY)
        # Mock evaluation engine to return medium mastery 0.5 (STAY)
        with patch.object(self.orchestrator.mastery_engine, "estimate") as mock_estimate:
            mock_estimate.return_value = MagicMock(
                mastery=0.5, confidence=1.0, reasoning="STAY reasoning",
                evidence=MagicMock(matched_signals=[], missing_signals=[]),
                metadata={}
            )
            submit_res1 = self.orchestrator.submit_answer(
                candidate_id=self.candidate_id,
                concept="Python Basics",
                question=q1,
                answer="Standard python response."
            )
            self.assertEqual(submit_res1["next_concept"], "Python Basics")
            self.assertEqual(submit_res1["decision"], "stay")
            self.assertEqual(submit_res1["state"], "ACTIVE")

        # Turn 2 (STAY)
        with patch.object(self.orchestrator.mastery_engine, "estimate") as mock_estimate:
            mock_estimate.return_value = MagicMock(
                mastery=0.5, confidence=1.0, reasoning="STAY reasoning",
                evidence=MagicMock(matched_signals=[], missing_signals=[]),
                metadata={}
            )
            submit_res2 = self.orchestrator.submit_answer(
                candidate_id=self.candidate_id,
                concept="Python Basics",
                question=q1,
                answer="Standard python response."
            )
            self.assertEqual(submit_res2["next_concept"], "Python Basics")
            self.assertEqual(submit_res2["decision"], "stay")
            self.assertEqual(submit_res2["state"], "ACTIVE")

        # Turn 3 (STAY -> raises TraversalLoopDetected, caught by submit_answer, failed safely)
        with patch.object(self.orchestrator.mastery_engine, "estimate") as mock_estimate:
            mock_estimate.return_value = MagicMock(
                mastery=0.5, confidence=1.0, reasoning="STAY reasoning",
                evidence=MagicMock(matched_signals=[], missing_signals=[]),
                metadata={}
            )
            submit_res3 = self.orchestrator.submit_answer(
                candidate_id=self.candidate_id,
                concept="Python Basics",
                question=q1,
                answer="Standard python response."
            )
            # The exception should be caught, resulting in FAILED state and terminate_branch decision
            self.assertEqual(submit_res3["decision"], "terminate_branch")
            self.assertEqual(submit_res3["state"], "FAILED")

    def test_recalibrated_weights_prioritize_ml_over_helpers(self) -> None:
        """Verify that candidate skills including ML and Python/SQL activate Machine Learning first."""
        resume_json = {
            "skills": ["Machine Learning", "Python", "SQL"],
            "education": [],
            "projects": []
        }
        res = self.orchestrator.start_interview(
            candidate_id="ml_priority_cand",
            candidate_name="ML Candidate",
            candidate_email="ml@example.com",
            resume_json=resume_json
        )
        self.assertEqual(res["domain"], "machine_learning")
        self.assertEqual(res["current_concept"], "Supervised Learning")

    def test_complete_traversal_python_domain(self) -> None:
        """Verify complete traversal concept progression in Python domain succeeds without loops under high mastery."""
        resume_py = {"skills": ["Python"]}
        start_res = self.orchestrator.start_interview(
            candidate_id="traversal_cand",
            candidate_name="Py Traversal",
            candidate_email="pyt@example.com",
            resume_json=resume_py
        )
        self.assertEqual(start_res["domain"], "python")
        self.assertEqual(start_res["current_concept"], "Python Basics")

        current_concept = "Python Basics"
        visited_concepts = [current_concept]
        
        with patch.object(self.orchestrator.mastery_engine, "estimate") as mock_estimate:
            mock_estimate.return_value = MagicMock(
                mastery=0.9, confidence=1.0, reasoning="ADVANCE reasoning",
                evidence=MagicMock(matched_signals=[], missing_signals=[]),
                metadata={}
            )
            
            for i in range(15):
                res = self.orchestrator.submit_answer(
                    candidate_id="traversal_cand",
                    concept=current_concept,
                    question="Dummy question?",
                    answer="Superb answer."
                )
                if res["state"] == "COMPLETED":
                    break
                
                next_c = res["next_concept"]
                self.assertIsNotNone(next_c)
                self.assertNotEqual(next_c, current_concept, f"Should not loop on concept {current_concept}")
                current_concept = next_c
                visited_concepts.append(current_concept)
            
            # Verify the interview finished successfully
            self.assertEqual(res["state"], "COMPLETED")
