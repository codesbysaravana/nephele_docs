import asyncio
import logging
import sys
import os

# Ensure backend package can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.models.domain import InterviewSession
from backend.interview.orchestrator import InterviewOrchestrator

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

async def main():
    print("=== Testing Nephele Interview Orchestrator ===\n")
    
    # 1. Create a session
    session = InterviewSession()
    session.candidate.name = "Alice Engineer"
    
    # 2. Instantiate Orchestrator
    orchestrator = InterviewOrchestrator(session)
    print(f"Initial State: {orchestrator.session.current_state.value}")
    
    # 3. Start Interview
    print("\n--- Triggering Start ---")
    reply = await orchestrator.start_interview()
    print(f"Agent: {reply}")
    print(f"Current State: {orchestrator.session.current_state.value}")
    
    # 4. Simulate Candidate message
    print("\n--- Simulating Candidate Message ---")
    reply = await orchestrator.process_candidate_message("Hello, yes my name is Alice.", duration=3.5)
    print(f"Agent: {reply}")
    print(f"Current State: {orchestrator.session.current_state.value}")
    
    # 5. Simulate another message
    print("\n--- Simulating Candidate Message ---")
    reply = await orchestrator.process_candidate_message("Let's just pick a role.", duration=2.0)
    print(f"Agent: {reply}")
    print(f"Current State: {orchestrator.session.current_state.value}")

    # 6. Simulate role selection
    print("\n--- Simulating Candidate Message ---")
    reply = await orchestrator.process_candidate_message("I'm interviewing for Backend Engineer.", duration=4.0)
    print(f"Agent: {reply}")
    print(f"Current State: {orchestrator.session.current_state.value}")
    if orchestrator.session.current_round_type:
        print(f"Current Round: {orchestrator.session.current_round_type.value}")
    
    # 7. Simulate answering a question in a round
    print("\n--- Simulating Candidate Message ---")
    reply = await orchestrator.process_candidate_message("I've been a backend engineer for 5 years.", duration=10.0)
    print(f"Agent: {reply}")
    print(f"Current State: {orchestrator.session.current_state.value}")

if __name__ == "__main__":
    asyncio.run(main())
