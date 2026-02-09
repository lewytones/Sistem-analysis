"""
Базовый класс для всех моделей SQLAlchemy
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime, Boolean, func
from datetime import datetime

Base = declarative_base()

class BaseModel(Base):
    """Базовая модель с аудит полями"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    
    def soft_delete(self):
        """Мягкое удаление записи"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()