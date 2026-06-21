"""Domain registry loading and token normalization utilities."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


def normalize_token(value: str) -> str:
    """Normalize a token for stable registry and alias lookup."""
    lowered = value.strip().lower()
    return re.sub(r"\s+", " ", lowered)


class DomainRegistry:
    """Loads alias and technology registries and resolves resume tokens."""

    def __init__(
        self,
        aliases_path: str | Path,
        registry_path: str | Path,
    ) -> None:
        aliases_payload = json.loads(Path(aliases_path).read_text(encoding="utf-8"))
        registry_payload = json.loads(Path(registry_path).read_text(encoding="utf-8"))

        self.alias_to_domain: Dict[str, str] = {}
        for domain, aliases in aliases_payload.items():
            self.alias_to_domain[normalize_token(domain)] = domain
            for alias in aliases:
                self.alias_to_domain[normalize_token(alias)] = domain

        self.token_registry: Dict[str, Dict[str, object]] = {
            normalize_token(token): config
            for token, config in registry_payload.items()
        }

    def resolve_alias(self, token: str) -> Optional[str]:
        """Resolve token through alias mapping into a canonical domain."""
        return self.alias_to_domain.get(normalize_token(token))

    def resolve_registry(self, token: str) -> Optional[Tuple[str, float]]:
        """Resolve token through skill/project registry with a base weight."""
        config = self.token_registry.get(normalize_token(token))
        if not config:
            return None
        return str(config["domain"]), float(config["weight"])

    def canonical_domains(self) -> List[str]:
        """Return known canonical domains from aliases and registry."""
        domains = set(self.alias_to_domain.values())
        for entry in self.token_registry.values():
            domains.add(str(entry["domain"]))
        return sorted(domains)
