"""
Nephele Interview Engine — Conversation Manager.

Manages the conversational memory for an interview session.
Provides utilities for building optimized context windows for the LLM
to prevent token limit exhaustion while maintaining context.
"""

from typing import List, Dict, Optional

from backend.models.domain import InterviewSession
from backend.models.enums import RoundType


class ConversationManager:
    """
    Maintains and shapes the conversational history of an interview session.
    """

    def __init__(self, session: InterviewSession, max_qa_pairs: int = 5):
        """
        Args:
            session: The InterviewSession domain object to wrap.
            max_qa_pairs: Maximum number of previous Q&A turns to include
                          in the dynamic context window.
        """
        self.session = session
        self.max_qa_pairs = max_qa_pairs

    def build_llm_context(self) -> str:
        """
        Build a concise, sliding-window text summary of the conversation
        history to inject into the LLM prompt.
        
        It includes:
        - Candidate profile snippet
        - Current Round info
        - The last N questions and answers
        """
        context_parts = []
        
        # 1. Candidate Context
        context_parts.append("--- CANDIDATE PROFILE ---")
        context_parts.append(self.session.candidate.to_context_summary())
        
        # 2. Round Context
        if self.session.current_round_type:
            context_parts.append(f"\n--- CURRENT ROUND: {self.session.current_round_type.display_name} ---")
            context_parts.append(f"Difficulty Level: {self.session.current_difficulty.value.upper()}")
            
            # 3. Recent Q&A History
            context_parts.append("\n--- RECENT CONVERSATION HISTORY ---")
            
            # Get the most recent Q&A pairs (up to max_qa_pairs)
            # We match questions and answers by index/ID conceptually.
            # In our session, `questions` and `answers` grow together, 
            # but answers are recorded *after* questions.
            
            # Zip the most recent questions and answers
            recent_q_count = min(len(self.session.questions), self.max_qa_pairs)
            recent_questions = self.session.questions[-recent_q_count:] if recent_q_count > 0 else []
            
            for q in recent_questions:
                context_parts.append(f"Q: {q.question_text}")
                # Find the corresponding answer
                matching_answers = [a for a in self.session.answers if a.question_id == q.id]
                if matching_answers:
                    ans = matching_answers[0]
                    context_parts.append(f"A: {ans.transcript}")
                    # Briefly add previous evaluation context if available
                    if ans.answer_score > 0:
                        context_parts.append(f"[System Note: Prev Answer Score: {ans.answer_score:.1f}/100]")
                else:
                    context_parts.append("A: (Pending...)")
        else:
             context_parts.append("\n--- PRE-INTERVIEW CHAT ---")
             # Just append the last few raw conversation history dicts
             recent_msgs = self.session.conversation_history[-self.max_qa_pairs * 2:]
             for msg in recent_msgs:
                 role_name = "Agent" if msg["role"] == "assistant" else "Candidate"
                 context_parts.append(f"{role_name}: {msg['content']}")

        return "\n".join(context_parts)

    def is_duplicate_question(self, question_hash: str) -> bool:
        """Check if a question has already been asked."""
        return question_hash in self.session.asked_question_hashes

    def record_question(self, question_hash: str) -> None:
        """Mark a question as asked to prevent repetition."""
        self.session.asked_question_hashes.add(question_hash)
