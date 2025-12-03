"""
订阅刷新历史记录模型
用于记录每次订阅刷新的详细信息，支持状态监控和历史查询
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Index
from datetime import datetime
from app.core.database import Base


class SubscriptionRefreshHistory(Base):
    """订阅刷新历史记录"""
    __tablename__ = "subscription_refresh_history"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False, index=True)
    subscription_title = Column(String(255), nullable=True)  # 订阅标题（冗余字段，便于查询）
    status = Column(String(20), nullable=False, index=True)  # 状态：running, success, failed, cancelled
    trigger_type = Column(String(20), nullable=False)  # 触发类型：auto, manual, scheduled
    start_time = Column(DateTime, nullable=False, index=True)  # 开始时间
    end_time = Column(DateTime, nullable=True)  # 结束时间
    duration_ms = Column(Integer, nullable=True)  # 耗时（毫秒）
    
    # 刷新结果
    results_count = Column(Integer, default=0)  # 找到的结果数量
    downloaded_count = Column(Integer, default=0)  # 下载的数量
    skipped_count = Column(Integer, default=0)  # 跳过的数量
    error_count = Column(Integer, default=0)  # 错误数量
    
    # 详细信息
    search_query = Column(Text, nullable=True)  # 搜索查询
    search_sites = Column(JSON, nullable=True)  # 搜索的站点列表
    matched_rules = Column(JSON, nullable=True)  # 匹配的规则
    error_message = Column(Text, nullable=True)  # 错误信息
    error_details = Column(JSON, nullable=True)  # 错误详情
    
    # 性能指标
    search_duration_ms = Column(Integer, nullable=True)  # 搜索耗时
    download_duration_ms = Column(Integer, nullable=True)  # 下载耗时
    total_duration_ms = Column(Integer, nullable=True)  # 总耗时
    
    # 元数据
    extra_metadata = Column(JSON, nullable=True)  # 其他元数据（避免使用metadata保留字）
    created_at = Column(DateTime, default=datetime.utcnow, index=True)  # 创建时间
    
    # 索引
    __table_args__ = (
        Index('idx_refresh_subscription_created', 'subscription_id', 'created_at'),
        Index('idx_refresh_status_created', 'status', 'created_at'),
        Index('idx_refresh_trigger_created', 'trigger_type', 'created_at'),
    )


class SubscriptionRefreshStatus(Base):
    """订阅刷新状态（实时状态）"""
    __tablename__ = "subscription_refresh_status"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False, unique=True, index=True)
    status = Column(String(20), nullable=False, index=True)  # 状态：idle, running, queued, error
    current_refresh_id = Column(Integer, ForeignKey("subscription_refresh_history.id"), nullable=True)  # 当前刷新记录ID
    last_refresh_time = Column(DateTime, nullable=True)  # 最后刷新时间
    next_refresh_time = Column(DateTime, nullable=True, index=True)  # 下次刷新时间
    last_success_time = Column(DateTime, nullable=True)  # 最后成功时间
    last_error_time = Column(DateTime, nullable=True)  # 最后错误时间
    consecutive_failures = Column(Integer, default=0)  # 连续失败次数
    total_refreshes = Column(Integer, default=0)  # 总刷新次数
    total_successes = Column(Integer, default=0)  # 总成功次数
    total_failures = Column(Integer, default=0)  # 总失败次数
    success_rate = Column(Integer, default=100)  # 成功率（百分比）
    avg_duration_ms = Column(Integer, nullable=True)  # 平均耗时（毫秒）
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 更新时间

