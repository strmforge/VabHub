"""
音乐榜单源模型

定义榜单数据来源平台（如 Apple Music、网易云、QQ音乐等）
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Index
from datetime import datetime
from app.core.database import Base


class MusicChartSource(Base):
    """
    音乐榜单源
    
    表示一个榜单数据来源平台，如：
    - apple_music: Apple Music
    - itunes: iTunes
    - netease: 网易云音乐
    - qqmusic: QQ音乐
    - custom_rss: 自定义 RSS 源
    """
    __tablename__ = "music_chart_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 平台标识（唯一）
    platform = Column(String(50), nullable=False, unique=True, index=True)
    # 显示名称
    display_name = Column(String(100), nullable=False)
    # 描述
    description = Column(Text, nullable=True)
    
    # 平台配置（JSON）
    # 例如：{ "api_base_url": "...", "region": "CN", "api_key": "..." }
    config = Column(JSON, nullable=True)
    
    # 是否启用
    is_enabled = Column(Boolean, default=True, index=True)
    
    # 图标 URL（可选）
    icon_url = Column(String(500), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_music_chart_sources_enabled_platform", "is_enabled", "platform"),
    )
