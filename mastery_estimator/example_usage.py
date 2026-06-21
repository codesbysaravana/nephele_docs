"""Example runner for Phase 3 mastery estimation."""

from __future__ import annotations

import json

from .estimation_engine import MasteryEstimationEngine
from .models import EvaluationStrategy


def run_examples() -> None:
    engine = MasteryEstimationEngine()

    examples = [
        {
            "concept": "Overfitting",
            "question": "What is overfitting?",
            "answer": "When a model memorizes training data and fails to generalize.",
        },
        {
            "concept": "Overfitting",
            "question": "What is overfitting?",
            "answer": "I don't know.",
        },
    ]

    for item in examples:
        result = engine.estimate(
            concept=item["concept"],
            question=item["question"],
            answer=item["answer"],
            strategy=EvaluationStrategy.HYBRID,
        )
        print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    run_examples()
