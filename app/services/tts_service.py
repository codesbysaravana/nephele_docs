import logging
import asyncio
from io import BytesIO
from gtts import gTTS
import httpx

from app.config import DEEPGRAM_API_KEY

logger = logging.getLogger(__name__)

async def generate_speech_audio(text: str) -> bytes:
    """
    Generates TTS audio. Uses Deepgram for low latency if API key is present,
    otherwise falls back to gTTS.
    """
    logger.info(f"Generating TTS audio for: '{text[:30]}...'")
    try:
        if DEEPGRAM_API_KEY:
            # Deepgram Aura TTS
            url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en"
            headers = {
                "Authorization": f"Token {DEEPGRAM_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {"text": text}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload, timeout=10.0)
                response.raise_for_status()
                logger.info("Deepgram TTS audio generated successfully.")
                return response.content

        # Fallback to gTTS
        def _generate():
            tts = gTTS(text=text, lang='en')
            fp = BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()
            
        audio_bytes = await asyncio.to_thread(_generate)
        logger.info("gTTS audio generated successfully.")
        return audio_bytes
    except Exception as e:
        logger.error(f"TTS generation error: {e}", exc_info=True)
        return b""
