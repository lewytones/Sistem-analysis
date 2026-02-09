"""
Конфигурация приложения через Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache
import logging

class Settings(BaseSettings):
    # Базовые настройки
    PROJECT_NAME: str = "Review Analysis System"
    PROJECT_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str
    
    
    # База данных
    DATABASE_URL: str = "postgresql+asyncpg://review_user:review_password@postgres:5432/reviews"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str
    REDIS_CACHE_TTL: int = 3600  # seconds
    
    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    # NLP
    USE_TRANSFORMERS: bool = True
    FALLBACK_TO_TEXTBLOB: bool = True
    SENTIMENT_THRESHOLD_POSITIVE: float = 0.6
    SENTIMENT_THRESHOLD_NEGATIVE: float = 0.4
    RUSSIAN_MODEL_PATH: str = "DeepPavlov/rubert-base-cased-sentiment"
    ENGLISH_MODEL_PATH: str = "cardiffnlp/twitter-roberta-base-sentiment"
    
    # API
    API_RATE_LIMIT: int = 100  # requests per minute
    API_TIMEOUT: int = 120  # seconds
    CORS_ORIGINS: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)