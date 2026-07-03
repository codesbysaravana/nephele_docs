# NEPHELE — Complete Project Reference Manual & Architecture Guide

Welcome to **PROJECT.md**, the authoritative, exhaustive technical manual for **Nephele** — the AI Interviewer & Robotics Evaluation Engine. 

This document details **every single directory, module, file, class, method, and function** across the entire project. Whether you are onboarding a frontend developer, auditing for production readiness, or rebuilding the backend from scratch, this document serves as the absolute source of truth.

---

## Table of Contents

1. [High-Level Architecture & Deployment Topology](#1-high-level-architecture--deployment-topology)
2. [Module 1: Core Application & HTTP API (`app/`)](#2-module-1-core-application--http-api-app)
   - [Config & Entry Points (`app/main.py`, `app/config.py`)](#21-config--entry-points)
   - [Data Models (`app/models/`)](#22-data-models)
   - [Prompt Engineering (`app/prompts/`)](#23-prompt-engineering)
   - [Resume Intelligence Pipeline (`app/resume/`)](#24-resume-intelligence-pipeline)
   - [Coding Challenge Engine (`app/coding/`)](#25-coding-challenge-engine)
   - [Voice I/O Services (`app/services/`)](#26-voice-io-services)
   - [HTTP Routers (`app/routes/`)](#27-http-routers)
3. [Module 2: Core Intelligence Engine (`backend/`)](#3-module-2-core-intelligence-engine-backend)
   - [Domain Models & Events (`backend/models/`)](#31-domain-models--events)
   - [Interview State & Orchestration (`backend/interview/`)](#32-interview-state--orchestration)
   - [Cognitive AI Layer (`backend/ai/`)](#33-cognitive-ai-layer)
4. [Module 3: Computer Vision & Edge Robotics (`edge/vision/`)](#4-module-3-computer-vision--edge-robotics-edgevision)
   - [Camera Capture Layer (`edge/vision/camera/`)](#41-camera-capture-layer)
   - [MediaPipe Detection Layer (`edge/vision/detection/`)](#42-mediapipe-detection-layer)
   - [Behavioral Analytics Layer (`edge/vision/analytics/`)](#43-behavioral-analytics-layer)
   - [Edge Networking & Output (`edge/vision/networking/`)](#44-edge-networking--output)
5. [Module 4: Testing Suite & Standalone Demos (`tests/`, `demo.py`)](#5-module-4-testing-suite--standalone-demos)
6. [How to Hook Everything into `app/main.py` for Frontend Readiness](#6-how-to-hook-everything-into-appmainpy-for-frontend-readiness)

---

<a id="1-high-level-architecture--deployment-topology"></a>
## 1. High-Level Architecture & Deployment Topology

Nephele is architected into three primary execution layers:
```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             FRONTEND WEB APPLICATION                             │
│                  (React / Next.js / Vue — HTTP REST + WebSockets)                │
└─────────────────────────┬──────────────────────────────▲─────────────────────────┘
                          │ HTTP POST / GET              │ WebSocket Stream
                          ▼                              │ (Live Signals / Audio)
┌────────────────────────────────────────────────────────┴─────────────────────────┐
│                          FASTAPI APPLICATION LAYER (`app/`)                      │
│   ├── Routers: /resume, /coding, /chat, /ws/interview, /ws/vision                │
│   └── Services: Resume Parser, Coding Evaluation, AssemblyAI STT, Pyttsx3 TTS    │
└─────────────────────────┬────────────────────────────────────────────────────────┘
                          │ Python Function Calls & Async Events
                          ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                        CORE INTELLIGENCE ENGINE (`backend/`)                     │
│   ├── State Machine (FSM): Governs 19 discrete interview states                  │
│   ├── Orchestrator: Central brain linking answers, signals, and dynamic pacing   │
│   ├── MultiModal Fusion: Combines Vision + Audio + Language scores               │
│   └── Cognitive Engine: Single-pass Groq LLM evaluation & question generation    │
└─────────────────────────▲────────────────────────────────────────────────────────┘
                          │ WebSocket (/ws/vision) or Direct Method Hook
                          │
┌─────────────────────────┴────────────────────────────────────────────────────────┐
│                        EDGE VISION SUBSYSTEM (`edge/vision/`)                    │
│   ├── Runs on Edge Device / Raspberry Pi 4 / Local Webcam                        │
│   ├── Camera Thread → Face Detection → 478 Landmarks → Eye Contact & Head Pose   │
│   └── Emits JSON telemetry @ 15+ FPS                                             │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

<a id="2-module-1-core-application--http-api-app"></a>
## 2. Module 1: Core Application & HTTP API (`app/`)

### <a id="21-config--entry-points"></a>2.1 Config & Entry Points

#### `app/__init__.py`
* **Purpose**: Marks `app/` as a Python package.

#### `app/config.py`
* **Purpose**: Loads application environment variables from `.env` files using `python-dotenv`.
* **Attributes**:
  - `GEMINI_API_KEY`: Loaded from OS environment (legacy/unused).
  - `DEEPGRAM_API_KEY`: Loaded from OS environment (legacy/unused).
  - `ASSEMBLYAI_API_KEY`: API key used by `stt_service.py` for live transcription.
  - `GROQ_API_KEY`: Core LLM authentication key used across all intelligence pipelines.

#### `app/main.py`
* **Purpose**: The ASGI application factory executed by Uvicorn (`uvicorn app.main:app`).
* **Attributes**:
  - `app = FastAPI(...)`: The core FastAPI application instance.
* **Current State**: Currently only includes `app.routes.interview.router`.
* **Frontend Readiness Requirement**: Must be updated to include CORS middleware, mount `resume` and `coding` routers, expose real-time WebSocket endpoints, and handle lifecycle startup/shutdown.

---

### <a id="22-data-models"></a>2.2 Data Models (`app/models/`)

#### `app/models/__init__.py`
* **Purpose**: Package initializer for HTTP API Pydantic schemas.

#### `app/models/candidate_profile.py`
* **Purpose**: Defines strict Pydantic schemas for structured resume data and evaluated candidate profiles returned to frontend clients.
* **Enums**:
  - `CandidateLevel`: Categorizes seniority (`Beginner`, `Intermediate`, `Advanced`).
* **Classes & Fields**:
  - `Project`: Represents a project (`title: str`, `description: str`, `technologies: List[str]`).
  - `Experience`: Represents job history (`role: str`, `company: str`, `duration: str`, `description: str`).
  - `Education`: Represents academic history (`degree: str`, `field_of_study: str`, `institution: str`, `year: str`).
  - `ResumeData`: Raw deserialized resume (`name`, `email`, `phone`, `skills`, `technologies`, `projects`, `experience`, `education`, `certifications`, `domains`).
  - `CandidateProfile`: Full intelligence profile (`resume_data`, `candidate_level`, `primary_domains`, `strength_areas`, `project_count`, `total_experience_years`, `recommended_interview_focus`).

#### `app/models/coding_models.py`
* **Purpose**: Pydantic schemas representing coding challenge generation and evaluation requests/responses.
* **Classes & Fields**:
  - `TestCase`: A single test execution verification (`input: str`, `expected_output: str`, `explanation: Optional[str]`).
  - `CodingQuestion`: Full coding challenge (`title`, `description`, `difficulty`, `topic`, `time_complexity_hint`, `space_complexity_hint`, `test_cases`, `starter_code`).
  - `CodingEvaluation`: Multi-dimensional score for candidate explanation (`score: float`, `strengths: List[str]`, `areas_for_improvement: List[str]`, `optimal_complexity: str`, `feedback: str`).

---

### <a id="23-prompt-engineering"></a>2.3 Prompt Engineering (`app/prompts/`)

#### `app/prompts/__init__.py`
* **Purpose**: Package initializer for system prompts.

#### `app/prompts/resume_analysis.py`
* **Functions**:
  - `get_resume_analysis_prompt(raw_text: str) -> str`: Returns a structured prompt instructing Groq Llama 4 to parse unstructured resume PDF/DOCX text into exact `ResumeData` JSON format.

#### `app/prompts/resume_questions.py`
* **Functions**:
  - `get_resume_questions_prompt(profile: CandidateProfile) -> str`: Formats a candidate's level, domains, and strengths into instructions requesting exactly 10 calibrated technical and behavioral interview questions.

#### `app/prompts/coding_questions.py`
* **Functions**:
  - `get_coding_question_prompt(topic: str, difficulty: str, skills: list[str] | None) -> str`: Instructs the LLM to generate an algorithmic problem tailored to the candidate's primary programming language.

#### `app/prompts/coding_evaluation.py`
* **Functions**:
  - `get_coding_evaluation_prompt(question_title, question_desc, candidate_explanation) -> str`: Instructs the LLM to act as a senior technical interviewer grading a candidate's verbal solution breakdown on a 1.0–10.0 scale.

---

### <a id="24-resume-intelligence-pipeline"></a>2.4 Resume Intelligence Pipeline (`app/resume/`)

#### `app/resume/__init__.py`
* **Purpose**: Package initializer exposing `ResumeAnalyzer`.

#### `app/resume/parser.py`
* **Purpose**: Extracts raw text strings from binary document files.
* **Functions**:
  - `extract_resume_text(file_path: str) -> str`: Detects `.pdf` vs `.docx` and routes to appropriate extractor.
  - `_extract_from_pdf(file_path: str) -> str`: Uses PyMuPDF (`fitz`) to iterate through pages and extract plain text.
  - `_extract_from_docx(file_path: str) -> str`: Uses `python-docx` to iterate through paragraphs and extract plain text.

#### `app/resume/extractor.py`
* **Purpose**: Transforms raw text strings into validated `ResumeData` models via LLM JSON extraction.
* **Classes & Methods**:
  - `ResumeExtractor`:
    - `__init__()`: Initializes asynchronous Groq client (`AsyncGroq`).
    - `async extract(raw_text: str) -> ResumeData`: Sends prompt to Llama 4 in JSON mode (`{"type": "json_object"}`), deserializes JSON, and gracefully returns empty `ResumeData()` on parser errors.

#### `app/resume/profile_builder.py`
* **Purpose**: Applies deterministic, heuristic intelligence to raw `ResumeData` without making LLM calls.
* **Classes & Methods**:
  - `ProfileBuilder`:
    - `build(resume: ResumeData) -> CandidateProfile`: Computes metrics and synthesizes profile.
    - `_estimate_experience_years(experience: list) -> float`: Parses date strings (e.g., "Jan 2020 - Present", "3 yrs") using regex to compute accurate career tenure.
    - `_determine_level(years: float, project_count: int) -> CandidateLevel`: Classifies candidate level based on years and project count.
    - `_identify_domains(resume: ResumeData) -> list[str]`: Matches skills and text against domain keyword dictionaries (e.g., matching "docker" or "kubernetes" to DevOps).
    - `_extract_strengths(resume: ResumeData, domains: list[str]) -> list[str]`: Ranks strongest skill clusters.
    - `_recommend_focus(level: CandidateLevel, domains: list[str]) -> list[str]`: Generates a recommended interview itinerary.

#### `app/resume/analyzer.py`
* **Purpose**: Facade orchestrating the 3-step resume processing pipeline.
* **Classes & Methods**:
  - `ResumeAnalyzer`:
    - `__init__()`: Initializes extractor and Groq client.
    - `async analyze(file_path: str) -> CandidateProfile`: Executes `parse → extract → build`.
    - `async generate_questions(profile: CandidateProfile) -> list[str]`: Generates 10 customized interview questions from a built profile.

---

### <a id="25-coding-challenge-engine"></a>2.5 Coding Challenge Engine (`app/coding/`)

#### `app/coding/__init__.py`
* **Purpose**: Exposes `CodingEngine`, `DifficultyManager`, and `get_recommended_topics`.

#### `app/coding/coding_engine.py`
* **Purpose**: Manages generation and evaluation of technical coding rounds.
* **Classes & Methods**:
  - `CodingEngine`:
    - `__init__()`: Initializes Groq client.
    - `async generate_question(topic: str, difficulty: str, skills: list[str] | None) -> CodingQuestion`: Calls LLM to generate problem statement, starter code, and test cases. Falls back to Two Sum on API failure.
    - `async evaluate_response(question: CodingQuestion, candidate_explanation: str) -> CodingEvaluation`: Grades verbal explanations against optimal Big-O complexity.

#### `app/coding/difficulty_manager.py`
* **Purpose**: Implements dynamic difficulty progression based on candidate performance.
* **Classes & Methods**:
  - `DifficultyManager`:
    - `__init__()`: Tracks current step (`Easy`, `Medium`, `Hard`).
    - `get_next_difficulty(score: float) -> str`: Increases difficulty if score >= 8.0; decreases if <= 5.0.

#### `app/coding/topics.py`
* **Purpose**: Skill-to-topic heuristic recommendation mapping.
* **Functions**:
  - `get_recommended_topics(skills: list[str]) -> list[str]`: Maps skills like `python` or `sql` to topics like `Arrays & Hashing` or `Database Design`.

---

### <a id="26-voice-io-services"></a>2.6 Voice I/O Services (`app/services/`)

#### `app/services/__init__.py`
* **Purpose**: Package initializer for services.

#### `app/services/stt_service.py`
* **Purpose**: Live speech-to-text audio streaming using AssemblyAI WebSockets and `sounddevice`.
* **Functions**:
  - `speech_to_text() -> str`: Captures 16-bit PCM microphone audio in a background thread, sends chunks over AssemblyAI WebSocket, and blocks until an end-of-turn final transcript is returned.

#### `app/services/tts_service.py`
* **Purpose**: Offline text-to-speech engine wrapper.
* **Functions**:
  - `speak(text: str)`: Synthesizes speech using `pyttsx3` through local system speakers.

#### `app/services/llm_service.py`
* **Purpose**: Prototype streaming chat service wrapper around Groq.
* **Classes & Methods**:
  - `InterviewAgent`:
    - `generate_response(user_message: str) -> str`: Sends prompt to Llama 4 and returns response.

---

### <a id="27-http-routers"></a>2.7 HTTP Routers (`app/routes/`)

#### `app/routes/__init__.py`
* **Purpose**: Package initializer for API endpoints.

#### `app/routes/resume.py`
* **Endpoints**:
  - `POST /resume/upload`: Accepts multipart `UploadFile` (.pdf/.docx), saves temporarily, runs `ResumeAnalyzer.analyze()`, cleans up temp file, returns `CandidateProfile` JSON.
  - `POST /resume/questions`: Accepts `CandidateProfile` JSON body, returns 10 AI-generated questions.

#### `app/routes/coding.py`
* **Endpoints**:
  - `GET /coding/question`: Query params (`topic`, `difficulty`, `skills`), returns `CodingQuestion`.
  - `POST /coding/evaluate`: Accepts `{question: CodingQuestion, explanation: str}`, returns `CodingEvaluation`.

#### `app/routes/interview.py`
* **Endpoints**:
  - `GET /chat?message=...`: Prototype chat endpoint calling `InterviewAgent`.

---

<a id="3-module-2-core-intelligence-engine-backend"></a>
## 3. Module 2: Core Intelligence Engine (`backend/`)

### <a id="31-domain-models--events"></a>3.1 Domain Models & Events (`backend/models/`)

#### `backend/models/__init__.py`
* **Purpose**: Exposes enums and domain entities.

#### `backend/models/enums.py`
* **Enums**:
  - `InterviewState`: 19 discrete FSM states (`IDLE`, `GREETING`, `HR_ROUND`, `TECHNICAL_ROUND`, `COMPLETED`, etc.).
  - `RoundType`: Enum defining round metadata (`display_name`, `focus_areas`).
  - `Difficulty`: Enum for scaling (`EASY`, `MEDIUM`, `HARD`, `EXPERT`) with `.increase()` and `.decrease()` helpers.

#### `backend/models/domain.py`
* **Classes**:
  - `CandidateInfo`: Candidate metadata (`name`, `email`, `target_role`, `profile`).
  - `VisionSnapshot`: Running metrics snapshot (`face_visible`, `engagement_score`, `eye_contact_score`, `pitch`, `yaw`, `roll`). Uses Welford's online mean algorithm (`update_from_frame()`).
  - `AudioSnapshot`: Audio signal metrics (`words_per_minute`, `silence_ratio`, `filler_word_ratio`).
  - `MultiModalSignals`: Aggregate signal packet (`vision`, `audio`, `language_*` scores, `overall_confidence`).
  - `QuestionRecord` & `AnswerRecord`: Historical turn records tracking timestamps, transcripts, vision snapshots, and LLM evaluations.
  - `SessionConfig`: Configuration rules (`round_order`, `question_limits`, `max_follow_ups`).
  - `InterviewSession`: Root aggregate storing current state, FSM history, candidate info, questions/answers, signals, and dynamic scoring.

#### `backend/models/events.py`
* **Classes**:
  - `Event`: Base event class (`event_type`, `session_id`, `timestamp`).
  - Subclasses: `StateChangedEvent`, `QuestionAskedEvent`, `AnswerReceivedEvent`, `VisionUpdateEvent`, `ScoreUpdatedEvent`, `SessionCompletedEvent`.

---

### <a id="32-interview-state--orchestration"></a>3.2 Interview State & Orchestration (`backend/interview/`)

#### `backend/interview/state_machine.py`
* **Purpose**: Table-driven Finite State Machine governing interview lifecycle.
* **Classes & Methods**:
  - `InterviewStateMachine`:
    - `TRANSITIONS`: Dictionary defining valid state transitions.
    - `add_hook(state, event, callback)`: Registers entry/exit callbacks.
    - `add_guard(from_state, trigger, guard)`: Registers transition guard conditions.
    - `trigger(trigger, session_id, **kwargs)`: Validates guard, executes exit hooks, transitions state, and executes enter hooks.

#### `backend/interview/orchestrator.py`
* **Purpose**: Central brain coordinating session state, multi-modal signals, and cognitive evaluation.
* **Classes & Methods**:
  - `InterviewOrchestrator`:
    - `__init__(session)`: Initializes FSM, ConversationManager, MultiModalFusionEngine, AdaptiveDecisionEngine, and CognitiveEngine.
    - `async start_interview() -> str`: Triggers `start` transition and returns opening greeting.
    - `async process_candidate_message(transcript, duration) -> str`: Core loop: records answer → fuses vision/audio metrics → calculates adaptive pacing → executes single LLM call for grading and next question generation → advances FSM round if complete.
    - `update_vision_signals(...)`: Callback fed by real-time camera updates.

#### `backend/interview/conversation_manager.py`
* **Purpose**: Token window manager ensuring prompts stay within LLM context limits.
* **Classes & Methods**:
  - `ConversationManager`:
    - `build_llm_context() -> str`: Compiles candidate profile summary, current round rules, and last $N$ Q&A pairs into an optimized prompt window.

#### `backend/interview/adaptive_engine.py`
* **Purpose**: Dynamic decision-making engine controlling pacing and intervention.
* **Classes & Methods**:
  - `AdaptiveDecisionEngine`:
    - `analyze(session, latest_score, behavioral_trends) -> AdaptiveDecision`: Returns `new_difficulty`, `action` (`next_question`, `follow_up`, `re_engage`), and behavioral directives (e.g., "Candidate out of frame, politely ask them to return").

#### `backend/interview/multimodal_fusion.py`
* **Purpose**: Signal processing buffer detecting historical behavioral anomalies.
* **Classes & Methods**:
  - `MultiModalFusionEngine`:
    - `process_vision_frame(...)`: Updates rolling deques (`maxlen=100`) for eye contact, engagement, and visibility.
    - `analyze_behavioral_trends() -> dict`: Checks for boolean anomaly flags (`sustained_engagement_drop`, `poor_eye_contact`, `face_lost`).
    - `compute_audio_confidence(wpm, silence, filler) -> float`: Evaluates speech pace stability.

---

### <a id="33-cognitive-ai-layer"></a>3.3 Cognitive AI Layer (`backend/ai/`)

#### `backend/ai/cognitive_engine.py`
* **Purpose**: Low-latency AI evaluation and question generation.
* **Classes & Methods**:
  - `CognitiveEngine`:
    - `async evaluate_and_generate(...) -> Tuple[dict, QuestionRecord]`: Sends conversation window, answer, and adaptive directives to Groq Llama 4 in JSON mode. Returns 5-dimension evaluation scores (`technical_correctness`, `communication_quality`, `answer_depth`, `relevance`, `professionalism`) along with the exact text for the next interview question.

---

<a id="4-module-3-computer-vision--edge-robotics-edgevision"></a>
## 4. Module 3: Computer Vision & Edge Robotics (`edge/vision/`)

### <a id="41-camera-capture-layer"></a>4.1 Camera Capture Layer (`edge/vision/camera/`)

#### `edge/vision/camera/camera_service.py`
* **Purpose**: Threaded camera reader decoupled from frame processing.
* **Classes & Methods**:
  - `CameraService`: Runs background daemon thread pulling OpenCV video frames (`cv2.VideoCapture`) into a thread-safe ring buffer, ensuring processing algorithms never block camera FPS.

---

### <a id="42-mediapipe-detection-layer"></a>4.2 MediaPipe Detection Layer (`edge/vision/detection/`)

#### `edge/vision/detection/face_detector.py`
* **Purpose**: Ultra-fast bounding box detection using MediaPipe BlazeFace short-range TFLite model.
* **Classes & Methods**:
  - `FaceDetector`: Downloads model cache if missing, runs inference, returns `FaceDetectionResult` (`face_visible`, `confidence`, `bounding_box`).

#### `edge/vision/detection/facemesh_detector.py`
* **Purpose**: High-precision 478 3D facial landmark extraction (including refined iris landmarks).
* **Classes & Methods**:
  - `FaceMeshDetector`: Downloads model cache, extracts normalized landmark mesh for gaze and head pose calculation.

---

### <a id="43-behavioral-analytics-layer"></a>4.3 Behavioral Analytics Layer (`edge/vision/analytics/`)

#### `edge/vision/analytics/eye_contact.py`
* **Purpose**: Gaze estimation algorithm measuring iris positioning relative to eye corners.
* **Classes & Methods**:
  - `EyeContactDetector`: Calculates horizontal (`left_right_ratio`) and vertical (`up_down_ratio`) iris offsets, applies Exponential Moving Average (EMA `alpha=0.3`), and returns `EyeContactResult` (`eye_contact: bool`, `eye_contact_score: 0-100`).

#### `edge/vision/analytics/head_pose.py`
* **Purpose**: 3D head rotation estimation using Perspective-n-Point (PnP).
* **Classes & Methods**:
  - `HeadPoseEstimator`: Solves `cv2.solvePnP` between 3D standard facial model points and 2D MediaPipe landmarks to calculate exact `pitch` (up/down), `yaw` (left/right), and `roll` (tilt) angles in degrees.

#### `edge/vision/analytics/engagement.py`
* **Purpose**: Multi-signal composite scoring engine.
* **Classes & Methods**:
  - `EngagementAnalyzer`: Computes weighted engagement score:
    $$\text{Score} = 0.25(\text{FaceVisible}) + 0.40(\text{EyeContact}) + 0.20(\text{HeadPosePenalty}) + 0.15(\text{Confidence})$$
    Applies quadratic penalty for head rotation away from camera (`yaw > 30°` or `pitch > 25°`) and smooths transitions via EMA (`alpha=0.2`).

---

### <a id="44-edge-networking--output"></a>4.4 Edge Networking & Output (`edge/vision/networking/`, `models/`, `utils/`)

#### `edge/vision/models/metrics.py`
* **Purpose**: Dataclass serialization schemas (`VisionMetrics`) packaging face, eye, pose, engagement, and FPS metrics into JSON payloads.

#### `edge/vision/networking/websocket_client.py`
* **Purpose**: Threaded async WebSocket telemetry client (`WebSocketClient`) streaming JSON metric payloads to backend servers (`ws://localhost:8000/ws/vision`) at up to 15+ FPS with auto-reconnect backoff.

#### `edge/vision/utils/fps.py` & `drawing.py`
* **Purpose**: Rolling window FPS counter (`FPSCounter`) and OpenCV debug overlay renderer (`OverlayDrawer`) drawing bounding boxes, eye gaze vectors, head pose axes, and live diagnostic bars on local displays.

#### `edge/vision/main.py`
* **Purpose**: Main executable pipeline (`VisionPipeline`) orchestrating camera capture, detection, landmark extraction, analytics, WebSocket streaming, and graceful shutdown handling (`python -m edge.vision.main`).

---

<a id="5-module-4-testing-suite--standalone-demos"></a>
## 5. Module 4: Testing Suite & Standalone Demos (`tests/`, `demo.py`)

#### Standalone Demo Script (`demo.py`)
* **Purpose**: Full hardware-in-the-loop CLI prototype running local camera detection alongside live AssemblyAI STT microphone loops and Pyttsx3 speaker synthesis, driving the `InterviewOrchestrator` directly without HTTP routers.

#### Integration & Unit Tests (`tests/`)
* **Core Tests**:
  - `test_full_intelligence.py`: Verifies multi-turn orchestrator flow and cognitive scoring.
  - `test_orchestrator.py`: Tests FSM state progression.
  - `test_resume_coding.py`: Integration test checking resume extraction and coding challenge scoring.
* **Vision Suite (`tests/vision/`)**: Comprehensive Pytest unit tests verifying accuracy of eye contact ratios, PnP head pose math, Welford online averaging, FPS calculation, and JSON serialization.

---

<a id="6-how-to-hook-everything-into-appmainpy-for-frontend-readiness"></a>
## 6. How to Hook Everything into `app/main.py` for Frontend Readiness

To connect a React/Next.js frontend to this backend, `app/main.py` must act as the **unified API Gateway** combining REST routers, CORS headers, real-time WebSockets, and shared session memory.

### Required Architecture in `app/main.py`

```python
import logging
from typing import Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# 1. Import existing HTTP Routers
from app.routes.resume import router as resume_router
from app.routes.coding import router as coding_router
from app.routes.interview import router as interview_router

# 2. Import Backend Intelligence Engine Components
from backend.models.domain import InterviewSession, CandidateInfo
from backend.interview.orchestrator import InterviewOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nephele.gateway")

app = FastAPI(
    title="Nephele AI Interview Gateway",
    version="1.0.0",
    description="Unified REST and WebSocket server for Nephele Frontend"
)

# ---------------------------------------------------------------------------
# A. CORS MIDDLEWARE (Frontend Readiness)
# ---------------------------------------------------------------------------
# Allow Next.js / React local development servers and production domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# B. MOUNT REST ROUTERS
# ---------------------------------------------------------------------------
app.include_router(resume_router, prefix="/api/v1/resume", tags=["Resume Pipeline"])
app.include_router(coding_router, prefix="/api/v1/coding", tags=["Coding Engine"])
app.include_router(interview_router, prefix="/api/v1/chat", tags=["Legacy Chat"])

# ---------------------------------------------------------------------------
# C. IN-MEMORY SESSION STORE (Active Interview Orchestrators)
# ---------------------------------------------------------------------------
# Maps session_id -> InterviewOrchestrator instance
active_sessions: Dict[str, InterviewOrchestrator] = {}

# ---------------------------------------------------------------------------
# D. SESSION MANAGEMENT ENDPOINTS
# ---------------------------------------------------------------------------
@app.post("/api/v1/sessions/create", tags=["Session Management"])
async def create_session(candidate_name: str = "Candidate", role: str = "Software Engineer"):
    """Creates a new live interview session and initializes the orchestrator."""
    session = InterviewSession(candidate=CandidateInfo(name=candidate_name, target_role=role))
    orchestrator = InterviewOrchestrator(session)
    active_sessions[session.id] = orchestrator
    logger.info(f"Created new interview session: {session.id}")
    return {"session_id": session.id, "state": session.current_state.value}

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "active_sessions": len(active_sessions)}

# ---------------------------------------------------------------------------
# E. REAL-TIME WEBSOCKETS (Frontend <-> Orchestrator Communication)
# ---------------------------------------------------------------------------
@app.websocket("/ws/vision/{session_id}")
async def vision_websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    Receives live VisionMetrics JSON @ 15 FPS from Edge Camera or Frontend Browser
    and injects them directly into the running session orchestrator.
    """
    await websocket.accept()
    orchestrator = active_sessions.get(session_id)
    if not orchestrator:
        await websocket.close(code=4004, reason="Session not found")
        return

    try:
        while True:
            data = await websocket.receive_json()
            # Feed vision telemetry into backend orchestrator
            orchestrator.update_vision_signals(
                eye_contact=data.get("eye_contact_score", 0.0),
                engagement=data.get("engagement_score", 0.0),
                yaw=data.get("yaw", 0.0),
                pitch=data.get("pitch", 0.0),
                roll=data.get("roll", 0.0),
                face_visible=data.get("face_visible", False)
            )
    except WebSocketDisconnect:
        logger.info(f"Vision WebSocket disconnected for session {session_id}")

@app.websocket("/ws/interview/{session_id}")
async def interview_websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    Bi-directional communication loop for the live interview:
    Frontend sends candidate speech transcripts -> Orchestrator evaluates -> Returns AI speech & state.
    """
    await websocket.accept()
    orchestrator = active_sessions.get(session_id)
    if not orchestrator:
        await websocket.close(code=4004, reason="Session not found")
        return

    try:
        # Trigger greeting on initial connection
        greeting = await orchestrator.start_interview()
        await websocket.send_json({
            "type": "agent_speech",
            "text": greeting,
            "state": orchestrator.session.current_state.value,
            "difficulty": orchestrator.session.current_difficulty.value
        })

        while True:
            payload = await websocket.receive_json()
            msg_type = payload.get("type")

            if msg_type == "candidate_answer":
                transcript = payload.get("transcript", "")
                duration = payload.get("duration_seconds", 5.0)

                # Process through Cognitive Engine & FSM
                ai_response = await orchestrator.process_candidate_message(transcript, duration)

                await websocket.send_json({
                    "type": "agent_speech",
                    "text": ai_response,
                    "state": orchestrator.session.current_state.value,
                    "round": orchestrator.session.current_round_type.display_name if orchestrator.session.current_round_type else None,
                    "difficulty": orchestrator.session.current_difficulty.value,
                    "latest_fused_score": orchestrator.session.last_answer.answer_score if orchestrator.session.last_answer else 0.0
                })
    except WebSocketDisconnect:
        logger.info(f"Interview WebSocket disconnected for session {session_id}")
```

### Summary of Frontend Communication Protocol
1. **Frontend Boot**: Frontend makes REST call to `POST /api/v1/resume/upload` to parse PDF and display skills.
2. **Session Start**: Frontend calls `POST /api/v1/sessions/create` to get a unique `session_id`.
3. **Connect WebSockets**:
   - Opens `ws://localhost:8000/ws/vision/{session_id}` and streams browser webcam MediaPipe metrics @ 15 FPS.
   - Opens `ws://localhost:8000/ws/interview/{session_id}` to receive the opening AI greeting and send candidate speech transcripts.
4. **Interactive Loop**: Every spoken turn updates candidate difficulty and progresses the FSM seamlessly in real time.
