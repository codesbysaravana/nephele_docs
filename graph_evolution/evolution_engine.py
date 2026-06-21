"""Graph Evolution Engine orchestrating class for aggregating statistics, analyzing relationships, and generating evolution reports."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from interview_engine.chroma_store import ChromaStore
from interview_engine.database import DatabaseManager
from .statistics_collector import StatisticsCollector
from .misconception_miner import MisconceptionMiner
from .edge_updater import EdgeUpdater

logger = logging.getLogger(__name__)


class GraphEvolutionEngine:
    """The central manager of the graph evolution system, coordinating stats collection, mining, and edge updates."""

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        chroma_store: Optional[ChromaStore] = None
    ) -> None:
        self.db = db_manager or DatabaseManager()
        self.chroma = chroma_store or ChromaStore()

        self.collector = StatisticsCollector(self.db)
        self.miner = MisconceptionMiner(self.db, self.chroma)
        self.updater = EdgeUpdater(self.db)

    def collect_statistics(self) -> Dict[str, Any]:
        """Aggregate concept traversal counts and success/failure statistics."""
        return self.collector.collect_statistics()

    def analyze_relationships(self, domain: str = "machine_learning") -> Dict[str, Any]:
        """Compute data-driven edge strengths and recommendations for domain concepts."""
        return self.updater.analyze_relationships(domain)

    def mine_misconceptions(self) -> Dict[str, Any]:
        """Extract candidate wrong answers, misconception frequencies, and confusion pairs."""
        return self.miner.mine_misconceptions()

    def generate_evolution_report(self, domain: str = "machine_learning") -> Dict[str, Any]:
        """Synthesize a complete data-driven evolution report for the knowledge graph."""
        logger.info(f"Generating knowledge graph evolution report for domain '{domain}'...")
        
        stats = self.collect_statistics()
        rel_analysis = self.analyze_relationships(domain)
        misconceptions = self.mine_misconceptions()
        difficulties = self.updater.infer_concept_difficulty()

        concepts = stats.get("concepts", {})

        # 1. Most Failed Concepts (highest failure rate)
        most_failed = sorted(
            [{"concept": cid, "failure_rate": info["failure_rate"]} for cid, info in concepts.items()],
            key=lambda x: x["failure_rate"],
            reverse=True
        )[:5]

        # 2. Most Successful Concepts (highest success rate)
        most_successful = sorted(
            [{"concept": cid, "success_rate": info["success_rate"]} for cid, info in concepts.items()],
            key=lambda x: x["success_rate"],
            reverse=True
        )[:5]

        # 3. Concept Difficulty Rankings (highest difficulty score first)
        difficulty_rankings = sorted(
            [
                {
                    "concept": cid, 
                    "difficulty_score": info["difficulty_score"], 
                    "classification": info["classification"]
                } 
                for cid, info in difficulties.items()
            ],
            key=lambda x: x["difficulty_score"],
            reverse=True
        )

        logger.info(f"Evolution report generated for '{domain}': {len(difficulty_rankings)} ranked concepts, {len(rel_analysis.get('existing_edge_recommendations', []))} edge recommendations.")
        
        return {
            "domain": domain,
            "most_failed_concepts": most_failed,
            "most_successful_concepts": most_successful,
            "concept_difficulty_rankings": difficulty_rankings,
            "existing_edge_recommendations": rel_analysis.get("existing_edge_recommendations", []),
            "new_relationship_suggestions": rel_analysis.get("new_relationship_suggestions", []),
            "mined_misconceptions": misconceptions.get("misconception_frequency", []),
            "concept_confusion_pairs": misconceptions.get("concept_confusion_pairs", [])
        }
