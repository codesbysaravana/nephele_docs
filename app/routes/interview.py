from fastapi import APIRouter

from app.agents.interview_agent import InterviewAgent

router = APIRouter()

agent = InterviewAgent()


@router.get("/chat")
def chat(message: str):

    reply = agent.chat(message)

    return {
        "response": reply
    }
