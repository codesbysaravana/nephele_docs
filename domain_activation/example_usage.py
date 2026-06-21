"""Example runner for Phase 2 domain activation."""

from __future__ import annotations

import json
from pathlib import Path

from .activation_engine import DomainActivationEngine


def run_example() -> None:
    resume = {
        "name": "Prasanth",
        "skills": ["Python", "Machine Learning", "TensorFlow", "SQL"],
        "projects": [
            {
                "name": "Fraud Detection",
                "technologies": ["Python", "XGBoost"],
            }
        ],
        "experience_level": "Student",
        "domains": ["Machine Learning", "Data Science"],
    }

    engine = DomainActivationEngine(base_dir=Path(__file__).parent)
    result = engine.activate(resume)

    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    run_example()
