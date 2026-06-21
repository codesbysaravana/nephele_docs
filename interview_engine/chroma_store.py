"""ChromaDB store adapter wrapping the new production-ready ChromaService."""

from __future__ import annotations

import logging
from typing import Any, List, Optional
import chromadb

from .storage.chroma.service import ChromaService

logger = logging.getLogger(__name__)


class ChromaStore:
    """Wrapper delegating legacy vector store calls to the production-ready ChromaService."""

    def __init__(self, client: Optional[chromadb.ClientAPI] = None) -> None:
        self.service = ChromaService(client=client)

    def store_question(self, question_text: str, concept: str, question_id: Optional[str] = None) -> str:
        """Store a question wording in Chroma."""
        return self.service.store_question(question_text, concept, question_id)

    def store_answer(self, answer_text: str, concept: str, question_id: str, answer_id: Optional[str] = None) -> str:
        """Store candidate's answer wording in Chroma."""
        # Use default candidate ID for backward compatibility
        return self.service.store_answer(
            answer_text=answer_text,
            concept=concept,
            question_id=question_id,
            candidate_id="default_candidate",
            answer_id=answer_id
        )

    def store_misconception(self, concept: str, misconception: str) -> str:
        """Store a misconception mapped to a concept."""
        return self.service.store_misconception(concept, misconception)

    def store_example(self, concept: str, question: str, reference_answer: str) -> str:
        """Store a reference concept example."""
        return self.service.store_example(concept, question, reference_answer)

    def retrieve_similar_questions(self, concept: str, limit: int = 3) -> List[str]:
        """Retrieve past questions associated with a concept."""
        return self.service.retrieve_similar_questions(concept, limit)

    def retrieve_similar_answers(self, query_text: str, limit: int = 3) -> List[str]:
        """Perform semantic search for similar candidate answers."""
        return self.service.retrieve_similar_answers(query_text, limit)

    def retrieve_misconceptions(self, concept: str, limit: int = 3) -> List[str]:
        """Retrieve common misconceptions for a concept."""
        return self.service.retrieve_misconceptions(concept, limit)

    def retrieve_examples(self, concept: str, limit: int = 3) -> List[str]:
        """Retrieve reference examples for a concept."""
        return self.service.retrieve_examples(concept, limit)

    def store_question_variant(self, question_text: str, parent_question_id: str, concept: str) -> str:
        """Store a semantic question variant in Chroma."""
        return self.service.store_question_variant(question_text, parent_question_id, concept)

    def retrieve_question_variants(self, parent_question_id: str, limit: int = 3) -> List[str]:
        """Retrieve question variants for a parent question ID from Chroma."""
        return self.service.retrieve_question_variants(parent_question_id, limit)

    def store_question_history_log(
        self,
        question_text: str,
        concept: str,
        difficulty: str,
        candidate_response: str,
        outcome: float,
        session_id: str
    ) -> str:
        """Store question outcome history log in Chroma."""
        return self.service.store_question_history_log(
            question_text, concept, difficulty, candidate_response, outcome, session_id
        )

    def retrieve_similar_history(self, query_text: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Retrieve similar past question history records and their outcomes from Chroma."""
        return self.service.retrieve_similar_history(query_text, limit)

    def retrieve_similar_questions_semantic(self, query_text: str, limit: int = 3) -> List[tuple[str, float]]:
        """Retrieve semantically similar questions and their distances from Chroma."""
        return self.service.retrieve_similar_questions_semantic(query_text, limit)


