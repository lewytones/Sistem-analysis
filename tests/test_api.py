"""
Тесты API эндпоинтов
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.database import get_db, Base, engine
from app.models import Review

client = TestClient(app)

@pytest.fixture
async def setup_database():
    """Фикстура для настройки базы данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_create_review(setup_database):
    """Тест создания отзыва"""
    review_data = {
        "text": "Отличный продукт! Очень доволен покупкой.",
        "source": "website"
    }
    
    response = client.post("/api/v1/reviews/", json=review_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["text"] == review_data["text"]
    assert data["source"] == review_data["source"]
    assert "id" in data

@pytest.mark.asyncio
async def test_get_reviews(setup_database):
    """Тест получения списка отзывов"""
    # Создание тестовых отзывов
    review1 = Review(text="Хороший товар", source="test", language="ru")
    review2 = Review(text="Bad product", source="test", language="en")
    
    async with AsyncSession(engine) as db:
        db.add(review1)
        db.add(review2)
        await db.commit()
    
    response = client.get("/api/v1/reviews/?limit=10")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

@pytest.mark.asyncio
async def test_health_check():
    """Тест проверки работоспособности"""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

@pytest.mark.asyncio
async def test_rate_limiting():
    """Тест ограничения частоты запросов"""
    # Отправка множества запросов для тестирования rate limiting
    for _ in range(105):  # Больше лимита в 100
        response = client.post("/api/v1/reviews/", json={
            "text": "Test review",
            "source": "test"
        })
    
    # Последний запрос должен вернуть 429
    assert response.status_code == 429