"""
用户模型
LAUNCH-1 L3-1 增强：添加 role 字段
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"  # 只读用户


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role = Column(String(20), default=UserRole.USER.value, nullable=False)  # 用户角色
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    manga_download_jobs = relationship("MangaDownloadJob", back_populates="user")
    
    @property
    def is_admin(self) -> bool:
        """是否是管理员"""
        return self.is_superuser or self.role == UserRole.ADMIN.value
    
    @property
    def is_viewer_only(self) -> bool:
        """是否只读用户"""
        return self.role == UserRole.VIEWER.value
    
    @classmethod
    async def get_by_username(cls, db: AsyncSession, username: str) -> Optional["User"]:
        """根据用户名获取用户"""
        from sqlalchemy import select
        result = await db.execute(select(cls).where(cls.username == username))
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_by_email(cls, db: AsyncSession, email: str) -> Optional["User"]:
        """根据邮箱获取用户"""
        from sqlalchemy import select
        result = await db.execute(select(cls).where(cls.email == email))
        return result.scalar_one_or_none()
    
    async def save(self, db: AsyncSession):
        """保存用户"""
        db.add(self)
        await db.commit()
        await db.refresh(self)

