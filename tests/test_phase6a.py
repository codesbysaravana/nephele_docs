"""Integration tests for Phase 6A: PostgreSQL (SQLAlchemy 2.x), repositories, and ChromaDB services."""

from __future__ import annotations

import unittest
from datetime import datetime

import chromadb
from sqlalchemy import text

from interview_engine.database import DatabaseManager, reset_mock_db
from interview_engine.chroma_store import ChromaStore
from interview_engine.storage.postgres.service import PostgresService
from interview_engine.storage.postgres.models import (
    Base,
    Candidate,
    ResumeData,
    InterviewSession,
    ConceptProgress,
    ConceptEvaluation,
    DomainMastery,
    InterviewReport,
    GraphStatistics,
)
from interview_engine.storage.postgres.repositories import (
    CandidateRepository,
    InterviewRepository,
    MasteryRepository,
    ReportRepository,
    GraphStatsRepository,
)
from interview_engine.storage.chroma.service import ChromaService
from interview_engine.storage.persistence_service import PersistenceService


class TestPhase6APersistence(unittest.TestCase):
    def setUp(self) -> None:
        # Use a clean, isolated SQLite DB for testing
        self.pg_service = PostgresService(database_url="sqlite:///test_nephele.db")
        self.pg_service.drop_tables()
        self.pg_service.create_tables()

        # Initialize test ChromaDB in-memory client and service
        self.chroma_client = chromadb.EphemeralClient()
        
        # Clean up any existing collections to prevent test pollution in process memory
        for col_name in ["questions", "answers", "misconceptions", "concept_examples", "interview_memory"]:
            try:
                self.chroma_client.delete_collection(col_name)
            except Exception:
                pass
                
        self.chroma_service = ChromaService(client=self.chroma_client)

        # Initialize Unified Persistence Service
        self.persistence = PersistenceService(self.pg_service, self.chroma_service)

        self.candidate_id = "test_cand_999"
        self.candidate_name = "Jane Architect"
        self.candidate_email = "jane@nephele.ai"

    def tearDown(self) -> None:
        self.pg_service.drop_tables()

    def test_postgres_repository_operations(self) -> None:
        """Test candidate, resume, session, progress, evaluation, mastery, and report repositories."""
        with self.pg_service.session() as session:
            cand_repo, int_repo, mast_repo, rep_repo, stats_repo = self.persistence.get_repositories(session)

            # 1. Create and save Candidate
            cand = Candidate(id=self.candidate_id, name=self.candidate_name, email=self.candidate_email)
            cand_repo.save(cand)
            
            # Verify candidate saved
            db_cand = cand_repo.get_by_id(self.candidate_id)
            self.assertIsNotNone(db_cand)
            self.assertEqual(db_cand.name, self.candidate_name)

            # 2. Save candidate's ResumeData
            resume = ResumeData(
                candidate_id=self.candidate_id,
                resume_text="Experienced ML Architect.",
                skills={"languages": ["Python", "C++"]},
                education=[{"degree": "PhD"}],
                projects=[{"name": "Nephele"}]
            )
            cand_repo.save_resume(resume)
            
            # Verify resume saved
            db_resume = cand_repo.get_resume(self.candidate_id)
            self.assertIsNotNone(db_resume)
            self.assertEqual(db_resume.resume_text, "Experienced ML Architect.")
            self.assertEqual(db_resume.skills["languages"], ["Python", "C++"])

            # 3. Create and save InterviewSession
            sess = InterviewSession(
                id="sess_uuid_1",
                candidate_id=self.candidate_id,
                state="ACTIVE",
                domain="machine_learning",
                current_concept="Supervised Learning",
                visited_concepts=["Supervised Learning"],
                mastery_history=[0.85],
                success_streak=1,
                failure_streak=0,
                accelerated=False,
                terminated=False
            )
            int_repo.save_session(sess)
            
            # Verify session saved
            db_sess = int_repo.get_session("sess_uuid_1")
            self.assertIsNotNone(db_sess)
            self.assertEqual(db_sess.current_concept, "Supervised Learning")
            self.assertEqual(db_sess.visited_concepts, ["Supervised Learning"])

            # 4. Save ConceptProgress
            progress = ConceptProgress(
                candidate_id=self.candidate_id,
                concept_id="Supervised Learning",
                mastery=0.85,
                decision="advance"
            )
            int_repo.add_concept_progress(progress)

            # 5. Save ConceptEvaluation
            evaluation = ConceptEvaluation(
                candidate_id=self.candidate_id,
                concept_id="Supervised Learning",
                question="What is Supervised Learning?",
                answer="Learning with labeled data.",
                mastery=0.90,
                confidence=1.0,
                matched_signals=["labeled_data"],
                missing_signals=[],
                reasoning=["Excellent answer."],
                strategy="hybrid",
                metadata_={"duration_seconds": 45}
            )
            int_repo.add_concept_evaluation(evaluation)
            
            # Verify evaluations retrieved
            evals = int_repo.get_evaluations(self.candidate_id)
            self.assertEqual(len(evals), 1)
            self.assertEqual(evals[0].concept_id, "Supervised Learning")
            self.assertEqual(evals[0].metadata_, {"duration_seconds": 45})

            # 6. Save and fetch DomainMastery
            mastery = DomainMastery(
                candidate_id=self.candidate_id,
                domain_id="machine_learning",
                mastery=0.875
            )
            mast_repo.save_domain_mastery(mastery)
            
            db_mastery = mast_repo.get_domain_mastery(self.candidate_id, "machine_learning")
            self.assertIsNotNone(db_mastery)
            self.assertEqual(float(db_mastery.mastery), 0.875)

            # 7. Save and fetch InterviewReport
            report = InterviewReport(
                candidate_id=self.candidate_id,
                session_id="sess_uuid_1",
                concept_scores={"Supervised Learning": 0.90},
                domain_scores={"machine_learning": 0.875},
                strong_concepts=["Supervised Learning"],
                weak_concepts=[],
                recommended_topics=["Train-Test Split"],
                summary="Jane performed exceptionally well."
            )
            rep_repo.save_report(report)
            
            db_report = rep_repo.get_report("sess_uuid_1")
            self.assertIsNotNone(db_report)
            self.assertEqual(db_report.summary, "Jane performed exceptionally well.")
            self.assertEqual(db_report.recommended_topics, ["Train-Test Split"])

            # 8. Save and fetch GraphStatistics
            stats = GraphStatistics(
                domain_id="machine_learning",
                total_concepts=15,
                total_edges=20,
                max_depth=5,
                density=0.35
            )
            stats_repo.save_stats(stats)
            
            db_stats = stats_repo.get_stats("machine_learning")
            self.assertIsNotNone(db_stats)
            self.assertEqual(db_stats.total_concepts, 15)
            self.assertEqual(float(db_stats.density), 0.35)

    def test_chroma_service_memory_operations(self) -> None:
        """Test storing and semantic retrieval of answers, questions, misconceptions, and interview memories."""
        # 1. Store misconception
        self.chroma_service.store_misconception("Supervised Learning", "More features always make models better.")
        misconceptions = self.chroma_service.retrieve_misconceptions("Supervised Learning", limit=1)
        self.assertEqual(len(misconceptions), 1)
        self.assertIn("More features", misconceptions[0])

        # 2. Store question
        qid = self.chroma_service.store_question("Describe overfitting.", "Overfitting")
        self.assertIsNotNone(qid)

        # 3. Store answer
        aid = self.chroma_service.store_answer("Overfitting is high variance.", "Overfitting", qid, self.candidate_id)
        self.assertIsNotNone(aid)

        # Retrieve similar answer
        similar_answers = self.chroma_service.retrieve_similar_answers("high variance overfitting", limit=1)
        self.assertEqual(len(similar_answers), 1)
        self.assertIn("high variance", similar_answers[0])

        # 4. Store concept example
        self.chroma_service.store_example("Underfitting", "Simple model", "Lacks capacity")
        examples = self.chroma_service.retrieve_examples("Underfitting", limit=1)
        self.assertEqual(len(examples), 1)
        self.assertIn("Simple model", examples[0])

        # 5. Store and retrieve interview memory (candidate behavior/vision observations)
        self.chroma_service.store_memory(
            candidate_id=self.candidate_id,
            memory_text="Eye contact ratio was 85% with positive facial engagement.",
            metadata={"source": "eye_contact_tracker"}
        )
        
        memories = self.chroma_service.retrieve_memory(self.candidate_id, "gaze ratio facial engagement", limit=1)
        self.assertEqual(len(memories), 1)
        self.assertIn("Eye contact ratio", memories[0])

    def test_legacy_wrapper_compatibility(self) -> None:
        """Verify that DatabaseManager and ChromaStore wrapper layers still function properly on top of the new services."""
        # Reset local SQLite tables and reports view via wrapper helper
        reset_mock_db()

        db_mgr = DatabaseManager()
        chroma_store = ChromaStore(client=self.chroma_client)

        # Write candidate via wrapper
        db_mgr.persist_candidate(
            candidate_id=self.candidate_id,
            name=self.candidate_name,
            email=self.candidate_email,
            resume_text="Jane Architect Profile.",
            skills={"tech": ["Python"]},
            education=[],
            projects=[]
        )

        # Store domain mastery
        db_mgr.persist_domain_mastery(self.candidate_id, "machine_learning", 0.95)

        # Store report
        db_mgr.persist_report(
            candidate_id=self.candidate_id,
            session_id="sess_wrapper_1",
            concept_scores={},
            domain_scores={},
            strong_concepts=[],
            weak_concepts=[],
            recommended_topics=[],
            summary="Legacy wrapper test summary."
        )

        # Verify SQL-compat query on reports view (which points to interview_reports)
        conn = db_mgr.get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT summary FROM reports WHERE candidate_id = %s;", (self.candidate_id,))
                row = cur.fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row[0], "Legacy wrapper test summary.")

        # Test chroma wrapper retrieval
        chroma_store.store_misconception("Overfitting", "Using all features is always correct.")
        mcs = chroma_store.retrieve_misconceptions("Overfitting", limit=1)
        self.assertEqual(len(mcs), 1)
        self.assertIn("all features", mcs[0])
