"""
漫画源模型
"""
from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    JSON,
    Enum as SAEnum,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums.manga_source_type import MangaSourceType


class MangaSource(Base):
    """漫画源配置"""
    __tablename__ = "manga_sources"

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False, comment="用户自定义名称")
    type = Column(SAEnum(MangaSourceType), nullable=False, comment="源类型枚举")
    base_url = Column(String(512), nullable=False, comment="源服务基础地址")

    api_key = Column(String(512), nullable=True, comment="Token / API Key")
    username = Column(String(128), nullable=True, comment="某些源需要的用户名")
    password = Column(String(256), nullable=True, comment="密码（Phase 1 先明文存）")

    is_enabled = Column(Boolean, default=True, nullable=False, comment="是否启用")

    # 每种类型特有配置（比如 OPDS 路径前缀、默认库 ID 等）
    extra_config = Column(JSON, nullable=True, comment="额外配置（JSON）")

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # 关联关系
    download_jobs = relationship("MangaDownloadJob", back_populates="source")

