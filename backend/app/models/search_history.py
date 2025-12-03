"""
搜索历史模型
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from datetime import datetime
from app.core.database import Base


class SearchHistory(Base):
    """搜索历史模型"""
    __tablename__ = "search_history"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(255), nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)  # 用户ID（如果启用用户系统）
    media_type = Column(String(20), nullable=True)  # 媒体类型
    filters = Column(Text, nullable=True)  # 筛选条件（JSON字符串）
    result_count = Column(Integer, default=0)  # 搜索结果数量
    searched_at = Column(DateTime, default=datetime.utcnow, index=True)  # 搜索时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

