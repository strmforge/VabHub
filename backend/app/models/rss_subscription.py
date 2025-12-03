"""
RSS订阅模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Index, UniqueConstraint, ForeignKey
from datetime import datetime
from app.core.database import Base


class RSSSubscription(Base):
    """RSS订阅模型"""
    __tablename__ = "rss_subscriptions"
    
    # 添加复合索引优化查询性能
    __table_args__ = (
        # 复合索引：enabled + next_check（用于查找需要刷新的订阅）
        Index('idx_enabled_next_check', 'enabled', 'next_check'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'} if hasattr(Base, 'metadata') and hasattr(Base.metadata, 'bind') and str(Base.metadata.bind.url).startswith('mysql') else {},
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 订阅归属用户
    name = Column(String(255), nullable=False, index=True)  # 订阅名称（添加索引）
    url = Column(String(500), nullable=False)  # RSS URL
    site_id = Column(Integer, nullable=True, index=True)  # 关联站点ID（添加索引）
    enabled = Column(Boolean, default=True, index=True)  # 是否启用（添加索引）
    interval = Column(Integer, default=30)  # 刷新间隔（分钟）
    last_check = Column(DateTime, nullable=True, index=True)  # 最后检查时间（添加索引）
    next_check = Column(DateTime, nullable=True, index=True)  # 下次检查时间（添加索引）
    last_item_hash = Column(String(64), nullable=True)  # 最后处理的RSS项哈希（用于增量更新）
    
    # 过滤规则
    filter_rules = Column(JSON, nullable=True)  # 过滤规则（包含/排除关键字、正则等）
    download_rules = Column(JSON, nullable=True)  # 下载规则（质量、大小、做种数等）
    filter_group_ids = Column(JSON, nullable=False, default=list)  # 过滤规则组ID列表
    
    # 统计信息
    total_items = Column(Integer, default=0)  # 总处理项数
    downloaded_items = Column(Integer, default=0)  # 已下载项数
    skipped_items = Column(Integer, default=0)  # 跳过项数
    error_count = Column(Integer, default=0)  # 错误计数
    
    # 元数据
    description = Column(Text, nullable=True)  # 订阅描述
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RSSItem(Base):
    """RSS项模型（用于记录已处理的RSS项）"""
    __tablename__ = "rss_items"
    
    # 添加复合索引优化查询性能
    __table_args__ = (
        # 唯一索引：subscription_id + item_hash（防止重复项）
        UniqueConstraint('subscription_id', 'item_hash', name='uq_subscription_item_hash'),
        # 复合索引：subscription_id + processed（用于查询未处理项）
        Index('idx_subscription_processed', 'subscription_id', 'processed'),
        # 复合索引：subscription_id + downloaded（用于查询已下载项）
        Index('idx_subscription_downloaded', 'subscription_id', 'downloaded'),
        # 复合索引：subscription_id + created_at（用于排序）
        Index('idx_subscription_created', 'subscription_id', 'created_at'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'} if hasattr(Base, 'metadata') and hasattr(Base.metadata, 'bind') and str(Base.metadata.bind.url).startswith('mysql') else {},
    )
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, nullable=False, index=True)  # RSS订阅ID
    item_hash = Column(String(64), nullable=False, index=True)  # RSS项哈希（title + link）
    title = Column(String(500), nullable=False, index=True)  # RSS项标题（添加索引用于搜索）
    link = Column(String(500), nullable=False)  # RSS项链接
    description = Column(Text, nullable=True)  # RSS项描述
    pub_date = Column(DateTime, nullable=True, index=True)  # 发布时间（添加索引用于排序）
    processed = Column(Boolean, default=False, index=True)  # 是否已处理（添加索引）
    downloaded = Column(Boolean, default=False, index=True)  # 是否已下载（添加索引）
    download_task_id = Column(String(100), nullable=True, index=True)  # 关联下载任务ID（添加索引）
    created_at = Column(DateTime, default=datetime.utcnow, index=True)  # 创建时间（添加索引用于排序）
    processed_at = Column(DateTime, nullable=True)  # 处理时间

