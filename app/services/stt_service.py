import json
import logging
import asyncio
from urllib.parse import urlencode
import websockets

from app.config import ASSEMBLYAI_API_KEY

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
CONNECTION_PARAMS = {"speech_model": "u3-rt-pro", "sample_rate": SAMPLE_RATE}
API_ENDPOINT = f"wss://streaming.assemblyai.com/v3/ws?{urlencode(CONNECTION_PARAMS)}"

class AssemblyAIStreamer:
    def __init__(self, on_transcript_callback):
        self.on_transcript = on_transcript_callback
        self.ws = None
        self._receive_task = None
        self.is_connected = False
        self._closing = False

    async def connect(self):
        try:
            self.ws = await websockets.connect(
                API_ENDPOINT,
                additional_headers={"Authorization": ASSEMBLYAI_API_KEY}
            )
            self.is_connected = True
            self._receive_task = asyncio.create_task(self._receive_loop())
            logger.info("Connected to AssemblyAI Streaming WS")
        except Exception as e:
            logger.error(f"Failed to connect to AssemblyAI: {e}")
            self.is_connected = False

    async def _reconnect(self):
        if self._closing:
            return
        logger.info("Attempting to reconnect to AssemblyAI...")
        await asyncio.sleep(2)
        await self.connect()

    async def _receive_loop(self):
        try:
            async for message in self.ws:
                data = json.loads(message)
                if data.get("type") == "Turn":
                    text = data.get("transcript", "")
                    is_final = data.get("end_of_turn", False)
                    if text:
                        await self.on_transcript(text, is_final)
        except Exception as e:
            logger.error(f"AssemblyAI receive error: {e}")
        finally:
            self.is_connected = False
            if not self._closing:
                asyncio.create_task(self._reconnect())

    async def send_audio(self, audio_chunk: bytes):
        if self.ws and self.is_connected:
            try:
                await self.ws.send(audio_chunk)
            except Exception as e:
                logger.error(f"Error sending audio to AssemblyAI: {e}")
                self.is_connected = False

    async def close(self):
        self._closing = True
        if self._receive_task:
            self._receive_task.cancel()
        if self.ws and self.is_connected:
            try:
                await self.ws.send(json.dumps({"type": "Terminate"}))
                await self.ws.close()
            except Exception:
                pass
        self.is_connected = False
        logger.info("AssemblyAI Streaming WS closed")
