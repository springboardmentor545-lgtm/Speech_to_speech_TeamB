from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Float,
    Boolean,
    JSON,
)
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    mode = Column(String)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    stats = Column(JSON, nullable=True)

    transcripts = relationship("Transcript", back_populates="session")
    eval_metrics = relationship("EvalMetrics", back_populates="session")


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True)
    filename = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    language = Column(String, default="en")
    text = Column(Text, nullable=True)
    status = Column(String, default="queued")  # queued, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    stats = Column(JSON, nullable=True)

    session = relationship("Session", back_populates="transcripts")
    translations = relationship("Translation", back_populates="transcript")


class Translation(Base):
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, index=True)
    transcript_id = Column(Integer, ForeignKey("transcripts.id"), index=True)
    src_lang = Column(String, default="en")
    tgt_lang = Column(String, default="es")
    src_text = Column(Text)
    tgt_text = Column(Text)
    finalized = Column(Boolean, default=False)

    transcript = relationship("Transcript", back_populates="translations")


class GlossaryRule(Base):
    __tablename__ = "glossary_rules"

    id = Column(Integer, primary_key=True, index=True)
    source_term = Column(String, index=True)
    target_term = Column(String)
    language_pair = Column(String)  # e.g., "en-es"


class EvalMetrics(Base):
    __tablename__ = "eval_metrics"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), index=True)
    language = Column(String)
    bleu = Column(Float)
    latency_p95 = Column(Float)
    latency_p99 = Column(Float)
    errors = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="eval_metrics")