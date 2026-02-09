"""
Анализ аспектов с использованием spaCy и правил
"""
from typing import Dict, List, Tuple
import spacy
from spacy.matcher import Matcher
import logging

logger = logging.getLogger(__name__)

class AspectExtractor:
    """Извлечение аспектов из текста"""
    
    def __init__(self):
        # Загрузка моделей spaCy для русского и английского
        try:
            self.nlp_ru = spacy.load("ru_core_news_sm")
            self.nlp_en = spacy.load("en_core_web_sm")
            logger.info("spaCy models loaded successfully")
        except OSError:
            logger.error("spaCy models not found. Please install: "
                       "python -m spacy download ru_core_news_sm en_core_web_sm")
            raise
        
        # Паттерны для извлечения аспектов
        self.aspect_patterns = {
            'ru': [
                # Качество продукта
                [{'LOWER': {'IN': ['качество', 'продукт', 'товар']}}],
                # Сервис
                [{'LOWER': {'IN': ['сервис', 'обслуживание', 'помощь']}}],
                # Цена
                [{'LOWER': {'IN': ['цена', 'стоимость', 'дорого', 'дешево']}}],
                # Доставка
                [{'LOWER': {'IN': ['доставка', 'отправка', 'прибытие']}}],
                # Упаковка
                [{'LOWER': {'IN': ['упаковка', 'пакет', 'коробка']}}],
            ],
            'en': [
                # Product quality
                [{'LOWER': {'IN': ['quality', 'product', 'item']}}],
                # Service
                [{'LOWER': {'IN': ['service', 'support', 'help']}}],
                # Price
                [{'LOWER': {'IN': ['price', 'cost', 'expensive', 'cheap']}}],
                # Delivery
                [{'LOWER': {'IN': ['delivery', 'shipping', 'arrival']}}],
                # Packaging
                [{'LOWER': {'IN': ['packaging', 'package', 'box']}}],
            ]
        }
        
        # Инициализация матчера
        self.matchers = {}
        for lang in ['ru', 'en']:
            nlp = self.nlp_ru if lang == 'ru' else self.nlp_en
            matcher = Matcher(nlp.vocab)
            
            for i, pattern in enumerate(self.aspect_patterns[lang]):
                matcher.add(f"ASPECT_{i}", [pattern])
            
            self.matchers[lang] = matcher
    
    def extract_aspects(self, text: str, language: str = 'ru') -> Dict[str, List[str]]:
        """
        Извлечение аспектов из текста
        
        Args:
            text: Текст для анализа
            language: Язык текста (ru/en)
            
        Returns:
            Словарь с найденными аспектами
        """
        aspects = {}
        
        try:
            # Выбор модели в зависимости от языка
            nlp = self.nlp_ru if language == 'ru' else self.nlp_en
            matcher = self.matchers[language]
            
            # Обработка текста
            doc = nlp(text)
            matches = matcher(doc)
            
            # Извлечение аспектов
            for match_id, start, end in matches:
                aspect = doc[start:end].text.lower()
                span = doc[start:end]
                
                # Получение контекста (предложение)
                sentence = span.sent.text
                
                if aspect not in aspects:
                    aspects[aspect] = []
                aspects[aspect].append(sentence)
            
            logger.info(f"Extracted {len(aspects)} aspects from text")
            
        except Exception as e:
            logger.error(f"Aspect extraction failed: {e}")
        
        return aspects
    
    def classify_aspect_sentiment(self, aspect_text: str, sentiment_analyzer) -> Dict:
        """
        Классификация тональности для каждого аспекта
        
        Args:
            aspect_text: Текст, связанный с аспектом
            sentiment_analyzer: Экземпляр анализатора тональности
            
        Returns:
            Словарь с тональностью и уверенностью
        """
        try:
            result = sentiment_analyzer.analyze(aspect_text)
            return {
                'sentiment': result['sentiment'],
                'confidence': result['confidence']
            }
        except Exception as e:
            logger.error(f"Aspect sentiment classification failed: {e}")
            return {
                'sentiment': 'neutral',
                'confidence': 0.5
            }