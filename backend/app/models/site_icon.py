"""
站点图标模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from datetime import datetime
from app.core.database import Base


class SiteIcon(Base):
    """站点图标模型"""
    __tablename__ = "site_icons"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="站点名称")
    domain = Column(String(255), nullable=False, index=True, comment="域名Key（用于匹配）")
    url = Column(String(500), nullable=True, comment="图标URL地址")
    base64 = Column(Text, nullable=True, comment="图标Base64编码（用于缓存）")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 添加唯一索引
    __table_args__ = (
        Index('idx_site_icon_domain', 'domain', unique=True),
    )

