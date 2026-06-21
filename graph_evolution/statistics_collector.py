"""Statistics Collector for accumulating concept traversal and mastery distribution statistics from Postgres."""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional

from interview_engine.database import DatabaseManager
from interview_engine.storage.postgres.models import ConceptEvaluation

logger = logging.getLogger(__name__)


class StatisticsCollector:
    """Queries persistent databases to compute concept metrics and edge traversal frequency."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    def collect_statistics(self) -> Dict[str, Any]:
        """Aggregate concept outcomes and transition frequencies from historical concept evaluations."""
        logger.info("Collecting graph evolution statistics from database...")

        # 1. Fetch all concept evaluations ordered chronologically per candidate
        evals: List[Dict[str, Any]] = []
        with self.db.service.session() as session:
            rows = session.query(ConceptEvaluation).order_by(
                ConceptEvaluation.candidate_id,
                ConceptEvaluation.id
            ).all()
            for r in rows:
                evals.append({
                    "candidate_id": r.candidate_id,
                    "concept_id": r.concept_id,
                    "mastery": float(r.mastery),
                    "confidence": float(r.confidence),
                    "missing_signals": r.missing_signals or [],
                    "matched_signals": r.matched_signals or [],
                    "latency": float(r.metadata_.get("latency", 0.0)) if r.metadata_ else 0.0
                })

        # 2. Aggregate concept-level metrics
        concept_data: Dict[str, Dict[str, Any]] = {}
        for ev in evals:
            cid = ev["concept_id"]
            if cid not in concept_data:
                concept_data[cid] = {
                    "mastery_scores": [],
                    "latencies": [],
                    "success_count": 0,
                    "failure_count": 0,
                }
            data = concept_data[cid]
            data["mastery_scores"].append(ev["mastery"])
            data["latencies"].append(ev["latency"])
            
            if ev["mastery"] >= 0.80:
                data["success_count"] += 1
            elif ev["mastery"] <= 0.40:
                data["failure_count"] += 1

        concept_aggregates: Dict[str, Dict[str, Any]] = {}
        for cid, data in concept_data.items():
            scores = data["mastery_scores"]
            latencies = data["latencies"]
            n = len(scores)

            avg_mastery = sum(scores) / n if n > 0 else 0.0
            avg_latency = sum(latencies) / n if n > 0 else 0.0
            
            variance = sum((x - avg_mastery) ** 2 for x in scores) / n if n > 0 else 0.0
            std_dev = math.sqrt(variance)

            concept_aggregates[cid] = {
                "traversal_frequency": n,
                "success_rate": round(data["success_count"] / n, 4) if n > 0 else 0.0,
                "failure_rate": round(data["failure_count"] / n, 4) if n > 0 else 0.0,
                "average_mastery": round(avg_mastery, 4),
                "average_latency": round(avg_latency, 3),
                "min_mastery": round(min(scores), 4) if scores else 0.0,
                "max_mastery": round(max(scores), 4) if scores else 0.0,
                "std_dev_mastery": round(std_dev, 4)
            }

        # 3. Compute relationship frequencies
        candidate_paths: Dict[str, List[str]] = {}
        for ev in evals:
            cand = ev["candidate_id"]
            if cand not in candidate_paths:
                candidate_paths[cand] = []
            candidate_paths[cand].append(ev["concept_id"])

        relationship_frequency: Dict[tuple[str, str], int] = {}
        for cand, path in candidate_paths.items():
            for i in range(len(path) - 1):
                edge = (path[i], path[i+1])
                relationship_frequency[edge] = relationship_frequency.get(edge, 0) + 1

        rel_freq_formatted = [
            {"source": src, "target": tgt, "frequency": freq}
            for (src, tgt), freq in relationship_frequency.items()
        ]

        logger.info(f"Statistics collected: {len(concept_aggregates)} concepts, {len(rel_freq_formatted)} relationship transitions.")
        return {
            "concepts": concept_aggregates,
            "relationships": rel_freq_formatted
        }
