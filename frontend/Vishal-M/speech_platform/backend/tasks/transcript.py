import json
from datetime import datetime
import structlog
from ..database import SessionLocal
from ..models import Transcript
from ..utils.transcription import transcribe_audio_file

logger = structlog.get_logger()

# --- helper: convert result from transcribe_audio_file into a safe string for DB ---
def _safe_text_from_result(result) -> str:
    """
    Ensure the returned value is a string that can be safely written into the DB text column.
    If result is:
      - a dict: try to return result['text'] if present, else JSON-dump the dict
      - a string: return it as-is
      - None / other: return an informative placeholder
    """
    try:
        if result is None:
            return ""
        if isinstance(result, str):
            return result
        if isinstance(result, dict):
            # Prefer the extracted 'text' if available and string
            text = result.get("text")
            if isinstance(text, str):
                return text
            # Otherwise include the whole dict as JSON (safe for DB)
            return json.dumps(result, ensure_ascii=False)
        # fallback to stringification
        return str(result)
    except Exception:
        # On any unexpected error, fallback to safe string
        return repr(result)


def _update_failed_status(db, transcript_id: int, error_message: str):
    """
    Helper to safely mark a transcript as failed. This uses rollback before making changes
    in case the session is in a failed state.
    """
    try:
        # Make sure transaction is clean
        try:
            db.rollback()
        except Exception:
            pass

        transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
        if transcript:
            transcript.status = "failed"
            # store a safe string (avoid storing dicts directly)
            transcript.text = f"[TRANSCRIPTION ERROR] {error_message}"
            transcript.updated_at = datetime.utcnow()
            db.add(transcript)
            db.commit()
            logger.info("Transcript marked as failed", transcript_id=transcript_id)
    except Exception as ex:
        logger.error("Failed to update transcript to failed state", error=str(ex), transcript_id=transcript_id)
        try:
            db.rollback()
        except Exception:
            pass


def transcribe_audio_file_task(file_path: str, transcript_id: int, language: str):
    """
    Background task: convert/ASR -> update DB record.
    This function creates its own DB session (SessionLocal).
    """
    db = SessionLocal()
    try:
        # Call the transcription helper. It may return dict or string or raise.
        logger.info("Background transcription task started", file=file_path, transcript_id=transcript_id, language=language)
        result = transcribe_audio_file(session_id=transcript_id, file_path=file_path)  # your util
        logger.info("Transcription util returned", result_type=type(result).__name__)

        # Convert to safe string for DB
        safe_text = _safe_text_from_result(result)

        # Update DB record
        transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
        if not transcript:
            logger.warning("Transcript DB record not found", transcript_id=transcript_id)
            return

        transcript.text = safe_text
        transcript.status = "completed"
        transcript.updated_at = datetime.utcnow()
        db.add(transcript)

        try:
            db.commit()
            db.refresh(transcript)
            logger.info("Transcription completed and DB updated", transcript_id=transcript_id, file=file_path)
        except Exception as commit_err:
            # If commit fails, rollback and mark as failed
            logger.error("DB commit failed after transcription", error=str(commit_err), transcript_id=transcript_id)
            db.rollback()
            _update_failed_status(db, transcript_id, f"DB commit error: {str(commit_err)}")

    except Exception as e:
        # Log original error
        logger.error("Transcription failed in background", error=str(e), file_path=file_path, transcript_id=transcript_id)
        # Try to update the transcript row to failed (safe string)
        try:
            _update_failed_status(db, transcript_id, str(e))
        except Exception as ex:
            logger.error("Failed to mark transcript failed after transcription exception", error=str(ex), transcript_id=transcript_id)
    finally:
        try:
            db.close()
        except Exception:
            pass
