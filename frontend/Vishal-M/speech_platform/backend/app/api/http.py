# app/api/http.py
from fastapi import APIRouter
from . import endpoints_m1, endpoints_m2

router = APIRouter()

# Include all endpoint files
router.include_router(endpoints_m1.router, tags=["Milestone 1 - Transcription"])
router.include_router(endpoints_m2.router, tags=["Milestone 2 - Translation"])