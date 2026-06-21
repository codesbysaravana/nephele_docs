"""Confidence and prioritization scoring for domain activation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


SOURCE_MULTIPLIERS = {
    "skills": 1.00,
    "domains": 1.10,
    "project_technologies": 1.15,
    "project_names": 0.80,
}


@dataclass
class DomainEvidence:
    """Evidence bucket for one domain before confidence aggregation."""

    weighted_sum: float = 0.0
    evidence_count: int = 0
    evidence: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "skills": [],
            "domains": [],
            "project_technologies": [],
            "project_names": [],
        }
    )


def add_evidence(bucket: DomainEvidence, source: str, token: str, base_weight: float) -> None:
    """Add one evidence item to a domain bucket."""
    multiplier = SOURCE_MULTIPLIERS.get(source, 1.0)
    contribution = base_weight * multiplier

    bucket.weighted_sum += contribution
    bucket.evidence_count += 1

    values = bucket.evidence.setdefault(source, [])
    if token not in values:
        values.append(token)


def compute_confidence(bucket: DomainEvidence) -> float:
    """Convert evidence into confidence in the range [0.0, 0.99]."""
    diversity = sum(1 for values in bucket.evidence.values() if values)
    diversity_bonus = max(0, diversity - 1) * 0.03

    score = bucket.weighted_sum + diversity_bonus
    return max(0.0, min(0.99, score))


def compute_priority(confidence: float, evidence_count: int) -> float:
    """Compute priority score for interview ordering."""
    density_bonus = min(0.25, evidence_count * 0.02)
    return confidence + density_bonus
