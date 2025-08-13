"""
セキュアAIチャット - ベースモデル
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime
from datetime import datetime

# SQLAlchemy Base
Base = declarative_base()

class BaseModel(Base):
    """ベースモデル - 共通フィールドを定義"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)