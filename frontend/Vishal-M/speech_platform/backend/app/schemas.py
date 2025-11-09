# app/schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SessionBase(BaseModel):
    mode: str

class SessionCreate(SessionBase):
    pass

class Session(SessionBase):
    id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    stats: Optional[str] = None

    class Config:
        from_attributes = True

class TranscriptBase(BaseModel):
    filename: str
    file_path: Optional[str] = None
    status: str = "pending"
    text: Optional[str] = None
    language: str = "en"

class TranscriptCreate(TranscriptBase):
    session_id: int

class Transcript(TranscriptBase):
    id: int
    session_id: int

    class Config:
        from_attributes = True

class TranslationBase(BaseModel):
    transcript_id: int
    src_lang: str
    tgt_lang: str
    src_text: str
    tgt_text: str
    finalized: bool = False

class TranslationCreate(TranslationBase):
    pass

class Translation(TranslationBase):
    id: int

    class Config:
        from_attributes = True

class GlossaryRuleInput(BaseModel):
    source_term: str
    target_term: str
    language_pair: str

class GlossaryRuleCreate(GlossaryRuleInput):
    pass

class GlossaryRule(GlossaryRuleInput):
    id: int

    class Config:
        from_attributes = True

class EvalMetricsBase(BaseModel):
    session_id: int
    language: str
    bleu: Optional[float] = None
    latency_p95: Optional[float] = None
    latency_p99: Optional[float] = None
    errors: Optional[int] = 0

class EvalMetricsCreate(EvalMetricsBase):
    pass

class EvalMetrics(EvalMetricsBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class TranslateRequest(BaseModel):
    text: str
    source_language: str
    target_language: str
    glossary_rules: Optional[List[GlossaryRuleInput]] = []


class SpeechToTextResponse(BaseModel):
    text: str
    language: str
    confidence: float