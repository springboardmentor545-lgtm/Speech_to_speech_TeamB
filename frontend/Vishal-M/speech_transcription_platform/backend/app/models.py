from sqlalchemy import Column, Integer, String, Text, DateTime, Index, Enum
from sqlalchemy.sql import func
from .database import Base
import enum

class TranscriptStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, index=True)
    language = Column(String(10), index=True)
    text = Column(Text)
    status = Column(
        Enum(TranscriptStatus),
        default=TranscriptStatus.PENDING,
        nullable=False,
        index=True
    )
    error_message = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index('idx_status_created', 'status', 'created_at'),
        Index('idx_language_created', 'language', 'created_at'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "language": self.language,
            "text": self.text,
            "status": self.status.value,
            "error_message": self.error_message,
            "duration_seconds": self.duration_seconds,
            "file_size_bytes": self.file_size_bytes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }
