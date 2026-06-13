import pyttsx3
import logging

logger = logging.getLogger(__name__)

def speak(text):
    logger.info(f"TTS playback start: '{text}'")
    try:
        engine = pyttsx3.init()
        voice = engine.getProperty('voice')
        logger.info(f"TTS audio device/voice selected: {voice}")
        engine.say(text)
        engine.runAndWait()
        logger.info("TTS playback end")
    except Exception as e:
        logger.error(f"TTS playback error: {e}", exc_info=True)

