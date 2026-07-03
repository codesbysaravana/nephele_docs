# Nephele Architecture & Module Documentation

This document serves as the primary technical documentation for the Nephele AI project. It provides a complete reverse-engineered mental model of the entire system, its pipelines, and its individual modules.

---

## 1. Overall Architecture

Nephele is a multi-modal, real-time AI robotic assistant platform designed primarily for mock interviews and candidate evaluation. The architecture is split across three main environments:

1. **Edge Vision Pipeline (`edge/`)**: A Python-based computer vision application intended to run on an edge device (like a Raspberry Pi 4). It captures camera feeds, runs lightweight ML models (FaceMesh, Head Pose) to extract behavioral metrics, and streams these metrics via WebSockets.
2. **FastAPI Backend (`app/` & `backend/`)**: The core intelligence and orchestration layer. It exposes REST APIs for static operations (resume upload, coding challenge generation) and WebSockets for real-time operations. It fuses multi-modal signals, manages the interview state machine, and interfaces with Large Language Models (LLMs).
3. **Frontend SPA (`client/`)**: A framework-less Vanilla JS, HTML5, and TailwindCSS Single Page Application that acts as the control interface ("face") of the robot. It connects to the backend APIs and WebSockets, rendering state changes surgically without full page reloads.

---

## 2. Request Flow

1. **Client Interaction**: User triggers an action on the SPA (e.g., uploads a resume, starts an interview).
2. **REST API**: For static requests, the SPA calls `app/routes/`. The route validates the request and delegates to a service layer or engine (`app/resume/analyzer.py` or `app/coding/coding_engine.py`), which calls the Groq LLM API and returns structured JSON.
3. **WebSocket Initiation**: When a live interview starts, the SPA connects to `/ws/interview/{session_id}`. Simultaneously, the Edge pipeline (or browser simulator) connects to `/ws/vision/{session_id}`.
4. **Real-time Loop**:
   - Edge sends VisionMetrics (15 FPS).
   - Backend `InterviewOrchestrator` buffers metrics in `MultiModalFusionEngine`.
   - Candidate speaks -> SPA sends transcript -> Orchestrator fuses metrics, evaluates via `CognitiveEngine`, updates state, and sends AI response back to SPA.

---

## 3. Specific Pipelines & Flows

### Voice Pipeline
Currently, the pipeline relies on the frontend or an external STT/TTS mechanism to convert voice to text. The backend `app/services/stt_service.py` and `tts_service.py` exist as stubs/services. The orchestrator expects text transcripts (`candidate_answer` event) and returns text (`agent_speech` event) which the frontend visualizes.

### AI Pipeline
1. `InterviewOrchestrator` receives a transcript.
2. `MultiModalFusionEngine` aggregates recent vision frames and computes an audio confidence score.
3. `AdaptiveDecisionEngine` looks at behavioral trends (e.g., face lost, disengagement) and the preliminary score to decide the next action (follow-up, increase difficulty).
4. `CognitiveEngine` performs a single Groq LLM call (JSON mode) using the conversation history, adaptive decision, and transcript to simultaneously output evaluation scores (1-10) and the exact text of the next question.

### File Upload Pipeline
1. Frontend uploads a PDF/DOCX via `FormData` to `/api/v1/resume/upload`.
2. `app/routes/resume.py` validates file extension and size (Max 10MB), saving it to a temporary OS directory.
3. `ResumeAnalyzer` processes the file, extracting structured text and converting it into a `CandidateProfile`.
4. The temporary file is cleaned up, and the JSON profile is returned.

### Resume Analysis Flow
1. Text is extracted from the uploaded file (`extractor.py`).
2. The text is parsed (`parser.py`) and sent to the LLM via `profile_builder.py` using `resume_analysis.py` prompts.
3. The LLM returns a structured JSON containing skills, experience, and education.
4. The frontend can subsequently call `/resume/questions` to generate 10 calibrated interview questions based on this profile.

### Mock Interview Flow
1. SPA calls `/sessions/create` to instantiate an `InterviewSession` and `InterviewOrchestrator` in memory.
2. SPA connects to `/ws/interview/{session_id}`.
3. Orchestrator triggers the `InterviewStateMachine` from `IDLE` -> `GREETING`.
4. Orchestrator manages rounds based on `InterviewConfig` (e.g., HR -> Technical -> Behavioral).
5. Ends when all rounds are exhausted, returning a final evaluation card.

### Transcript Flow
1. SPA captures user input (text or speech-to-text) and sends a JSON payload: `{"type": "candidate_answer", "transcript": "...", "duration_seconds": 5.0}`.
2. Backend evaluates and responds with `{"type": "agent_speech", "text": "...", "fused_confidence": 85.5}`.
3. SPA `transcript-view.js` appends both messages to a scrolling DOM container.

### Unimplemented / Missing Flows
The following modules were requested for analysis but are **not present** in the current repository source code. They represent stubs or planned future features:
- **QR Module**
- **Attendance Module**
- **Classroom Module**
- **Authentication Flow** (No JWT, OAuth, or session middleware exists in `app/main.py`).

