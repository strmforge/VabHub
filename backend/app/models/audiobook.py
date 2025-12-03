"""
有声书相关模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, Index
from datetime import datetime
from app.core.database import Base


class AudiobookFile(Base):
    """
    有声书文件模型
    
    表示一个有声书文件（MP3、M4B、FLAC 等），关联到 EBook 作品。
    
    语义说明：
    - AudiobookFile 代表同一作品的音频载体，通过 ebook_id 关联到 EBook
    - 同一作品（EBook）可以有多个 AudiobookFile（不同格式、不同来源、不同朗读者）
    - 与 EBookFile 类似，都是作品的载体，只是格式不同
    """
    __tablename__ = "audiobook_files"
    
    id = Column(Integer, primary_key=True, index=True)
    ebook_id = Column(Integer, ForeignKey("ebooks.id", ondelete="CASCADE"), nullable=False, index=True)  # 关联到作品
    file_path = Column(String(1000), nullable=False, unique=True, index=True)  # 文件路径（绝对或相对）
    file_size_bytes = Column(Integer, nullable=True)  # 文件大小（字节）
    file_size_mb = Column(Float, nullable=True)  # 文件大小（MB，计算字段）
    format = Column(String(20), nullable=False, index=True)  # 文件格式：mp3, m4b, m4a, flac, ogg, opus, aac 等
    duration_seconds = Column(Integer, nullable=True)  # 时长（秒）
    bitrate_kbps = Column(Integer, nullable=True)  # 比特率（kbps）
    channels = Column(Integer, nullable=True)  # 声道数（1=单声道, 2=立体声）
    sample_rate_hz = Column(Integer, nullable=True)  # 采样率（Hz）
    narrator = Column(String(255), nullable=True, index=True)  # 朗读者/旁白
    language = Column(String(20), nullable=True)  # 语言代码，如 "zh-CN", "en"
    source_site_id = Column(String(100), nullable=True, index=True)  # 来源站点 ID
    source_torrent_id = Column(String(100), nullable=True)  # 来源种子 ID
    download_task_id = Column(Integer, nullable=True, index=True)  # 关联的下载任务 ID（如果有）
    is_deleted = Column(Boolean, default=False, index=True)  # 是否已删除
    is_tts_generated = Column(Boolean, nullable=False, default=False, index=True)  # 是否由 TTS 自动生成
    tts_provider = Column(String(50), nullable=True)  # TTS 提供商（dummy/http/edge_tts 等）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 注意：所有需要索引的字段已在 Column 定义时设置了 index=True
    # 不需要在 __table_args__ 中重复定义
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 自动计算 file_size_mb
        if self.file_size_bytes and not self.file_size_mb:
            self.file_size_mb = round(self.file_size_bytes / (1024 ** 2), 2)

