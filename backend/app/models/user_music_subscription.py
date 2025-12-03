"""
用户音乐订阅模型

用户可以订阅榜单或关键字，自动搜索和下载新曲目
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, Enum
from datetime import datetime
from enum import Enum as PyEnum
from app.core.database import Base


class MusicSubscriptionType(str, PyEnum):
    """音乐订阅类型"""
    CHART = "chart"      # 榜单订阅
    KEYWORD = "keyword"  # 关键字订阅


class UserMusicSubscription(Base):
    """
    用户音乐订阅
    
    支持两种订阅类型：
    1. 榜单订阅：检测榜单新增曲目并自动搜索下载
    2. 关键字订阅：根据关键字定期搜索新资源
    """
    __tablename__ = "user_music_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 用户 ID
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 订阅类型
    subscription_type = Column(
        Enum(MusicSubscriptionType),
        default=MusicSubscriptionType.CHART,
        nullable=False,
        index=True
    )
    
    # 订阅的榜单（仅CHART类型使用）
    chart_id = Column(Integer, ForeignKey("music_charts.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # 关键字订阅字段（仅KEYWORD类型使用）
    music_query = Column(String(500), nullable=True, index=True)  # 搜索关键字
    music_site = Column(String(100), nullable=True)  # 指定站点（可选）
    music_quality = Column(String(50), nullable=True)  # 质量偏好（FLAC/MP3/320等）
    
    # 订阅状态
    status = Column(String(20), default="active", index=True)  # active / paused
    
    # 是否自动发起 PT 搜索
    auto_search = Column(Boolean, default=True)
    
    # 找到资源后是否自动下载
    auto_download = Column(Boolean, default=False)
    
    # 每次运行最多处理的新曲目数
    max_new_tracks_per_run = Column(Integer, default=10)
    
    # 搜索质量偏好（flac / mp3_320 / any）
    quality_preference = Column(String(20), nullable=True, default="flac")
    
    # 优先站点（JSON 数组，如 ["orpheus", "redacted"]）
    preferred_sites = Column(String(500), nullable=True)
    
    # 安全策略字段（复用视频订阅的安全策略）
    allow_hr = Column(Boolean, default=False)  # 是否允许 HR/H&R
    allow_h3h5 = Column(Boolean, default=False)  # 是否允许 H3/H5 等扩展规则
    strict_free_only = Column(Boolean, default=False)  # 只下载 free/促销种
    
    # 最后运行时间
    last_run_at = Column(DateTime, nullable=True)
    
    # 最后运行结果统计
    last_run_new_count = Column(Integer, nullable=True)
    last_run_search_count = Column(Integer, nullable=True)
    last_run_download_count = Column(Integer, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        # 榜单订阅唯一约束（包含subscription_type确保唯一性）
        Index("ix_user_music_subs_user_chart_type", "user_id", "subscription_type", "chart_id", unique=True),
        # 关键字订阅唯一约束（包含subscription_type确保唯一性）
        Index("ix_user_music_subs_user_query_type", "user_id", "subscription_type", "music_query", unique=True),
        # 状态和运行时间索引
        Index("ix_user_music_subs_status_last_run", "status", "last_run_at"),
        # 订阅类型索引
        Index("ix_user_music_subs_type_status", "subscription_type", "status"),
    )
