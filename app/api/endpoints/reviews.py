"""
Основное приложение FastAPI
"""
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
import logging
import structlog
from typing import AsyncGenerator

from app.config import settings
from app.database import engine, SessionLocal
from app.models import Base
from app.api.endpoints import reviews, tasks, analytics
from app.utils.logging import configure_logging

# Настройка логирования
configure_logging()
logger = structlog.get_logger()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Контекстный менеджер для жизненного цикла приложения"""
    # Инициализация при запуске
    logger.info("Starting application...")
    
    # Создание таблиц в базе данных
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Application started successfully")
    
    yield
    
    # Очистка при завершении
    logger.info("Shutting down application...")
    await engine.dispose()
    logger.info("Application shut down")

# Создание приложения
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Интеллектуальная система анализа отзывов с поддержкой русского языка",
    lifespan=lifespan
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

# Rate limiting middleware
@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    """Добавление заголовков rate limiting"""
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(settings.API_RATE_LIMIT)
    return response

# Роутеры
app.include_router(
    reviews.router,
    prefix="/api/v1/reviews",
    tags=["Reviews"]
)

app.include_router(
    tasks.router,
    prefix="/api/v1/tasks",
    tags=["Batch Processing"]
)

app.include_router(
    analytics.router,
    prefix="/api/v1/analytics",
    tags=["Analytics"]
)

@app.get("/health")
async def health_check():
    """Проверка работоспособности системы"""
    return {
        "status": "healthy",
        "version": settings.PROJECT_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/docs")
async def custom_openapi():
    """Кастомная документация с примерами"""
    return app.openapi()

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Обработчик ошибок HTTP"""
    logger.error("HTTP exception", status_code=exc.status_code, detail=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status": "error"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Обработчик общих ошибок"""
    logger.error("Unexpected error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "status": "error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )