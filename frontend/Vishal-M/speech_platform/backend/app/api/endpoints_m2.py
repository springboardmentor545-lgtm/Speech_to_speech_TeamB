# app/api/endpoints_m2.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import structlog

# --- UPDATED IMPORTS ---
from app.database import get_db
from app.models import EvalMetrics
from app.schemas import TranslateRequest
from app.services.translation import translate_text
# --- END UPDATED IMPORTS ---

logger = structlog.get_logger()
router = APIRouter()

@router.post("/translate")
async def translate_endpoint(request: TranslateRequest, db: Session = Depends(get_db)):
    try:
        result_dict = translate_text(
            text=request.text,
            source_language=request.source_language,
            target_language=request.target_language,
            glossary_rules=request.glossary_rules
        )

        if result_dict.get('success'):
            logger.info("✅ Translation completed", src=request.source_language, tgt=request.target_language)
            return {"translated_text": result_dict.get('translated_text')}
        else:
            error_msg = result_dict.get('error', 'Unknown translation error')
            logger.error("❌ Translation failed", error=error_msg, src=request.source_language, tgt=request.target_language)
            raise HTTPException(status_code=500, detail=error_msg)

    except Exception as e:
        logger.error("❌ /translate endpoint failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


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
    voices = [
        {"name": "en-US-JennyNeural", "locale": "en-US", "gender": "Female"},
        {"name": "en-US-GuyNeural", "locale": "en-US", "gender": "Male"},
        {"name": "es-ES-ElviraNeural", "locale": "es-ES", "gender": "Female"},
    ]
    return {"voices": voices}