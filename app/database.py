# app/database.py
import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# DATABASE_URL берём из окружения, если не задан — fallback на sqlite для локальной разработки
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./dev.db")

# Асинхронный движок
engine = create_async_engine(
    DATABASE_URL,  # Должно быть: postgresql+asyncpg://...
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG
)

# Асинхронный фабричный объект сессий
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Быстрая зависимость для FastAPI endpoints
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session

# Экспортируем явным образом
__all__ = ["engine", "SessionLocal", "get_session"]

Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()