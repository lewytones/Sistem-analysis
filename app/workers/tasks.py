"""
Celery задачи для асинхронной обработки
"""
from celery import Celery
from celery.result import AsyncResult
from typing import List
import logging

from app.config import settings
from app.database import SessionLocal
from app.services.analysis import ReviewAnalyzer

logger = logging.getLogger(__name__)

# Инициализация Celery
celery_app = Celery(
    'review_analysis',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.task_routes = {
    'app.workers.tasks.*': 'review-analysis-queue'
}

@celery_app.task(bind=True, max_retries=3)
def analyze_review_batch(self, review_ids: List[int]):
    """
    Celery задача для пакетного анализа отзывов
    
    Args:
        review_ids: Список ID отзывов для анализа
        
    Returns:
        Словарь с результатами обработки
    """
    try:
        logger.info(f"Starting batch analysis for {len(review_ids)} reviews")
        
        # Создание сессии базы данных
        db = SessionLocal()
        analyzer = ReviewAnalyzer()
        
        results = {
            'total': len(review_ids),
            'processed': 0,
            'failed': 0,
            'failed_ids': []
        }
        
        # Обработка каждого отзыва
        for review_id in review_ids:
            try:
                analyzer.analyze_and_save(review_id, db)
                results['processed'] += 1
            except Exception as e:
                logger.error(f"Failed to analyze review {review_id}: {e}")
                results['failed'] += 1
                results['failed_ids'].append(review_id)
        
        db.close()
        
        logger.info(f"Batch analysis completed: {results}")
        
        return results
        
    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        raise self.retry(exc=e, countdown=60)

def get_task_status(task_id: str) -> dict:
    """
    Получение статуса задачи
    
    Args:
        task_id: ID задачи Celery
        
    Returns:
        Словарь со статусом задачи
    """
    task_result = AsyncResult(task_id, app=celery_app)
    
    return {
        'task_id': task_id,
        'status': task_result.status,
        'result': task_result.result if task_result.ready() else None,
        'ready': task_result.ready(),
        'success': task_result.successful() if task_result.ready() else None
    }