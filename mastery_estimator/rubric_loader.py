"""Rubric loading helpers for concept-centric evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .models import ConceptRubric, RubricSignal


class RubricLoader:
    """Loads concept rubrics from JSON files."""

    def __init__(self, rubric_dir: str | Path) -> None:
        self.rubric_dir = Path(rubric_dir)

    def load_concept_rubric(self, concept: str) -> ConceptRubric:
        concept_key = _concept_to_key(concept)
        path = self.rubric_dir / f"{concept_key}.json"
        if not path.exists():
            return ConceptRubric(
                concept=concept,
                required_signals=[
                    RubricSignal(
                        signal_id=f"{concept_key}_core",
                        description=f"Core understanding of {concept}",
                        keywords=[concept.lower()] + concept.lower().split(),
                        weight=1.0
                    )
                ],
                optional_signals=[],
                reference_answer=f"Reference answer for {concept}"
            )

        payload = json.loads(path.read_text(encoding="utf-8"))
        return _rubric_from_payload(payload)

    def list_available_concepts(self) -> Dict[str, Path]:
        concepts: Dict[str, Path] = {}
        for path in self.rubric_dir.glob("*.json"):
            concepts[path.stem] = path
        return concepts


def _rubric_from_payload(payload: dict) -> ConceptRubric:
    required = [
        RubricSignal(
            signal_id=item["signal_id"],
            description=item["description"],
            keywords=item.get("keywords", []),
            weight=float(item.get("weight", 1.0)),
        )
        for item in payload.get("required_signals", [])
    ]

    optional = [
        RubricSignal(
            signal_id=item["signal_id"],
            description=item["description"],
            keywords=item.get("keywords", []),
            weight=float(item.get("weight", 0.5)),
        )
        for item in payload.get("optional_signals", [])
    ]

    return ConceptRubric(
        concept=payload["concept"],
        required_signals=required,
        optional_signals=optional,
        reference_answer=payload.get("reference_answer", ""),
    )


def _concept_to_key(concept: str) -> str:
    return "_".join(concept.strip().lower().split())
