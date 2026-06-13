"""
Nephele Interview Engine — Orchestrator.

The central brain of the interview system. It holds the current Session,
manages the FSM, consumes multi-modal signals, and coordinates with
AI components (LLM, Scorer) to drive the interview forward.
"""

import logging
from typing import Optional, Tuple

from backend.models.domain import (
    AnswerRecord,
    InterviewSession,
    MultiModalSignals,
    QuestionRecord,
)
from backend.models.enums import Difficulty, InterviewState, RoundType
from backend.models.events import StateChangedEvent

from .state_machine import InterviewStateMachine, TransitionError
from .conversation_manager import ConversationManager
from .multimodal_fusion import MultiModalFusionEngine
from .adaptive_engine import AdaptiveDecisionEngine
from backend.ai.cognitive_engine import CognitiveEngine

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# MOCK EVENT BUS
# (To be replaced when WebSocket layer is built)
# ---------------------------------------------------------------------------
class MockEventBus:
    def publish(self, event):
        logger.info(f"MockEventBus published: {event.event_type} - {event.to_dict()}")


# ---------------------------------------------------------------------------
# ORCHESTRATOR
# ---------------------------------------------------------------------------

class InterviewOrchestrator:
    """
    Coordinates the entire interview lifecycle for a single session.
    """

    def __init__(self, session: InterviewSession):
        self.session = session
        self.state_machine = InterviewStateMachine(initial_state=session.current_state)
        
        # Initialize Core Intelligence Engines
        self.conversation = ConversationManager(session, max_qa_pairs=4)
        self.fusion = MultiModalFusionEngine(history_capacity=100)
        self.adaptive = AdaptiveDecisionEngine(score_threshold_up=85.0, score_threshold_down=50.0)
        self.cognitive = CognitiveEngine()
        
        self.event_bus = MockEventBus()

        self._register_state_hooks()

    def _register_state_hooks(self) -> None:
        """Wire up FSM transitions to orchestrator actions."""
        # When entering any state, publish a StateChangedEvent
        for state in InterviewState:
            self.state_machine.add_hook(
                state, 'enter', self._on_enter_state
            )

    def _on_enter_state(self, session_id: str, state: InterviewState, event: str, trigger: str, **kwargs) -> None:
        """Generic hook called on every state entry."""
        self.session.previous_state = self.session.current_state
        self.session.current_state = state
        
        evt = StateChangedEvent(
            session_id=self.session.id,
            from_state=self.session.previous_state or InterviewState.IDLE,
            to_state=state,
            trigger=trigger
        )
        self.event_bus.publish(evt)

    async def start_interview(self) -> str:
        """Trigger the start of the interview."""
        self.state_machine.trigger("start", self.session.id)
        # Simplified greeting. Later this can be LLM-generated.
        greeting_text = f"Hello {self.session.candidate.name or 'there'}. Welcome to Nephele. I am your AI Interviewer. How are you today?"
        return greeting_text

    async def process_candidate_message(self, transcript: str, duration: float) -> str:
        """
        Main entry point for candidate speech.
        
        1. Records the answer.
        2. Applies multi-modal metrics.
        3. Evaluates and Generates next step using Cognitive Engine.
        """
        if not self.session.is_active:
            logger.warning(f"Message received but session {self.session.id} is not active.")
            return "The interview is currently paused or completed."

        # Add user transcript to history
        self.session.add_to_history("user", transcript)

        # Handle non-round states linearly for now (Setup Phase)
        if not self.session.is_in_round:
            response_text = self._handle_pre_interview(transcript)
            self.session.add_to_history("assistant", response_text)
            return response_text

        # ---------------------------------------------------------
        # IN-ROUND INTERVIEW PROCESSING
        # ---------------------------------------------------------

        # 1. Create Answer Record
        last_q = self.session.last_question
        answer = AnswerRecord(
            question_id=last_q.id if last_q else "",
            session_id=self.session.id,
            transcript=transcript,
            duration_seconds=duration,
        )

        # 2. Snapshot Vision & Audio Metrics (from Fusion Engine)
        answer.vision_metrics = self.session.current_signals.vision
        
        # Minimal Audio approximation for demo
        # (Assuming ~150 wpm for normal speech)
        words = len(transcript.split())
        wpm = (words / duration) * 60 if duration > 0 else 0
        self.session.current_signals.audio.words_per_minute = wpm
        answer.audio_metrics = self.session.current_signals.audio

        # 3. Analyze Behavioral Trends (Vision rolling buffer)
        behavioral_trends = self.fusion.analyze_behavioral_trends()

        # 4. Adaptive Decision (What should we do next?)
        # We pass a preliminary score based on audio/vision to the adaptive engine
        # before the LLM grades the actual text.
        audio_conf = self.fusion.compute_audio_confidence(wpm, 0.1, 0.0)
        prelim_score = (self.session.current_signals.vision.engagement_score * 0.4) + (audio_conf * 0.6)
        
        adaptive_decision = self.adaptive.analyze(
            self.session, 
            latest_score=prelim_score, 
            behavioral_trends=behavioral_trends
        )
        
        # Apply difficulty changes
        self.session.current_difficulty = adaptive_decision.new_difficulty

        # 5. Build LLM Context Window
        context = self.conversation.build_llm_context()

        # 6. Cognitive Engine (Single Call: Evaluate + Generate)
        scores, next_q = await self.cognitive.evaluate_and_generate(
            context_window=context,
            latest_transcript=transcript,
            adaptive_decision=adaptive_decision,
            session_id=self.session.id,
            round_type=self.session.current_round_type or RoundType.HR,
            difficulty=self.session.current_difficulty
        )

        # 7. Update Answer Record with LLM Scores
        answer.language_scores = scores
        self.session.current_signals.language_technical = scores.get("technical_correctness", 0.0)
        self.session.current_signals.language_communication = scores.get("communication_quality", 0.0)
        self.session.current_signals.language_depth = scores.get("answer_depth", 0.0)
        self.session.current_signals.language_relevance = scores.get("relevance", 0.0)

        # Calculate final fused score for the answer
        answer.answer_score = self.session.current_signals.overall_confidence
        self.session.answers.append(answer)
        
        logger.info(f"Answer Fused Score: {answer.answer_score:.1f}/100")

        # Link follow-up if applicable
        if adaptive_decision.action == "follow_up" and last_q:
            next_q.parent_question_id = last_q.id
            next_q.follow_up_depth = last_q.follow_up_depth + 1

        # 8. Check Round Progression
        if self.session.current_round_question_count >= self.session.current_round_config_limit and adaptive_decision.action != "follow_up":
            # Time to move to the next round
            try:
                self.state_machine.trigger("round_complete", self.session.id)
                response_text = "That concludes this round. Let's move on to the next section. " + next_q.question_text
                
                # Advance round in session config
                next_idx = self.session.current_round_index + 1
                if next_idx < len(self.session.config.round_order):
                    self.session.current_round_index = next_idx
                    self.session.current_round_type = self.session.config.round_order[next_idx]
                    next_q.round_type = self.session.current_round_type
            except TransitionError:
                response_text = "Thank you. We have reached the end of the interview questions."
                return response_text
        else:
            response_text = next_q.question_text

        # Record the new question
        self.session.questions.append(next_q)
        self.conversation.record_question(next_q.question_hash)

        # Reset signals and buffers for the NEXT answer window
        self.session.current_signals.reset_for_next_answer()
        self.fusion.clear_buffers()

        self.session.add_to_history("assistant", response_text)
        return response_text


    def _handle_pre_interview(self, transcript: str) -> str:
        """Handles linear progression before the actual rounds start."""
        response_text = "I received your message."
        
        if self.session.current_state == InterviewState.GREETING:
            self.state_machine.trigger("greeting_done", self.session.id)
            response_text = "Before we begin, could you please verify your name?"
        elif self.session.current_state == InterviewState.CANDIDATE_VERIFICATION:
            self.state_machine.trigger("skip_resume", self.session.id)
            response_text = "Great. And what specific role are you interviewing for today?"
        elif self.session.current_state == InterviewState.ROLE_SELECTION:
            # Extract role from transcript roughly
            self.session.candidate.target_role = transcript.strip()
            self.state_machine.trigger("role_selected", self.session.id)
            self.state_machine.trigger("setup_done", self.session.id)
            
            # Setup first round
            self.session.current_round_index = 0
            self.session.current_round_type = self.session.config.round_order[0]
            
            # Seed the first question
            first_q = QuestionRecord(
                session_id=self.session.id,
                round_type=self.session.current_round_type,
                difficulty=self.session.current_difficulty,
                question_text="Could you please tell me a little bit about yourself and your background?"
            )
            self.session.questions.append(first_q)
            self.conversation.record_question(first_q.question_hash)
            
            response_text = f"Thank you. I have set your role to {self.session.candidate.target_role}. Let's begin the {self.session.current_round_type.display_name} round. {first_q.question_text}"

        return response_text

    def update_vision_signals(self, eye_contact: float, engagement: float, yaw: float, pitch: float, roll: float, face_visible: bool) -> None:
        """Called by the WebSocket handler when new vision metrics arrive from Edge."""
        # Update Fusion Engine
        self.fusion.process_vision_frame(
            signals=self.session.current_signals,
            eye_contact=eye_contact,
            engagement=engagement,
            yaw=yaw,
            pitch=pitch,
            roll=roll,
            face_visible=face_visible
        )
