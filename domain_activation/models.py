"""Data models for domain activation outputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(slots=True)
class ActiveDomain:
    """Activated domain with confidence, entry concepts, and evidence."""

    domain: str
    confidence: float
    entry_concepts: List[str] = field(default_factory=list)
    priority_score: float = 0.0
    evidence: Dict[str, List[str]] = field(default_factory=dict)


@dataclass(slots=True)
class ActivationResult:
    """Domain activation result consumed by downstream interview services."""

    active_domains: List[ActiveDomain] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "active_domains": [
                {
                    "domain": item.domain,
                    "confidence": round(item.confidence, 2),
                    "entry_concepts": item.entry_concepts,
                    "priority_score": round(item.priority_score, 3),
                    "evidence": item.evidence,
                }
                for item in self.active_domains
            ]
        }
