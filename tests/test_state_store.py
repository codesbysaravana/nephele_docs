import pytest
import os
from datetime import datetime
from app.models.domain import InterviewSession, CandidateProfile, InterviewConfig
from app.models.enums import InterviewState, RoundType, Difficulty
from app.interview.state_store import SQLiteStateStore

@pytest.fixture
def state_store():
    # Use in-memory SQLite for testing to avoid disk IO and cleanup
    store = SQLiteStateStore(db_path=":memory:")
    yield store

def test_sqlite_state_store_save_and_load(state_store):
    candidate = CandidateProfile(
        id="test_cand_1",
        name="Alice",
        skills={"languages": ["Python"]}
    )
    
    session = InterviewSession(
        id="sess_123",
        candidate=candidate,
        current_state=InterviewState.TECHNICAL_ROUND,
        current_round_type=RoundType.TECHNICAL,
        current_difficulty=Difficulty.HARD
    )
    
    # Save the session
    state_store.save_session(session)
    
    # Load the session
    loaded_session = state_store.get_session("sess_123")
    
    assert loaded_session is not None
    assert loaded_session.id == "sess_123"
    assert loaded_session.candidate.name == "Alice"
    assert loaded_session.current_state == InterviewState.TECHNICAL_ROUND
    assert loaded_session.current_round_type == RoundType.TECHNICAL
    assert loaded_session.current_difficulty == Difficulty.HARD
    
    # Check that unknown ID returns None
    assert state_store.get_session("unknown_sess") is None
