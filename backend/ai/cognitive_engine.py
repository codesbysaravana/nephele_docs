"""
Nephele Interview Engine — Cognitive Engine.

Combines answer evaluation and question generation into a single LLM call
to minimize latency. Uses the Groq API with JSON mode to ensure structured
outputs.
"""

import json
import logging
from typing import Tuple, Dict

import groq
from app.config import GROQ_API_KEY
from backend.models.domain import QuestionRecord
from backend.models.enums import RoundType, Difficulty
from backend.interview.adaptive_engine import AdaptiveDecision

logger = logging.getLogger(__name__)


class CognitiveEngine:
    """
    Handles interactions with the LLM. 
    Evaluates answers and generates the next question simultaneously.
    """

    SYSTEM_PROMPT = """You are Nephele, a professional AI Interviewer.
Your task is to EVALUATE the candidate's last answer and GENERATE the next question.

You MUST respond in valid JSON format matching this schema exactly:
{
    "evaluation": {
        "technical_correctness": float (1.0 to 10.0),
        "communication_quality": float (1.0 to 10.0),
        "answer_depth": float (1.0 to 10.0),
        "relevance": float (1.0 to 10.0),
        "professionalism": float (1.0 to 10.0)
    },
    "next_question_text": "string (the exact words you will speak next)"
}

Rules for the Next Question:
1. Speak naturally and professionally.
2. If this is a follow-up, dig deeper into the previous answer.
3. If moving to a new question, ensure it matches the current round and difficulty.
4. Do NOT use markdown actions (e.g., *nods*).
5. Always acknowledge their previous answer briefly before asking the next question.
"""

    def __init__(self, model_name: str = "meta-llama/llama-4-scout-17b-16e-instruct"):
        """Initialize the Groq client."""
        # Using a model that robustly supports JSON mode.
        self.client = groq.AsyncGroq(api_key=GROQ_API_KEY)
        self.model_name = model_name

    async def evaluate_and_generate(
        self,
        context_window: str,
        latest_transcript: str,
        adaptive_decision: AdaptiveDecision,
        session_id: str,
        round_type: RoundType,
        difficulty: Difficulty,
    ) -> Tuple[Dict[str, float], QuestionRecord]:
        """
        Single LLM call to evaluate the last answer and generate the next question.
        """
        
        # Build the user prompt
        user_prompt = f"""
{context_window}

--- LATEST CANDIDATE ANSWER ---
{latest_transcript}

--- INSTRUCTIONS FOR NEXT QUESTION ---
Current Round: {round_type.display_name}
Target Difficulty: {difficulty.value.upper()}
Action: {adaptive_decision.action.upper()}
Behavioral Directive: {adaptive_decision.behavioral_directive or 'None'}

Please provide the evaluation of the latest answer and the text for the next question.
Ensure output is ONLY valid JSON.
"""

        try:
            logger.info(f"[Session {session_id}] Calling CognitiveEngine (Model: {self.model_name})...")
            completion = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            raw_response = completion.choices[0].message.content
            logger.debug(f"LLM JSON Response: {raw_response}")
            
            data = json.loads(raw_response)
            
            # Extract evaluation
            eval_data = data.get("evaluation", {})
            scores = {
                "technical_correctness": float(eval_data.get("technical_correctness", 5.0)),
                "communication_quality": float(eval_data.get("communication_quality", 5.0)),
                "answer_depth": float(eval_data.get("answer_depth", 5.0)),
                "relevance": float(eval_data.get("relevance", 5.0)),
                "professionalism": float(eval_data.get("professionalism", 5.0)),
            }
            
            # Extract next question
            next_q_text = data.get("next_question_text", "Could you tell me more about that?")
            
            # Create the Question Record
            next_q = QuestionRecord(
                session_id=session_id,
                round_type=round_type,
                difficulty=difficulty,
                question_text=next_q_text
            )
            
            # Track follow-up lineage (simplified: if action is follow-up, mark it)
            if adaptive_decision.action == "follow_up":
                next_q.parent_question_id = "previous_question_id" # Real ID linked in orchestrator
                
            return scores, next_q

        except Exception as e:
            logger.error(f"Cognitive Engine failed: {e}", exc_info=True)
            # Fallback
            fallback_scores = {
                "technical_correctness": 5.0,
                "communication_quality": 5.0,
                "answer_depth": 5.0,
                "relevance": 5.0,
                "professionalism": 5.0,
            }
            fallback_q = QuestionRecord(
                session_id=session_id,
                round_type=round_type,
                difficulty=difficulty,
                question_text="Thank you. Could you elaborate a bit more on your experience?"
            )
            return fallback_scores, fallback_q
