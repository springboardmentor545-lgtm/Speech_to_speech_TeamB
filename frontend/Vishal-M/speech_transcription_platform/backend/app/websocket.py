from fastapi import APIRouter, WebSocket, WebSocketDisconnect, WebSocketException
import azure.cognitiveservices.speech as speechsdk
import asyncio
from typing import Optional

from .transcription import transcription_service
from .logger import get_logger

router = APIRouter(prefix="/ws", tags=["websocket"])
logger = get_logger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info("websocket_connected", client_id=client_id)

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info("websocket_disconnected", client_id=client_id)

manager = ConnectionManager()

@router.websocket("/recognize-continuous")
async def websocket_continuous_recognition(websocket: WebSocket):
    client_id = f"continuous_{id(websocket)}"
    await manager.connect(websocket, client_id)

    stream: Optional[speechsdk.audio.PushAudioInputStream] = None
    recognizer = None
    ffmpeg_process = None
    
    try:
        # Define the audio format for the Speech SDK
        # This should be raw PCM audio
        audio_format = speechsdk.audio.AudioStreamFormat(samples_per_second=16000, bits_per_sample=16, channels=1)
        stream = speechsdk.audio.PushAudioInputStream(stream_format=audio_format)

        async def send_result(result: dict):
            try:
                if client_id in manager.active_connections:
                    await manager.active_connections[client_id].send_json(result)
            except Exception as e:
                logger.error("failed_to_send_result", error=str(e))

        recognizer = await transcription_service.recognize_continuous(
            stream,
            send_result
        )

        # Start ffmpeg process to convert webm/opus to raw pcm
        ffmpeg_command = [
            "ffmpeg",
            "-i", "pipe:0",        # Input from stdin
            "-f", "s16le",         # Output format: signed 16-bit little-endian PCM
            "-acodec", "pcm_s16le", # Audio codec
            "-ar", "16000",        # Sample rate
            "-ac", "1",            # Mono channel
            "pipe:1"               # Output to stdout
        ]

        ffmpeg_process = await asyncio.create_subprocess_exec(
            *ffmpeg_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        async def read_ffmpeg_stdout():
            while True:
                if ffmpeg_process.stdout:
                    data = await ffmpeg_process.stdout.read(1024)
                    if not data:
                        break
                    stream.write(data)
                else:
                    break

        async def read_ffmpeg_stderr():
            while True:
                if ffmpeg_process.stderr:
                    line = await ffmpeg_process.stderr.readline()
                    if not line:
                        break
                    logger.info(f"ffmpeg_stderr: {line.decode().strip()}")
                else:
                    break

        stdout_task = asyncio.create_task(read_ffmpeg_stdout())
        stderr_task = asyncio.create_task(read_ffmpeg_stderr())

        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_bytes(),
                    timeout=30.0
                )
                if data:
                    if ffmpeg_process.stdin:
                        ffmpeg_process.stdin.write(data)
                        await ffmpeg_process.stdin.drain()
                    else:
                        break
            except asyncio.TimeoutError:
                logger.warning("websocket_receive_timeout", client_id=client_id)
                break
            except WebSocketDisconnect:
                logger.info("websocket_client_disconnected", client_id=client_id)
                break
        
        if ffmpeg_process.stdin:
            ffmpeg_process.stdin.close()
            await ffmpeg_process.wait()

        await stdout_task
        await stderr_task


    except Exception as e:
        logger.error("continuous_recognition_error", error=str(e), client_id=client_id)
        try:
            await websocket.send_json({
                "status": "error",
                "error": str(e)
            })
        except:
            pass
    finally:
        if recognizer:
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    recognizer.stop_continuous_recognition
                )
            except:
                pass

        if stream:
            stream.close()
            
        if ffmpeg_process and ffmpeg_process.returncode is None:
            ffmpeg_process.kill()
            await ffmpeg_process.wait()

        manager.disconnect(client_id)

        try:
            await websocket.close()
        except:
            pass

@router.websocket("/recognize-once")
async def websocket_single_recognition(websocket: WebSocket):
    client_id = f"once_{id(websocket)}"
    await manager.connect(websocket, client_id)

    stream: Optional[speechsdk.audio.PushAudioInputStream] = None

    try:
        stream = speechsdk.audio.PushAudioInputStream()

        timeout_duration = 10.0
        start_time = asyncio.get_event_loop().time()

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout_duration:
                break

            try:
                remaining = timeout_duration - elapsed
                data = await asyncio.wait_for(
                    websocket.receive_bytes(),
                    timeout=min(remaining, 1.0)
                )
                stream.write(data)
            except asyncio.TimeoutError:
                break
            except WebSocketDisconnect:
                break

        stream.close()

        result = await transcription_service.recognize_from_stream(stream)
        await websocket.send_json(result)

    except Exception as e:
        logger.error("single_recognition_error", error=str(e), client_id=client_id)
        try:
            await websocket.send_json({
                "status": "error",
                "error": str(e)
            })
        except:
            pass
    finally:
        if stream:
            try:
                stream.close()
            except:
                pass

        manager.disconnect(client_id)

        try:
            await websocket.close()
        except:
            pass
