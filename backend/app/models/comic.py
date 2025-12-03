"""
漫画相关模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Float, ForeignKey, Index
from datetime import datetime
from app.core.database import Base


class Comic(Base):
    """
    漫画作品模型（Work-level Entity）
    
    表示一个漫画作品（work），是逻辑上的"作品层实体"。
    
    语义说明：
    - Comic 代表"漫画作品 + 某个卷（volume）"，而不是单个文件
    - 同一部作品（相同 title+author+series+volume_index）只对应一个 Comic 记录
    - 同一部作品可以有多个文件版本（不同格式、不同来源），都通过 ComicFile 关联到同一个 Comic
    
    去重规则：
    - 使用规范化后的 (title, author, series, volume_index) 组合进行匹配
    - 匹配逻辑由 ComicWorkResolver 负责，确保同一作品不会重复创建 Comic 记录
    """
    __tablename__ = "comics"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)  # 作品名（必填）
    original_title = Column(String(255), nullable=True)  # 原名（可选）
    author = Column(String(255), nullable=True, index=True)  # 作者/原作（可选）
    illustrator = Column(String(255), nullable=True)  # 漫画家/作画（可选）
    series = Column(String(255), nullable=True, index=True)  # 系列名（可选）
    volume_index = Column(Integer, nullable=True)  # 卷号/话数（可选，整数）
    language = Column(String(20), nullable=True, default="zh-CN")  # 语言代码，如 "zh-CN", "en", "ja"
    region = Column(String(10), nullable=True, index=True)  # 地区（如 "CN", "JP", "US", "KR"）
    publish_year = Column(Integer, nullable=True)  # 出版年份（可选）
    tags = Column(Text, nullable=True)  # 标签（JSON 字符串或逗号分隔）
    description = Column(Text, nullable=True)  # 简介
    cover_url = Column(String(500), nullable=True)  # 封面图片 URL
    extra_metadata = Column(JSON, nullable=True)  # 附加元数据（JSON）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 创建索引以支持常见查询
    __table_args__ = (
        Index("ix_comics_author_title", "author", "title"),
        Index("ix_comics_series_volume", "series", "volume_index"),
    )


class ComicFile(Base):
    """
    漫画文件模型
    
    表示漫画的一个具体文件（CBZ、CBR、ZIP、RAR 等）
    """
    __tablename__ = "comic_files"
    
    id = Column(Integer, primary_key=True, index=True)
    comic_id = Column(Integer, ForeignKey("comics.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(1000), nullable=False, unique=True, index=True)  # 文件路径（绝对或相对）
    file_size_bytes = Column(Integer, nullable=True)  # 文件大小（字节）
    file_size_mb = Column(Float, nullable=True)  # 文件大小（MB，计算字段）
    format = Column(String(20), nullable=False, index=True)  # 文件格式：cbz, cbr, zip, rar 等
    page_count = Column(Integer, nullable=True)  # 页数（可选，先留字段，暂时可以不填）
    source_site_id = Column(String(100), nullable=True, index=True)  # 来源站点 ID
    source_torrent_id = Column(String(100), nullable=True)  # 来源种子 ID
    download_task_id = Column(Integer, nullable=True, index=True)  # 关联的下载任务 ID（如果有）
    is_deleted = Column(Boolean, default=False, index=True)  # 是否已删除
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 自动计算 file_size_mb
        if self.file_size_bytes and not self.file_size_mb:
            self.file_size_mb = round(self.file_size_bytes / (1024 ** 2), 2)

