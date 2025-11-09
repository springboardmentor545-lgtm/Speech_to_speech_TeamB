# app/api/endpoints_m1.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import os, csv, io, shutil
from datetime import datetime
import structlog

# --- UPDATED IMPORTS ---
from app.database import get_db
from app.models import Transcript, Session as SessionModel
from app.schemas import Transcript as TranscriptSchema
from app.tasks.transcript import transcribe_audio_file_task
# --- END UPDATED IMPORTS ---

logger = structlog.get_logger()
router = APIRouter()
EXPORT_DIR = "exports"
UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

            
@router.post("/upload", response_model=TranscriptSchema)
async def upload_audio_file_endpoint(
    file: UploadFile = File(...),
    language: str = Form("en-US"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    try:
        safe_filename = os.path.basename(file.filename or "unknown_file")
        file_ext = os.path.splitext(safe_filename)[1].lower()
        
        supported_formats = [
            '.wav', '.mp3', '.ogg', '.flac', '.aiff', '.au',
            '.webm', '.m4a', '.opus', '.wave',
            '.mp4', '.mov', '.avi', '.wmv', '.flv', '.3gp'
        ]
        
        if file_ext not in supported_formats:
            logger.warning(f"Unsupported file format: {file_ext}", filename=safe_filename)
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported audio/video format: {file_ext}."
            )
        
        unique_filename = safe_filename
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        session_db = SessionModel(mode="file_upload", started_at=datetime.utcnow())
        db.add(session_db)
        db.commit()
        db.refresh(session_db)

        transcript = Transcript(
            session_id=session_db.id,
            filename=unique_filename,
            file_path=file_path,
            status="queued",
            language=language
        )
        db.add(transcript)
        db.commit()
        db.refresh(transcript)

        background_tasks.add_task(transcribe_audio_file_task, file_path, transcript.id, language)
        logger.info("Transcription task scheduled", transcript_id=transcript.id, file=file_path)

        return transcript

    except Exception as e:
        logger.error("Upload failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"File upload failed: {e}")

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


@router.get("/export/csv")
def export_multilingual_transcripts(db: Session = Depends(get_db)):
    try:
        transcripts = db.query(Transcript).all()
        if not transcripts:
            raise HTTPException(status_code=404, detail="No transcripts found to export.")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"transcripts_{timestamp}.csv"
        stream = io.StringIO()
        stream.write('\ufeff') # UTF-8 BOM for Excel
        writer = csv.writer(stream)
        
        writer.writerow(["id", "filename", "language", "transcription"])
        for t in transcripts:
            writer.writerow([
                t.id,
                t.filename or "unknown",
                t.language or "unknown",
                (t.text or "").strip()
            ])
        
        stream.seek(0)
        
        return StreamingResponse(
            iter([stream.getvalue()]),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={csv_filename}"}
        )

    except Exception as e:
        logger.error("Failed to export CSV", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to export CSV: {str(e)}")