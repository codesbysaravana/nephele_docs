"""Domain activation engine for resume-driven graph activation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .confidence_engine import DomainEvidence, add_evidence, compute_confidence, compute_priority
from .models import ActivationResult, ActiveDomain
from .registry import DomainRegistry


class DomainActivationEngine:
    """Activates graph domains from structured resume evidence."""

    def __init__(
        self,
        base_dir: str | Path,
        min_confidence: float = 0.50,
    ) -> None:
        base = Path(base_dir)
        self.min_confidence = min_confidence

        self.registry = DomainRegistry(
            aliases_path=base / "aliases.json",
            registry_path=base / "registry.json",
        )

        # Domain metadata comes from graph domain files.
        self.domain_catalog = self._load_domain_catalog(
            base.parent / "knowledge_graph" / "domains"
        )

    def activate(self, resume: Dict[str, object]) -> ActivationResult:
        """Activate and prioritize domains from resume JSON."""
        buckets: Dict[str, DomainEvidence] = {}

        for skill in resume.get("skills", []) or []:
            self._process_token(buckets, "skills", str(skill))

        for declared_domain in resume.get("domains", []) or []:
            self._process_token(buckets, "domains", str(declared_domain))

        for project in resume.get("projects", []) or []:
            if not isinstance(project, dict):
                continue
            name = str(project.get("name", "")).strip()
            if name:
                self._process_token(buckets, "project_names", name)

            for technology in project.get("technologies", []) or []:
                self._process_token(buckets, "project_technologies", str(technology))

        active_domains: List[ActiveDomain] = []
        for domain, bucket in buckets.items():
            confidence = compute_confidence(bucket)
            if confidence < self.min_confidence:
                continue

            priority_score = compute_priority(confidence, bucket.evidence_count)
            active_domains.append(
                ActiveDomain(
                    domain=domain,
                    confidence=confidence,
                    entry_concepts=self._entry_concepts_for_domain(domain),
                    priority_score=priority_score,
                    evidence=bucket.evidence,
                )
            )

        active_domains.sort(
            key=lambda item: (item.priority_score, item.confidence, sum(len(v) for v in item.evidence.values())),
            reverse=True,
        )

        return ActivationResult(active_domains=active_domains)

    def _process_token(self, buckets: Dict[str, DomainEvidence], source: str, raw_token: str) -> None:
        token = raw_token.strip()
        if not token:
            return

        # Collect candidate domain matches first to avoid counting
        # the same token twice for the same domain.
        candidates: Dict[str, float] = {}

        alias_domain = self.registry.resolve_alias(token)
        if alias_domain:
            candidates[alias_domain] = max(candidates.get(alias_domain, 0.0), 0.60)

        resolved = self.registry.resolve_registry(token)
        if resolved:
            domain, weight = resolved
            candidates[domain] = max(candidates.get(domain, 0.0), weight)

        for domain, weight in candidates.items():
            bucket = buckets.setdefault(domain, DomainEvidence())
            add_evidence(bucket, source, token, base_weight=weight)

    def _entry_concepts_for_domain(self, domain: str) -> List[str]:
        metadata = self.domain_catalog.get(domain, {})
        return list(metadata.get("entry_concepts", []))

    @staticmethod
    def _load_domain_catalog(domains_dir: Path) -> Dict[str, Dict[str, object]]:
        catalog: Dict[str, Dict[str, object]] = {}
        if not domains_dir.exists():
            return catalog

        for path in domains_dir.glob("*.json"):
            payload = json.loads(path.read_text(encoding="utf-8"))
            domain_id = payload.get("domain_id")
            if not domain_id:
                continue
            catalog[str(domain_id)] = payload

        return catalog
