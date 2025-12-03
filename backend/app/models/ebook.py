"""
电子书相关模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Float, ForeignKey, Index
from datetime import datetime
from app.core.database import Base


class EBook(Base):
    """
    电子书作品模型（Work-level Entity）
    
    表示一个书籍作品（work），是逻辑上的"作品层实体"。
    
    语义说明：
    - EBook 代表"书籍作品 + 某个卷（volume）"，而不是单个文件
    - 同一部作品（相同 ISBN 或相同 title+author+series+volume）只对应一个 EBook 记录
    - 同一部作品可以有多个文件版本（不同格式、不同来源），都通过 EBookFile 关联到同一个 EBook
    - 未来扩展：有声书（Audiobook）等也可以通过共享 EBook.id 作为作品 ID 进行关联
    
    去重规则：
    - 优先使用 ISBN 作为唯一标识（如果存在）
    - 无 ISBN 时，使用规范化后的 (title, author, series, volume_index) 组合进行匹配
    - 匹配逻辑由 EBookWorkResolver 负责，确保同一作品不会重复创建 EBook 记录
    """
    __tablename__ = "ebooks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    original_title = Column(String(255), nullable=True)
    author = Column(String(255), nullable=True, index=True)
    series = Column(String(255), nullable=True, index=True)  # 系列名
    volume_index = Column(String(50), nullable=True)  # 卷号/集数（可能是 "1", "Vol.1", "第1卷" 等）
    language = Column(String(20), nullable=True, default="zh-CN")  # 语言代码，如 "zh-CN", "en"
    publish_year = Column(Integer, nullable=True)  # 出版年份
    isbn = Column(String(20), nullable=True, index=True)  # ISBN（逻辑上唯一，同一 ISBN 只对应一个 EBook）
    tags = Column(Text, nullable=True)  # 标签（JSON 字符串或逗号分隔）
    description = Column(Text, nullable=True)  # 简介
    cover_url = Column(String(500), nullable=True)  # 封面图片 URL
    extra_metadata = Column(JSON, nullable=True)  # 附加元数据（JSON）
    # extra_metadata 可以包含以下结构：
    # {
    #   "novel_source": {
    #     "type": "local_txt",
    #     "archived_txt_path": "./data/novel_uploads/source_txt/xxx_safe_name.txt",
    #     "original_txt_path": "/data/inbox/xxx.txt",  # 可选
    #     "imported_at": "2025-11-22T03:00:00Z"
    #   }
    # }
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 创建索引以支持常见查询
    __table_args__ = (
        Index("ix_ebooks_author_title", "author", "title"),
        Index("ix_ebooks_series_volume", "series", "volume_index"),
    )


class EBookFile(Base):
    """
    电子书文件模型
    
    表示电子书的一个具体文件（EPUB、PDF、MOBI 等）
    """
    __tablename__ = "ebook_files"
    
    id = Column(Integer, primary_key=True, index=True)
    ebook_id = Column(Integer, ForeignKey("ebooks.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(1000), nullable=False, unique=True, index=True)  # 文件路径（绝对或相对）
    file_size_bytes = Column(Integer, nullable=True)  # 文件大小（字节）
    file_size_mb = Column(Float, nullable=True)  # 文件大小（MB，计算字段）
    format = Column(String(20), nullable=False, index=True)  # 文件格式：epub, mobi, azw3, pdf, txt 等
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

