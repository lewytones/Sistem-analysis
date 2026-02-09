"""
Основное приложение FastAPI
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from datetime import datetime
import structlog
from app.config import settings

from app.models.base import Base
from app.api.endpoints import reviews, tasks, analytics

# Настройка структурированного логирования
import logging
logger = logging.getLogger(__name__)
logger = structlog.get_logger()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Инициализация при старте
    logger.info("starting_application", version=settings.PROJECT_VERSION)
    
    # Создание таблиц (в продакшене используйте Alembic миграции)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Очистка при завершении
    logger.info("shutting_down_application")
    await engine.dispose()

# Создание приложения
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Интеллектуальная система анализа отзывов с поддержкой русского языка",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Настройка rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(reviews.router, prefix="/api/v1/reviews", tags=["Reviews"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Batch Processing"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])

@app.get("/health")
async def health_check():
    """Эндпоинт проверки работоспособности системы"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    """Корневой эндпоинт с информацией о системе"""
    return {
        "message": "Review Analysis System API",
        "version": settings.PROJECT_VERSION,
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )