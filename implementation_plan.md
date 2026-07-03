# Frontend Readiness & API Gateway Integration Plan

Transform `app/main.py` from a minimal prototype (only mounting `/chat`) into a robust, production-grade API Gateway capable of serving a modern frontend (Next.js/React) over REST and WebSockets.

## User Review Required

> [!IMPORTANT]
> **API Routing Versioning**: All endpoints will be mounted under an API prefix (`/api/v1/resume`, `/api/v1/coding`) to follow production API design standards. The legacy `/chat` endpoint will be available under `/api/v1/chat`.

> [!WARNING]
> **In-Memory Session Storage**: Interview sessions (`active_sessions`) will be stored in memory inside `app/main.py`. This means restarting the server clears active interview sessions. For multi-instance scaling in production, a Redis store would replace this dict.

## Open Questions

1. **Frontend Origin**: Currently configuring CORS for `http://localhost:3000` and `http://localhost:5173`. Are there any additional production or staging frontend domains you want added to the whitelist?

## Proposed Changes

### Core API Gateway Layer

#### [MODIFY] [main.py](file:///c:/Users/csara/Downloads/nephele_/nephele/nephele/app/main.py)
- **Add CORS Middleware**: Configure `CORSMiddleware` with credentials support for frontend origins.
- **Mount All REST Routers**:
  - Mount `app.routes.resume.router` under `/api/v1/resume`.
  - Mount `app.routes.coding.router` under `/api/v1/coding`.
  - Mount `app.routes.interview.router` under `/api/v1/chat`.
- **Add Session Management Endpoints**:
  - `POST /api/v1/sessions/create`: Instantiates an `InterviewSession` and `InterviewOrchestrator`, returns `{session_id, state}`.
  - `GET /health`: Server health check and active session count.
- **Add Real-Time WebSocket Endpoints**:
  - `WEBSOCKET /ws/vision/{session_id}`: Receives 15 FPS JSON telemetry from Edge/Frontend webcam and updates `orchestrator.update_vision_signals(...)`.
  - `WEBSOCKET /ws/interview/{session_id}`: Handles bi-directional interview turns (`start_interview()` greeting + `process_candidate_message()` loop).

## Verification Plan

### Automated Tests
- Run Pytest across existing suites to ensure no regressions:
  ```powershell
  pytest tests/test_full_intelligence.py tests/test_orchestrator.py -v
  ```
- Add a new integration test verifying `app/main.py` routes and websocket endpoints using FastAPI `TestClient`.

### Manual Verification
- Start the server using `uvicorn app.main:app --reload`.
- Hit `GET http://localhost:8000/health` to confirm server readiness.
- Hit `POST http://localhost:8000/api/v1/sessions/create` to verify session initialization.
