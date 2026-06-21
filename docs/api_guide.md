# Nephele API Guide

This guide describes the HTTP routes, parameters, request schemas, and JSON response formats exposed by the Nephele API.

---

## 1. Interview Operations

### Start Interview
Initializes candidate demographics, evaluates resume skills, activates a domain, and selects the starting concept question.
- **Route**: `POST /start`
- **Payload**:
  ```json
  {
    "candidate_id": "unique_cand_123",
    "name": "Jane Doe",
    "email": "jane@example.com",
    "resume": {
      "skills": ["Python", "SQL", "Supervised Learning"],
      "education": ["BS in Data Science"],
      "projects": []
    }
  }
  ```
- **Response**:
  ```json
  {
    "session_id": "unique_cand_123",
    "state": "ACTIVE",
    "domain": "machine_learning",
    "current_concept": "Supervised Learning",
    "question": "What is the primary objective of supervised learning models?"
  }
  ```

### Submit Answer
Grades candidate answer, records traversal results, updates streaks, and retrieves the next concept question.
- **Route**: `POST /submit`
- **Payload**:
  ```json
  {
    "candidate_id": "unique_cand_123",
    "concept": "Supervised Learning",
    "question": "What is the primary objective of supervised learning models?",
    "answer": "To map input features to known target labels using historical data."
  }
  ```
- **Response**:
  ```json
  {
    "decision": "advance_node",
    "next_concept": "Overfitting",
    "question": "How do you define overfitting in machine learning algorithms?",
    "mastery": 0.95,
    "confidence": 0.9,
    "state": "ACTIVE"
  }
  ```

---

## 2. Exporter Downloads

### Export Candidate Report
- **Route**: `GET /api/reports/{candidate_id}/export`
- **Parameters**: `format` (Optional: `json` | `csv` | `pdf`)
- **Headers**: Returns file payload with matching attachment name.

### Export Evolution Report
- **Route**: `GET /api/reports/evolution/export`
- **Parameters**: `domain` (default: `machine_learning`), `format` (`json` | `csv` | `pdf`)

---

## 3. Control & Administration

### Admin Overview Statistics
- **Route**: `GET /api/admin/overview`
- **Response**:
  ```json
  {
    "total_candidates": 14,
    "total_sessions": 14,
    "active_sessions": 2,
    "completed_sessions": 12,
    "average_system_mastery": 0.745,
    "system_status": "ONLINE"
  }
  ```

### System Health Status
- **Route**: `GET /api/admin/system-health`
- **Response**:
  ```json
  {
    "overall_status": "healthy",
    "database": "healthy",
    "chromadb": "healthy",
    "providers": {
      "Gemini": true,
      "Groq": true,
      "OpenAI": false
    },
    "execution_mode": "production"
  }
  ```
