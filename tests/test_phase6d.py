"""Integration tests for Phase 6D: Voice Interview Runtime Integration."""

import os
import unittest
from pathlib import Path
import chromadb

from interview_engine.chroma_store import ChromaStore
from interview_engine.database import DatabaseManager
from interview_engine.storage.postgres.models import ConceptEvaluation, InterviewSession, QuestionResponseLog, QuestionEffectiveness
from interview_engine.storage.postgres.service import PostgresService
from runtime.interview_runtime import (
    MockSTT,
    MockTTS,
    CameraAdapter,
    InterviewRuntimeManager,
)


class TestPhase6D(unittest.TestCase):
    def setUp(self) -> None:
        # 1. Initialize isolated SQLite DB for testing
        self.pg_service = PostgresService(database_url="sqlite:///test_nephele_6d.db")
        self.pg_service.drop_tables()
        self.pg_service.create_tables()

        self.db_manager = DatabaseManager()
        self.db_manager.service = self.pg_service

        # 2. Ephemeral Chroma store
        self.chroma_client = chromadb.EphemeralClient()
        self.chroma_store = ChromaStore(client=self.chroma_client)

        # 3. Configure mock STT responses for simulation
        self.mock_stt = MockSTT(responses=[
            "supervised learning",
            "train-test split",
            "underfitting"
        ])
        self.mock_tts = MockTTS()
        self.camera_adapter = CameraAdapter()

        # 4. Instantiate manager
        self.bank_dir = Path(__file__).parent.parent / "question_bank"
        self.manager = InterviewRuntimeManager(
            db_manager=self.db_manager,
            chroma_store=self.chroma_store,
            stt_provider=self.mock_stt,
            tts_provider=self.mock_tts,
            camera_adapter=self.camera_adapter,
        )
        self.manager.question_layer.question_bank = {}
        # Resolve question layer bank directory explicitly
        self.manager.question_layer.bank_dir = self.bank_dir
        # Reload static banks
        self.manager.question_layer.__init__(
            db_manager=self.db_manager,
            chroma_store=self.chroma_store,
            bank_dir=self.bank_dir
        )

        self.candidate_id = "candidate_e2e_456"
        self.resume_json = {
            "skills": ["Machine Learning"],
            "education": [{"degree": "Bachelors", "field": "Computer Science"}],
            "projects": [{"name": "Classifier", "technologies": ["Python", "scikit-learn"]}]
        }

    def tearDown(self) -> None:
        self.pg_service.drop_tables()

    def test_camera_adapter_metrics(self) -> None:
        """Verify CameraAdapter consumes individual frame details and aggregates averages correctly."""
        self.camera_adapter.reset()
        self.camera_adapter.consume_frame_metrics(eye_contact_score=80.0, engagement_score=90.0, pitch=2.0, yaw=-3.0)
        self.camera_adapter.consume_frame_metrics(eye_contact_score=70.0, engagement_score=80.0, pitch=4.0, yaw=-1.0)
        
        avg = self.camera_adapter.get_average_metrics()
        self.assertEqual(avg["eye_contact_score"], 75.0)
        self.assertEqual(avg["engagement_score"], 85.0)
        # Derived attention: max(0.0, 100.0 - (abs(pitch) + abs(yaw)) * 2)
        # Frame 1: 100 - (2+3)*2 = 90
        # Frame 2: 100 - (4+1)*2 = 90
        self.assertEqual(avg["attention_score"], 90.0)

    def test_runtime_lifecycle_and_traversal(self) -> None:
        """Simulate a live interview cycle: start, TTS play, camera consume, STT transcript, evaluate & progress."""
        # 1. Start Runtime
        start_res = self.manager.start_runtime(
            candidate_id=self.candidate_id,
            candidate_name="Alex Voice",
            candidate_email="alex.voice@example.com",
            resume_json=self.resume_json
        )
        self.assertEqual(start_res["state"], "ACTIVE")
        self.assertEqual(start_res["domain"], "machine_learning")
        self.assertEqual(start_res["current_concept"], "Supervised Learning")
        self.assertIsNotNone(start_res["question"])
        
        first_question = start_res["question"]

        # 2. Test TTS question output playback
        audio_meta = self.manager.generate_audio_question(first_question)
        self.assertEqual(audio_meta["provider"], "mock")
        self.assertEqual(audio_meta["text_length"], len(first_question))

        # 3. Simulate camera frames while candidate speaks
        self.manager.camera_adapter.consume_frame_metrics(eye_contact_score=95.0, engagement_score=90.0, pitch=1.0, yaw=1.0)
        self.manager.camera_adapter.consume_frame_metrics(eye_contact_score=85.0, engagement_score=80.0, pitch=3.0, yaw=1.0)

        # 4. Transcribe spoken response using STT provider
        answer_text = self.manager.receive_transcript()
        self.assertEqual("supervised learning", answer_text)

        # 5. Submit answer, running evaluation and graph traversal
        submit_res = self.manager.submit_answer(
            candidate_id=self.candidate_id,
            concept="Supervised Learning",
            question=first_question,
            answer=answer_text,
            latency=5.4
        )

        self.assertEqual(submit_res["decision"], "advance")
        self.assertEqual(submit_res["next_concept"], "Train-Test Split")
        self.assertEqual(submit_res["state"], "ACTIVE")
        self.assertGreaterEqual(submit_res["mastery"], 0.8)
        self.assertIsNotNone(submit_res["question"])

        # 6. Verify SQL persistence (ConceptEvaluation metadata contains engagement)
        with self.pg_service.session() as session:
            eval_record = session.query(ConceptEvaluation).filter(ConceptEvaluation.concept_id == "Supervised Learning").first()
            self.assertIsNotNone(eval_record)
            self.assertEqual(eval_record.answer, answer_text)
            
            # Retrieve JSON metadata
            meta = eval_record.metadata_
            self.assertIn("engagement_metrics", meta)
            self.assertEqual(meta["engagement_metrics"]["eye_contact_score"], 90.0) # avg of 95 and 85
            self.assertEqual(meta["engagement_metrics"]["engagement_score"], 85.0) # avg of 90 and 80

            # Verify question response log & effectiveness
            resp_log = session.query(QuestionResponseLog).filter(QuestionResponseLog.concept_id == "Supervised Learning").first()
            self.assertIsNotNone(resp_log)
            self.assertEqual(float(resp_log.latency), 5.4)
            self.assertEqual(resp_log.candidate_answer, answer_text)

            effectiveness = session.query(QuestionEffectiveness).filter(QuestionEffectiveness.question_id == resp_log.question_id).first()
            self.assertIsNotNone(effectiveness)
            self.assertEqual(effectiveness.total_responses, 1)

    def test_pause_and_resume(self) -> None:
        """Verify interview pause and resume transition the database and in-memory states."""
        self.manager.start_runtime(
            candidate_id=self.candidate_id,
            candidate_name="Tester",
            candidate_email="tester@example.com",
            resume_json=self.resume_json
        )
        self.assertEqual(self.manager.session_state, "ACTIVE")

        # Pause
        self.manager.pause_interview(self.candidate_id)
        self.assertEqual(self.manager.session_state, "PAUSED")
        with self.pg_service.session() as session:
            db_sess = session.query(InterviewSession).filter(InterviewSession.candidate_id == self.candidate_id).first()
            self.assertEqual(db_sess.state, "PAUSED")

        # Resume
        self.manager.resume_interview(self.candidate_id)
        self.assertEqual(self.manager.session_state, "ACTIVE")
        with self.pg_service.session() as session:
            db_sess = session.query(InterviewSession).filter(InterviewSession.candidate_id == self.candidate_id).first()
            self.assertEqual(db_sess.state, "ACTIVE")

    def test_session_recovery(self) -> None:
        """Verify a suspended session can be recovered fully, reconstructing concept histories and transcripts."""
        # 1. Run a session turn
        self.manager.start_runtime(
            candidate_id=self.candidate_id,
            candidate_name="Alex Recovery",
            candidate_email="alex.rec@example.com",
            resume_json=self.resume_json
        )
        q1 = self.manager.question_history[0]["question_text"]
        ans1 = self.manager.receive_transcript()
        
        self.manager.submit_answer(
            candidate_id=self.candidate_id,
            concept="Supervised Learning",
            question=q1,
            answer=ans1,
            latency=4.2
        )

        # 2. Instantiate a fresh manager to simulate recovery
        fresh_manager = InterviewRuntimeManager(
            db_manager=self.db_manager,
            chroma_store=self.chroma_store,
            stt_provider=self.mock_stt,
            tts_provider=self.mock_tts,
            camera_adapter=self.camera_adapter,
        )
        # Reload bank explicitly
        fresh_manager.question_layer.__init__(
            db_manager=self.db_manager,
            chroma_store=self.chroma_store,
            bank_dir=self.bank_dir
        )

        # Recover
        recovered = fresh_manager.recover_session(self.candidate_id)
        self.assertTrue(recovered)

        # Verify recovered values in fresh manager
        self.assertEqual(fresh_manager.candidate_id, self.candidate_id)
        self.assertEqual(fresh_manager.domain, "machine_learning")
        self.assertEqual(fresh_manager.current_concept, "Train-Test Split")
        self.assertEqual(fresh_manager.session_state, "ACTIVE")
        self.assertEqual(len(fresh_manager.visited_concepts), 2) # Supervised Learning, Train-Test Split
        self.assertEqual(fresh_manager.visited_concepts[0], "Supervised Learning")
        
        # Verify transcript history is rebuilt chronologically
        # Turn 1: Interviewer Q1
        # Turn 2: Candidate Ans1
        # Turn 3: Interviewer Q2 (the active recovered question)
        self.assertEqual(len(fresh_manager.transcript_history), 3)
        self.assertEqual(fresh_manager.transcript_history[0]["role"], "interviewer")
        self.assertEqual(fresh_manager.transcript_history[0]["text"], q1)
        self.assertEqual(fresh_manager.transcript_history[1]["role"], "candidate")
        self.assertEqual(fresh_manager.transcript_history[1]["text"], ans1)
        self.assertEqual(fresh_manager.transcript_history[2]["role"], "interviewer")
        self.assertIsNotNone(fresh_manager.transcript_history[2]["text"])

        # Verify question history is rebuilt
        self.assertEqual(len(fresh_manager.question_history), 2)
        self.assertEqual(fresh_manager.question_history[0]["concept"], "Supervised Learning")
        self.assertEqual(fresh_manager.question_history[1]["concept"], "Train-Test Split")

    def test_conclude_and_report_generation(self) -> None:
        """Verify stop_interview transitions session state, aggregates scores, and persists final report."""
        self.manager.start_runtime(
            candidate_id=self.candidate_id,
            candidate_name="Alex Stop",
            candidate_email="alex.stop@example.com",
            resume_json=self.resume_json
        )
        
        q1 = self.manager.question_history[0]["question_text"]
        ans1 = self.manager.receive_transcript()
        
        # Submit first answer
        self.manager.submit_answer(
            candidate_id=self.candidate_id,
            concept="Supervised Learning",
            question=q1,
            answer=ans1,
            latency=3.8
        )

        # Conclude
        stop_res = self.manager.stop_interview(self.candidate_id)
        self.assertEqual(stop_res["state"], "COMPLETED")
        self.assertIsNotNone(stop_res["domain_mastery"])
        
        report = stop_res["report"]
        self.assertEqual(report["candidate_id"], self.candidate_id)
        self.assertEqual(report["domain"], "machine_learning")
        self.assertIn("Supervised Learning", report["concept_scores"])

        # Verify report database entry
        with self.pg_service.session() as session:
            db_sess = session.query(InterviewSession).filter(InterviewSession.candidate_id == self.candidate_id).first()
            self.assertEqual(db_sess.state, "COMPLETED")
            
            # Check persisted reports view
            from sqlalchemy import text
            row = session.execute(text("SELECT summary FROM interview_reports WHERE candidate_id = :cid"), {"cid": self.candidate_id}).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], report["summary"])
