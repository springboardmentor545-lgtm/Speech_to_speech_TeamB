# app/main.py
import os
from dotenv import load_dotenv

load_dotenv()

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

# --- UPDATED IMPORTS ---
from app.api.http import router as api_router
from app.api.websocket import router as ws_router
from app.database import engine
from app.models import Base
# --- END UPDATED IMPORTS ---

# (Rest of the file is identical to before)
# ... (structlog config) ...

logger = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="AI-Powered Speech Translation API (M1 & M2)",
    description="Backend for speech transcription and translation.",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(ws_router)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created")

@app.get("/")
async def root():
    return {"message": "AI-Powered Speech Translation API (M1 & M2)"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}