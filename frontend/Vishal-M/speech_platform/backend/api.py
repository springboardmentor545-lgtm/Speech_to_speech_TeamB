from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Form, Request , Response
from fastapi.responses import FileResponse,StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List
import os,csv,io,base64,json
import uuid
import pandas as pd
from datetime import datetime
from database import get_db, SessionLocal
from models import Transcript, Translation, Session as SessionModel, EvalMetrics, GlossaryRule, Base
from schemas import TranscriptCreate, TranslationCreate, EvalMetricsCreate, GlossaryRuleCreate, TranslateRequest, TTSRequest, Transcript as TranscriptSchema
from utils.transcription import transcribe_audio_file
from utils.translation import translate_text
from utils.tts import text_to_speech
from utils.packaging import generate_hls_manifest, generate_webvtt
import structlog
import shutil
# from utils.transcription import ContinuousTranscriber # No longer used in api.py

logger = structlog.get_logger()

# NOTE: prefix /api so frontend calls like /api/upload work
router = APIRouter()
EXPORT_DIR = "exports"
UPLOAD_DIR = "uploads"

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

            
@router.post("/upload", response_model=TranscriptSchema)
async def upload_audio_file_endpoint(
    file: UploadFile = File(...),
    language: str = Form("en-US"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Upload endpoint. Saves the file, creates DB records and schedules background transcription.
    """
    try:
        # Sanitize filename to avoid directory traversal or invalid chars
        safe_filename = os.path.basename(file.filename or "unknown_file")
        
        # --- MODIFICATION ---
        # Removed uuid to use the original filename as requested.
        # WARNING: This can cause file collisions if two users upload
        # a file with the exact same name.
        unique_filename = safe_filename
        # unique_filename = f"{uuid.uuid4()}_{safe_filename}" # Old line
        # --- END MODIFICATION ---
        
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        # Save file to uploads/
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Create session record
        session_db = SessionModel(mode="file_upload", started_at=datetime.utcnow())
        db.add(session_db)
        db.commit()
        db.refresh(session_db)

        # Create transcript record in DB with 'queued' status
        transcript = Transcript(
            session_id=session_db.id,
            filename=unique_filename, # This now uses the original filename
            file_path=file_path, # Store the path
            status="queued", # Start as queued
            language=language
        )
        db.add(transcript)
        db.commit()
        db.refresh(transcript)

        # Add background task (FastAPI BackgroundTasks). The background task opens its own DB session.
        background_tasks.add_task(transcribe_audio_file_task, file_path, transcript.id, language)
        logger.info("Transcription task scheduled", transcript_id=transcript.id, file=file_path)

        return transcript

    except Exception as e:
        logger.error("Upload failed", error=str(e), exc_info=True)
        # Be careful not to expose detailed internal errors to the client
        raise HTTPException(status_code=500, detail=f"File upload failed: {e}")


def _update_transcript_status(db: Session, transcript_id: int, status: str, text: str = None, language: str = None):
    """
    Helper to safely update a transcript's status, text, and language.
    """
    try:
        # Make sure transaction is clean
        db.rollback()
    except Exception:
        pass # Ignore if rollback fails

    try:
        transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
        if not transcript:
            logger.warning("Transcript DB record not found during update", transcript_id=transcript_id)
            return

        transcript.status = status
        if text is not None:
            transcript.text = text
        if language is not None:
            transcript.language = language
            
        transcript.updated_at = datetime.utcnow()
        db.add(transcript)
        db.commit()
        logger.info(f"Transcript {transcript_id} updated to status: {status}")
    except Exception as ex:
        logger.error("Failed to update transcript status", error=str(ex), transcript_id=transcript_id)
        db.rollback()


def transcribe_audio_file_task(file_path: str, transcript_id: int, language: str):
    """
    Background task:
    1. Update status to 'processing'
    2. Call transcription util
    3. Update status to 'completed' or 'failed' with results
    """
    db = SessionLocal()
    try:
        # 1. Mark as 'processing'
        _update_transcript_status(db, transcript_id, "processing")
        
        logger.info("Background transcription task started", file=file_path, transcript_id=transcript_id, language=language)
        
        # 2. Call the transcription helper.
        # It now returns a dict with status, text, and language
        result_data = transcribe_audio_file(session_id=transcript_id, file_path=file_path, language=language)  # your util
        logger.info("Transcription util returned", result_status=result_data.get("status"))

        # 3. Update DB record with final status
        _update_transcript_status(
            db,
            transcript_id,
            status=result_data.get("status", "failed"),
            text=result_data.get("text", "[Error: No text returned]"),
            language=result_data.get("language", language) # Persist detected language
        )
        
        logger.info("Transcription task finished", transcript_id=transcript_id, file=file_path)

    except Exception as e:
        # Log original error
        logger.error("Transcription task failed", error=str(e), file_path=file_path, transcript_id=transcript_id, exc_info=True)
        # Try to update the transcript row to failed
        try:
            _update_transcript_status(db, transcript_id, "failed", text=f"[Task Error: {e}]")
        except Exception as ex:
            logger.error("Failed to mark transcript failed after task exception", error=str(ex), transcript_id=transcript_id)
    finally:
        db.close()



@router.get("/transcripts", response_model=List[TranscriptSchema])
def get_transcripts(db: Session = Depends(get_db)):
    try:
        transcripts = db.query(Transcript).order_by(Transcript.created_at.desc()).all()
        return transcripts
    except Exception as e:
        logger.error("Error fetching transcripts", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transcripts/{transcript_id}", response_model=TranscriptSchema)
def get_transcript_status(transcript_id: int, db: Session = Depends(get_db)):
    try:
        transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
        if not transcript:
            raise HTTPException(status_code=404, detail="Transcript not found")
        return transcript
    except Exception as e:
        logger.error("Error fetching transcript", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trigger_translation")
async def trigger_translation(payload: dict):
    from utils.translation import translate_text
    db = SessionLocal()
    try:
        transcript = db.query(Transcript).filter_by(id=payload["transcript_id"]).first()
        if not transcript:
            raise HTTPException(status_code=404, detail="Transcript not found")

        translated_text = await translate_text(transcript.text, transcript.language, "es")

        # Optionally save to a Translation table
        return {"source": transcript.text, "translated": translated_text}
    finally:
        db.close()

@router.get("/export/translations", response_class=FileResponse)
def export_translations():
    db = SessionLocal()
    try:
        translations = db.query(Translation).all()
        if not translations:
            raise HTTPException(status_code=404, detail="No translations found")

        os.makedirs(EXPORT_DIR, exist_ok=True)
        filename = f"translations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(EXPORT_DIR, filename)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "source_text", "translated_text", "source_language", "target_language", "timestamp", "bleu", "latency_p95", "latency_p99"])
            for t in translations:
                writer.writerow([
                    t.id, t.source_text, t.translated_text, t.source_language,
                    t.target_language, t.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    t.bleu, t.latency_p95, t.latency_p99
                ])

        return FileResponse(path=filepath, filename=filename, media_type="text/csv")
    finally:
        db.close()


@router.get("/export/csv")
def export_multilingual_transcripts(db: Session = Depends(get_db)):
    """
    Export all transcripts as a CSV file, streamed directly to the user.
    Includes ID, Filename, Language, and Transcription text.
    """
    try:
        transcripts = db.query(Transcript).all()
        if not transcripts:
            raise HTTPException(status_code=404, detail="No transcripts found to export.")

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"transcripts_{timestamp}.csv"

        # Use io.StringIO to create an in-memory file
        stream = io.StringIO()
        writer = csv.writer(stream)
        
        # Write header
        writer.writerow(["id", "filename", "language", "transcription"])

        # Write data rows
        for t in transcripts:
            writer.writerow([
                t.id,
                t.filename or "unknown",
                t.language or "unknown",
                (t.text or "").strip()
            ])
        
        # Reset stream position to the beginning
        stream.seek(0)
        
        # Return a StreamingResponse
        return StreamingResponse(
            iter([stream.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={csv_filename}"}
        )

    except Exception as e:
        logger.error("Failed to export CSV", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to export CSV: {str(e)}")


@router.post("/translate")
async def translate_endpoint(request: TranslateRequest, db: Session = Depends(get_db)):
    try:
        modified_text = request.text
        if request.glossary_rules:
            for rule in request.glossary_rules:
                # Corrected:
                if rule.language_pair == f"{request.source_language}-{request.target_language}":
                    modified_text = modified_text.replace(rule.source_term, rule.target_term)

        translated_text = await translate_text(
            text=modified_text,
            source_language=request.source_language,
            target_language=request.target_language,
            glossary_rules=request.glossary_rules
        )

        logger.info("✅ Translation completed", src=request.source_language, tgt=request.target_language)
        return {"translated_text": translated_text}

    except Exception as e:
        logger.error("❌ Translation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@router.post("/tts")
async def tts_endpoint(req: Request):
    try:
        data = await req.json()
        text = data.get("text")
        target_language = data.get("target_language", "en-US")

        if not text:
            raise HTTPException(status_code=400, detail="Missing text input")

        logger.info("Generating TTS", text_len=len(text))

        audio_base64 = text_to_speech(text=text, target_language=target_language)
        if not audio_base64 or audio_base64.startswith("[TTS ERROR"):
            raise HTTPException(status_code=500, detail="TTS failed to generate audio")

        audio_bytes = base64.b64decode(audio_base64)
        return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/wav")

    except Exception as e:
        logger.error("TTS generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")

@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    try:
        metrics = db.query(EvalMetrics).all()
        return metrics
    except Exception as e:
        logger.error("Error fetching metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices")
def get_voices():
    """
    Return a list of TTS voices (static sample).
    """
    voices = [
        {"name": "en-US-JennyNeural", "locale": "en-US", "gender": "Female"},
        {"name": "en-US-GuyNeural", "locale": "en-US", "gender": "Male"},
        {"name": "es-ES-ElviraNeural", "locale": "es-ES", "gender": "Female"},
    ]
    return {"voices": voices}


@router.get("/subtitles/{session_id}.vtt")
def get_subtitles(session_id: int, db: Session = Depends(get_db)):
    """
    Generate WebVTT from translations associated with transcripts of a session.
    Uses Translation.translated_text field.
    """
    try:
        translations = db.query(Translation).filter(Translation.transcript_id.in_(
            db.query(Transcript.id).filter(Transcript.session_id == session_id)
        )).all()

        vtt_content = "WEBVTT\n\n"
        # Simple timestamping; in production you'd use real segment timestamps
        for i, trans in enumerate(translations):
            start_seconds = i * 5
            end_seconds = start_seconds + 5
            def fmt(t):
                h = t // 3600
                m = (t % 3600) // 60
                s = t % 60
                return f"{h:02}:{m:02}:{s:02}.000"
            vtt_content += f"{i+1}\n{fmt(start_seconds)} --> {fmt(end_seconds)}\n{(trans.translated_text or '').strip()}\n\n"

        return Response(content=vtt_content, media_type="text/vtt")
    except Exception as e:
        logger.error("Subtitle generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ott/{session_id}/manifest.m3u8")
def get_hls_manifest(session_id: int):
    try:
        manifest = generate_hls_manifest(session_id)
        return Response(content=manifest, media_type="application/vnd.apple.mpegurl")
    except Exception as e:
        logger.error("HLS manifest generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ott/{session_id}/webvtt")
def get_webvtt(session_id: int):
    try:
        vtt_content = generate_webvtt(session_id)
        return Response(content=vtt_content, media_type="text/vtt")
    except Exception as e:
        logger.error("WebVTT generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) 
    