"""Integration tests for Phase 6B: Fallback Mastery Evaluator, LLM Providers, Cost Tracking, and Chroma Context."""

import os
import unittest
from unittest.mock import MagicMock, patch

import chromadb

from interview_engine.chroma_store import ChromaStore
from interview_engine.database import DatabaseManager
from interview_engine.storage.postgres.models import EvaluationHistory, ProviderMetrics
from interview_engine.storage.postgres.service import PostgresService
from mastery_estimator.base import BaseEvaluator
from mastery_estimator.estimation_engine import MasteryEstimationEngine
from mastery_estimator.fallback import FallbackEvaluator
from mastery_estimator.models import ConceptRubric, EvaluationStrategy, RubricSignal
from mastery_estimator.providers import GeminiEvaluator, GroqEvaluator, OpenAIEvaluator, compute_cost


class TestPhase6B(unittest.TestCase):
    def setUp(self) -> None:
        self.pg_service = PostgresService(database_url="sqlite:///test_nephele_6b.db")
        self.pg_service.drop_tables()
        self.pg_service.create_tables()

        self.db_manager = DatabaseManager()
        # Override the database service inside db_manager to use our test DB
        self.db_manager.service = self.pg_service

        # Initialize mock Chroma client and store
        self.chroma_client = chromadb.EphemeralClient()
        self.chroma_store = ChromaStore(client=self.chroma_client)

        # Rubric for testing
        self.rubric = ConceptRubric(
            concept="Overfitting",
            required_signals=[
                RubricSignal("memorization", "Model memorizes training data", ["memorize", "memorization"], 0.5),
                RubricSignal(
                    "poor_generalization", "Model fails to generalize", ["generalize", "poor generalization"], 0.5
                ),
            ],
            optional_signals=[RubricSignal("high_variance", "High variance", ["variance"], 0.2)],
            reference_answer="Model memorizes train data and fails to generalize.",
        )

    def tearDown(self) -> None:
        self.pg_service.drop_tables()

    def test_cost_calculation(self) -> None:
        """Verify cost calculation handles different models and providers correctly."""
        # Groq
        cost = compute_cost("groq", "llama3-70b-8192", 1000, 500)
        self.assertAlmostEqual(cost, (1000 / 1e6) * 0.59 + (500 / 1e6) * 0.79)

        # Gemini
        cost = compute_cost("gemini", "gemini-1.5-pro", 1000, 500)
        self.assertAlmostEqual(cost, (1000 / 1e6) * 7.0 + (500 / 1e6) * 21.0)

        # OpenAI
        cost = compute_cost("openai", "gpt-4o-mini", 1000, 500)
        self.assertAlmostEqual(cost, (1000 / 1e6) * 0.15 + (500 / 1e6) * 0.60)

    def test_fallback_evaluator_all_keys_missing(self) -> None:
        """Verify fallback to local RubricEvaluator (LLMEvaluator) when no keys are in environment."""
        # Ensure no api keys in env
        with patch.dict(os.environ, {}, clear=True):
            fallback = FallbackEvaluator(db_manager=self.db_manager)
            # Evaluate using fallback. It should fallback to rubric evaluator.
            result = fallback.evaluate(
                concept="Overfitting",
                question="What is overfitting?",
                answer="memorizes training data but fails to generalize to unseen data",
                rubric=self.rubric,
            )
            # Verify result matches LLMEvaluator output
            self.assertIsNotNone(result)
            self.assertEqual(result.concept, "Overfitting")
            self.assertIn("memorization", result.evidence.matched_signals)
            self.assertIn("poor_generalization", result.evidence.matched_signals)
            self.assertTrue(result.mastery > 0.8)

            # Verify that the DB log exists for evaluation_history with rubric provider
            with self.pg_service.session() as session:
                histories = session.query(EvaluationHistory).all()
                self.assertEqual(len(histories), 1)
                self.assertEqual(histories[0].provider, "rubric")
                self.assertEqual(float(histories[0].mastery), result.mastery)

    @patch("mastery_estimator.providers.Groq")
    def test_fallback_evaluator_groq_success(self, mock_groq_class: MagicMock) -> None:
        """Verify fallback evaluator records prompt results and metrics upon successful Groq execution."""
        # Configure mock Groq client
        mock_client = MagicMock()
        mock_groq_class.return_value = mock_client

        # Configure mock chat completions response
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(
                message=MagicMock(
                    content="""{
                "mastery": 0.95,
                "confidence": 0.98,
                "matched_signals": ["memorization", "poor_generalization"],
                "missing_signals": [],
                "reasoning": ["Excellent answer addressing all core signals."]
            }"""
                )
            )
        ]
        mock_completion.usage = MagicMock(prompt_tokens=150, completion_tokens=60, total_tokens=210)
        mock_client.chat.completions.create.return_value = mock_completion

        # Call evaluator under fallback with GROQ_API_KEY set
        with patch.dict(os.environ, {"GROQ_API_KEY": "test_groq_key"}):
            fallback = FallbackEvaluator(db_manager=self.db_manager)
            result = fallback.evaluate(
                concept="Overfitting",
                question="What is overfitting?",
                answer="memorizes training data and fails to generalize",
                rubric=self.rubric,
            )

            self.assertIsNotNone(result)
            self.assertEqual(result.mastery, 0.95)
            self.assertEqual(result.confidence, 0.98)
            self.assertEqual(result.evidence.matched_signals, ["memorization", "poor_generalization"])
            self.assertEqual(result.reasoning, ["Excellent answer addressing all core signals."])
            self.assertEqual(result.metadata["model"], "llama3-70b-8192")

            # Verify DB entries
            with self.pg_service.session() as session:
                histories = session.query(EvaluationHistory).all()
                self.assertEqual(len(histories), 1)
                self.assertEqual(histories[0].provider, "groq")
                self.assertEqual(float(histories[0].mastery), 0.95)

                metrics = session.query(ProviderMetrics).all()
                self.assertEqual(len(metrics), 1)
                self.assertEqual(metrics[0].provider, "groq")
                self.assertEqual(metrics[0].prompt_tokens, 150)
                self.assertEqual(metrics[0].completion_tokens, 60)
                self.assertAlmostEqual(float(metrics[0].cost), compute_cost("groq", "llama3-70b-8192", 150, 60), places=5)

    @patch("mastery_estimator.providers.Groq")
    @patch("mastery_estimator.providers.genai.GenerativeModel")
    @patch("mastery_estimator.providers.genai.configure")
    def test_fallback_chain_groq_fails_gemini_succeeds(
        self, mock_configure: MagicMock, mock_genai_model_class: MagicMock, mock_groq_class: MagicMock
    ) -> None:
        """Verify that provider failures trigger fallback progression down the chain."""
        # Mock Groq client to raise connection error
        mock_groq_client = MagicMock()
        mock_groq_class.return_value = mock_groq_client
        mock_groq_client.chat.completions.create.side_effect = Exception("Groq connection timeout")

        # Mock Gemini model to succeed
        mock_model = MagicMock()
        mock_genai_model_class.return_value = mock_model

        mock_response = MagicMock()
        mock_response.text = """{
            "mastery": 0.88,
            "confidence": 0.92,
            "matched_signals": ["memorization"],
            "missing_signals": ["poor_generalization"],
            "reasoning": ["Partially correct, missed generalization."]
        }"""
        mock_response.usage_metadata = MagicMock(
            prompt_token_count=200, candidates_token_count=70, total_token_count=270
        )
        mock_model.generate_content.return_value = mock_response

        # Execute under fallback with both API keys set
        env_vars = {"GROQ_API_KEY": "groq_key", "GEMINI_API_KEY": "gemini_key"}
        with patch.dict(os.environ, env_vars):
            fallback = FallbackEvaluator(db_manager=self.db_manager)
            result = fallback.evaluate(
                concept="Overfitting",
                question="What is overfitting?",
                answer="memorizes training data",
                rubric=self.rubric,
            )

            self.assertIsNotNone(result)
            self.assertEqual(result.mastery, 0.88)
            self.assertEqual(result.evidence.matched_signals, ["memorization"])

            # Verify DB entries - provider should be gemini
            with self.pg_service.session() as session:
                histories = session.query(EvaluationHistory).all()
                self.assertEqual(len(histories), 1)
                self.assertEqual(histories[0].provider, "gemini")

                metrics = session.query(ProviderMetrics).all()
                self.assertEqual(len(metrics), 1)
                self.assertEqual(metrics[0].provider, "gemini")
                self.assertEqual(metrics[0].prompt_tokens, 200)

    def test_chroma_context_augmentation(self) -> None:
        """Verify estimation engine queries Chroma and passes context to evaluator."""
        # Seed Chroma store with misconceptions, similar answers, and examples
        self.chroma_store.store_misconception("Overfitting", "More parameters are always better.")
        self.chroma_store.store_example(
            "Overfitting", "What is overfitting?", "When a model fits training data too closely."
        )

        # Instantiate Estimation Engine with our test services
        engine = MasteryEstimationEngine(db_manager=self.db_manager, chroma_store=self.chroma_store)

        # We can mock the evaluator to inspect the context string passed to it
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate.return_value = MagicMock(
            mastery=0.9,
            confidence=0.9,
            reasoning=[],
            evidence=MagicMock(matched_signals=[], missing_signals=[]),
            strategy=EvaluationStrategy.LLM,
            metadata={},
        )
        engine._evaluators[EvaluationStrategy.LLM] = mock_evaluator

        # Estimate concept mastery
        engine.estimate(
            concept="Overfitting",
            question="What is overfitting?",
            answer="memorizes training data",
            strategy=EvaluationStrategy.LLM,
        )

        # Verify mock_evaluator.evaluate was called and 'context' kwarg is not None
        mock_evaluator.evaluate.assert_called_once()
        args, kwargs = mock_evaluator.evaluate.call_args
        context = kwargs.get("context")
        self.assertIsNotNone(context)
        self.assertIn("More parameters are always better.", context)
        self.assertIn("When a model fits training data too closely.", context)
