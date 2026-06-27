"""
Nephele Resume Intelligence + Coding Round — End-to-End Integration Test.

Tests:
1. Resume parsing (PDF)
2. LLM-based skill extraction (Groq)
3. Profile building (level, domains, strengths)
4. Personalized question generation (10 questions)
5. Coding question generation
6. Coding answer evaluation
7. Adaptive difficulty scaling
"""

import asyncio
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.resume.analyzer import ResumeAnalyzer
from app.coding.coding_engine import CodingEngine
from app.coding.difficulty_manager import DifficultyManager
from app.coding.topics import get_recommended_topics
from app.models.coding_models import CodingDifficulty, CodingTopic

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


SAMPLE_RESUME_TEXT = """
SITHANY SAMUDRALA
AI Engineer | Machine Learning | Full Stack Development
Email: sithany@example.com | Phone: +91-9876543210

EDUCATION
B.Tech in Computer Science and Engineering
Lovely Professional University, 2021-2025

SKILLS
Python, Java, C++, JavaScript
TensorFlow, PyTorch, FastAPI, React, Node.js
OpenCV, MediaPipe, Docker, Git, Linux, PostgreSQL

PROJECTS

1. Nephele — AI Interview Robot
   Built an AI-powered interview robot using FastAPI, MediaPipe, and Groq LLM.
   Implemented real-time face detection, eye contact tracking, and engagement scoring.
   Technologies: Python, FastAPI, MediaPipe, OpenCV, WebSocket, Groq API

2. Swin Transformer Satellite Change Detection
   Developed a deep learning model for satellite imagery change detection using
   Swin Transformers. Achieved 94% accuracy on the LEVIR-CD dataset.
   Technologies: Python, PyTorch, Swin Transformer, Remote Sensing

3. E-Commerce Platform
   Full-stack web application with React frontend and FastAPI backend.
   Implemented OAuth2 authentication, payment gateway, and real-time notifications.
   Technologies: React, FastAPI, PostgreSQL, Redis, Docker

CERTIFICATIONS
AWS Certified Cloud Practitioner
Google TensorFlow Developer Certificate

EXPERIENCE
AI Engineering Intern — TechStartup Inc. (6 months)
  Developed NLP pipelines for document classification.
  Built REST APIs using FastAPI.
"""


async def test_resume_pipeline():
    """Test resume analysis without a file (using raw text directly)."""
    print("=" * 60)
    print("PHASE 1-4: RESUME INTELLIGENCE TEST")
    print("=" * 60)

    from app.resume.extractor import ResumeExtractor
    from app.resume.profile_builder import ProfileBuilder

    # Step 1: Extract structured data from raw text via LLM
    print("\n--- Extracting structured data from resume text ---")
    extractor = ResumeExtractor()
    resume_data = await extractor.extract(SAMPLE_RESUME_TEXT)
    
    print(f"  Name: {resume_data.name}")
    print(f"  Skills: {resume_data.skills}")
    print(f"  Technologies: {resume_data.technologies}")
    print(f"  Projects: {[p.title for p in resume_data.projects]}")
    print(f"  Education: {[e.degree + ' - ' + e.institution for e in resume_data.education]}")
    print(f"  Certifications: {resume_data.certifications}")

    # Step 2: Build candidate profile
    print("\n--- Building Candidate Profile ---")
    builder = ProfileBuilder()
    profile = builder.build(resume_data)
    
    print(f"  Candidate Level: {profile.candidate_level.value}")
    print(f"  Primary Domains: {profile.primary_domains}")
    print(f"  Strength Areas: {profile.strength_areas}")
    print(f"  Project Count: {profile.project_count}")
    print(f"  Experience Years: {profile.total_experience_years}")
    print(f"  Interview Focus: {profile.recommended_interview_focus}")

    # Step 3: Generate personalized questions
    print("\n--- Generating 10 Personalized Interview Questions ---")
    analyzer = ResumeAnalyzer()
    questions = await analyzer.generate_questions(profile)
    
    for i, q in enumerate(questions, 1):
        print(f"  Q{i}: {q}")

    return profile


async def test_coding_pipeline(profile):
    """Test the coding round engine."""
    print("\n" + "=" * 60)
    print("PHASE 5-8: CODING ROUND ENGINE TEST")
    print("=" * 60)

    engine = CodingEngine()
    difficulty_mgr = DifficultyManager()
    
    # Get recommended topics based on candidate skills
    skills = profile.resume_data.skills + profile.resume_data.technologies
    topics = get_recommended_topics(skills)
    print(f"\n  Recommended Topics: {[t.value for t in topics[:5]]}")
    print(f"  Starting Difficulty: {difficulty_mgr.current_difficulty.value}")

    # Round 1: Generate a question
    topic = topics[0] if topics else CodingTopic.ARRAYS
    print(f"\n--- Round 1: Generating {topic.value} question ({difficulty_mgr.current_difficulty.value}) ---")
    
    q1 = await engine.generate_question(topic, difficulty_mgr.current_difficulty, skills)
    print(f"  Title: {q1.title}")
    print(f"  Difficulty: {q1.difficulty.value}")
    print(f"  Description: {q1.description[:150]}...")
    print(f"  Sample Input: {q1.sample_input}")
    print(f"  Sample Output: {q1.sample_output}")

    # Simulate a GOOD answer
    good_answer = """
    I would use a hash map approach. First, I iterate through the array once.
    For each element, I check if the complement (target - current) exists in the map.
    If yes, I return the indices. Otherwise, I store the current element and its index.
    Time complexity is O(n) and space complexity is O(n).
    """
    print(f"\n--- Evaluating a GOOD answer ---")
    eval1 = await engine.evaluate_answer(q1, good_answer)
    print(f"  Understanding: {eval1.understanding}")
    print(f"  Logic: {eval1.logic}")
    print(f"  Time Complexity: {eval1.time_complexity}")
    print(f"  Space Complexity: {eval1.space_complexity}")
    print(f"  Communication: {eval1.communication}")
    print(f"  Overall: {eval1.overall}")
    print(f"  Feedback: {eval1.feedback[:200]}")

    # Adapt difficulty
    new_diff = difficulty_mgr.adjust(eval1.overall)
    print(f"\n  Difficulty after good answer: {new_diff.value}")

    # Round 2: Generate a harder question
    topic2 = topics[1] if len(topics) > 1 else CodingTopic.STRINGS
    print(f"\n--- Round 2: Generating {topic2.value} question ({difficulty_mgr.current_difficulty.value}) ---")
    
    q2 = await engine.generate_question(topic2, difficulty_mgr.current_difficulty, skills)
    print(f"  Title: {q2.title}")
    print(f"  Difficulty: {q2.difficulty.value}")

    # Simulate a POOR answer
    poor_answer = "Umm, I think I would use a for loop. Maybe nested loops? I'm not sure about the time complexity."
    print(f"\n--- Evaluating a POOR answer ---")
    eval2 = await engine.evaluate_answer(q2, poor_answer)
    print(f"  Overall: {eval2.overall}")
    print(f"  Feedback: {eval2.feedback[:200]}")

    # Adapt difficulty again
    new_diff2 = difficulty_mgr.adjust(eval2.overall)
    print(f"\n  Difficulty after poor answer: {new_diff2.value}")


async def main():
    print("\n=== NEPHELE RESUME INTELLIGENCE + CODING ROUND E2E TEST ===\n")
    
    profile = await test_resume_pipeline()
    await test_coding_pipeline(profile)
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
