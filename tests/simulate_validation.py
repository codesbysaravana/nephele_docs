import requests
import json
import sys

def main():
    base_url = "http://127.0.0.1:8000"
    candidate_id = f"test_val_life_cycle_999"
    
    print(f"--- STARTING VALIDATION INTERVIEW FOR CANDIDATE: {candidate_id} ---")
    
    # 1. Start Interview
    start_payload = {
        "candidate_id": candidate_id,
        "name": "Validation Tester",
        "email": "val_tester@nephele.ai",
        "resume": {
            "skills": ["Machine Learning", "Python", "SQL"]
        }
    }
    
    res = requests.post(f"{base_url}/start", json=start_payload)
    if res.status_code != 200:
        print(f"FAIL: /start returned status code {res.status_code}: {res.text}")
        sys.exit(1)
        
    start_data = res.json()
    print(f"SUCCESS: /start response: {json.dumps(start_data, indent=2)}")
    
    current_concept = start_data["current_concept"]
    question = start_data["question"]
    
    print(f"Submitting response for first concept: '{current_concept}'")
    submit_payload = {
        "candidate_id": candidate_id,
        "concept": current_concept,
        "question": question,
        "answer": "This is a validation answer for " + current_concept
    }
    
    res = requests.post(f"{base_url}/submit", json=submit_payload)
    if res.status_code != 200:
        print(f"FAIL: /submit for '{current_concept}' failed with status {res.status_code}: {res.text}")
        sys.exit(1)
        
    submit_data = res.json()
    print(f"Submit Response: {json.dumps(submit_data, indent=2)}")
    
    next_concept = submit_data.get("next_concept")
    print(f"Next concept returned by traversal: {next_concept}")

if __name__ == "__main__":
    main()
