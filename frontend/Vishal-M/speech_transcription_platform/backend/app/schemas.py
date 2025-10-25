from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
from enum import Enum

class TranscriptStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TranscriptBase(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    language: Optional[str] = Field(None, max_length=10)
    text: Optional[str] = None
    status: TranscriptStatus = TranscriptStatus.PENDING

class TranscriptCreate(TranscriptBase):
    file_size_bytes: Optional[int] = None

class TranscriptUpdate(BaseModel):
    language: Optional[str] = None
    text: Optional[str] = None
    status: Optional[TranscriptStatus] = None
    error_message: Optional[str] = None
    duration_seconds: Optional[int] = None

class TranscriptResponse(TranscriptBase):
    id: int
    error_message: Optional[str] = None
    duration_seconds: Optional[int] = None
    file_size_bytes: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    database: str
    azure_speech: str

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime
