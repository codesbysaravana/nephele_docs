from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.agents.interview_agent import InterviewAgent
from interview_engine.orchestrator import InterviewOrchestrator

router = APIRouter()
agent = InterviewAgent()
orchestrator = InterviewOrchestrator()


class StartRequest(BaseModel):
    candidate_id: str
    name: str
    email: str
    resume: Dict[str, Any]


class SubmitRequest(BaseModel):
    candidate_id: str
    concept: str
    question: str
    answer: str


@router.get("/chat")
def chat(message: str):
    reply = agent.chat(message)
    return {
        "response": reply
    }


@router.post("/start")
def start_interview(req: StartRequest):
    try:
        return orchestrator.start_interview(
            candidate_id=req.candidate_id,
            candidate_name=req.name,
            candidate_email=req.email,
            resume_json=req.resume
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit")
def submit_answer(req: SubmitRequest):
    try:
        from interview_engine.storage.postgres.service import PostgresService
        from sqlalchemy import text
        pg = PostgresService()
        with pg.session() as db:
            query = text("SELECT state FROM interview_sessions WHERE candidate_id = :cid")
            res = db.execute(query, {"cid": req.candidate_id}).fetchone()
            if not res:
                raise HTTPException(status_code=404, detail=f"Interview session for candidate ID '{req.candidate_id}' not found.")
            state = res[0]
            if state == "PAUSED":
                raise HTTPException(status_code=400, detail="Session is currently paused. Please resume before submitting responses.")
            elif state in ("COMPLETED", "FAILED"):
                raise HTTPException(status_code=400, detail=f"Interview session has already concluded (status: {state}).")

        return orchestrator.submit_answer(
            candidate_id=req.candidate_id,
            concept=req.concept,
            question=req.question,
            answer=req.answer
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/next_question")
def get_next_question(candidate_id: str, mode: str = "static"):
    try:
        return orchestrator.get_next_question(candidate_id=candidate_id, mode=mode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mastery")
def get_mastery(candidate_id: str, domain: str):
    try:
        mastery = orchestrator.get_domain_mastery(candidate_id=candidate_id, domain=domain)
        return {"candidate_id": candidate_id, "domain": domain, "domain_mastery": mastery}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report")
def get_report(candidate_id: str):
    try:
        return orchestrator.generate_report(candidate_id=candidate_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pause")
def pause_interview(candidate_id: str = Query(...)):
    try:
        return orchestrator.pause_interview(candidate_id=candidate_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume")
def resume_interview(candidate_id: str = Query(...)):
    try:
        return orchestrator.resume_interview(candidate_id=candidate_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
