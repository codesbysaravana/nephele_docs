import json
import threading
import logging
from urllib.parse import urlencode

import sounddevice as sd
import websocket

from app.config import ASSEMBLYAI_API_KEY

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
CONNECTION_PARAMS = {"speech_model": "u3-rt-pro", "sample_rate": SAMPLE_RATE}
API_ENDPOINT = f"wss://streaming.assemblyai.com/v3/ws?{urlencode(CONNECTION_PARAMS)}"

def speech_to_text():
    logger.info("STT session start")
    final_transcript = ""
    stop = threading.Event()
    audio_thread = None

    def on_open(ws):
        logger.info("STT WebSocket connection established")
        print("Listening (Speak into your microphone)...")

        def stream_audio():
            logger.info("Microphone stream audio thread started")
            try:
                default_device = sd.query_devices(kind='input')
                logger.info(f"Microphone audio device selected: {default_device.get('name', 'Unknown')}")
            except Exception as e:
                logger.warning(f"Could not query default audio input device: {e}")

            try:
                with sd.RawInputStream(
                    samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=800
                ) as mic:
                    while not stop.is_set():
                        try:
                            frames, _ = mic.read(800)
                            if stop.is_set():
                                break
                            ws.send(bytes(frames), websocket.ABNF.OPCODE_BINARY)
                        except Exception as e:
                            logger.error(f"STT Mic read/send error: {e}", exc_info=True)
                            break
            except Exception as e:
                logger.error(f"STT Microphone stream error: {e}", exc_info=True)
            finally:
                logger.info("Microphone stream audio thread ending")

        nonlocal audio_thread
        audio_thread = threading.Thread(target=stream_audio, daemon=True)
        audio_thread.start()

    def on_message(ws, message):
        nonlocal final_transcript
        data = json.loads(message)
        if data.get("type") == "Turn":
            text = data.get("transcript", "")
            is_final = data.get("end_of_turn", False)
            print(f"You: {text}", end="\n" if is_final else "\r")
            
            if is_final:
                logger.info(f"STT final transcription received: '{text}'")
                final_transcript = text
                stop.set()
                if ws.sock and ws.sock.connected:
                    try:
                        ws.send(json.dumps({"type": "Terminate"}))
                    except Exception as e:
                        logger.debug(f"Failed to send Terminate message: {e}")
                try:
                    ws.close()
                except Exception as e:
                    logger.debug(f"Failed to close WS inside on_message: {e}")

    def on_error(ws, error):
        if isinstance(error, websocket.ABNF) and error.opcode == websocket.ABNF.OPCODE_CLOSE:
            return
        logger.error(f"STT WebSocket Error: {error}")
        stop.set()

    def on_close(ws, status, msg):
        logger.info(f"STT WebSocket connection closed (status={status}, msg={msg})")
        stop.set()

    ws = websocket.WebSocketApp(
        API_ENDPOINT,
        header={"Authorization": ASSEMBLYAI_API_KEY},
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )

    logger.info("Connecting to STT WebSocket API...")
    ws_thread = threading.Thread(target=ws.run_forever, daemon=True)
    ws_thread.start()

    try:
        while not stop.is_set() and ws_thread.is_alive():
            ws_thread.join(0.1)
    except KeyboardInterrupt:
        logger.info("STT interrupted by user keyboard interrupt")
        stop.set()
        if ws.sock and ws.sock.connected:
            try:
                ws.send(json.dumps({"type": "Terminate"}))
            except Exception:
                pass
        ws.close()
    finally:
        stop.set()
        if audio_thread and audio_thread.is_alive():
            logger.info("Waiting for microphone thread to stop...")
            audio_thread.join(timeout=1.0)
        if ws_thread and ws_thread.is_alive():
            logger.info("Waiting for STT WebSocket thread to stop...")
            ws_thread.join(timeout=1.0)

    logger.info(f"STT session end. Final Transcript: '{final_transcript.strip()}'")
    return final_transcript.strip()

