"""
媒体服务器模型
支持Plex、Jellyfin、Emby
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text, Float, Index
from datetime import datetime
from app.core.database import Base


class MediaServer(Base):
    """媒体服务器模型"""
    __tablename__ = "media_servers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)  # 服务器名称
    server_type = Column(String(50), nullable=False, index=True)  # 服务器类型: plex, jellyfin, emby
    url = Column(String(500), nullable=False)  # 服务器地址
    api_key = Column(String(500), nullable=True)  # API密钥（用于Jellyfin/Emby）
    token = Column(String(500), nullable=True)  # Token（用于Plex）
    username = Column(String(255), nullable=True)  # 用户名（用于Plex）
    password = Column(String(255), nullable=True)  # 密码（用于Plex，加密存储）
    user_id = Column(String(255), nullable=True)  # 用户ID（用于Jellyfin/Emby）
    
    enabled = Column(Boolean, default=True, index=True)  # 是否启用
    sync_enabled = Column(Boolean, default=True)  # 是否启用同步
    sync_interval = Column(Integer, default=3600)  # 同步间隔（秒）
    last_sync = Column(DateTime, nullable=True)  # 最后同步时间
    next_sync = Column(DateTime, nullable=True)  # 下次同步时间
    
    # 状态信息
    status = Column(String(50), default="unknown")  # 状态: online, offline, error
    last_check = Column(DateTime, nullable=True)  # 最后检查时间
    error_message = Column(Text, nullable=True)  # 错误信息
    
    # 配置信息
    libraries = Column(JSON, nullable=True)  # 媒体库列表
    sync_watched_status = Column(Boolean, default=True)  # 同步观看状态
    sync_playback_status = Column(Boolean, default=True)  # 同步播放状态
    sync_metadata = Column(Boolean, default=True)  # 同步元数据
    
    # 统计信息
    total_movies = Column(Integer, default=0)  # 电影总数
    total_tv_shows = Column(Integer, default=0)  # 电视剧总数
    total_episodes = Column(Integer, default=0)  # 剧集总数
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_media_server_type_enabled', 'server_type', 'enabled'),
    )


class MediaServerSyncHistory(Base):
    """媒体服务器同步历史"""
    __tablename__ = "media_server_sync_history"
    
    id = Column(Integer, primary_key=True, index=True)
    media_server_id = Column(Integer, nullable=False, index=True)  # 媒体服务器ID
    sync_type = Column(String(50), nullable=False)  # 同步类型: metadata, watched_status, playback_status, libraries
    status = Column(String(50), nullable=False)  # 状态: success, failed, partial
    items_synced = Column(Integer, default=0)  # 同步的项目数
    items_failed = Column(Integer, default=0)  # 失败的项目数
    duration = Column(Float, nullable=True)  # 同步耗时（秒）
    error_message = Column(Text, nullable=True)  # 错误信息
    started_at = Column(DateTime, default=datetime.utcnow, index=True)  # 开始时间
    completed_at = Column(DateTime, nullable=True)  # 完成时间
    
    __table_args__ = (
        Index('idx_media_server_sync_server_ts', 'media_server_id', 'started_at'),
    )


class MediaServerItem(Base):
    """媒体服务器媒体项"""
    __tablename__ = "media_server_items"
    
    id = Column(Integer, primary_key=True, index=True)
    media_server_id = Column(Integer, nullable=False, index=True)  # 媒体服务器ID
    server_item_id = Column(String(255), nullable=False, index=True)  # 服务器中的项目ID
    media_type = Column(String(50), nullable=False, index=True)  # 媒体类型: movie, tv_show, episode
    title = Column(String(500), nullable=False)  # 标题
    year = Column(Integer, nullable=True)  # 年份
    tmdb_id = Column(Integer, nullable=True, index=True)  # TMDB ID
    imdb_id = Column(String(50), nullable=True, index=True)  # IMDB ID
    
    # 观看状态
    watched = Column(Boolean, default=False)  # 是否已观看
    watched_at = Column(DateTime, nullable=True)  # 观看时间
    play_count = Column(Integer, default=0)  # 播放次数
    play_percentage = Column(Float, default=0.0)  # 播放进度（百分比）
    last_played = Column(DateTime, nullable=True)  # 最后播放时间
    
    # 元数据
    poster_url = Column(String(500), nullable=True)  # 海报URL
    backdrop_url = Column(String(500), nullable=True)  # 背景图URL
    overview = Column(Text, nullable=True)  # 简介
    rating = Column(Float, nullable=True)  # 评分
    genres = Column(JSON, nullable=True)  # 类型列表
    
    # 同步信息
    last_synced = Column(DateTime, nullable=True)  # 最后同步时间
    sync_status = Column(String(50), default="pending")  # 同步状态: pending, synced, error
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_media_server_item_server_type', 'media_server_id', 'media_type'),
        Index('idx_media_server_item_tmdb', 'tmdb_id'),
        Index('idx_media_server_item_imdb', 'imdb_id'),
    )


class MediaServerPlaybackSession(Base):
    """媒体服务器播放会话"""
    __tablename__ = "media_server_playback_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    media_server_id = Column(Integer, nullable=False, index=True)  # 媒体服务器ID
    item_id = Column(Integer, nullable=False, index=True)  # 媒体项ID
    session_id = Column(String(255), nullable=False, index=True)  # 会话ID
    user_id = Column(String(255), nullable=True)  # 用户ID
    user_name = Column(String(255), nullable=True)  # 用户名
    
    # 播放信息
    is_paused = Column(Boolean, default=False)  # 是否暂停
    is_playing = Column(Boolean, default=False)  # 是否正在播放
    position_ticks = Column(Integer, default=0)  # 播放位置（刻度）
    play_percentage = Column(Float, default=0.0)  # 播放进度（百分比）
    
    # 客户端信息
    client_name = Column(String(255), nullable=True)  # 客户端名称
    device_name = Column(String(255), nullable=True)  # 设备名称
    device_type = Column(String(50), nullable=True)  # 设备类型
    
    started_at = Column(DateTime, default=datetime.utcnow, index=True)  # 开始时间
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 更新时间
    
    __table_args__ = (
        Index('idx_media_server_playback_server_ts', 'media_server_id', 'started_at'),
    )

