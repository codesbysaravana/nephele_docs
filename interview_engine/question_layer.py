"""Question Intelligence Layer for retrieving, generating, and tracking interview questions."""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from groq import Groq
from openai import OpenAI

from .chroma_store import ChromaStore
from .database import DatabaseManager

logger = logging.getLogger(__name__)


def _call_llm_chain(prompt: str) -> str:
    """Executes the fallback LLM chain for question layer tasks, returning the raw response content."""
    providers = [
        ("groq", "llama3-70b-8192", lambda k: Groq(api_key=k)),
        ("gemini", "gemini-1.5-pro", lambda k: None),
        ("openai", "gpt-4o-mini", lambda k: OpenAI(api_key=k))
    ]

    for provider, model, client_factory in providers:
        key_name = f"{provider.upper()}_API_KEY"
        key = os.environ.get(key_name)
        if not key:
            continue
        try:
            if provider == "groq":
                client = client_factory(key)
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a professional technical interviewer. Return only JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
                return completion.choices[0].message.content or ""
            elif provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=key)
                m = genai.GenerativeModel(model)
                response = m.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        response_mime_type="application/json",
                        temperature=0.7
                    )
                )
                return response.text or ""
            elif provider == "openai":
                client = client_factory(key)
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a professional technical interviewer. Return only JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
                return completion.choices[0].message.content or ""
        except Exception as e:
            logger.warning(f"Question Layer: LLM provider {provider} failed: {e}")

    raise RuntimeError("All LLM providers failed or API keys missing.")


