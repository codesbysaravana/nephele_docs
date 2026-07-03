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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# Also mount resume and coding at root level for backward compatibility with existing tests/tools
app.include_router(resume_router, prefix="/resume", tags=["Resume Pipeline (Legacy)"])
app.include_router(coding_router, prefix="/coding", tags=["Coding Engine (Legacy)"])

# ---------------------------------------------------------------------------
# C. IN-MEMORY SESSION STORE (Active Interview Orchestrators)
# ---------------------------------------------------------------------------
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
