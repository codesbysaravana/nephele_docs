import asyncio
import logging
import time
import threading

from app.services.stt_service import speech_to_text
from app.services.tts_service import speak

from backend.models.domain import InterviewSession
from backend.interview.orchestrator import InterviewOrchestrator
from edge.vision.main import VisionPipeline

# Configure logging to console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(filename)s:%(lineno)d) - %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Initializing Nephele Voice Interview Agent...")
    
    # 1. Initialize the new Orchestrator Session
    session = InterviewSession()
    orchestrator = InterviewOrchestrator(session)
    
    # 2. Start Vision Pipeline locally for demo
    def on_vision_metrics(metrics: dict):
        orchestrator.update_vision_signals(
            eye_contact=metrics.get("eye_contact_score", 0.0),
            engagement=metrics.get("engagement_score", 0.0),
            yaw=metrics.get("yaw", 0.0),
            pitch=metrics.get("pitch", 0.0),
            roll=metrics.get("roll", 0.0),
            face_visible=metrics.get("face_visible", False)
        )

    logger.info("Starting local camera vision pipeline...")
    vision = VisionPipeline(
        enable_websocket=False, 
        show_display=True, 
        on_metrics=on_vision_metrics
    )
    vision_thread = threading.Thread(target=vision.start, daemon=True)
    vision_thread.start()
    
    logger.info("Nephele Core Intelligence Ready.")

    # Wait a second for camera warmup
    time.sleep(1.0)

    # 3. Trigger the start of the interview
    logger.info("State Transition: [STARTING] -> Triggering interview start...")
    reply = await orchestrator.start_interview()
    
    logger.info("State Transition: [SPEAKING] -> Playing greeting...")
    speak(reply)
    time.sleep(0.5)

    # 4. Main Voice Loop
    while True:
        logger.info("State Transition: [LISTENING] -> Waiting for user speech...")
        
        start_listen_time = time.time()
        user_text = speech_to_text()
        listen_duration = time.time() - start_listen_time

        if not user_text.strip():
            logger.info("State Transition: [IDLE] -> No speech detected / empty transcript. Skipping.")
            continue

        if user_text.lower() in ["exit", "quit", "stop interview"]:
            logger.info("Exit command received. Terminating Nephele voice loop.")
            speak("Thank you for your time. Ending the interview now.")
            break

        logger.info(f"State Transition: [THINKING] -> Orchestrator processing: '{user_text}'")
        
        # Process through the AI pipeline (Vision metrics are automatically updated via background thread callback)
        reply = await orchestrator.process_candidate_message(user_text, duration=listen_duration)

        logger.info("State Transition: [SPEAKING] -> Playing assistant response...")
        speak(reply)
        
        # Settle delay to allow audio device to close and room echo to subside
        logger.info("State Transition: [SETTLING] -> Pausing briefly before resuming listening...")
        time.sleep(0.5)

if __name__ == "__main__":
    try:
        if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program terminated by user keyboard interrupt.")
