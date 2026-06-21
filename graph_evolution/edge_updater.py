"""Edge Updater for computing edge strengths, inferring concept difficulty, and generating recommendations."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from graph_traversal.traversal_engine import find_graph_path
from knowledge_graph.graph_loader import load_graph_document
from interview_engine.database import DatabaseManager
from interview_engine.storage.postgres.models import ConceptEvaluation

logger = logging.getLogger(__name__)


class EdgeUpdater:
    """Computes statistics-driven edge analytics, infers concept difficulties, and suggests structural changes."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    def analyze_relationships(self, domain: str = "machine_learning") -> Dict[str, Any]:
        """Compute edge strengths, discover potential new concept associations, and suggest changes."""
        logger.info(f"Analyzing relationships for domain '{domain}'...")

        # 1. Fetch evaluations
        evals: List[Dict[str, Any]] = []
        with self.db.service.session() as session:
            rows = session.query(ConceptEvaluation).all()
            for r in rows:
                evals.append({
                    "candidate_id": r.candidate_id,
                    "concept_id": r.concept_id,
                    "mastery": float(r.mastery),
                    "latency": float(r.metadata_.get("latency", 0.0)) if r.metadata_ else 0.0
                })

        # Group evaluations by candidate
        candidate_mastery: Dict[str, Dict[str, float]] = {}
        for ev in evals:
            cand = ev["candidate_id"]
            if cand not in candidate_mastery:
                candidate_mastery[cand] = {}
            # Keep the highest mastery score achieved per candidate per concept
            candidate_mastery[cand][ev["concept_id"]] = max(
                candidate_mastery[cand].get(ev["concept_id"], 0.0),
                ev["mastery"]
            )

        # 2. Compute Edge Strengths for all evaluated concept pairs (A -> B)
        # Denominator: count of candidates who mastered A (mastery >= 0.80)
        # Numerator: count of candidates who mastered both A and B
        all_concepts = list({ev["concept_id"] for ev in evals})
        edge_strengths: Dict[tuple[str, str], Dict[str, Any]] = {}

        for src in all_concepts:
            for tgt in all_concepts:
                if src == tgt:
                    continue
                
                denom = 0
                num = 0
                for cand, mastery_map in candidate_mastery.items():
                    if src in mastery_map and mastery_map[src] >= 0.80:
                        denom += 1
                        if tgt in mastery_map and mastery_map[tgt] >= 0.80:
                            num += 1

                if denom > 0:
                    strength = num / denom
                    edge_strengths[(src, tgt)] = {
                        "strength": round(strength, 4),
                        "traversal_count": denom
                    }

        # 3. Load active domain graph structure
        existing_edges: Set[tuple[str, str]] = set()
        try:
            graph_path = find_graph_path(domain)
            graph = load_graph_document(graph_path)
            # Create a lookup mapping concept_id -> concept_name
            concept_name_lookup = {c.concept_id: c.concept_name for c in graph.concepts}
            # Also map concept_name -> concept_name for fallback
            for c in graph.concepts:
                concept_name_lookup[c.concept_name] = c.concept_name

            for edge in graph.edges:
                src_name = concept_name_lookup.get(edge.source_id, edge.source_id)
                tgt_name = concept_name_lookup.get(edge.target_id, edge.target_id)
                existing_edges.add((src_name, tgt_name))
        except Exception as e:
            logger.warning(f"Could not load domain graph edges: {e}")

        # 4. Generate recommendations for existing edges
        recommendations: List[Dict[str, Any]] = []
        for src, tgt in existing_edges:
            pair = (src, tgt)
            if pair in edge_strengths:
                stats = edge_strengths[pair]
                strength = stats["strength"]
                count = stats["traversal_count"]

                if strength >= 0.85 and count >= 3:
                    rec = "Increase relationship confidence"
                elif strength < 0.40 and count >= 3:
                    rec = "Review or weaken relationship"
                else:
                    rec = "Retain current relationship strength"

                recommendations.append({
                    "source": src,
                    "target": tgt,
                    "strength": strength,
                    "traversal_count": count,
                    "recommendation": rec
                })
                
                # Persist statistics to SQL table
                try:
                    self.db.persist_edge_statistics(
                        source_concept=src,
                        target_concept=tgt,
                        edge_strength=strength,
                        success_rate=strength,  # approximate success rate on target concept
                        failure_rate=round(1.0 - strength, 4),
                        traversal_count=count
                    )
                except Exception as db_err:
                    logger.error(f"Failed to persist edge stats to DB: {db_err}")

        # 5. Detect and suggest new concept relationships (Not currently connected)
        new_relationship_suggestions: List[Dict[str, Any]] = []
        for (src, tgt), stats in edge_strengths.items():
            if (src, tgt) not in existing_edges:
                strength = stats["strength"]
                count = stats["traversal_count"]
                
                # Suggest relationship if strong co-occurrence pattern is found
                if strength >= 0.70 and count >= 3:
                    new_relationship_suggestions.append({
                        "source": src,
                        "target": tgt,
                        "strength": strength,
                        "traversal_count": count,
                        "recommendation": f"Suggest new relationship candidate: {src} -> {tgt}"
                    })

        return {
            "edge_strengths": [
                {
                    "source": k[0],
                    "target": k[1],
                    "strength": v["strength"],
                    "traversal_count": v["traversal_count"]
                }
                for k, v in edge_strengths.items()
            ],
            "existing_edge_recommendations": recommendations,
            "new_relationship_suggestions": new_relationship_suggestions
        }

    def infer_concept_difficulty(self) -> Dict[str, Dict[str, Any]]:
        """Determine concept difficulties based on average mastery, failure rates, and time spent."""
        # 1. Fetch evaluations
        evals: List[Dict[str, Any]] = []
        with self.db.service.session() as session:
            rows = session.query(ConceptEvaluation).all()
            for r in rows:
                evals.append({
                    "concept_id": r.concept_id,
                    "mastery": float(r.mastery),
                    "latency": float(r.metadata_.get("latency", 0.0)) if r.metadata_ else 0.0
                })

        concept_stats: Dict[str, Dict[str, Any]] = {}
        for ev in evals:
            cid = ev["concept_id"]
            if cid not in concept_stats:
                concept_stats[cid] = {"mastery": [], "latency": [], "failure_count": 0}
            stats = concept_stats[cid]
            stats["mastery"].append(ev["mastery"])
            stats["latency"].append(ev["latency"])
            if ev["mastery"] <= 0.40:
                stats["failure_count"] += 1

        inferred_difficulties: Dict[str, Dict[str, Any]] = {}
        for cid, stats in concept_stats.items():
            n = len(stats["mastery"])
            avg_mastery = sum(stats["mastery"]) / n if n > 0 else 0.0
            avg_latency = sum(stats["latency"]) / n if n > 0 else 0.0
            fail_rate = stats["failure_count"] / n if n > 0 else 0.0

            # Difficulty is higher when mastery is low, failure rate is high, and latency is high
            # Base difficulty is 1.0 - average mastery.
            # Add a small penalty for high latencies (capped at 0.15 for average latencies >= 60s)
            latency_factor = min(0.15, avg_latency / 120.0)
            difficulty_score = (1.0 - avg_mastery) * 0.7 + fail_rate * 0.2 + latency_factor
            difficulty_score = max(0.0, min(1.0, difficulty_score))

            if difficulty_score < 0.40:
                classification = "basic"
            elif difficulty_score < 0.75:
                classification = "intermediate"
            else:
                classification = "advanced"

            inferred_difficulties[cid] = {
                "difficulty_score": round(difficulty_score, 4),
                "classification": classification,
                "average_mastery": round(avg_mastery, 4),
                "average_latency_seconds": round(avg_latency, 3),
                "failure_rate": round(fail_rate, 4)
            }

        return inferred_difficulties

    def analyze_candidate_trends(self, candidate_id: str) -> Dict[str, Any]:
        """Detect improving, declining, or commonly misunderstood concepts for a candidate."""
        evals: List[Dict[str, Any]] = []
        with self.db.service.session() as session:
            rows = session.query(ConceptEvaluation).filter(
                ConceptEvaluation.candidate_id == candidate_id
            ).order_by(ConceptEvaluation.id).all()
            for r in rows:
                evals.append({
                    "concept_id": r.concept_id,
                    "mastery": float(r.mastery)
                })

        # Group evaluations by concept maintaining order
        concept_history: Dict[str, List[float]] = {}
        for ev in evals:
            cid = ev["concept_id"]
            if cid not in concept_history:
                concept_history[cid] = []
            concept_history[cid].append(ev["mastery"])

        improving: List[str] = []
        declining: List[str] = []
        misunderstood: List[str] = []

        for cid, history in concept_history.items():
            if len(history) >= 2:
                # Calculate trend slope (latest vs average of history)
                latest = history[-1]
                prev_avg = sum(history[:-1]) / len(history[:-1])
                diff = latest - prev_avg
                if diff >= 0.15:
                    improving.append(cid)
                elif diff <= -0.15:
                    declining.append(cid)
            
            # Misunderstood if final score is poor
            if history[-1] <= 0.40:
                misunderstood.append(cid)

        return {
            "candidate_id": candidate_id,
            "improving_concepts": improving,
            "declining_concepts": declining,
            "misunderstood_concepts": misunderstood
        }
