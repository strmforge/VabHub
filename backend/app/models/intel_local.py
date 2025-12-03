"""
Local Intel 相关模型
用于持久化 HR 状态、站点防护配置和站内信事件
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Index
from datetime import datetime
from app.core.database import Base


# HRCase 模型已迁移至 app/modules/hr_case/models.py
# 为了向后兼容，提供别名导入
from app.modules.hr_case.models import HrCase as HRCase


class SiteGuardProfile(Base):
    """
    站点防护配置
    存储每个站点的扫描限速和风控状态
    """
    __tablename__ = "site_guard_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    site = Column(String(100), nullable=False, unique=True, index=True)
    
    # 风控状态
    last_block_start = Column(DateTime, nullable=True)  # 最后被阻止的开始时间
    last_block_end = Column(DateTime, nullable=True)  # 最后被阻止的结束时间
    last_block_cause = Column(String(255), nullable=True)  # 被阻止的原因
    
    # 扫描历史（用于自适应限速）
    last_full_scan_minutes = Column(Integer, nullable=True)  # 最后一次完整扫描的分钟数
    last_full_scan_pages = Column(Integer, nullable=True)  # 最后一次完整扫描的页数
    
    # 安全扫描参数（自适应调整）
    safe_scan_minutes = Column(Integer, default=10)  # 安全扫描分钟数
    safe_pages_per_hour = Column(Integer, default=200)  # 每小时安全页数
    
    # 时间戳
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class InboxEvent(Base):
    """
    站内信事件记录
    用于审计和去重
    """
    __tablename__ = "inbox_events"
    
    id = Column(Integer, primary_key=True, index=True)
    site = Column(String(100), nullable=False, index=True)
    
    # 消息内容（用于去重）
    message_hash = Column(String(64), nullable=False, index=True)  # 消息内容的哈希值
    message_text = Column(Text, nullable=True)  # 消息文本（可选，用于调试）
    
    # 事件类型
    event_type = Column(String(50), nullable=False, index=True)  # penalty, delete, throttle, other
    
    # 关联信息（如果可以从消息中提取）
    torrent_id = Column(String(100), nullable=True, index=True)  # 关联的种子ID（如果可提取）
    
    # 时间戳
    message_time = Column(DateTime, nullable=True)  # 消息时间（从站内信提取）
    processed_at = Column(DateTime, default=datetime.utcnow)  # 处理时间
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 创建唯一索引：site + message_hash（避免重复处理同一条消息）
    __table_args__ = (
        Index("ix_inbox_events_site_hash", "site", "message_hash", unique=True),
    )


class SiteGuardEvent(Base):
    """
    站点风控事件记录
    """

    __tablename__ = "site_guard_events"

    id = Column(Integer, primary_key=True, index=True)
    site = Column(String(100), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, default="block")
    created_at = Column(DateTime, default=datetime.utcnow)
    block_until = Column(DateTime, nullable=True)
    scan_minutes_before_block = Column(Integer, nullable=True)
    scan_pages_before_block = Column(Integer, nullable=True)
    cause = Column(String(255), nullable=True)


class InboxCursor(Base):
    """
    站内信游标（用于记录已处理到哪一封）
    """

    __tablename__ = "inbox_cursor"

    site = Column(String(100), primary_key=True)
    last_message_id = Column(String(255), nullable=True)
    last_checked_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TorrentIndex(Base):
    """
    PT 种子索引表（Phase 9）
    存储从 PT 站点抓取的种子结构化信息，用于本地搜索和排序
    """
    __tablename__ = "torrent_index"
    
    id = Column(Integer, primary_key=True, index=True)
    # 唯一标识：站点 + 种子ID
    site_id = Column(String(100), nullable=False, index=True)
    torrent_id = Column(String(100), nullable=False, index=True)
    
    # 标题 & 解析
    title_raw = Column(Text, nullable=False)  # 原始标题
    title_clean = Column(Text, nullable=True)  # 清洗后的标题（可选）
    
    # 分类 & 属性
    category = Column(String(50), nullable=True, index=True)  # movie/tv/anime/music 等
    is_hr = Column(Integer, default=0)  # 0=否, 1=是（使用 Integer 便于索引）
    is_free = Column(Integer, default=0)  # 0=否, 1=是
    is_half_free = Column(Integer, default=0)  # 0=否, 1=是（如 50%）
    
    # 资源信息
    size_bytes = Column(Integer, nullable=True)  # 文件大小（字节）
    seeders = Column(Integer, default=0, index=True)
    leechers = Column(Integer, default=0)
    completed = Column(Integer, nullable=True)  # 完成数（可选）
    
    # 时间
    published_at = Column(DateTime, nullable=True, index=True)  # 发布时间
    last_seen_at = Column(DateTime, nullable=False, index=True)  # 最后看到时间
    
    # 状态
    is_deleted = Column(Integer, default=0, index=True)  # 0=否, 1=是
    deleted_at = Column(DateTime, nullable=True)  # 删除时间
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 创建唯一索引：site_id + torrent_id
    __table_args__ = (
        Index("ix_torrent_index_site_torrent", "site_id", "torrent_id", unique=True),
        Index("ix_torrent_index_title", "title_raw"),  # 用于标题搜索
        Index("ix_torrent_index_published", "published_at"),  # 用于时间排序
    )

