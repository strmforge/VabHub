"""
音乐相关模型

包含 Music（作品/专辑级）和 MusicFile（文件级）两个模型。
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Float, ForeignKey, Index
from datetime import datetime
from app.core.database import Base


class Music(Base):
    """
    音乐作品/专辑模型（Work-level Entity）
    
    表示一个音乐作品或专辑（work），是逻辑上的"作品层实体"。
    
    语义说明：
    - Music 代表"专辑"或"单曲作品"，而不是单个文件
    - 同一作品（相同 artist + album + title）只对应一个 Music 记录
    - 同一作品可以有多个文件版本（不同格式、不同来源），都通过 MusicFile 关联到同一个 Music
    """
    __tablename__ = "musics"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)  # 标题（一般为专辑名或单曲名）
    artist = Column(String(255), nullable=False, index=True)  # 艺术家/歌手（必填或常用，尽量解析）
    album = Column(String(255), nullable=True, index=True)  # 专辑名（可选，如果是单曲）
    album_artist = Column(String(255), nullable=True)  # 专辑艺术家（可选）
    genre = Column(String(255), nullable=True)  # 风格（可选）
    language = Column(String(20), nullable=True)  # 语言代码（可选，如 "zh-CN", "en", "ja", "ko"）
    year = Column(Integer, nullable=True)  # 年份（可选）
    tags = Column(Text, nullable=True)  # 标签（JSON 字符串或逗号分隔）
    extra_metadata = Column(JSON, nullable=True)  # 附加元数据（JSON，记录解析到的原始 tag）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 创建索引以支持常见查询
    __table_args__ = (
        Index("ix_musics_artist_album", "artist", "album"),
        Index("ix_musics_artist_title", "artist", "title"),
    )


class MusicFile(Base):
    """
    音乐文件模型
    
    表示音乐的一个具体文件（MP3、FLAC、M4A 等）
    Phase 3 扩展：支持去重和质量优选
    """
    __tablename__ = "music_files"
    
    id = Column(Integer, primary_key=True, index=True)
    music_id = Column(Integer, ForeignKey("musics.id", ondelete="CASCADE"), nullable=False, index=True)  # 关联到作品
    file_path = Column(String(1000), nullable=False, unique=True, index=True)  # 文件路径（绝对或相对）
    file_size_bytes = Column(Integer, nullable=True)  # 文件大小（字节）
    file_size_mb = Column(Float, nullable=True)  # 文件大小（MB，计算字段）
    format = Column(String(20), nullable=False, index=True)  # 文件格式：mp3, flac, ape, m4a, aac, ogg, wav 等
    duration_seconds = Column(Integer, nullable=True)  # 时长（秒）
    bitrate_kbps = Column(Integer, nullable=True)  # 比特率（kbps）
    sample_rate_hz = Column(Integer, nullable=True)  # 采样率（Hz）
    channels = Column(Integer, nullable=True)  # 声道数（1=单声道, 2=立体声）
    bit_depth = Column(Integer, nullable=True)  # 位深度（16/24/32）
    track_number = Column(Integer, nullable=True)  # 轨道号（可选）
    disc_number = Column(Integer, nullable=True)  # 碟号（可选）
    source_site_id = Column(String(100), nullable=True, index=True)  # 来源站点 ID
    source_torrent_id = Column(String(100), nullable=True)  # 来源种子 ID
    download_task_id = Column(Integer, nullable=True, index=True)  # 关联的下载任务 ID（如果有）
    download_job_id = Column(Integer, ForeignKey("music_download_jobs.id", ondelete="SET NULL"), nullable=True, index=True)  # 关联的音乐下载任务
    
    # ========== 去重和质量优选 ==========
    is_preferred = Column(Boolean, default=True, index=True)  # 是否为当前 Music 的首选文件
    quality_score = Column(Float, nullable=True)  # 质量评分（用于比较）
    
    is_deleted = Column(Boolean, default=False, index=True)  # 是否已删除
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 自动计算 file_size_mb
        if self.file_size_bytes and not self.file_size_mb:
            self.file_size_mb = round(self.file_size_bytes / (1024 ** 2), 2)


# ========== 以下为音乐订阅和榜单相关模型（保留原有功能） ==========

class MusicSubscription(Base):
    """音乐订阅模型"""
    __tablename__ = "music_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # artist, album, playlist, genre
    platform = Column(String(50), nullable=False)  # spotify, apple_music, qq_music, netease
    target_id = Column(String(255), nullable=False)  # 目标ID
    target_name = Column(String(255), nullable=True)  # 目标名称
    status = Column(String(20), default="active")  # active, paused, completed
    auto_download = Column(Boolean, default=True)
    quality = Column(String(20), nullable=True)  # flac, mp3_320, mp3_128
    download_count = Column(Integer, default=0)
    last_check = Column(DateTime, nullable=True)
    next_check = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MusicTrack(Base):
    """音乐曲目模型"""
    __tablename__ = "music_tracks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=False)
    album = Column(String(255), nullable=True)
    duration = Column(Integer, nullable=True)  # 秒
    release_date = Column(DateTime, nullable=True)
    genre = Column(Text, nullable=True)  # 流派列表（JSON字符串）
    platform = Column(String(50), nullable=False)
    platform_id = Column(String(255), nullable=False, index=True)
    external_url = Column(String(500), nullable=True)
    preview_url = Column(String(500), nullable=True)
    cover_url = Column(String(500), nullable=True)
    popularity = Column(Float, nullable=True)
    file_path = Column(String(1000), nullable=True)  # 本地文件路径
    file_size_mb = Column(Float, nullable=True)
    quality = Column(String(20), nullable=True)  # flac, mp3_320, mp3_128
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MusicPlaylist(Base):
    """音乐播放列表模型"""
    __tablename__ = "music_playlists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    track_ids = Column(Text, nullable=True)  # 曲目ID列表（JSON字符串）
    cover_url = Column(String(500), nullable=True)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MusicLibrary(Base):
    """音乐库模型"""
    __tablename__ = "music_library"
    
    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(Integer, ForeignKey("music_tracks.id"), nullable=False)
    file_path = Column(String(1000), nullable=False, unique=True)
    file_size_mb = Column(Float, nullable=False)
    quality = Column(String(20), nullable=True)
    scan_date = Column(DateTime, default=datetime.utcnow)


class MusicChartRecord(Base):
    """音乐榜单持久化记录"""
    __tablename__ = "music_chart_entries"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(36), nullable=False, index=True)
    platform = Column(String(50), nullable=False, index=True)
    chart_type = Column(String(20), nullable=False, index=True)
    region = Column(String(10), nullable=False, index=True, default="CN")
    rank = Column(Integer, nullable=True)
    title = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=False)
    album = Column(String(255), nullable=True)
    external_url = Column(String(500), nullable=True)
    cover_url = Column(String(500), nullable=True)
    raw_data = Column(JSON, nullable=True)
    captured_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
