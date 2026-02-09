"""
Модель отзыва и результатов анализа
"""
from sqlalchemy import Column, String, Text, Float, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import BaseModel
import uuid

class Review(BaseModel):
    """Модель отзыва"""
    __tablename__ = "reviews"
    
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    text = Column(Text, nullable=False)
    source = Column(String(100), nullable=True)
    language = Column(String(10), nullable=True)  # ru/en/auto
    timestamp = Column(DateTime, default=func.now())
    
    # Связь с результатами анализа
    analysis = relationship(
        "AnalysisResult",
        back_populates="review",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self):
        return f"<Review(id={self.id}, language={self.language})>"

class AnalysisResult(BaseModel):
    """Модель результатов анализа"""
    __tablename__ = "analysis_results"
    
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    sentiment = Column(String(20), nullable=False)  # positive/negative/neutral
    confidence = Column(Float, nullable=False)
    aspects = Column(JSON, nullable=True)  # {aspect: {sentiment, confidence}}
    key_phrases = Column(JSON, nullable=True)  # {positive: [...], negative: [...]}
    emotion_intensity = Column(JSON, nullable=True)  # {joy: 0.8, anger: 0.2, ...}
    processed_at = Column(DateTime, default=func.now())
    
    # Связь с отзывом
    review = relationship("Review", back_populates="analysis")
    
    def __repr__(self):
        return f"<AnalysisResult(review_id={self.review_id}, sentiment={self.sentiment})>"