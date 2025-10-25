from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "Speech to Speech Team B Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    SPEECH_KEY: str
    SERVICE_REGION: str

    DATABASE_URL: str = "sqlite:///./transcription.db"
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]

    MAX_UPLOAD_SIZE: int = 52428800
    ALLOWED_AUDIO_FORMATS: List[str] = [".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"]
    TEMP_STORAGE_PATH: str = "./temp_audio"

    LOG_LEVEL: str = "INFO"
    RATE_LIMIT_PER_MINUTE: int = 60

    ENABLE_METRICS: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()
