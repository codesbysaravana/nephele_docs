"""Misconception Miner for mining candidate wrong answers and concept confusion pairs from evaluations."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from interview_engine.database import DatabaseManager
from interview_engine.chroma_store import ChromaStore
from interview_engine.storage.postgres.models import ConceptEvaluation

logger = logging.getLogger(__name__)


class MisconceptionMiner:
    """Mines pattern of failures, missing rubric signals, and concepts frequently confused together."""

    def __init__(self, db_manager: DatabaseManager, chroma_store: ChromaStore) -> None:
        self.db = db_manager
        self.chroma = chroma_store

    def mine_misconceptions(self) -> Dict[str, Any]:
        """Analyze concept evaluation outcomes to discover misconceptions and concept confusion pairs."""
        logger.info("Mining database for misconceptions and confusion pairs...")

        # 1. Fetch evaluations from database
        evals: List[Dict[str, Any]] = []
        with self.db.service.session() as session:
            rows = session.query(ConceptEvaluation).all()
            for r in rows:
                evals.append({
                    "candidate_id": r.candidate_id,
                    "concept_id": r.concept_id,
                    "question": r.question,
                    "answer": r.answer,
                    "mastery": float(r.mastery),
                    "missing_signals": r.missing_signals or [],
                    "matched_signals": r.matched_signals or []
                })

        # 2. Extract missing signals frequency per concept
        missing_freq: Dict[str, Dict[str, int]] = {}
        for ev in evals:
            cid = ev["concept_id"]
            if cid not in missing_freq:
                missing_freq[cid] = {}
            freq = missing_freq[cid]
            for sig in ev["missing_signals"]:
                freq[sig] = freq.get(sig, 0) + 1

        misconception_frequency_list = [
            {"concept": cid, "misconception": sig, "frequency": count}
            for cid, signals in missing_freq.items()
            for sig, count in signals.items()
        ]

        # 3. Classify and store explanations in Chroma for future references
        wrong_count = 0
        success_count = 0
        for ev in evals:
            cid = ev["concept_id"]
            if ev["mastery"] <= 0.40:
                wrong_count += 1
                try:
                    # Save incorrect answer to Chroma misconceptions collection
                    self.chroma.store_misconception(cid, ev["answer"])
                except Exception as e:
                    logger.debug(f"Failed to save incorrect answer to Chroma: {e}")
            elif ev["mastery"] >= 0.85:
                success_count += 1
                try:
                    # Save high-quality explanation to Chroma concept examples collection
                    self.chroma.store_example(cid, ev["question"], ev["answer"])
                except Exception as e:
                    logger.debug(f"Failed to save high-quality explanation to Chroma: {e}")

        # 4. Discover concept confusion pairs (concepts failed by same candidate in same session)
        failed_by_cand: Dict[str, set[str]] = {}
        for ev in evals:
            if ev["mastery"] <= 0.40:
                cand = ev["candidate_id"]
                if cand not in failed_by_cand:
                    failed_by_cand[cand] = set()
                failed_by_cand[cand].add(ev["concept_id"])

        confusion_pairs: Dict[tuple[str, str], int] = {}
        for cand, failed_set in failed_by_cand.items():
            failed_list = sorted(list(failed_set))
            for i in range(len(failed_list)):
                for j in range(i + 1, len(failed_list)):
                    pair = (failed_list[i], failed_list[j])
                    confusion_pairs[pair] = confusion_pairs.get(pair, 0) + 1

        confusion_pairs_formatted = [
            {"concept_a": c1, "concept_b": c2, "frequency": count}
            for (c1, c2), count in confusion_pairs.items()
        ]

        logger.info(f"Mining complete: discovered {len(confusion_pairs_formatted)} confusion pairs, stored {wrong_count} misconceptions and {success_count} good examples.")
        return {
            "misconception_frequency": misconception_frequency_list,
            "concept_confusion_pairs": confusion_pairs_formatted,
            "wrong_answers_count": wrong_count,
            "successful_answers_count": success_count
        }
