import asyncio
import logging
import sys
import os

# Ensure backend package can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.models.domain import InterviewSession
from backend.interview.orchestrator import InterviewOrchestrator
from backend.models.enums import Difficulty

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

async def simulate_vision(orchestrator, eye_contact, engagement, face_visible=True, duration_seconds=5):
    """Simulates sending a burst of vision metrics over the duration of an answer."""
    # Send ~2 frames per second
    frames = int(duration_seconds * 2)
    for _ in range(frames):
        orchestrator.update_vision_signals(
            eye_contact=eye_contact,
            engagement=engagement,
            yaw=0.0,
            pitch=0.0,
            roll=0.0,
            face_visible=face_visible
        )

async def main():
    print("=== Nephele AI Intelligence End-to-End Test ===\n")
    
    session = InterviewSession()
    session.candidate.name = "John Developer"
    session.candidate.experience_years = 4.0
    session.candidate.skills = {"languages": ["Python", "JavaScript"], "frameworks": ["FastAPI", "React"]}
    
    orchestrator = InterviewOrchestrator(session)
    
    # 1. Start
    print("\n--- [System] Starting Interview ---")
    reply = await orchestrator.start_interview()
    print(f"Nephele: {reply}")
    
    # 2. Greeting / Setup Flow
    print("\n--- [Candidate] Hello ---")
    reply = await orchestrator.process_candidate_message("Hi, yes, my name is John.", duration=3.0)
    print(f"Nephele: {reply}")
    
    print("\n--- [Candidate] Role ---")
    reply = await orchestrator.process_candidate_message("I am interviewing for the Senior Backend Engineer position.", duration=4.0)
    print(f"Nephele: {reply}")
    print(f"Current State: {orchestrator.session.current_state.value}")
    
    # 3. First Round - Question 1 (HR)
    # The setup generates the first question. Let's answer it.
    print("\n--- [Candidate] Answering Q1 (Good Answer, Good Vision) ---")
    await simulate_vision(orchestrator, eye_contact=85.0, engagement=90.0, duration_seconds=15)
    
    transcript = "I've been a backend engineer for 4 years, mainly using Python and FastAPI to build microservices. I really enjoy optimizing database queries and building scalable architectures."
    reply = await orchestrator.process_candidate_message(transcript, duration=15.0)
    
    print(f"Nephele: {reply}")
    
    # Check what the Cognitive Engine scored it
    last_answer = orchestrator.session.last_answer
    if last_answer:
        print(f"  [Debug] LLM Scores: {last_answer.language_scores}")
        print(f"  [Debug] Fused Score: {last_answer.answer_score:.1f}")
        print(f"  [Debug] Difficulty: {orchestrator.session.current_difficulty.value}")

    # 4. First Round - Question 2 (Follow-up or Next Q)
    print("\n--- [Candidate] Answering Q2 (Poor Answer, Poor Vision) ---")
    await simulate_vision(orchestrator, eye_contact=20.0, engagement=30.0, duration_seconds=8)
    
    transcript = "Uh, I don't really know much about that. I guess I just write code and hope it works."
    reply = await orchestrator.process_candidate_message(transcript, duration=8.0)
    
    print(f"Nephele: {reply}")
    
    last_answer = orchestrator.session.last_answer
    if last_answer:
        print(f"  [Debug] LLM Scores: {last_answer.language_scores}")
        print(f"  [Debug] Fused Score: {last_answer.answer_score:.1f}")
        print(f"  [Debug] Difficulty: {orchestrator.session.current_difficulty.value}")


if __name__ == "__main__":
    asyncio.run(main())
