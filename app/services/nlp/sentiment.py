"""
Анализ тональности с поддержкой русского и английского языков
"""
from typing import Dict, Tuple, Optional
import logging
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from textblob import TextBlob
from langdetect import detect

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Класс для анализа тональности текста"""
    
    def __init__(self, use_transformers: bool = True, fallback: bool = True):
        self.use_transformers = use_transformers
        self.fallback = fallback
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Загрузка моделей
        self.models = {}
        self.tokenizers = {}
        
        if use_transformers:
            try:
                # Русская модель
                self.tokenizers['ru'] = AutoTokenizer.from_pretrained(
                    "DeepPavlov/rubert-base-cased-sentiment"
                )
                self.models['ru'] = AutoModelForSequenceClassification.from_pretrained(
                    "DeepPavlov/rubert-base-cased-sentiment"
                ).to(self.device)
                
                # Английская модель
                self.tokenizers['en'] = AutoTokenizer.from_pretrained(
                    "cardiffnlp/twitter-roberta-base-sentiment"
                )
                self.models['en'] = AutoModelForSequenceClassification.from_pretrained(
                    "cardiffnlp/twitter-roberta-base-sentiment"
                ).to(self.device)
                
                logger.info("Transformers models loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load transformers models: {e}")
                if not fallback:
                    raise
                self.use_transformers = False
    
    def analyze(self, text: str, language: str = None) -> Dict:
        """
        Анализ тональности текста
        
        Args:
            text: Текст для анализа
            language: Язык текста (ru/en), если не указан - автоопределение
            
        Returns:
            Словарь с результатами анализа
        """
        # Определение языка
        if language is None:
            language = self._detect_language(text)
        
        # Выбор метода анализа
        if self.use_transformers and language in self.models:
            return self._analyze_with_transformers(text, language)
        else:
            return self._analyze_with_fallback(text, language)
    
    def _detect_language(self, text: str) -> str:
        """Автоопределение языка текста"""
        try:
            lang = detect(text)
            return 'ru' if lang.startswith('ru') else 'en'
        except:
            # По умолчанию русский (приоритет)
            return 'ru'
    
    def _analyze_with_transformers(self, text: str, language: str) -> Dict:
        """Анализ с использованием transformers"""
        try:
            tokenizer = self.tokenizers[language]
            model = self.models[language]
            
            # Токенизация
            inputs = tokenizer(text, return_tensors="pt", 
                             truncation=True, max_length=512)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Предсказание
            with torch.no_grad():
                outputs = model(**inputs)
                probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # Получение результатов
            probs = probabilities[0].cpu().numpy()
            
            if language == 'ru':
                # Для русской модели: [negative, neutral, positive]
                sentiment_scores = {
                    'negative': float(probs[0]),
                    'neutral': float(probs[1]),
                    'positive': float(probs[2])
                }
            else:
                # Для английской модели: [negative, neutral, positive]
                sentiment_scores = {
                    'negative': float(probs[0]),
                    'neutral': float(probs[1]),
                    'positive': float(probs[2])
                }
            
            # Определение доминирующей тональности
            dominant_sentiment = max(sentiment_scores, key=sentiment_scores.get)
            confidence = sentiment_scores[dominant_sentiment]
            
            return {
                'sentiment': dominant_sentiment,
                'confidence': confidence,
                'scores': sentiment_scores,
                'emotion_intensity': self._calculate_emotion_intensity(text, language)
            }
            
        except Exception as e:
            logger.error(f"Transformers analysis failed: {e}")
            if self.fallback:
                return self._analyze_with_fallback(text, language)
            raise
    
    def _analyze_with_fallback(self, text: str, language: str) -> Dict:
        """Резервный анализ с использованием TextBlob"""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            # Определение тональности по полярности
            if polarity > 0.1:
                sentiment = 'positive'
                confidence = min(1.0, polarity + 0.5)
            elif polarity < -0.1:
                sentiment = 'negative'
                confidence = min(1.0, abs(polarity) + 0.5)
            else:
                sentiment = 'neutral'
                confidence = 0.5
            
            return {
                'sentiment': sentiment,
                'confidence': confidence,
                'scores': {
                    'negative': max(0, -polarity),
                    'neutral': 0.5 if sentiment == 'neutral' else 0.2,
                    'positive': max(0, polarity)
                },
                'emotion_intensity': {}
            }
            
        except Exception as e:
            logger.error(f"Fallback analysis failed: {e}")
            # Возвращаем нейтральный результат по умолчанию
            return {
                'sentiment': 'neutral',
                'confidence': 0.5,
                'scores': {'negative': 0.3, 'neutral': 0.4, 'positive': 0.3},
                'emotion_intensity': {}
            }
    
    def _calculate_emotion_intensity(self, text: str, language: str) -> Dict:
        """
        Расчет интенсивности эмоций (упрощенная версия)
        В реальной системе здесь должна быть более сложная модель
        """
        # Простая эвристика для определения интенсивности эмоций
        text_lower = text.lower()
        
        emotion_keywords = {
            'joy': ['хорошо', 'отлично', 'прекрасно', 'рад', 'счастлив', 'good', 'great', 'excellent', 'happy', 'joy'],
            'anger': ['плохо', 'ужасно', 'злой', 'разочарован', 'ненавижу', 'bad', 'terrible', 'angry', 'hate', 'disappointed'],
            'sadness': ['грустно', 'печально', 'разочарование', 'sad', 'disappointed', 'unhappy'],
            'surprise': ['удивительно', 'неожиданно', 'шокирован', 'surprising', 'unexpected', 'shocked'],
            'fear': ['беспокоюсь', 'боюсь', 'опасаюсь', 'worry', 'fear', 'concerned']
        }
        
        intensities = {}
        for emotion, keywords in emotion_keywords.items():
            count = sum(1 for word in keywords if word in text_lower)
            intensities[emotion] = min(1.0, count * 0.2)  # Максимум 1.0
        
        # Нормализация
        total = sum(intensities.values())
        if total > 0:
            intensities = {k: v/total for k, v in intensities.items()}
        
        return intensities