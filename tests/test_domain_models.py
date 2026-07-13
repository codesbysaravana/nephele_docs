import pytest
from datetime import datetime
from app.models.domain import InterviewSession, CandidateProfile, InterviewConfig
from app.models.enums import InterviewState, RoundType, Difficulty

def test_interview_session_creation():
    """Verify that InterviewSession initializes correctly with domain models."""
    candidate = CandidateProfile(
        id="test_cand_1",
        name="John Doe",
        target_role="Backend Engineer",
        skills={"languages": ["Python", "Go"]},
        experience_years=5.0
    )
    
    config = InterviewConfig(
        round_order=[RoundType.HR, RoundType.TECHNICAL],
        starting_difficulty=Difficulty.MEDIUM,
    )
    
    session = InterviewSession(
        id="test_sess_1",
        candidate=candidate,
        config=config,
    )
    
    assert session.id == "test_sess_1"
    assert session.candidate.name == "John Doe"
    assert session.current_state == InterviewState.IDLE
    assert session.current_round_index == 0
    assert len(session.config.round_order) == 2
    assert session.config.starting_difficulty == Difficulty.MEDIUM
