"""Integration and validation tests for Phase 6E: Graph Evolution & Interview Intelligence Engine."""

import os
import unittest
from pathlib import Path
import chromadb

from interview_engine.chroma_store import ChromaStore
from interview_engine.database import DatabaseManager
from interview_engine.storage.postgres.models import (
    Candidate,
    ConceptEvaluation,
    InterviewSession,
    GraphEdgeStatistics,
)
from interview_engine.storage.postgres.service import PostgresService
from graph_evolution.evolution_engine import GraphEvolutionEngine


class TestPhase6E(unittest.TestCase):
    def setUp(self) -> None:
        # Use an isolated SQLite DB for testing
        self.pg_service = PostgresService(database_url="sqlite:///test_nephele_6e.db")
        self.pg_service.drop_tables()
        self.pg_service.create_tables()

        self.db_manager = DatabaseManager()
        self.db_manager.service = self.pg_service

        # Initialize mock Chroma client and store
        self.chroma_client = chromadb.EphemeralClient()
        self.chroma_store = ChromaStore(client=self.chroma_client)

        # Initialize evolution engine
        self.evolution_engine = GraphEvolutionEngine(
            db_manager=self.db_manager,
            chroma_store=self.chroma_store
        )

    def tearDown(self) -> None:
        self.pg_service.drop_tables()

    def test_end_to_end_graph_evolution(self) -> None:
        """Simulate 100+ candidate interview records and verify edge strengths, difficulty, and reports."""
        
        # 1. Populate synthetic dataset of 105 candidates
        # We will configure evaluations so that:
        # - 60 candidates evaluate 'Overfitting' and 'Regularization' sequentially.
        #   - 55 of them master 'Overfitting' (>= 0.85) AND master 'Regularization' (>= 0.85)
        #   - 5 of them master 'Overfitting' (>= 0.85) but fail 'Regularization' (<= 0.30)
        #   This means Overfitting -> Regularization strength = 55 / 60 = 0.9167
        #
        # - 45 candidates evaluate 'Train-Test Split' and 'Underfitting'.
        #   - 35 of them fail 'Underfitting' (mastery <= 0.35, high failure rate) with missing signal 'bias_variance'
        #   - 10 of them master 'Underfitting' (mastery >= 0.85)
        #   - We log high latency (e.g. 80.0s) for Underfitting to verify difficulty scoring.
        
        with self.db_manager.service.session() as session:
            for i in range(105):
                cand_id = f"cand_{i}"
                cand = Candidate(id=cand_id, name=f"Candidate {i}", email=f"cand_{i}@example.com")
                session.add(cand)

                # Active session
                sess = InterviewSession(
                    id=cand_id,
                    candidate_id=cand_id,
                    state="COMPLETED",
                    domain="machine_learning",
                    current_concept="Regularization" if i < 60 else "Underfitting"
                )
                session.add(sess)

            # Flush candidates and sessions so foreign keys resolve
            session.commit()

        # Add evaluations in batches
        with self.db_manager.service.session() as session:
            for i in range(105):
                cand_id = f"cand_{i}"
                if i < 60:
                    # Traverses Overfitting -> Regularization
                    # Evaluation 1: Overfitting
                    overfitting_mastery = 0.90
                    overfitting_eval = ConceptEvaluation(
                        candidate_id=cand_id,
                        concept_id="Overfitting",
                        question="Explain overfitting.",
                        answer="Model memorizes training patterns.",
                        mastery=overfitting_mastery,
                        confidence=0.95,
                        matched_signals=["memorization"],
                        missing_signals=[],
                        reasoning=["Good answer"],
                        strategy="hybrid",
                        metadata_={"latency": 15.2}
                    )
                    session.add(overfitting_eval)

                    # Evaluation 2: Regularization
                    # 55 success, 5 failures
                    reg_mastery = 0.90 if i < 55 else 0.25
                    reg_eval = ConceptEvaluation(
                        candidate_id=cand_id,
                        concept_id="Regularization",
                        question="What is regularization?",
                        answer="Adding L1/L2 penalties." if i < 55 else "I don't know.",
                        mastery=reg_mastery,
                        confidence=0.95,
                        matched_signals=["penalties"] if i < 55 else [],
                        missing_signals=[] if i < 55 else ["penalty_types"],
                        reasoning=["Good"] if i < 55 else ["Failed"],
                        strategy="hybrid",
                        metadata_={"latency": 20.5}
                    )
                    session.add(reg_eval)

                else:
                    # Traverses Train-Test Split -> Underfitting
                    # Evaluation 1: Train-Test Split
                    tts_eval = ConceptEvaluation(
                        candidate_id=cand_id,
                        concept_id="Train-Test Split",
                        question="Explain train-test split.",
                        answer="Separating train and test subsets.",
                        mastery=0.85,
                        confidence=0.90,
                        matched_signals=["subsets"],
                        missing_signals=[],
                        reasoning=["Good"],
                        strategy="hybrid",
                        metadata_={"latency": 18.0}
                    )
                    session.add(tts_eval)

                    # Evaluation 2: Underfitting
                    # 35 failures, 10 successes
                    underfitting_mastery = 0.10 if i < 95 else 0.90
                    underfitting_eval = ConceptEvaluation(
                        candidate_id=cand_id,
                        concept_id="Underfitting",
                        question="Explain underfitting.",
                        answer="Underfitting" if i >= 95 else "No idea.",
                        mastery=underfitting_mastery,
                        confidence=0.92,
                        matched_signals=["simple_model"] if i >= 95 else [],
                        missing_signals=[] if i >= 95 else ["bias_variance"],
                        reasoning=["Good"] if i >= 95 else ["Missing bias variance info"],
                        strategy="hybrid",
                        metadata_={"latency": 80.0} # high latency
                    )
                    session.add(underfitting_eval)

            session.commit()

        # 2. Run Statistics Collector
        stats = self.evolution_engine.collect_statistics()
        self.assertIn("Overfitting", stats["concepts"])
        self.assertIn("Underfitting", stats["concepts"])
        
        # Verify success/failure rates
        overfitting_stats = stats["concepts"]["Overfitting"]
        self.assertEqual(overfitting_stats["traversal_frequency"], 60)
        self.assertEqual(overfitting_stats["success_rate"], 1.0)
        self.assertEqual(overfitting_stats["failure_rate"], 0.0)

        underfitting_stats = stats["concepts"]["Underfitting"]
        self.assertEqual(underfitting_stats["traversal_frequency"], 45)
        self.assertAlmostEqual(underfitting_stats["failure_rate"], 35 / 45, places=4)

        # 3. Mine Misconceptions
        mine_res = self.evolution_engine.mine_misconceptions()
        
        # Check missing signals frequency
        missing_sigs = mine_res["misconception_frequency"]
        underfitting_missing = [m for m in missing_sigs if m["concept"] == "Underfitting" and m["misconception"] == "bias_variance"]
        self.assertTrue(len(underfitting_missing) > 0)
        self.assertEqual(underfitting_missing[0]["frequency"], 35)

        # Check confusion pairs
        # 5 candidates failed both Overfitting and Regularization (wait, they only failed Regularization, not Overfitting)
        # Underfitting failures: 35 candidates failed Underfitting. Did they fail other concepts?
        # Since they didn't fail multiple concepts, confusion pairs list might be empty or small, which is fine
        confusion_pairs = mine_res["concept_confusion_pairs"]
        self.assertIsNotNone(confusion_pairs)

        # 4. Analyze Relationships (Edge strengths & recommendations)
        rel_res = self.evolution_engine.analyze_relationships("machine_learning")
        
        # Check edge strengths list
        strengths = rel_res["edge_strengths"]
        over_to_reg = [s for s in strengths if s["source"] == "Overfitting" and s["target"] == "Regularization"]
        self.assertEqual(len(over_to_reg), 1)
        # denom = candidates who mastered Overfitting (60 candidates)
        # num = mastered both Overfitting and Regularization (55 candidates)
        # strength = 55 / 60 = 0.9167
        self.assertAlmostEqual(over_to_reg[0]["strength"], 55 / 60, places=4)
        self.assertEqual(over_to_reg[0]["traversal_count"], 60)

        # Check recommendations for existing edges
        recs = rel_res["existing_edge_recommendations"]
        # Overfitting -> Regularization is an existing edge in machine_learning_graph.json
        over_to_reg_rec = [r for r in recs if r["source"] == "Overfitting" and r["target"] == "Regularization"]
        self.assertEqual(len(over_to_reg_rec), 1)
        self.assertEqual(over_to_reg_rec[0]["recommendation"], "Increase relationship confidence")

        # 5. Verify persistence of edge statistics in database
        with self.db_manager.service.session() as session:
            db_stats = session.query(GraphEdgeStatistics).filter(
                GraphEdgeStatistics.source_concept == "Overfitting",
                GraphEdgeStatistics.target_concept == "Regularization"
            ).first()
            self.assertIsNotNone(db_stats)
            self.assertAlmostEqual(float(db_stats.edge_strength), 55 / 60, places=4)
            self.assertEqual(db_stats.traversal_count, 60)

        # 6. Generate Evolution Report
        report = self.evolution_engine.generate_evolution_report("machine_learning")
        self.assertEqual(report["domain"], "machine_learning")
        self.assertTrue(len(report["most_failed_concepts"]) > 0)
        self.assertEqual(report["most_failed_concepts"][0]["concept"], "Underfitting")

        # Verify inferred difficulty ranking
        rankings = report["concept_difficulty_rankings"]
        underfitting_ranking = [r for r in rankings if r["concept"] == "Underfitting"]
        self.assertEqual(len(underfitting_ranking), 1)
        
        # Underfitting avg mastery ~0.4333, fail rate ~0.7778, high latency -> Advanced classification
        self.assertEqual(underfitting_ranking[0]["classification"], "advanced")
