"""
Nephele Interview Engine — State Machine.

A table-driven finite state machine (FSM) that governs the interview flow.
It enforces valid transitions and executes optional callback hooks.
"""

import logging
from typing import Any, Callable, Dict, Optional

from app.models.enums import InterviewState

logger = logging.getLogger(__name__)


# Signature for transition guard/action callbacks
# callback(session_id, **kwargs) -> bool (guards) or None (actions)
TransitionCallback = Callable[..., Any]


class TransitionError(Exception):
    """Raised when an invalid transition is attempted."""
    pass


class InterviewStateMachine:
    """
    Finite State Machine for managing interview lifecycle.
    
    Provides strict transition rules, pre-transition guards, and 
    post-transition hooks.
    """

    # The transition table: {FromState: {trigger: ToState}}
    TRANSITIONS: Dict[InterviewState, Dict[str, InterviewState]] = {
        InterviewState.IDLE: {
            "start": InterviewState.GREETING,
        },
        InterviewState.GREETING: {
            "greeting_done": InterviewState.CANDIDATE_VERIFICATION,
            "error": InterviewState.ERROR,
        },
        InterviewState.CANDIDATE_VERIFICATION: {
            "verified": InterviewState.RESUME_COLLECTION,
            "skip_resume": InterviewState.ROLE_SELECTION,
            "error": InterviewState.ERROR,
        },
        InterviewState.RESUME_COLLECTION: {
            "resume_received": InterviewState.RESUME_ANALYSIS,
            "skip": InterviewState.ROLE_SELECTION,
            "error": InterviewState.ERROR,
        },
        InterviewState.RESUME_ANALYSIS: {
            "analysis_done": InterviewState.ROLE_SELECTION,
            "error": InterviewState.ERROR,
        },
        InterviewState.ROLE_SELECTION: {
            "role_selected": InterviewState.INTERVIEW_SETUP,
            "error": InterviewState.ERROR,
        },
        InterviewState.INTERVIEW_SETUP: {
            "setup_done": InterviewState.HR_ROUND,
            "error": InterviewState.ERROR,
        },
        
        # --- Rounds (linear flow by default) ---
        InterviewState.HR_ROUND: {
            "round_complete": InterviewState.TECHNICAL_ROUND,
            "needs_followup": InterviewState.FOLLOW_UP,
            "pause": InterviewState.PAUSED,
            "error": InterviewState.ERROR,
        },
        InterviewState.TECHNICAL_ROUND: {
            "round_complete": InterviewState.BEHAVIORAL_ROUND,
            "needs_followup": InterviewState.FOLLOW_UP,
            "pause": InterviewState.PAUSED,
            "error": InterviewState.ERROR,
        },
        InterviewState.BEHAVIORAL_ROUND: {
            "round_complete": InterviewState.SITUATIONAL_ROUND,
            "needs_followup": InterviewState.FOLLOW_UP,
            "pause": InterviewState.PAUSED,
            "error": InterviewState.ERROR,
        },
        InterviewState.SITUATIONAL_ROUND: {
            "round_complete": InterviewState.MCQ_ROUND,
            "needs_followup": InterviewState.FOLLOW_UP,
            "pause": InterviewState.PAUSED,
            "error": InterviewState.ERROR,
        },
        InterviewState.MCQ_ROUND: {
            "round_complete": InterviewState.EVALUATION,
            "needs_followup": InterviewState.FOLLOW_UP,
            "pause": InterviewState.PAUSED,
            "error": InterviewState.ERROR,
        },

        # --- Follow-Up Branches ---
        # Follow_up returns to the round it was called from.
        # Handled dynamically, but we define explicit returns for clarity.
        InterviewState.FOLLOW_UP: {
            "followup_done_hr": InterviewState.HR_ROUND,
            "followup_done_tech": InterviewState.TECHNICAL_ROUND,
            "followup_done_behav": InterviewState.BEHAVIORAL_ROUND,
            "followup_done_sit": InterviewState.SITUATIONAL_ROUND,
            "followup_done_mcq": InterviewState.MCQ_ROUND,
            "needs_followup": InterviewState.FOLLOW_UP, # chain follow-ups
            "error": InterviewState.ERROR,
        },

        # --- Post-Interview ---
        InterviewState.EVALUATION: {
            "eval_done": InterviewState.FEEDBACK,
            "error": InterviewState.ERROR,
        },
        InterviewState.FEEDBACK: {
            "feedback_done": InterviewState.REPORT_GENERATION,
            "error": InterviewState.ERROR,
        },
        InterviewState.REPORT_GENERATION: {
            "report_done": InterviewState.COMPLETED,
            "error": InterviewState.ERROR,
        },
        InterviewState.COMPLETED: {
            # Terminal state
        },

        # --- Meta States ---
        InterviewState.PAUSED: {
            "resume_hr": InterviewState.HR_ROUND,
            "resume_tech": InterviewState.TECHNICAL_ROUND,
            "resume_behav": InterviewState.BEHAVIORAL_ROUND,
            "resume_sit": InterviewState.SITUATIONAL_ROUND,
            "resume_mcq": InterviewState.MCQ_ROUND,
            "abort": InterviewState.COMPLETED,
        },
        InterviewState.ERROR: {
            "recover": InterviewState.PAUSED,
            "restart": InterviewState.IDLE,
            "abort": InterviewState.COMPLETED,
        }
    }

    def __init__(self, initial_state: InterviewState = InterviewState.IDLE):
        self._current_state = initial_state
        self._previous_state: Optional[InterviewState] = None
        
        # Hooks mapping: {(state, 'enter'|'exit'): list_of_callbacks}
        self._hooks: Dict[tuple, list] = {}
        
        # Guards mapping: {(from_state, trigger): guard_callback}
        self._guards: Dict[tuple, TransitionCallback] = {}

    @property
    def current_state(self) -> InterviewState:
        return self._current_state

    @property
    def previous_state(self) -> Optional[InterviewState]:
        return self._previous_state

    def add_hook(self, state: InterviewState, event: str, callback: TransitionCallback) -> None:
        """
        Register a callback to run when entering or exiting a state.
        event must be 'enter' or 'exit'.
        """
        if event not in ('enter', 'exit'):
            raise ValueError("Event must be 'enter' or 'exit'")
        key = (state, event)
        if key not in self._hooks:
            self._hooks[key] = []
        self._hooks[key].append(callback)

    def add_guard(self, from_state: InterviewState, trigger: str, guard: TransitionCallback) -> None:
        """
        Register a guard function that must return True for the transition to occur.
        """
        self._guards[(from_state, trigger)] = guard

    def can_transition(self, trigger: str) -> bool:
        """Check if a trigger is valid from the current state."""
        return trigger in self.TRANSITIONS.get(self._current_state, {})

    def trigger(self, trigger: str, session_id: str, **kwargs) -> InterviewState:
        """
        Attempt to transition the FSM using the given trigger.
        
        Args:
            trigger: The event name causing the transition.
            session_id: The interview session ID context.
            **kwargs: Extra context passed to guards and hooks.
            
        Returns:
            The new state.
            
        Raises:
            TransitionError: If the trigger is invalid or guard fails.
        """
        allowed_transitions = self.TRANSITIONS.get(self._current_state, {})
        
        if trigger not in allowed_transitions:
            raise TransitionError(
                f"Invalid trigger '{trigger}' from state {self._current_state.value}"
            )
            
        next_state = allowed_transitions[trigger]
        
        # 1. Check Guards
        guard = self._guards.get((self._current_state, trigger))
        if guard:
            try:
                if not guard(session_id=session_id, trigger=trigger, **kwargs):
                    raise TransitionError(
                        f"Guard prevented transition from {self._current_state.value} "
                        f"via '{trigger}'"
                    )
            except Exception as e:
                logger.error(f"Error evaluating guard for {trigger}: {e}", exc_info=True)
                raise TransitionError(f"Guard execution failed: {e}")

        # 2. Execute Exit Hooks (for current state)
        self._execute_hooks(self._current_state, 'exit', session_id, trigger=trigger, **kwargs)

        logger.info(
            f"FSM Transition [Session {session_id}]: "
            f"{self._current_state.value} --({trigger})--> {next_state.value}"
        )

        # 3. Perform Transition
        self._previous_state = self._current_state
        self._current_state = next_state

        # 4. Execute Enter Hooks (for new state)
        self._execute_hooks(self._current_state, 'enter', session_id, trigger=trigger, **kwargs)

        return self._current_state

    def _execute_hooks(self, state: InterviewState, event: str, session_id: str, **kwargs) -> None:
        """Execute all registered hooks for a given state and event."""
        hooks = self._hooks.get((state, event), [])
        for hook in hooks:
            try:
                hook(session_id=session_id, state=state, event=event, **kwargs)
            except Exception as e:
                # We log but don't stop the transition if a hook fails
                logger.error(
                    f"Error in {event} hook for {state.value} (Session {session_id}): {e}", 
                    exc_info=True
                )
