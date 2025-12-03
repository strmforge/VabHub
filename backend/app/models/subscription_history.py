"""
订阅历史记录模型
记录订阅的所有操作历史
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Float
from datetime import datetime
from app.core.database import Base


class SubscriptionHistory(Base):
    """订阅历史记录模型"""
    __tablename__ = "subscription_history"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False, index=True)
    
    # 操作信息
    action = Column(String(50), nullable=False)  # create, update, delete, enable, disable, search, download
    action_type = Column(String(50), nullable=False)  # operation, search, download
    
    # 操作详情
    description = Column(Text, nullable=True)  # 操作描述
    old_value = Column(JSON, nullable=True)  # 旧值（用于更新操作）
    new_value = Column(JSON, nullable=True)  # 新值（用于更新操作）
    
    # 搜索结果信息（如果是搜索操作）
    search_query = Column(String(500), nullable=True)  # 搜索关键词
    search_results_count = Column(Integer, nullable=True)  # 搜索结果数量
    search_params = Column(JSON, nullable=True)  # 搜索参数
    
    # 下载信息（如果是下载操作）
    download_task_id = Column(String(100), nullable=True)  # 下载任务ID
    download_title = Column(String(500), nullable=True)  # 下载标题
    download_size_gb = Column(Float, nullable=True)  # 下载大小
    
    # 状态信息
    status = Column(String(20), nullable=True)  # success, failed, partial
    error_message = Column(Text, nullable=True)  # 错误信息（如果失败）
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 用户信息（可选）
    user_id = Column(Integer, nullable=True)  # 操作用户ID

