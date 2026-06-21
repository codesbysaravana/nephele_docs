"""Report Generator for computing domain mastery and generating candidate evaluation reports."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from knowledge_graph.graph_loader import load_graph_document
from graph_traversal.graph_navigator import GraphNavigator
from graph_traversal.traversal_engine import find_graph_path

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Computes mastery aggregates and generates final candidate performance reports."""

    def calculate_domain_mastery(self, concept_scores: Dict[str, float]) -> float:
        """Calculate domain mastery as the simple average of evaluated concept masteries."""
        if not concept_scores:
            return 0.0
        scores = list(concept_scores.values())
        avg_score = sum(scores) / len(scores)
        return round(avg_score, 3)

    def generate_report(
        self,
        candidate_id: str,
        candidate_name: str,
        domain: str,
        concept_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate a complete evaluation report including scores, strengths, weaknesses, and study recommendations."""
        
        # 1. Calculate overall domain mastery
        domain_mastery = self.calculate_domain_mastery(concept_scores)
        
        # 2. Identify Strong (>= 0.80) and Weak (<= 0.40) concepts
        strong_concepts: List[str] = []
        weak_concepts: List[str] = []
        for concept, score in concept_scores.items():
            if score >= 0.80:
                strong_concepts.append(concept)
            elif score <= 0.40:
                weak_concepts.append(concept)

        # 3. Generate Recommended Topics using the Knowledge Graph
        recommended_topics: List[str] = []
        try:
            graph_path = find_graph_path(domain)
            graph = load_graph_document(graph_path)
            navigator = GraphNavigator(graph)
            
            for weak in weak_concepts:
                weak_node = navigator.lookup_concept(weak)
                if weak_node:
                    prereqs = navigator.get_prerequisites(weak_node.concept_id)
                    if prereqs:
                        for p in prereqs:
                            p_name = navigator.get_concept_name(p) or p
                            # Recommend prerequisite of weak concepts
                            if p_name not in recommended_topics:
                                recommended_topics.append(p_name)
                                
            # If no prerequisites are recommended, recommend the weak concepts themselves
            if not recommended_topics:
                recommended_topics = list(weak_concepts)
                
            # If still empty (e.g. no weak concepts), recommend next unvisited concept
            if not recommended_topics:
                # Find all concepts, recommend the next in progression
                all_concepts = [c.concept_name for c in graph.concepts]
                for c in all_concepts:
                    if c not in concept_scores:
                        recommended_topics.append(c)
                        break
        except Exception as e:
            logger.error(f"Error resolving recommendations from graph: {e}")
            recommended_topics = list(weak_concepts)

        # 4. Generate Interview Summary
        strong_str = ", ".join(strong_concepts) if strong_concepts else "none"
        weak_str = ", ".join(weak_concepts) if weak_concepts else "none"
        rec_str = ", ".join(recommended_topics) if recommended_topics else "none"
        
        summary = (
            f"Candidate {candidate_name} completed the technical interview in the '{domain}' domain, "
            f"demonstrating an overall domain mastery score of {domain_mastery:.1%}. "
            f"They showed strong conceptual understanding of: {strong_str}. "
            f"However, areas needing further review include: {weak_str}. "
            f"We recommend prioritizing study in the following areas: {rec_str}."
        )

        return {
            "candidate_id": candidate_id,
            "candidate_name": candidate_name,
            "domain": domain,
            "domain_scores": {domain: domain_mastery},
            "concept_scores": concept_scores,
            "strong_concepts": strong_concepts,
            "weak_concepts": weak_concepts,
            "recommended_topics": recommended_topics,
            "summary": summary
        }
