"""
字幕模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from datetime import datetime
from app.core.database import Base


class Subtitle(Base):
    """字幕模型"""
    __tablename__ = "subtitles"
    
    id = Column(Integer, primary_key=True, index=True)
    media_file_path = Column(String(500), nullable=False, index=True)  # 关联的媒体文件路径
    media_type = Column(String(20), nullable=False)  # 媒体类型：movie, tv
    media_title = Column(String(255), nullable=False)  # 媒体标题
    media_year = Column(Integer, nullable=True)  # 媒体年份
    season = Column(Integer, nullable=True)  # 季数（电视剧）
    episode = Column(Integer, nullable=True)  # 集数（电视剧）
    
    # 字幕信息
    subtitle_path = Column(String(500), nullable=False)  # 字幕文件路径
    language = Column(String(50), nullable=False, default="zh")  # 语言：zh, en等
    language_code = Column(String(10), nullable=False, default="chi")  # 语言代码：chi, eng等
    format = Column(String(10), nullable=False)  # 格式：srt, ass, vtt等
    source = Column(String(50), nullable=False)  # 来源：opensubtitles, subhd等
    source_id = Column(String(100), nullable=True)  # 来源ID
    
    # 字幕元数据
    download_url = Column(String(500), nullable=True)  # 下载URL
    file_size = Column(Integer, nullable=True)  # 文件大小（字节）
    rating = Column(Integer, nullable=True)  # 评分（1-5）
    downloads = Column(Integer, nullable=True)  # 下载次数
    
    # 状态信息
    is_embedded = Column(Boolean, default=False)  # 是否内嵌字幕
    is_external = Column(Boolean, default=True)  # 是否外挂字幕
    is_forced = Column(Boolean, default=False)  # 是否强制字幕
    is_hearing_impaired = Column(Boolean, default=False)  # 是否听力 impaired
    
    # 时间信息
    downloaded_at = Column(DateTime, default=datetime.utcnow)  # 下载时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SubtitleDownloadHistory(Base):
    """字幕下载历史记录"""
    __tablename__ = "subtitle_download_history"
    
    id = Column(Integer, primary_key=True, index=True)
    media_file_path = Column(String(500), nullable=False, index=True)  # 关联的媒体文件路径
    subtitle_id = Column(Integer, ForeignKey("subtitles.id"), nullable=True)  # 关联的字幕ID
    source = Column(String(50), nullable=False)  # 来源
    language = Column(String(50), nullable=False)  # 语言
    success = Column(Boolean, default=False)  # 是否成功
    error_message = Column(Text, nullable=True)  # 错误消息
    downloaded_at = Column(DateTime, default=datetime.utcnow)  # 下载时间

