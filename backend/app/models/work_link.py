"""
作品关联模型（Work Link）

用于记录用户手动标记的作品关联关系。
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, func
from datetime import datetime
from app.core.database import Base


class WorkLink(Base):
    """
    作品关联模型
    
    记录用户手动标记的 ebook 与其他媒体类型（video/comic/music）的关联关系。
    """
    __tablename__ = "work_links"
    
    id = Column(Integer, primary_key=True, index=True)
    ebook_id = Column(Integer, ForeignKey("ebooks.id", ondelete="CASCADE"), nullable=False, index=True)
    target_type = Column(String(32), nullable=False, index=True)  # "video" | "comic" | "music"
    target_id = Column(Integer, nullable=False, index=True)  # 对应 Media/Comic/Music 的 id
    relation = Column(String(16), nullable=False, index=True)  # "include" | "exclude"
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, index=True)
    
    # 唯一约束：同一个 ebook/target_type/target_id 只应有一条记录
    __table_args__ = (
        UniqueConstraint("ebook_id", "target_type", "target_id", name="uq_work_link_ebook_target"),
    )