### WebSocket Flow
Two distinct WebSocket channels operate concurrently per session:
1. **Vision Socket** (`/ws/vision/{id}`): High frequency (15 FPS), one-way stream from Edge/Frontend to Backend, pushing telemetry (yaw, pitch, eye contact).
2. **Interview Socket** (`/ws/interview/{id}`): Bi-directional, event-driven stream sending transcripts to the backend and receiving AI speech, state changes, and evaluation scores back.

---

## 4. Frontend Architecture

- **SPA Structure**: Built using Vanilla JavaScript ES6 modules without build tools like Vite or Webpack. Served via a simple static file server.
- **State Management**: Uses a custom reactive store (`client/js/state.js`). Components can subscribe to specific state keys (e.g., `store.subscribe('interviewState', callback)`). When `store.set()` is called, custom DOM events (`stateChange:key`) are dispatched, allowing for surgical, component-level DOM updates.
- **Routing**: Managed by `client/js/router.js`. All workspace pages (Home, Interview, Resume, Coding, Settings) are pre-rendered into the DOM inside `index.html`. The router parses the URL hash and toggles CSS visibility classes (e.g., `hidden`, `flex`) rather than destroying and recreating DOM nodes. This is critical to keep WebSockets alive across navigations.
- **Components**: Modular functions returning HTML template strings (e.g., `challenge-view.js`, `nephele-head.js`). DOM event bindings are handled in a centralized orchestrator (`app.js`).

## 5. FastAPI Architecture

- **Routers**: Split across functional domains (`routes/resume.py`, `routes/coding.py`, `routes/interview.py`).
- **Services/Engines**: Business logic is decoupled from HTTP transport. `routes/` simply unpack requests and pass them to engines like `CognitiveEngine` or `ResumeAnalyzer`.
- **Models**: Pure Python dataclasses in `backend/models/domain.py` act as the single source of truth (no ORM/Pydantic for the core engine logic to remain framework-agnostic).
- **Middleware**: Configured in `main.py` strictly for CORS (`allow_origins=["*"]`).
- **Startup/Dependency**: The orchestrators are held in a simple global in-memory dictionary (`active_sessions: Dict[str, InterviewOrchestrator]`) in `main.py`.

---

## 6. API Reference

### Session Management
- **POST `/api/v1/sessions/create`**
  - **Purpose**: Initializes a new interview orchestrator.
  - **Parameters**: `candidate_name` (query), `role` (query).
  - **Response**: `{"session_id": "uuid", "state": "GREETING"}`

- **GET `/health`**
  - **Purpose**: System health check.
  - **Response**: `{"status": "ok", "active_sessions": int}`

### WebSockets
- **WS `/ws/vision/{session_id}`**
  - **Purpose**: Ingests telemetry.
  - **Payload**: `{"eye_contact_score": float, "engagement_score": float, "yaw": float, "pitch": float, "roll": float, "face_visible": bool}`

- **WS `/ws/interview/{session_id}`**
  - **Purpose**: Core interview loop.
  - **Client Payload**: `{"type": "candidate_answer", "transcript": str, "duration_seconds": float}`
  - **Server Payload**: `{"type": "agent_speech", "text": str, "state": str, "round": str, "difficulty": str, "latest_fused_score": float}`

### Resume Pipeline
- **POST `/api/v1/resume/upload`**
  - **Purpose**: Upload and parse resume.
  - **Body**: `multipart/form-data` (file).
  - **Response**: `CandidateProfile` JSON.

- **POST `/api/v1/resume/questions`**
  - **Purpose**: Generate calibrated questions from a profile.
  - **Body**: `CandidateProfile` JSON.
  - **Response**: Array of 10 question strings.

### Coding Engine
- **GET `/api/v1/coding/generate`**
  - **Purpose**: Generate an algorithmic challenge.
  - **Params**: `topic` (str), `difficulty` (str), `skills` (list[str]).
  - **Response**: JSON Question Object.

- **POST `/api/v1/coding/evaluate`**
  - **Purpose**: Evaluate a candidate's verbal/text explanation of an algorithm.
  - **Body**: `{ "question": {...}, "explanation": str }`
  - **Response**: JSON Evaluation Object (scores and feedback).

---

## 7. Folder Structure

```
nephele/
├── app/                  # FastAPI Application Layer (HTTP/WS transport)
│   ├── routes/           # REST endpoints mapping
│   ├── services/         # External integrations (LLM, STT)
│   ├── resume/           # Resume processing pipeline
│   ├── coding/           # Coding challenge pipeline
│   └── main.py           # FastAPI server & WebSocket mounts
├── backend/              # Core Intelligence & Domain Logic (Framework Agnostic)
│   ├── ai/               # LLM Cognitive Engine
│   ├── interview/        # Orchestrator, FSM, Adaptive logic, Multi-modal fusion
│   └── models/           # Pure dataclasses (domain models)
├── client/               # Vanilla JS Frontend SPA
│   ├── components/       # Reusable UI elements (HTML generators)
│   ├── pages/            # Workspace views
│   ├── js/               # State, router, and API layer
│   └── css/              # Tailwind and custom animations
└── edge/                 # Edge Computer Vision Pipeline
    └── vision/           # Camera, FaceMesh, Analytics, WebSocket Client
```

