"""Integration and unit tests for Phase 6C: Production Question Intelligence Layer."""

import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import chromadb

from interview_engine.chroma_store import ChromaStore
from interview_engine.database import DatabaseManager
from interview_engine.question_layer import QuestionLayer
from interview_engine.storage.postgres.models import QuestionEffectiveness, QuestionResponseLog
from interview_engine.storage.postgres.service import PostgresService



class TestPhase6C(unittest.TestCase):
    def setUp(self) -> None:
        # Use an isolated SQLite DB for testing
        self.pg_service = PostgresService(database_url="sqlite:///test_nephele_6c.db")
        self.pg_service.drop_tables()
        self.pg_service.create_tables()

        self.db_manager = DatabaseManager()
        self.db_manager.service = self.pg_service

        # Initialize mock Chroma client and store
        self.chroma_client = chromadb.EphemeralClient()
        self.chroma_store = ChromaStore(client=self.chroma_client)

        # Initialize QuestionLayer with the test services and workspace path
        self.bank_dir = Path(__file__).parent.parent / "question_bank"
        self.qlayer = QuestionLayer(
            db_manager=self.db_manager,
            chroma_store=self.chroma_store,
            bank_dir=self.bank_dir
        )

        self.session_id = "test_session_123"

    def tearDown(self) -> None:
        self.pg_service.drop_tables()

    def test_difficulty_mapping(self) -> None:
        """Verify candidate mastery level maps correctly to question difficulty levels."""
        self.assertEqual(self.qlayer.map_difficulty(0.2), "basic")
        self.assertEqual(self.qlayer.map_difficulty(0.39), "basic")
        self.assertEqual(self.qlayer.map_difficulty(0.4), "intermediate")
        self.assertEqual(self.qlayer.map_difficulty(0.74), "intermediate")
        self.assertEqual(self.qlayer.map_difficulty(0.75), "advanced")
        self.assertEqual(self.qlayer.map_difficulty(0.99), "advanced")

    def test_difficulty_aligned_question_retrieval(self) -> None:
        """Verify static question strategy aligns to mapped mastery levels."""
        # 1. Low mastery -> Basic question
        q_basic = self.qlayer.generate_question("Overfitting", 0.2, self.session_id, strategy="static")
        self.assertEqual(q_basic["difficulty"], "basic")
        self.assertEqual(q_basic["concept"], "Overfitting")
        self.assertIn("validation loss curves", q_basic["question_text"])

        # 2. High mastery -> Advanced question
        q_adv = self.qlayer.generate_question("Overfitting", 0.9, self.session_id, strategy="static")
        self.assertEqual(q_adv["difficulty"], "advanced")
        self.assertIn("structural risk minimization", q_adv["question_text"])

    def test_exact_duplicate_prevention(self) -> None:
        """Verify that exact asked questions are detected as duplicates and paraphrased."""
        # Ask first question on Supervised Learning (basic)
        q1 = self.qlayer.generate_question("Supervised Learning", 0.2, self.session_id, strategy="static")
        
        # Persist outcome so it is recorded in session history
        self.qlayer.store_question_outcome(
            question_id=q1["question_id"],
            question_text=q1["question_text"],
            concept=q1["concept"],
            difficulty=q1["difficulty"],
            candidate_answer="Model learns from labeled data.",
            mastery_outcome=0.8,
            latency=12.5,
            session_id=self.session_id
        )

        # Check duplicate
        is_dup = self.qlayer.check_duplicate(q1["question_text"], self.session_id)
        self.assertTrue(is_dup)

        # Attempt to ask the same concept/mastery again.
        # The layer should generate an alternative wording/paraphrase of the question.
        q2 = self.qlayer.generate_question("Supervised Learning", 0.2, self.session_id, strategy="static")
        
        self.assertNotEqual(q1["question_text"], q2["question_text"])
        self.assertIn("labeled data", q2["question_text"])

    def test_semantic_duplicate_prevention_via_chroma(self) -> None:
        """Verify that semantically similar questions are detected as duplicates."""
        question_a = "What is overfitting?"
        question_b = "What is overfitting?" # identical wording for distance check mock

        # Add question_a to the Chroma questions collection (so semantic check triggers a match)
        self.chroma_store.store_question(question_a, "Overfitting", question_id="q_a")

        # Verify duplicate check returns True due to semantic cosine distance
        is_dup = self.qlayer.check_duplicate(question_b, self.session_id)
        self.assertTrue(is_dup)

    def test_adaptive_followups(self) -> None:
        """Verify follow-up questions adapt depending on candidate mastery scores."""
        # 1. Low mastery followup
        followup_low = self.qlayer.generate_followup(
            concept="Overfitting",
            question="What is overfitting?",
            candidate_answer="A model memorizes patterns.",
            mastery=0.2,
            session_id=self.session_id
        )
        self.assertEqual(followup_low["difficulty"], "basic")
        self.assertEqual(followup_low["source"], "static")
        self.assertIn("without looking at the loss curves", followup_low["question_text"])

        # 2. High mastery followup
        followup_high = self.qlayer.generate_followup(
            concept="Overfitting",
            question="What is overfitting?",
            candidate_answer="Model memorizes training data and fails to generalize.",
            mastery=0.9,
            session_id=self.session_id
        )
        self.assertEqual(followup_high["difficulty"], "advanced")
        self.assertIn("generalization bounds", followup_high["question_text"])

    def test_question_effectiveness_tracking(self) -> None:
        """Verify question outcomes are correctly saved and aggregates updated in PostgreSQL."""
        question_id = "test_q_999"
        question_text = "Explain Ridge regression."
        concept = "L2 Regularization"
        difficulty = "intermediate"

        # Log Response 1 (Score = 0.8, Latency = 10.0) -> Success (Score >= 0.5)
        self.qlayer.store_question_outcome(
            question_id=question_id,
            question_text=question_text,
            concept=concept,
            difficulty=difficulty,
            candidate_answer="Ridge regression adds L2 penalty.",
            mastery_outcome=0.8,
            latency=10.0,
            session_id=self.session_id
        )

        # Log Response 2 (Score = 0.2, Latency = 20.0) -> Failure (Score < 0.5)
        self.qlayer.store_question_outcome(
            question_id=question_id,
            question_text=question_text,
            concept=concept,
            difficulty=difficulty,
            candidate_answer="I don't know.",
            mastery_outcome=0.2,
            latency=20.0,
            session_id=self.session_id
        )

        # Check PostgreSQL database values
        with self.pg_service.session() as session:
            # Check individual logs
            logs = session.query(QuestionResponseLog).filter(QuestionResponseLog.question_id == question_id).all()
            self.assertEqual(len(logs), 2)

            # Check aggregate effectiveness metrics
            eff = session.query(QuestionEffectiveness).filter(QuestionEffectiveness.question_id == question_id).first()
            self.assertIsNotNone(eff)
            self.assertEqual(eff.total_responses, 2)
            self.assertAlmostEqual(float(eff.success_rate), 0.5) # 1 success, 1 failure
            self.assertAlmostEqual(float(eff.average_score), 0.5) # (0.8 + 0.2) / 2
            self.assertAlmostEqual(float(eff.average_latency), 15.0) # (10.0 + 20.0) / 2
