from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
import tempfile
import csv
import io
from datetime import datetime

from . import models, schemas
from .database import get_db
from .transcription import transcription_service
from .config import get_settings
from .logger import get_logger

router = APIRouter(prefix="/api", tags=["transcription"])
settings = get_settings()
logger = get_logger(__name__)

os.makedirs(settings.TEMP_STORAGE_PATH, exist_ok=True)

async def process_transcription_task(
    db: Session,
    file_path: str,
    transcript_id: int
):
    transcript = db.query(models.Transcript).filter(
        models.Transcript.id == transcript_id
    ).first()

    if not transcript:
        logger.error("transcript_not_found", transcript_id=transcript_id)
        return

    try:
        transcript.status = models.TranscriptStatus.PROCESSING
        db.commit()

        result = await transcription_service.transcribe_file(file_path)

        transcript.language = result.get("language", "unknown")
        transcript.text = result.get("text", "")
        transcript.processed_at = datetime.utcnow()

        if result.get("status") == "completed":
            transcript.status = models.TranscriptStatus.COMPLETED
        else:
            transcript.status = models.TranscriptStatus.FAILED
            transcript.error_message = result.get("error", "Unknown error")

        db.commit()
        logger.info("transcription_task_completed", transcript_id=transcript_id)

    except Exception as e:
        transcript.status = models.TranscriptStatus.FAILED
        transcript.error_message = str(e)
        db.commit()
        logger.error("transcription_task_failed", transcript_id=transcript_id, error=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@router.post("/upload", response_model=schemas.TranscriptResponse, status_code=202)
async def upload_audio_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Allowed: {', '.join(settings.ALLOWED_AUDIO_FORMATS)}"
        )

    try:
        file_size = 0
        with tempfile.NamedTemporaryFile(
            delete=False,
            dir=settings.TEMP_STORAGE_PATH,
            suffix=file_ext
        ) as temp_file:
            content = await file.read()
            file_size = len(content)

            if file_size > settings.MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE} bytes"
                )

            temp_file.write(content)
            temp_file_path = temp_file.name

        transcript = models.Transcript(
            filename=file.filename,
            status=models.TranscriptStatus.PENDING,
            file_size_bytes=file_size
        )
        db.add(transcript)
        db.commit()
        db.refresh(transcript)

        background_tasks.add_task(
            process_transcription_task,
            db,
            temp_file_path,
            transcript.id
        )

        logger.info("upload_accepted", filename=file.filename, transcript_id=transcript.id)
        return transcript

    except HTTPException:
        raise
    except Exception as e:
        logger.error("upload_failed", error=str(e), filename=file.filename)
        raise HTTPException(status_code=500, detail="File upload failed")

@router.get("/transcripts", response_model=List[schemas.TranscriptResponse])
def list_transcripts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Transcript)

    if status:
        try:
            status_enum = models.TranscriptStatus(status)
            query = query.filter(models.Transcript.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status value")

    transcripts = query.order_by(
        models.Transcript.created_at.desc()
    ).offset(skip).limit(limit).all()

    return transcripts

@router.get("/transcripts/{transcript_id}", response_model=schemas.TranscriptResponse)
def get_transcript(transcript_id: int, db: Session = Depends(get_db)):
    transcript = db.query(models.Transcript).filter(
        models.Transcript.id == transcript_id
    ).first()

    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    return transcript

@router.delete("/transcripts/{transcript_id}", status_code=204)
def delete_transcript(transcript_id: int, db: Session = Depends(get_db)):
    transcript = db.query(models.Transcript).filter(
        models.Transcript.id == transcript_id
    ).first()

    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    db.delete(transcript)
    db.commit()

    logger.info("transcript_deleted", transcript_id=transcript_id)
    return None

@router.get("/export/csv")
def export_transcripts_csv(db: Session = Depends(get_db)):
    transcripts = db.query(models.Transcript).order_by(
        models.Transcript.created_at.desc()
    ).all()

    stream = io.StringIO()
    stream.write('﻿')

    writer = csv.writer(stream)
    writer.writerow([
        "ID", "Filename", "Language", "Text", "Status",
        "Duration (s)", "File Size (bytes)", "Created At",
        "Processed At", "Error Message"
    ])

    for t in transcripts:
        writer.writerow([
            t.id,
            t.filename,
            t.language or "",
            t.text or "",
            t.status.value,
            t.duration_seconds or "",
            t.file_size_bytes or "",
            t.created_at.isoformat() if t.created_at else "",
            t.processed_at.isoformat() if t.processed_at else "",
            t.error_message or ""
        ])

    response = StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=transcripts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )

    logger.info("csv_export_completed", record_count=len(transcripts))
    return response
