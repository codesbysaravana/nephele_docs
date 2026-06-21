"""ChromaDB service for managing vector store collections, embeddings, and semantic queries."""

from __future__ import annotations

import hashlib
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.api import ClientAPI

logger = logging.getLogger(__name__)


def get_dummy_embedding(text: str, dim: int = 128) -> List[float]:
    """Generate a consistent, deterministic mock embedding based on MD5 hashing for offline tests."""
    h = hashlib.md5(text.encode("utf-8")).digest()
    emb = []
    for i in range(dim):
        val = float(h[i % len(h)]) / 127.5 - 1.0
        emb.append(val)
    return emb


class ChromaService:
    """Manages collections and semantic search operations on ChromaDB."""

    def __init__(self, client: Optional[ClientAPI] = None) -> None:
        if client is not None:
            self.client = client
        else:
            host = os.environ.get("CHROMA_SERVER_HOST")
            port = os.environ.get("CHROMA_SERVER_PORT")
            persist_path = os.environ.get("CHROMA_PERSIST_PATH")

            if host and port:
                logger.info(f"Connecting to ChromaDB client-server at {host}:{port}")
                self.client = chromadb.HttpClient(host=host, port=port)
            elif persist_path:
                logger.info(f"Connecting to persistent ChromaDB at {persist_path}")
                self.client = chromadb.PersistentClient(path=persist_path)
            else:
                logger.info("Initializing in-memory Ephemeral ChromaDB client")
                self.client = chromadb.EphemeralClient()

        # Ensure collections are created at initialization
        self.client.get_or_create_collection(name="questions", metadata={"hnsw:space": "cosine"})
        self.client.get_or_create_collection(name="answers", metadata={"hnsw:space": "cosine"})
        self.client.get_or_create_collection(name="misconceptions", metadata={"hnsw:space": "cosine"})
        self.client.get_or_create_collection(name="concept_examples", metadata={"hnsw:space": "cosine"})
        self.client.get_or_create_collection(name="interview_memory", metadata={"hnsw:space": "cosine"})
        self.client.get_or_create_collection(name="question_variants", metadata={"hnsw:space": "cosine"})
        self.client.get_or_create_collection(name="question_history", metadata={"hnsw:space": "cosine"})

    @property
    def questions(self):
        return self.client.get_or_create_collection(name="questions", metadata={"hnsw:space": "cosine"})

    @property
    def answers(self):
        return self.client.get_or_create_collection(name="answers", metadata={"hnsw:space": "cosine"})

    @property
    def misconceptions(self):
        return self.client.get_or_create_collection(name="misconceptions", metadata={"hnsw:space": "cosine"})

    @property
    def concept_examples(self):
        return self.client.get_or_create_collection(name="concept_examples", metadata={"hnsw:space": "cosine"})

    @property
    def interview_memory(self):
        return self.client.get_or_create_collection(name="interview_memory", metadata={"hnsw:space": "cosine"})

    @property
    def question_variants(self):
        return self.client.get_or_create_collection(name="question_variants", metadata={"hnsw:space": "cosine"})

    @property
    def question_history(self):
        return self.client.get_or_create_collection(name="question_history", metadata={"hnsw:space": "cosine"})

    def store_question(self, question_text: str, concept: str, question_id: Optional[str] = None) -> str:
        """Store a question with concept metadata."""
        qid = question_id or str(uuid.uuid4())
        emb = get_dummy_embedding(question_text)
        
        self.questions.add(
            ids=[qid],
            documents=[question_text],
            embeddings=[emb],
            metadatas=[{
                "concept": concept,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "question"
            }]
        )
        return qid

    def store_answer(
        self,
        answer_text: str,
        concept: str,
        question_id: str,
        candidate_id: str,
        answer_id: Optional[str] = None
    ) -> str:
        """Store candidate's answer with associated context."""
        aid = answer_id or str(uuid.uuid4())
        emb = get_dummy_embedding(answer_text)
        
        self.answers.add(
            ids=[aid],
            documents=[answer_text],
            embeddings=[emb],
            metadatas=[{
                "concept": concept,
                "question_id": question_id,
                "candidate_id": candidate_id,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "answer"
            }]
        )
        return aid

    def store_misconception(self, concept: str, misconception: str) -> str:
        """Store a common misconception mapped to a concept."""
        mid = str(uuid.uuid4())
        emb = get_dummy_embedding(misconception)
        
        self.misconceptions.add(
            ids=[mid],
            documents=[misconception],
            embeddings=[emb],
            metadatas=[{
                "concept": concept,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "misconception"
            }]
        )
        return mid

    def store_example(self, concept: str, question: str, reference_answer: str) -> str:
        """Store a reference concept example."""
        eid = str(uuid.uuid4())
        combined_text = f"Question: {question}\nAnswer: {reference_answer}"
        emb = get_dummy_embedding(combined_text)
        
        self.concept_examples.add(
            ids=[eid],
            documents=[combined_text],
            embeddings=[emb],
            metadatas=[{
                "concept": concept,
                "question": question,
                "reference_answer": reference_answer,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "example"
            }]
        )
        return eid

    def store_memory(
        self,
        candidate_id: str,
        memory_text: str,
        metadata: Optional[Dict[str, Any]] = None,
        memory_id: Optional[str] = None
    ) -> str:
        """Store a semantic interview memory (e.g. eye contact trends, visual behavioral signals)."""
        mid = memory_id or str(uuid.uuid4())
        emb = get_dummy_embedding(memory_text)
        
        meta = metadata or {}
        meta.update({
            "candidate_id": candidate_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        self.interview_memory.add(
            ids=[mid],
            documents=[memory_text],
            embeddings=[emb],
            metadatas=[meta]
        )
        return mid

    def retrieve_similar_questions(self, concept: str, limit: int = 3) -> List[str]:
        """Retrieve past questions associated with a concept."""
        try:
            results = self.questions.get(
                where={"concept": concept},
                limit=limit
            )
            return results.get("documents", []) or []
        except Exception as e:
            logger.error(f"Error retrieving questions from Chroma: {e}")
            return []

    def retrieve_similar_answers(self, query_text: str, limit: int = 3) -> List[str]:
        """Perform semantic search for similar candidate answers."""
        try:
            emb = get_dummy_embedding(query_text)
            results = self.answers.query(
                query_embeddings=[emb],
                n_results=limit
            )
            documents = results.get("documents", [])
            return documents[0] if documents else []
        except Exception as e:
            logger.error(f"Error retrieving answers from Chroma: {e}")
            return []

    def retrieve_misconceptions(self, concept: str, limit: int = 3) -> List[str]:
        """Retrieve common misconceptions for a concept."""
        try:
            results = self.misconceptions.get(
                where={"concept": concept},
                limit=limit
            )
            return results.get("documents", []) or []
        except Exception as e:
            logger.error(f"Error retrieving misconceptions from Chroma: {e}")
            return []

    def retrieve_examples(self, concept: str, limit: int = 3) -> List[str]:
        """Retrieve reference examples for a concept."""
        try:
            results = self.concept_examples.get(
                where={"concept": concept},
                limit=limit
            )
            return results.get("documents", []) or []
        except Exception as e:
            logger.error(f"Error retrieving concept examples from Chroma: {e}")
            return []

    def retrieve_memory(self, candidate_id: str, query_text: str, limit: int = 3) -> List[str]:
        """Perform semantic search over candidate interview memory."""
        try:
            emb = get_dummy_embedding(query_text)
            results = self.interview_memory.query(
                query_embeddings=[emb],
                n_results=limit,
                where={"candidate_id": candidate_id}
            )
            documents = results.get("documents", [])
            return documents[0] if documents else []
        except Exception as e:
            logger.error(f"Error retrieving memories from Chroma: {e}")
            return []

    def store_question_variant(self, question_text: str, parent_question_id: str, concept: str) -> str:
        """Store a semantic question variant."""
        vid = str(uuid.uuid4())
        emb = get_dummy_embedding(question_text)
        self.question_variants.add(
            ids=[vid],
            documents=[question_text],
            embeddings=[emb],
            metadatas=[{
                "parent_question_id": parent_question_id,
                "concept": concept,
                "timestamp": datetime.utcnow().isoformat()
            }]
        )
        return vid

    def retrieve_question_variants(self, parent_question_id: str, limit: int = 3) -> List[str]:
        """Retrieve question variants for a given parent question ID."""
        try:
            results = self.question_variants.get(
                where={"parent_question_id": parent_question_id},
                limit=limit
            )
            return results.get("documents", []) or []
        except Exception as e:
            logger.error(f"Error retrieving question variants from Chroma: {e}")
            return []

    def store_question_history_log(
        self,
        question_text: str,
        concept: str,
        difficulty: str,
        candidate_response: str,
        outcome: float,
        session_id: str
    ) -> str:
        """Store past question execution outcome for Chroma learning."""
        hid = str(uuid.uuid4())
        emb = get_dummy_embedding(question_text)
        self.question_history.add(
            ids=[hid],
            documents=[question_text],
            embeddings=[emb],
            metadatas=[{
                "concept": concept,
                "difficulty": difficulty,
                "candidate_response": candidate_response,
                "outcome": float(outcome),
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }]
        )
        return hid

    def retrieve_similar_history(self, query_text: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Perform semantic search over historical questions asked and return their outcomes."""
        try:
            emb = get_dummy_embedding(query_text)
            results = self.question_history.query(
                query_embeddings=[emb],
                n_results=limit
            )
            documents = results.get("documents", [])
            metadatas = results.get("metadatas", [])
            
            output = []
            if documents and metadatas:
                for doc, meta in zip(documents[0], metadatas[0]):
                    output.append({
                        "question_text": doc,
                        "concept": meta.get("concept"),
                        "difficulty": meta.get("difficulty"),
                        "candidate_response": meta.get("candidate_response"),
                        "outcome": meta.get("outcome"),
                        "session_id": meta.get("session_id")
                    })
            return output
        except Exception as e:
            logger.error(f"Error retrieving question history from Chroma: {e}")
            return []

    def retrieve_similar_questions_semantic(self, query_text: str, limit: int = 3) -> List[tuple[str, float]]:
        """Perform semantic search for similar questions, returning documents and their distances."""
        try:
            emb = get_dummy_embedding(query_text)
            results = self.questions.query(
                query_embeddings=[emb],
                n_results=limit
            )
            documents = results.get("documents", [])
            distances = results.get("distances", [])
            
            output = []
            if documents and distances:
                for doc, dist in zip(documents[0], distances[0]):
                    output.append((doc, float(dist)))
            return output
        except Exception as e:
            logger.error(f"Error retrieving similar questions semantically: {e}")
            return []


