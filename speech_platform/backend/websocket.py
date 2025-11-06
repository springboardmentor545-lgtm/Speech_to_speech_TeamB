import json
import uuid
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
from asyncio import Queue
import asyncio
from utils.transcription import ContinuousTranscriber

logger = logging.getLogger("uvicorn.error")

router = APIRouter()

#
# Holds all active WebSocket connections
#
class ConnectionManager:
    def __init__(self):
        self.active: Dict[str, WebSocket] = {}
        self.recorded_debug_raw = set()  # store first debug chunk only

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active:
            del self.active[client_id]

    async def send_json(self, client_id: str, payload: dict):
        try:
            if client_id in self.active:
                await self.active[client_id].send_text(json.dumps(payload))
        except Exception as e:
            logger.error(f"Failed sending JSON message: {e}")


manager = ConnectionManager()


@router.websocket("/transcribe/{language}")
async def websocket_endpoint(websocket: WebSocket, language: str):
    """
    Accepts raw PCM16 16kHz mono bytes from frontend and streams to Azure.
    Sends transcript messages (final + interim) back to the frontend.
    """
    client_id = str(uuid.uuid4())
    transcriber = None

    try:
        await manager.connect(websocket, client_id)
        logger.info(f"🔗 WebSocket connected: {client_id} (lang={language})")

        #
        # Create Azure continuous transcriber
        #
        # Note: This relies on the ContinuousTranscriber class in transcription.py
        # We'll create callbacks to send data back over the websocket.
        
        async def send_transcript_data(data):
            await manager.send_json(client_id, data)

        async def send_error_data(error_message):
             await manager.send_json(client_id, {"type": "error", "message": error_message})

        transcriber = ContinuousTranscriber(
            language=language,
            on_transcript=lambda data: asyncio.create_task(send_transcript_data(data)),
            on_error=lambda error_msg: asyncio.create_task(send_error_data(error_msg))
        )

        transcriber.start()

        #
        # Receive audio chunks (raw PCM16) from React
        #
        while True:
            message = await websocket.receive()

            # WebSocket bytestream (audio)
            if message["type"] == "websocket.receive" and "bytes" in message:
                raw = message["bytes"]

                if raw is None:
                    continue

                # optional debug raw file dump
                if client_id not in manager.recorded_debug_raw:
                    try:
                        with open(f"/tmp/debug_{client_id}.raw", "ab") as f:
                            f.write(raw)
                        manager.recorded_debug_raw.add(client_id)
                        logger.info(f"🧪 Saved first RAW chunk for debug: /tmp/debug_{client_id}.raw")
                    except Exception as e:
                        logger.warning(f"Debug write failed: {e}")

                try:
                    # Ensure strict bytes type
                    if isinstance(raw, memoryview):
                        raw = raw.tobytes()
                    elif isinstance(raw, bytearray):
                        raw = bytes(raw)

                    transcriber.push_audio(raw)

                except Exception as audio_err:
                    logger.error(f"❌ Error pushing audio: {audio_err}")

            # Text messages (not expected)
            elif message["type"] == "websocket.receive" and "text" in message:
                logger.debug(f"Text message received: {message['text']}")

            elif message["type"] == "websocket.disconnect":
                raise WebSocketDisconnect

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected: {client_id}")

    except Exception as e:
        logger.error(f"🔥 WebSocket error [{client_id}]: {e}", exc_info=True)
        await manager.send_json(client_id, {"type": "error", "message": str(e)})

    finally:
        if transcriber:
            transcriber.stop()

        manager.disconnect(client_id)
        logger.info(f"🧹 Cleaned session: {client_id}")