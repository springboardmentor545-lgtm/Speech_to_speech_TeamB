import os
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from datetime import datetime

from .database import engine, Base
from .config import get_settings
from .logger import setup_logging, get_logger
from . import api, websocket, schemas

settings = get_settings()
setup_logging()
logger = get_logger(__name__)

limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events"""
    try:
        logger.info("application_startup", version=settings.APP_VERSION)
        # Ensure database is initialized
        Base.metadata.create_all(bind=engine)
        # Create temp upload directory
        os.makedirs(settings.TEMP_STORAGE_PATH, exist_ok=True)
        yield
    except Exception as e:
        logger.error("startup_failed", error=str(e))
        raise
    finally:
        logger.info("application_shutdown")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("validation_error", errors=exc.errors(), body=exc.body)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=schemas.ErrorResponse(
            error="Validation Error",
            detail=str(exc.errors()),
            timestamp=datetime.utcnow()
        ).dict()
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=schemas.ErrorResponse(
            error="Internal Server Error",
            detail=str(exc) if settings.DEBUG else "An unexpected error occurred",
            timestamp=datetime.utcnow()
        ).dict()
    )

app.include_router(api.router)
app.include_router(websocket.router)

@app.get("/", tags=["root"])
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health", response_model=schemas.HealthResponse, tags=["monitoring"])
async def health_check():
    try:
        # Simple query to check DB connection
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        db_status = "unhealthy"

    azure_status = "healthy" if settings.SPEECH_KEY and settings.SERVICE_REGION else "not_configured"

    overall_status = "healthy" if db_status == "healthy" and azure_status == "healthy" else "degraded"

    return schemas.HealthResponse(
        status=overall_status,
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow(),
        database=db_status,
        azure_speech=azure_status
    )

# Placeholder for Prometheus metrics - requires prometheus-client setup
# from prometheus_client import make_asgi_app
# metrics_app = make_asgi_app()
# app.mount("/metrics", metrics_app)
@app.get("/metrics", tags=["monitoring"])
@limiter.exempt
async def metrics():
     return {"message": "Prometheus metrics endpoint (Not fully implemented)"}
