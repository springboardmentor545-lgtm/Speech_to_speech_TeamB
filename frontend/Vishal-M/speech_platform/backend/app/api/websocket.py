# app/api/websocket.py
import json
import uuid
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
from asyncio import Queue
import asyncio

# --- UPDATED IMPORT ---
from app.services.transcription_realtime import ContinuousTranscriber
# --- END UPDATED IMPORT ---

logger = logging.getLogger("uvicorn.error")

router = APIRouter()

class ConnectionManager:
    # (No changes to this class)
    def __init__(self):
        self.active: Dict[str, WebSocket] = {}
        self.recorded_debug_raw = set()
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
    client_id = str(uuid.uuid4())
    transcriber = None

    try:
        await manager.connect(websocket, client_id)
        logger.info(f"🔗 WebSocket connected: {client_id} (lang={language})")
        
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

        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.receive" and "bytes" in message:
                raw = message["bytes"]
                if raw is None:
                    continue
                try:
                    if isinstance(raw, memoryview):
                        raw = raw.tobytes()
                    elif isinstance(raw, bytearray):
                        raw = bytes(raw)
                    transcriber.push_audio(raw)
                except Exception as audio_err:
                    logger.error(f"❌ Error pushing audio: {audio_err}")

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