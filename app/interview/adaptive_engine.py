"""
Nephele Interview Engine — Adaptive Decision Engine.

Responsible for deciding how the interview should adapt based on the
candidate's performance and behavioral metrics. Controls difficulty
scaling, follow-up decisions, and pacing.
"""

import logging
from dataclasses import dataclass

from app.models.domain import InterviewSession
from app.models.enums import Difficulty

logger = logging.getLogger(__name__)


@dataclass
class AdaptiveDecision:
    """The outcome of the Adaptive Engine's analysis."""
    new_difficulty: Difficulty
    action: str  # "next_question", "follow_up", "end_topic"
    behavioral_directive: str  # e.g., "Candidate seems nervous, be encouraging."


class AdaptiveDecisionEngine:
    """
    Makes logic decisions for the interview flow based on fused metrics.
    """

    def __init__(self, score_threshold_up: float = 85.0, score_threshold_down: float = 50.0):
        self.threshold_up = score_threshold_up
        self.threshold_down = score_threshold_down

    def analyze(self, session: InterviewSession, latest_score: float, behavioral_trends: dict) -> AdaptiveDecision:
        """
        Determine the next steps for the interview.
        """
        current_diff = session.current_difficulty
        action = "next_question"
        directive = ""

        # 1. Behavioral Adjustments
        if behavioral_trends.get("face_lost"):
            directive = "The candidate is currently out of frame. Politely ask them to remain visible."
            action = "re_engage"
        elif behavioral_trends.get("sustained_engagement_drop"):
            directive = "The candidate seems disengaged. Try to make the next question more interactive or relatable."
        elif behavioral_trends.get("poor_eye_contact"):
            directive = "The candidate might be reading from notes. Ask a question that requires spontaneous problem-solving."
            
        # 2. Topic / Follow-up Logic
        if session.last_answer and session.last_answer.language_scores:
            scores = session.last_answer.language_scores
            # If technical correctness is good, but depth is low -> ask a follow-up to dig deeper.
            if scores.get("technical_correctness", 0) >= 7.0 and scores.get("answer_depth", 0) < 5.0:
                # Limit follow-ups to prevent infinite drilling
                last_q = session.last_question
                if last_q and last_q.follow_up_depth < session.config.max_follow_ups_per_question:
                    action = "follow_up"

        # 3. Difficulty Scaling
        new_diff = current_diff
        if latest_score >= self.threshold_up:
            new_diff = current_diff.increase()
            if new_diff != current_diff:
                logger.info(f"Difficulty increased to {new_diff.value}")
                if not directive:
                    directive = "The candidate is doing well. Ask a more challenging question."
        elif latest_score <= self.threshold_down:
            new_diff = current_diff.decrease()
            if new_diff != current_diff:
                logger.info(f"Difficulty decreased to {new_diff.value}")
                if not directive:
                    directive = "The candidate struggled with the last question. Offer a simpler, foundational question."

        return AdaptiveDecision(
            new_difficulty=new_diff,
            action=action,
            behavioral_directive=directive
        )
