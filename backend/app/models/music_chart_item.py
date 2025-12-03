"""
音乐榜单条目模型

存储榜单中的具体曲目信息
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Index
from datetime import datetime
import hashlib
from app.core.database import Base


class MusicChartItem(Base):
    """
    音乐榜单条目
    
    表示榜单中的一首曲目。
    注意：这是"候选曲目"，不一定对应本地 MusicTrack。
    """
    __tablename__ = "music_chart_items"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联的榜单
    chart_id = Column(Integer, ForeignKey("music_charts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 榜单名次
    rank = Column(Integer, nullable=True)
    
    # 曲目信息
    title = Column(String(255), nullable=False)
    artist_name = Column(String(255), nullable=False)
    album_name = Column(String(255), nullable=True)
    
    # 外部 ID（JSON，如 { "apple_music_id": "...", "isrc": "..." }）
    external_ids = Column(JSON, nullable=True)
    
    # 时长（秒）
    duration_seconds = Column(Integer, nullable=True)
    
    # 封面 URL
    cover_url = Column(String(500), nullable=True)
    
    # 外部链接
    external_url = Column(String(500), nullable=True)
    
    # 去重哈希（基于 title + artist_name 生成）
    hash_key = Column(String(64), nullable=False, index=True)
    
    # 抓取批次 ID（用于追踪同一次抓取的条目）
    batch_id = Column(String(36), nullable=True, index=True)
    
    # 首次出现时间（在该榜单中）
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    
    # 最后更新时间（排名变化等）
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_music_chart_items_chart_hash", "chart_id", "hash_key", unique=True),
        Index("ix_music_chart_items_chart_rank", "chart_id", "rank"),
        Index("ix_music_chart_items_first_seen", "first_seen_at"),
    )
    
    @staticmethod
    def generate_hash_key(title: str, artist_name: str) -> str:
        """生成去重哈希"""
        normalized = f"{title.strip().lower()}|{artist_name.strip().lower()}"
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]
