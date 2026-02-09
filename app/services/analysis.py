"""
Основной сервис анализа отзывов
"""
from typing import Dict, Any
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Review, AnalysisResult
from app.services.nlp.sentiment import SentimentAnalyzer
from app.services.nlp.aspects import AspectExtractor
from app.services.nlp.phrases import KeyPhraseExtractor
from app.config import settings

logger = logging.getLogger(__name__)

class ReviewAnalyzer:
    """Основной класс для анализа отзывов"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer(
            use_transformers=settings.USE_TRANSFORMERS,
            fallback=settings.FALLBACK_TO_TEXTBLOB
        )
        self.aspect_extractor = AspectExtractor()
        self.phrase_extractor = KeyPhraseExtractor()
    
    async def analyze_and_save(self, review_id: int, db: AsyncSession):
        """
        Полный анализ отзыва и сохранение результатов
        
        Args:
            review_id: ID отзыва
            db: Сессия базы данных
        """
        try:
            # Получение отзыва из базы
            query = select(Review).where(Review.id == review_id)
            result = await db.execute(query)
            review = result.scalar_one_or_none()
            
            if not review:
                logger.error(f"Review {review_id} not found")
                return
            
            # Определение языка
            language = self._detect_language(review.text)
            review.language = language
            
            # Анализ тональности
            sentiment_result = self.sentiment_analyzer.analyze(review.text, language)
            
            # Анализ аспектов
            aspects = self.aspect_extractor.extract_aspects(review.text, language)
            
            # Анализ тональности по аспектам
            aspect_sentiments = {}
            for aspect, sentences in aspects.items():
                combined_text = " ".join(sentences)
                aspect_sentiment = self.aspect_extractor.classify_aspect_sentiment(
                    combined_text, self.sentiment_analyzer
                )
                aspect_sentiments[aspect] = aspect_sentiment
            
            # Извлечение ключевых фраз
            key_phrases = self.phrase_extractor.extract_key_phrases(
                review.text, sentiment_result['sentiment']
            )
            
            # Создание записи с результатами анализа
            analysis_result = AnalysisResult(
                review_id=review_id,
                sentiment=sentiment_result['sentiment'],
                confidence=sentiment_result['confidence'],
                aspects=aspect_sentiments,
                key_phrases=key_phrases,
                emotion_intensity=sentiment_result.get('emotion_intensity', {})
            )
            
            db.add(analysis_result)
            await db.commit()
            
            logger.info(f"Analysis completed for review {review_id}")
            
        except Exception as e:
            logger.error(f"Analysis failed for review {review_id}: {e}")
            await db.rollback()
    
    def _detect_language(self, text: str) -> str:
        """Определение языка текста"""
        # Используем встроенный метод анализатора тональности
        return self.sentiment_analyzer._detect_language(text)
    
    async def analyze_batch(self, review_ids: list, db: AsyncSession):
        """
        Пакетный анализ отзывов
        
        Args:
            review_ids: Список ID отзывов
            db: Сессия базы данных
        """
        logger.info(f"Starting batch analysis for {len(review_ids)} reviews")
        
        for review_id in review_ids:
            await self.analyze_and_save(review_id, db)
        
        logger.info(f"Batch analysis completed for {len(review_ids)} reviews")