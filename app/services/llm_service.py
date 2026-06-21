from groq import Groq
from app.config import GROQ_API_KEY
import logging

logger = logging.getLogger(__name__)

client = Groq(api_key=GROQ_API_KEY or "MOCK_KEY")

SYSTEM_PROMPT = """
You are Nephele, a professional AI Interview Assistant.

Your purpose is to conduct mock interviews and provide career guidance.

Rules:

- Speak professionally.
- Speak naturally.
- Do NOT roleplay.
- Do NOT describe actions.
- Do NOT use expressions like:
  *beep*
  *extends hand*
  *robot noises*
  *whirs*
  *processing*
- Do NOT use stage directions.
- Never use markdown actions surrounded by *.
- Never pretend to physically move.
- Respond exactly like a professional interviewer.

Your personality:
- Polite
- Professional
- Encouraging
- Concise

Example:

User: Hello

Assistant:
Hello. Welcome to Nephele. I'm your AI interview assistant. How can I help you today?

Example:

User: Ask me a DSA question.

Assistant:
Certainly. Here's a medium-level DSA question:

Given an array of integers...
"""

def generate_response(user_input: str):
    logger.info(f"LLM request start with input: '{user_input}'")
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.strip()},
                {"role": "user", "content": user_input}
            ],
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            stream=True,
            stop=None
        )

        full_response = ""
        for chunk in completion:
            text = chunk.choices[0].delta.content or ""
            print(text, end="", flush=True)
            full_response += text
        
        print() # Add a newline after the streamed response
        logger.info(f"LLM response received. Length: {len(full_response)} chars.")
        return full_response
    except Exception as e:
        logger.error(f"LLM request error: {e}", exc_info=True)
        raise
