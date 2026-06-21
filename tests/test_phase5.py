"""Integration tests for the Phase 5 Knowledge Graph Interview Engine pipeline."""

from __future__ import annotations

import unittest
from pathlib import Path

import chromadb
from interview_engine.orchestrator import InterviewOrchestrator
from interview_engine.database import DatabaseManager, reset_mock_db
from interview_engine.chroma_store import ChromaStore
from interview_engine.question_layer import QuestionLayer
from interview_engine.report_generator import ReportGenerator


class TestPhase5Integration(unittest.TestCase):
    def setUp(self) -> None:
        # Reset database and initialize components
        reset_mock_db()
        self.db = DatabaseManager()
        
        # Use clean ephemeral Chroma client
        self.chroma_client = chromadb.EphemeralClient()
        
        # Clean up any existing collections to prevent test pollution in process memory
        for col_name in ["questions", "answers", "misconceptions", "concept_examples", "interview_memory"]:
            try:
                self.chroma_client.delete_collection(col_name)
            except Exception:
                pass
                
        self.chroma_store = ChromaStore(client=self.chroma_client)
        
        self.question_layer = QuestionLayer()
        self.report_gen = ReportGenerator()
        
        self.orchestrator = InterviewOrchestrator(
            db_manager=self.db,
            chroma_store=self.chroma_store,
            question_layer=self.question_layer,
            report_generator=self.report_gen
        )

        self.candidate_id = "e2e_student_123"
        self.candidate_name = "Alex Machine"
        self.candidate_email = "alex@example.com"
        
        # Setup simulated resume
        self.resume_json = {
            "skills": ["Machine Learning"],
            "education": [{"degree": "Master of Science", "field": "AI", "institution": "Tech University"}],
            "projects": [
                {
                    "name": "Predictive Modeler",
                    "technologies": ["Python", "scikit-learn"]
                }
            ]
        }

    def test_end_to_end_interview_flow(self) -> None:
        """Simulate a complete interview, testing domain activation, traversal, DB, Chroma, and reporting."""
        
        # 1. Start Interview (Verify Domain Activation and Entry Concept Wording)
        start_res = self.orchestrator.start_interview(
            candidate_id=self.candidate_id,
            candidate_name=self.candidate_name,
            candidate_email=self.candidate_email,
            resume_json=self.resume_json
        )
        
        self.assertEqual(start_res["session_id"], self.candidate_id)
        self.assertEqual(start_res["state"], "ACTIVE")
        self.assertEqual(start_res["domain"], "machine_learning")
        self.assertEqual(start_res["current_concept"], "Supervised Learning")
        self.assertIsNotNone(start_res["question"])
        
        # Verify Candidate and Session exist in PostgreSQL mock DB
        conn = self.db.get_connection()
        with conn:
            with conn.cursor() as cur:
                # Query Candidate
                cur.execute("SELECT name, email FROM candidates WHERE id = %s;", (self.candidate_id,))
                cand_row = cur.fetchone()
                self.assertIsNotNone(cand_row)
                self.assertEqual(cand_row[0], self.candidate_name)
                
                # Query Session
                cur.execute("SELECT domain, state FROM interview_sessions WHERE candidate_id = %s;", (self.candidate_id,))
                sess_row = cur.fetchone()
                self.assertIsNotNone(sess_row)
                self.assertEqual(sess_row[0], "machine_learning")
                self.assertEqual(sess_row[1], "ACTIVE")

        # 2. Candidate Answers the First Question (Supervised Learning)
        # We simulate a strong answer (high mastery >= 0.80) to advance
        ans_res_1 = self.orchestrator.submit_answer(
            candidate_id=self.candidate_id,
            concept="Supervised Learning",
            question=start_res["question"],
            answer="supervised learning"
        )
        
        self.assertEqual(ans_res_1["decision"], "advance")
        self.assertEqual(ans_res_1["next_concept"], "Train-Test Split")
        self.assertGreaterEqual(ans_res_1["mastery"], 0.80)
        self.assertIsNotNone(ans_res_1["question"])

        # 3. Candidate Answers the Second Question (Train-Test Split)
        # We simulate a strong answer to advance
        ans_res_2 = self.orchestrator.submit_answer(
            candidate_id=self.candidate_id,
            concept="Train-Test Split",
            question=ans_res_1["question"],
            answer="train-test split"
        )
        
        self.assertEqual(ans_res_2["decision"], "advance")
        self.assertEqual(ans_res_2["next_concept"], "Underfitting")
        
        # 4. Candidate Answers the Third Question (Underfitting)
        # Let's simulate a weak answer (mastery <= 0.40) to trigger a backtrack or stay
        ans_res_3 = self.orchestrator.submit_answer(
            candidate_id=self.candidate_id,
            concept="Underfitting",
            question=ans_res_2["question"],
            answer="i don't know"
        )
        
        self.assertEqual(ans_res_3["decision"], "backtrack")
        # Backtracking from Underfitting (whose prerequisite is Train-Test Split)
        # Since Train-Test Split is already visited, it falls back to Train-Test Split
        self.assertEqual(ans_res_3["next_concept"], "Train-Test Split")
        self.assertLessEqual(ans_res_3["mastery"], 0.40)

        # 5. Let's retrieve similar answers and misconceptions from Chroma DB
        # Verify that questions and answers were cached
        similar_qs = self.chroma_store.retrieve_similar_questions("Supervised Learning", limit=5)
        self.assertTrue(len(similar_qs) > 0)
        
        similar_ans = self.chroma_store.retrieve_similar_answers("supervised learning", limit=1)
        self.assertTrue(len(similar_ans) > 0)
        self.assertIn("supervised", similar_ans[0])

        # Verify misconceptions retrieve successfully
        misconceptions = self.chroma_store.retrieve_misconceptions("Supervised Learning", limit=5)
        self.assertTrue(len(misconceptions) > 0)

        # 6. Get Domain Mastery Score
        domain_mastery = self.orchestrator.get_domain_mastery(self.candidate_id, "machine_learning")
        
        # We evaluated: Supervised Learning (>=0.80), Train-Test Split (>=0.80), Underfitting (<=0.40)
        # The mastery score should reflect the simple average of these unique concept scores.
        self.assertGreater(domain_mastery, 0.0)
        self.assertLess(domain_mastery, 1.0)
        
        # Verify domain mastery persisted in PostgreSQL
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT mastery FROM domain_mastery WHERE candidate_id = %s AND domain_id = 'machine_learning';",
                    (self.candidate_id,)
                )
                mast_row = cur.fetchone()
                self.assertIsNotNone(mast_row)
                self.assertAlmostEqual(float(mast_row[0]), domain_mastery, places=4)

        # 7. Generate Evaluation Report
        report = self.orchestrator.generate_report(self.candidate_id)
        
        self.assertEqual(report["candidate_id"], self.candidate_id)
        self.assertEqual(report["candidate_name"], self.candidate_name)
        self.assertEqual(report["domain"], "machine_learning")
        self.assertIn("Supervised Learning", report["concept_scores"])
        self.assertIn("Underfitting", report["weak_concepts"])
        self.assertIn("Supervised Learning", report["strong_concepts"])
        # recommended_topics should contain the prerequisites of weak concepts (Underfitting's prereq is Train-Test Split)
        self.assertIn("Train-Test Split", report["recommended_topics"])
        self.assertIsNotNone(report["summary"])
        
        # Verify report persisted in DB
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT summary FROM reports WHERE candidate_id = %s;", (self.candidate_id,))
                rep_row = cur.fetchone()
                self.assertIsNotNone(rep_row)
                self.assertEqual(rep_row[0], report["summary"])

        print("\nSUCCESS: E2E Phase 5 Integration Test completed and verified.")


if __name__ == "__main__":
    unittest.main()
