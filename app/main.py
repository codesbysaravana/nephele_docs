import logging
from typing import Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 1. Import existing HTTP Routers
from app.routes.resume import router as resume_router
from app.routes.coding import router as coding_router
# 2. Import Backend Intelligence Engine Components
from app.models.domain import InterviewSession, CandidateInfo
from app.interview.orchestrator import InterviewOrchestrator
from app.interview.state_store import state_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nephele.gateway")

app = FastAPI(
    title="Nephele AI Interview Gateway",
    version="1.0.0",
    description="Unified REST and WebSocket server for Nephele Frontend"
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception at {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected internal server error occurred.", "error": str(exc)}
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
    
    # Save to SQLite
    state_store.save_session(session)
    
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
        # Try loading from SQLite
        session = state_store.get_session(session_id)
        if session:
            orchestrator = InterviewOrchestrator(session)
            active_sessions[session_id] = orchestrator
        else:
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
    Frontend streams PCM audio -> AssemblyAI STT -> Orchestrator -> AI Response -> TTS.
    """
    await websocket.accept()
    orchestrator = active_sessions.get(session_id)
    if not orchestrator:
        session = state_store.get_session(session_id)
        if session:
            orchestrator = InterviewOrchestrator(session)
            active_sessions[session_id] = orchestrator
        else:
            await websocket.close(code=4004, reason="Session not found")
            return

    from app.services.stt_service import AssemblyAIStreamer

    # Async callback for when AssemblyAI emits a transcript
    async def on_transcript(text: str, is_final: bool):
        if not is_final:
            # Send partial transcript to frontend to trigger barge-in / interrupt
            try:
                await websocket.send_json({"type": "partial_transcript", "text": text})
            except Exception:
                pass
            return
            
        if is_final:
            # Process through Orchestrator
            ai_response = await orchestrator.process_candidate_message(text, duration=5.0)  # Approximate duration for now
            state_store.save_session(orchestrator.session)

            await websocket.send_json({
                "type": "agent_speech",
                "text": ai_response,
                "state": orchestrator.session.current_state.value,
                "round": orchestrator.session.current_round_type.display_name if orchestrator.session.current_round_type else None,
                "difficulty": orchestrator.session.current_difficulty.value,
                "latest_fused_score": orchestrator.session.last_answer.answer_score if orchestrator.session.last_answer else 0.0
            })
            
            from app.services.tts_service import generate_speech_audio
            audio_bytes = await generate_speech_audio(ai_response)
            if audio_bytes:
                await websocket.send_bytes(audio_bytes)

    stt = AssemblyAIStreamer(on_transcript)
    await stt.connect()

    try:
        greeting = await orchestrator.start_interview()
        await websocket.send_json({
            "type": "agent_speech",
            "text": greeting,
            "state": orchestrator.session.current_state.value,
            "difficulty": orchestrator.session.current_difficulty.value
        })

        while True:
            message = await websocket.receive()
            if "bytes" in message and message["bytes"]:
                # Frontend sent PCM audio
                await stt.send_audio(message["bytes"])
            elif "text" in message and message["text"]:
                payload = json.loads(message["text"])
                # Handle control messages if needed
                if payload.get("type") == "candidate_answer":
                    # Fallback for text transcripts
                    text = payload.get("transcript", "")
                    duration = payload.get("duration_seconds", 5.0)
                    ai_response = await orchestrator.process_candidate_message(text, duration)
                    state_store.save_session(orchestrator.session)
                    await websocket.send_json({
                        "type": "agent_speech",
                        "text": ai_response,
                        "state": orchestrator.session.current_state.value,
                        "round": orchestrator.session.current_round_type.display_name if orchestrator.session.current_round_type else None,
                        "difficulty": orchestrator.session.current_difficulty.value,
                        "latest_fused_score": orchestrator.session.last_answer.answer_score if orchestrator.session.last_answer else 0.0
                    })
                    
                    audio_bytes = await generate_speech_audio(ai_response)
                    if audio_bytes:
                        await websocket.send_bytes(audio_bytes)

    except WebSocketDisconnect:
        logger.info(f"Interview WebSocket disconnected for session {session_id}")
    finally:
        await stt.close()
