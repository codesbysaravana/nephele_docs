"""Load testing simulation script for testing concurrent candidate sessions."""

from __future__ import annotations

import concurrent.futures
import logging
import os
import time
from typing import Any, Dict, List
import psutil

from runtime.interview_runtime import InterviewRuntimeManager
from interview_engine.database import DatabaseManager, reset_mock_db
from interview_engine.chroma_store import ChromaStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_memory_usage_mb() -> float:
    """Return resident set size memory usage in Megabytes."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def simulate_single_interview(candidate_idx: int) -> List[float]:
    """Simulate a full end-to-end traversal interview for a single candidate, tracking turn latencies."""
    cand_id = f"load_test_cand_{candidate_idx}_{int(time.time())}"
    
    db = DatabaseManager()
    chroma = ChromaStore()
    
    runtime = InterviewRuntimeManager(db_manager=db, chroma_store=chroma)
    
    resume_json = {
        "skills": ["Machine Learning"],
        "education": ["BS in Computer Science"],
        "projects": ["House Price Prediction Model"],
        "resume_text": "Experienced machine learning engineer with skills in Python and SQL databases."
    }

    # 1. Start interview
    runtime.start_runtime(
        candidate_id=cand_id,
        candidate_name=f"Load Tester {candidate_idx}",
        candidate_email=f"tester{candidate_idx}@example.com",
        resume_json=resume_json
    )

    turn_latencies = []
    
    # 2. Simulate 4 interview turns (A typical interview trajectory length)
    mock_responses = [
        "Supervised learning uses labeled training data to map inputs to outputs.",
        "Overfitting is when a model fits training data too closely but fails to generalize to new data.",
        "Regularization adds a penalty term like L1 or L2 to the loss function to prevent overfitting.",
        "We can split our data into training and test splits to evaluate performance."
    ]

    for turn in range(4):
        # Fetch current active concept
        concept = runtime.current_concept or "Supervised Learning"
        question = runtime.question_history[-1]["question_text"] if runtime.question_history else "What is supervised learning?"
        answer = mock_responses[turn % len(mock_responses)]

        # Time submit answer operation
        start_time = time.time()
        res = runtime.submit_answer(
            candidate_id=cand_id,
            concept=concept,
            question=question,
            answer=answer
        )
        duration = time.time() - start_time
        turn_latencies.append(duration)

        if res["state"] in ("COMPLETED", "FAILED"):
            break

    # 3. Stop session and compile report
    runtime.stop_interview(cand_id)
    
    return turn_latencies


def run_load_test_scenario(concurrency: int) -> Dict[str, Any]:
    """Run a scenario of N concurrent candidates and calculate latency and memory statistics."""
    logger.info(f"--- RUNNING CONCURRENCY SCENARIO: {concurrency} SESSIONS ---")
    
    # Reset DB and Chroma before scenario to keep it clean
    try:
        reset_mock_db()
    except Exception as e:
        logger.warning(f"Database reset skipped or failed: {e}")

    start_mem = get_memory_usage_mb()
    start_time = time.time()

    all_latencies = []
    
    # Execute sessions concurrently in a thread pool
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(simulate_single_interview, idx)
            for idx in range(concurrency)
        ]
        
        for fut in concurrent.futures.as_completed(futures):
            try:
                latencies = fut.result()
                all_latencies.extend(latencies)
            except Exception as e:
                logger.error(f"Error in simulated session: {e}", exc_info=True)

    end_time = time.time()
    end_mem = get_memory_usage_mb()

    total_duration = end_time - start_time
    avg_turn_latency = sum(all_latencies) / len(all_latencies) if all_latencies else 0.0
    p95_turn_latency = sorted(all_latencies)[int(len(all_latencies) * 0.95)] if all_latencies else 0.0

    return {
        "concurrency": concurrency,
        "total_duration_seconds": round(total_duration, 2),
        "turn_count": len(all_latencies),
        "average_turn_latency_seconds": round(avg_turn_latency, 3),
        "p95_turn_latency_seconds": round(p95_turn_latency, 3),
        "memory_growth_mb": round(end_mem - start_mem, 2),
        "peak_memory_mb": round(end_mem, 2)
    }


def main():
    """Execute standard load scenarios and display results."""
    logger.info("Initializing system load tests...")
    
    scenarios = [10, 50, 100]
    results = []

    for concurrency in scenarios:
        res = run_load_test_scenario(concurrency)
        results.append(res)
        
    print("\n" + "="*80)
    print(" NEPHELE LOAD TESTING PERFORMANCE SUMMARY")
    print("="*80)
    print(f"{'Concurrency':<12} | {'Duration (s)':<12} | {'Turns Run':<10} | {'Avg Latency (s)':<16} | {'P95 Latency (s)':<16} | {'Mem Growth (MB)':<16}")
    print("-"*80)
    for r in results:
        print(f"{r['concurrency']:<12} | {r['total_duration_seconds']:<12} | {r['turn_count']:<10} | {r['average_turn_latency_seconds']:<16} | {r['p95_turn_latency_seconds']:<16} | {r['memory_growth_mb']:<16}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
