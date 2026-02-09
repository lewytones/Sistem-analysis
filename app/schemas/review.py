"""
Pydantic схемы для валидации данных
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List
from datetime import datetime
import re

class ReviewBase(BaseModel):
    """Базовая схема отзыва"""
    text: str = Field(..., min_length=1, max_length=10000)
    source: Optional[str] = Field(None, max_length=100)
    
    @validator('text')
    def sanitize_text(cls, v):
        """Очистка текста от потенциальных угроз"""
        # Удаление HTML тегов
        v = re.sub(r'<[^>]*>', '', v)
        # Удаление потенциально опасных символов
        v = re.sub(r'[<>{}[\]()]', '', v)
        return v.strip()

class ReviewCreate(ReviewBase):
    """Схема для создания отзыва"""
    pass

class ReviewResponse(ReviewBase):
    """Схема ответа отзыва"""
    id: int
    uuid: str
    language: str
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class SentimentAnalysis(BaseModel):
    """Результат анализа тональности"""
    sentiment: str = Field(..., pattern="^(positive|negative|neutral)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    emotion_intensity: Optional[Dict[str, float]] = None

class AspectSentiment(BaseModel):
    """Тональность по аспекту"""
    sentiment: str
    confidence: float

class AspectAnalysis(BaseModel):
    """Результат анализа аспектов"""
    aspects: Dict[str, AspectSentiment]
    key_phrases: Dict[str, List[str]]

class AnalysisResultResponse(BaseModel):
    """Полный результат анализа"""
    review_id: int
    sentiment: SentimentAnalysis
    aspects: AspectAnalysis
    processed_at: datetime
    
    class Config:
        from_attributes = True