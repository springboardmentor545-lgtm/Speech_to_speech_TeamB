# app/tasks/transcript.py
from sqlalchemy.orm import Session
from datetime import datetime
import structlog

# --- UPDATED IMPORTS ---
from app.database import SessionLocal
from app.models import Transcript
from app.services.transcription_file import transcribe_audio_file
# --- END UPDATED IMPORTS ---

logger = structlog.get_logger()

def _update_transcript_status(db: Session, transcript_id: int, status: str, text: str = None, language: str = None):
    """
    Helper to safely update a transcript's status, text, and language.
    """
    try:
        db.rollback()
    except Exception:
        pass 

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
        result_data = transcribe_audio_file(session_id=transcript_id, file_path=file_path, language=language)
        logger.info("Transcription util returned", result_status=result_data.get("status"))

        # 3. Update DB record with final status
        _update_transcript_status(
            db,
            transcript_id,
            status=result_data.get("status", "failed"),
            text=result_data.get("text", "[Error: No text returned]"),
            language=result_data.get("language", language)
        )
        
        logger.info("Transcription task finished", transcript_id=transcript_id, file=file_path)

    except Exception as e:
        logger.error("Transcription task failed", error=str(e), file_path=file_path, transcript_id=transcript_id, exc_info=True)
        try:
            _update_transcript_status(db, transcript_id, "failed", text=f"[Task Error: {e}]")
        except Exception as ex:
            logger.error("Failed to mark transcript failed after task exception", error=str(ex), transcript_id=transcript_id)
    finally:
        db.close()