class QuestionLayer:
    """Manages question selection, difficulty alignment, duplicate prevention, and adaptive follow-up generation."""

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        chroma_store: Optional[ChromaStore] = None,
        bank_dir: Optional[str | Path] = None
    ) -> None:
        self.db = db_manager or DatabaseManager()
        self.chroma = chroma_store or ChromaStore()

        # Load and cache all static question banks
        self.question_bank: Dict[tuple[str, str], List[Dict[str, Any]]] = {}
        
        resolved_bank_dir = Path(bank_dir) if bank_dir else Path(__file__).parent.parent / "question_bank"
        if resolved_bank_dir.exists():
            for fpath in resolved_bank_dir.glob("*.json"):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for item in data:
                            c = item.get("concept", "").strip()
                            d = item.get("difficulty", "").strip().lower()
                            if c and d:
                                key = (c, d)
                                if key not in self.question_bank:
                                    self.question_bank[key] = []
                                self.question_bank[key].append(item)
                except Exception as e:
                    logger.error(f"Failed to load question bank file {fpath}: {e}")

    def _get_fingerprint(self, text: str) -> str:
        """Generate a normalized fingerprint of the question text to detect duplicates."""
        return re.sub(r"[^\w]", "", text.lower()).strip()

    def check_duplicate(self, question_text: str, session_id: str) -> bool:
        """Verify if a question wording is duplicate based on fingerprint, history, or semantic similarity."""
        fingerprint = self._get_fingerprint(question_text)
        if not fingerprint:
            return True

        # 1. History Check (Postgres logs)
        try:
            logs = self.db.get_session_question_logs(session_id)
            for log in logs:
                q_text = log.get("question_text") if isinstance(log, dict) else log.question_text
                if self._get_fingerprint(q_text) == fingerprint:
                    return True
        except Exception as e:
            logger.error(f"Error querying session question logs: {e}")

        # 2. Semantic Similarity Check (Chroma distance check)
        try:
            similar = self.chroma.retrieve_similar_questions_semantic(question_text, limit=3)
            # Distance threshold of < 0.15 indicates extreme semantic similarity (essentially a duplicate)
            for doc, dist in similar:
                if dist < 0.15:
                    logger.info(f"Duplicate detected via Chroma semantic similarity (distance={dist:.3f})")
                    return True
        except Exception as e:
            logger.error(f"Error checking semantic similarity in Chroma: {e}")

        return False

    def map_difficulty(self, mastery: float) -> str:
        """Map candidate mastery level to question difficulty category."""
        if mastery < 0.4:
            return "basic"
        elif mastery < 0.75:
            return "intermediate"
        else:
            return "advanced"

    def retrieve_question(self, concept: str, difficulty: str, strategy: str = "static") -> Dict[str, Any]:
        """Simple retrieval of a question from the bank or Chroma without duplicate checking."""
        key = (concept.strip(), difficulty.lower())
        items = self.question_bank.get(key, [])

        if strategy == "chroma":
            try:
                similar = self.chroma.retrieve_similar_questions(concept, limit=1)
                if similar:
                    return {
                        "question_id": f"{concept}_{difficulty}_chroma",
                        "question_text": similar[0],
                        "difficulty": difficulty,
                        "concept": concept,
                        "followups": ["Can you expand on that?", "What are the limitations of this approach?"]
                    }
            except Exception as e:
                logger.error(f"Error retrieving question from Chroma: {e}")

        if items:
            item = items[0]
            return {
                "question_id": f"{concept}_{difficulty}_static_0",
                "question_text": item["question"],
                "difficulty": difficulty,
                "concept": concept,
                "followups": item.get("followups", [])
            }

        # Fallback question wording if no questions exist
        fallback_text = f"Could you explain your understanding of {concept} and its practical applications at a {difficulty} level?"
        return {
            "question_id": f"{concept}_{difficulty}_fallback",
            "question_text": fallback_text,
            "difficulty": difficulty,
            "concept": concept,
            "followups": [
                f"What are the key trade-offs to consider when working with {concept}?",
                f"How would you optimize or scale your implementation of {concept}?"
            ]
        }

    def generate_question(
        self,
        concept: str,
        mastery: float,
        session_id: str,
        strategy: str = "hybrid"
    ) -> Dict[str, Any]:
        """Retrieve or generate question wording aligned to mastery level and avoiding duplicates."""
        difficulty = self.map_difficulty(mastery)
        key = (concept.strip(), difficulty)
        items = self.question_bank.get(key, [])

        # Filter out questions already asked in this session
        available_items = []
        for idx, item in enumerate(items):
            q_text = item["question"]
            if not self.check_duplicate(q_text, session_id):
                available_items.append((idx, item))

        # Helper to construct fallback variation if all static items are duplicates
        def _get_paraphrase_fallback(base_question: str) -> str:
            intros = [
                "Building on that, let's explore",
                "Moving forward, I'd like to ask about",
                "Great. Let's delve into",
                "Now, let's turn our attention to"
            ]
            import random
            intro = random.choice(intros)
            q_clean = base_question.replace("Can you explain", "").replace("What is", "").replace("Explain", "").strip()
            q_clean = q_clean[0].lower() + q_clean[1:] if q_clean else ""
            return f"{intro} {concept}. {base_question}"

        # 1. Static Strategy
        if strategy == "static":
            if available_items:
                idx, item = available_items[0]
                return {
                    "question_id": f"{concept}_{difficulty}_static_{idx}",
                    "question_text": item["question"],
                    "difficulty": difficulty,
                    "concept": concept,
                    "source": "static"
                }
            else:
                # Fallback wording paraphrase
                base = items[0]["question"] if items else f"Explain the core components of {concept}."
                return {
                    "question_id": f"{concept}_{difficulty}_static_paraphrase",
                    "question_text": _get_paraphrase_fallback(base),
                    "difficulty": difficulty,
                    "concept": concept,
                    "source": "static"
                }

        # 2. Chroma Strategy
        elif strategy == "chroma":
            try:
                similar = self.chroma.retrieve_similar_questions(concept, limit=5)
                for q in similar:
                    if not self.check_duplicate(q, session_id):
                        return {
                            "question_id": f"{concept}_{difficulty}_chroma_retrieved",
                            "question_text": q,
                            "difficulty": difficulty,
                            "concept": concept,
                            "source": "chroma"
                        }
            except Exception as e:
                logger.error(f"Error in Chroma question strategy: {e}")

            # Fallback to static
            return self.generate_question(concept, mastery, session_id, strategy="static")

        # 3. LLM Strategy
        elif strategy == "llm":
            try:
                prompt = f"""Generate a technical interview question for the concept '{concept}' at '{difficulty}' difficulty.
The question should be engaging, technically accurate, and encourage a detailed explanation.
Return ONLY a valid JSON object matching this schema:
{{
  "question_text": "string (the question wording)"
}}
"""
                res = _call_llm_chain(prompt)
                cleaned = res.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                parsed = json.loads(cleaned.strip())
                q_text = parsed.get("question_text", "").strip()
                if q_text and not self.check_duplicate(q_text, session_id):
                    return {
                        "question_id": f"{concept}_{difficulty}_llm_{uuid.uuid4().hex[:6]}",
                        "question_text": q_text,
                        "difficulty": difficulty,
                        "concept": concept,
                        "source": "llm"
                    }
            except Exception as e:
                logger.warning(f"LLM question generation failed: {e}. Falling back to static.")
            
            return self.generate_question(concept, mastery, session_id, strategy="static")

        # 4. Hybrid Strategy (Default)
        else:
            # Try to fetch non-duplicate static question first
            if available_items:
                idx, item = available_items[0]
                return {
                    "question_id": f"{concept}_{difficulty}_static_{idx}",
                    "question_text": item["question"],
                    "difficulty": difficulty,
                    "concept": concept,
                    "source": "static"
                }

            # Otherwise, try to fetch cached variants from Chroma
            base_item = items[0] if items else None
            if base_item:
                parent_qid = f"{concept}_{difficulty}_static_0"
                try:
                    variants = self.chroma.retrieve_question_variants(parent_qid, limit=5)
                    for v in variants:
                        if not self.check_duplicate(v, session_id):
                            return {
                                "question_id": f"{concept}_{difficulty}_chroma_variant",
                                "question_text": v,
                                "difficulty": difficulty,
                                "concept": concept,
                                "source": "chroma"
                            }
                except Exception as e:
                    logger.error(f"Error fetching Chroma variants: {e}")

            # If all else fails, generate a new variant using LLM
            if base_item:
                try:
                    parent_qid = f"{concept}_{difficulty}_static_0"
                    prompt = f"""Paraphrase and rewrite this technical interview question to make it unique and distinct, but preserve the exact core concept and difficulty:
'{base_item["question"]}'
Return ONLY a valid JSON object matching this schema:
{{
  "question_text": "string (the new question wording)"
}}
"""
                    res = _call_llm_chain(prompt)
                    cleaned = res.strip()
                    if cleaned.startswith("```json"):
                        cleaned = cleaned[7:]
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3]
                    parsed = json.loads(cleaned.strip())
                    new_q = parsed.get("question_text", "").strip()
                    if new_q and not self.check_duplicate(new_q, session_id):
                        # Store variant in Chroma for future learning
                        try:
                            self.chroma.store_question_variant(new_q, parent_qid, concept)
                        except Exception as store_err:
                            logger.error(f"Failed to cache generated variant in Chroma: {store_err}")

                        return {
                            "question_id": f"{concept}_{difficulty}_llm_variant",
                            "question_text": new_q,
                            "difficulty": difficulty,
                            "concept": concept,
                            "source": "llm"
                        }
                except Exception as e:
                    logger.warning(f"Failed to generate LLM variant: {e}")

            # Offline/LLM failed final fallback: Paraphrase static question locally
            base_q = base_item["question"] if base_item else f"Can you explain your understanding of {concept}?"
            return {
                "question_id": f"{concept}_{difficulty}_hybrid_local_paraphrase",
                "question_text": _get_paraphrase_fallback(base_q),
                "difficulty": difficulty,
                "concept": concept,
                "source": "hybrid"
            }

    def generate_followup(
        self,
        concept: str,
        question: str,
        candidate_answer: str,
        mastery: float,
        session_id: str
    ) -> Dict[str, Any]:
        """Generate an adaptive follow-up question based on the candidate's answer and current mastery."""
        difficulty = self.map_difficulty(mastery)
        key = (concept.strip(), difficulty)
        items = self.question_bank.get(key, [])

        # Fetch static follow-ups
        static_followups = []
        if items:
            static_followups = items[0].get("followups", [])
        if not static_followups and (concept.strip(), "basic") in self.question_bank:
            static_followups = self.question_bank[(concept.strip(), "basic")][0].get("followups", [])

        # Determine index based on mastery: basic mastery gets first, high gets second
        f_idx = 0 if mastery < 0.6 else min(1, len(static_followups) - 1)
        fallback_followup = static_followups[f_idx] if static_followups else "Can you elaborate on your explanation?"

        # Attempt LLM generation
        try:
            prompt = f"""You are a technical interviewer. The candidate was asked the question:
'{question}'
They provided the answer:
'{candidate_answer}'
For the concept '{concept}', based on their answer and their mastery score of {mastery:.2f}, generate an adaptive follow-up question.
- If the candidate performed well (e.g. mastery >= 0.7), ask a deeper or more advanced follow-up question on the same concept.
- If the candidate struggled (e.g. mastery < 0.5), ask a clarifying question or a simpler guiding sub-question.
Return ONLY a valid JSON object matching this schema:
{{
  "followup_text": "string (the follow-up question wording)"
}}
"""
            res = _call_llm_chain(prompt)
            cleaned = res.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            parsed = json.loads(cleaned.strip())
            f_text = parsed.get("followup_text", "").strip()
            if f_text and not self.check_duplicate(f_text, session_id):
                return {
                    "question_id": f"{concept}_{difficulty}_followup_llm",
                    "question_text": f_text,
                    "difficulty": difficulty,
                    "concept": concept,
                    "source": "llm"
                }
        except Exception as e:
            logger.warning(f"Adaptive LLM follow-up generation failed: {e}. Falling back to static.")

        return {
            "question_id": f"{concept}_{difficulty}_followup_static",
            "question_text": fallback_followup,
            "difficulty": difficulty,
            "concept": concept,
            "source": "static"
        }

    def store_question_outcome(
        self,
        question_id: str,
        question_text: str,
        concept: str,
        difficulty: str,
        candidate_answer: str,
        mastery_outcome: float,
        latency: float,
        session_id: str
    ) -> None:
        """Store the question response log and update aggregate effectiveness metrics."""
        # 1. Save to PostgreSQL
        try:
            self.db.persist_question_response(
                session_id=session_id,
                question_id=question_id,
                question_text=question_text,
                concept_id=concept,
                difficulty=difficulty,
                candidate_answer=candidate_answer,
                mastery_outcome=mastery_outcome,
                latency=latency
            )
        except Exception as e:
            logger.error(f"Failed to persist question outcome to DB: {e}")

        # 2. Save to Chroma question history collection
        try:
            self.chroma.store_question_history_log(
                question_text=question_text,
                concept=concept,
                difficulty=difficulty,
                candidate_response=candidate_answer,
                outcome=mastery_outcome,
                session_id=session_id
            )
        except Exception as e:
            logger.error(f"Failed to save question history log to Chroma: {e}")

    def get_question(
        self,
        concept: str,
        mode: str = "static",
        context_history: Optional[List[Dict[str, str]]] = None,
        chroma_store: Optional[ChromaStore] = None
    ) -> str:
        """Legacy compatibility wrapper. Retrieves question wording."""
        strategy = mode if mode in ("static", "chroma", "llm", "hybrid") else "static"
        mastery = 0.5
        session_id = "default_session"
        orig_chroma = self.chroma
        if chroma_store:
            self.chroma = chroma_store
        try:
            res = self.generate_question(concept, mastery, session_id, strategy=strategy)
            return res["question_text"]
        finally:
            self.chroma = orig_chroma

