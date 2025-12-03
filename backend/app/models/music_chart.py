"""
音乐榜单模型

定义具体的榜单（如"华语新歌榜"、"热歌榜"等）
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index
from datetime import datetime
from app.core.database import Base


class MusicChart(Base):
    """
    音乐榜单
    
    表示一个具体的榜单，属于某个 MusicChartSource。
    例如：
    - Apple Music 中国热歌榜
    - 网易云音乐飙升榜
    - QQ音乐新歌榜
    """
    __tablename__ = "music_charts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联的榜单源
    source_id = Column(Integer, ForeignKey("music_chart_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 平台内部标识（如 playlist id、RSS 路径等）
    chart_key = Column(String(255), nullable=False)
    
    # 显示名称
    display_name = Column(String(200), nullable=False)
    
    # 描述
    description = Column(Text, nullable=True)
    
    # 地区（可选）
    region = Column(String(20), nullable=True, default="CN")
    
    # 榜单类型（hot/new/rising/custom 等）
    chart_type = Column(String(50), nullable=True, default="hot")
    
    # 是否启用
    is_enabled = Column(Boolean, default=True, index=True)
    
    # 最后抓取时间
    last_fetched_at = Column(DateTime, nullable=True)
    
    # 抓取间隔（分钟），默认 60 分钟
    fetch_interval_minutes = Column(Integer, default=60)
    
    # 最大条目数（抓取时限制）
    max_items = Column(Integer, default=100)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_music_charts_source_key", "source_id", "chart_key", unique=True),
        Index("ix_music_charts_enabled_source", "is_enabled", "source_id"),
    )