---

## 8. Technical Debt & Improvement Opportunities

### Technical Debt
1. **In-Memory State**: `active_sessions` in `main.py` is an in-memory dictionary. If the server restarts, all active interviews drop. This prevents horizontal scaling (multiple uvicorn workers).
2. **Missing Persistence**: There is no database layer attached. Profiles, transcripts, and scores vanish after the session ends.
3. **Mock Event Bus**: `backend/interview/orchestrator.py` uses a `MockEventBus`. State transitions log to console rather than emitting actionable events to an external message broker (like Redis PubSub).
4. **Duplicated Routes**: Routes are mounted twice in `main.py` (e.g., `/api/v1/resume` and `/resume` for legacy support).
5. **Security/Auth**: Absolutely no authentication mechanisms are present. APIs and WebSockets are completely open.
6. **Hardcoded Edge Values**: `edge/vision/main.py` defaults to `localhost:8000`.

### Improvement Opportunities (Do Not Implement Yet)
1. **Implement Redis State Store**: Move `InterviewSession` objects into Redis to allow for stateless FastAPI workers and session recovery.
2. **Database Integration**: Implement SQLAlchemy or Motor (MongoDB) to persist `CandidateProfile` and historical interview results.
3. **True STT/TTS Integration**: Wire up `stt_service.py` to stream audio chunks over WebSockets rather than relying on frontend transcript string payloads.
4. **WebRTC Integration**: For true real-time, low-latency audio/video, upgrade the Vision/Interview WebSockets to a WebRTC connection.

---

## 9. Comprehensive Module Dictionary

### `backend.interview.orchestrator`
- **Purpose**: The central brain of the interview system.
- **Responsibilities**: Manages the FSM, consumes multi-modal signals, and coordinates AI components.
- **Files**: `backend/interview/orchestrator.py`
- **Classes**: `InterviewOrchestrator`, `MockEventBus`
- **Dependencies**: `InterviewStateMachine`, `ConversationManager`, `MultiModalFusionEngine`, `AdaptiveDecisionEngine`, `CognitiveEngine`.
- **Used by**: `app/main.py` (WebSocket endpoints).
- **Current implementation status**: Fully functional in-memory orchestrator.
- **Known limitations**: Uses mock event bus; bound to server memory.

### `backend.interview.multimodal_fusion`
- **Purpose**: Processes high-frequency vision and audio signals.
- **Responsibilities**: Maintains rolling windows to detect behavioral trends (e.g., sustained loss of engagement). Calculates overall audio confidence.
- **Files**: `backend/interview/multimodal_fusion.py`
- **Classes**: `MultiModalFusionEngine`
- **Inputs**: Edge VisionMetrics (Yaw, Pitch, Eye Contact, Engagement).
- **Used by**: `InterviewOrchestrator`.

### `backend.interview.adaptive_engine`
- **Purpose**: Decides how the interview should adapt based on performance.
- **Responsibilities**: Controls difficulty scaling, follow-up decisions, and behavioral directives.
- **Classes**: `AdaptiveDecisionEngine`, `AdaptiveDecision`
- **Used by**: `InterviewOrchestrator` to modify state before calling the LLM.

### `backend.ai.cognitive_engine`
- **Purpose**: Handles interactions with the Large Language Model.
- **Responsibilities**: Evaluates answers and generates the next question simultaneously to minimize latency.
- **Classes**: `CognitiveEngine`
- **Dependencies**: `groq` (Async API).
- **Inputs**: Conversation history, transcript, adaptive directives.
- **Outputs**: JSON containing evaluation scores (1-10) and next question text.

### `backend.models.domain`
- **Purpose**: Single source of truth for domain entities.
- **Responsibilities**: Defines the shape of data.
- **Files**: `backend/models/domain.py`, `enums.py`, `events.py`.
- **Classes**: `InterviewSession`, `CandidateProfile`, `QuestionRecord`, `AnswerRecord`, `MultiModalSignals`.
- **Dependencies**: Native Python `dataclasses`.
- **Current status**: Complete, framework-agnostic.

### `app.routes.resume`
- **Purpose**: HTTP transport for the Resume Analysis pipeline.
- **Responsibilities**: Validates file uploads, delegates to `ResumeAnalyzer`, and cleans up OS temporary files.
- **API endpoints**: `POST /upload`, `POST /questions`.
- **Dependencies**: `app.resume.analyzer`.
- **Frontend components using it**: `client/pages/resume.js`, `client/js/api.js`.

### `edge.vision.main`
- **Purpose**: Entry point for the physical robot/camera hardware.
- **Responsibilities**: Captures frames, runs FaceMesh, analyzes head pose and eye contact, and streams JSON telemetry over WebSockets.
- **Files**: `edge/vision/main.py`
- **Classes**: `VisionPipeline`
- **Dependencies**: OpenCV, MediaPipe, Websockets.
- **Outputs**: Sends data to `ws://backend/ws/vision`.
- **Known limitations**: Currently runs locally, highly CPU intensive without Edge TPU optimization.
