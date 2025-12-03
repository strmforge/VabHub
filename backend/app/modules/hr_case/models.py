"""
HR案件系统统一模型
整合HR状态和生命周期信息，提供统一的数据访问接口
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field
from sqlalchemy import (
    Column, Integer, String, DateTime, Float, Boolean, Text, JSON,
    Index, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from app.core.database import Base


class HrCaseStatus(str, Enum):
    """HR案件状态"""
    NONE = "none"
    ACTIVE = "active"
    SAFE = "safe"
    VIOLATED = "violated"
    UNKNOWN = "unknown"


class HrCaseLifeStatus(str, Enum):
    """HR案件生命周期状态"""
    ALIVE = "alive"
    DELETED = "deleted"


# SQLAlchemy ORM模型
class HrCase(Base):
    """HR案件数据库模型"""
    
    __tablename__ = "hr_cases"
    
    # 主键和基础标识
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, nullable=False, index=True)  # 关联sites表
    site_key = Column(String(50), nullable=False, index=True)  # 站点标识，如 "hdhome"
    torrent_id = Column(String(255), nullable=False, index=True)
    infohash = Column(String(64), nullable=True, index=True)  # 可选，用于匹配本地任务
    
    # 状态枚举
    status = Column(String(20), nullable=False, default=HrCaseStatus.NONE, index=True)
    life_status = Column(String(20), nullable=False, default=HrCaseLifeStatus.ALIVE, index=True)
    
    # HR要求与进度
    requirement_ratio = Column(Float, nullable=True)
    requirement_hours = Column(Float, nullable=True)
    seeded_hours = Column(Float, nullable=False, default=0.0)
    current_ratio = Column(Float, nullable=True)
    
    # 时间线
    entered_at = Column(DateTime, nullable=True, index=True)  # 进入HR时间
    deadline = Column(DateTime, nullable=True, index=True)  # HR截止时间
    first_seen_at = Column(DateTime, nullable=True, index=True)  # 首次发现时间
    last_seen_at = Column(DateTime, nullable=True, index=True)  # 最后更新时间
    penalized_at = Column(DateTime, nullable=True, index=True)  # 被处罚时间
    deleted_at = Column(DateTime, nullable=True, index=True)  # 种子被删除时间
    resolved_at = Column(DateTime, nullable=True, index=True)  # 最终解决时间
    
    # 元数据和扩展
    last_email_notice_at = Column(DateTime, nullable=True)  # 最后邮件通知时间
    raw_data = Column(JSON, nullable=True)  # 原始站点数据
    notes = Column(Text, nullable=True)  # 备注信息
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 移除relationship定义以避免循环导入，只保留外键
    # site = relationship("Site", back_populates="hr_cases")
    
    # 复合索引优化查询性能
    __table_args__ = (
        Index('idx_site_torrent', 'site_key', 'torrent_id', unique=True),
        Index('idx_status_deadline', 'status', 'deadline'),
        Index('idx_site_status', 'site_key', 'status'),
        Index('idx_active_hr', 'site_key', 'status', 'life_status'),
        {'extend_existing': True}  # 解决表重复定义问题
    )
    
    def __repr__(self) -> str:
        return f"<HrCase(id={self.id}, site={self.site_key}, torrent={self.torrent_id[:8]}..., status={self.status})>"
    
    @property
    def is_active_hr(self) -> bool:
        """是否为活跃HR状态"""
        return self.status == HrCaseStatus.ACTIVE and self.life_status == HrCaseLifeStatus.ALIVE
    
    @property
    def is_safe(self) -> bool:
        """是否为安全状态（可删除/移动）"""
        return self.status in [HrCaseStatus.SAFE, HrCaseStatus.NONE, HrCaseStatus.UNKNOWN]
    
    @property
    def hours_remaining(self) -> Optional[float]:
        """HR剩余小时数"""
        if not self.deadline:
            return None
        now = datetime.utcnow()
        if self.deadline <= now:
            return 0.0
        delta = self.deadline - now
        return delta.total_seconds() / 3600.0
    
    @property
    def progress_percentage(self) -> Optional[float]:
        """HR进度百分比"""
        if not self.requirement_hours or self.requirement_hours <= 0:
            return None
        return min(100.0, (self.seeded_hours / self.requirement_hours) * 100.0)


# Pydantic模型用于API
class HrCaseBase(BaseModel):
    """HR案件基础模型"""
    site_id: int
    site_key: str
    torrent_id: str
    infohash: Optional[str] = None
    status: HrCaseStatus = HrCaseStatus.NONE
    life_status: HrCaseLifeStatus = HrCaseLifeStatus.ALIVE
    requirement_ratio: Optional[float] = None
    requirement_hours: Optional[float] = None
    seeded_hours: float = 0.0
    current_ratio: Optional[float] = None
    entered_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    penalized_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    last_email_notice_at: Optional[datetime] = None
    raw_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class HrCaseCreate(HrCaseBase):
    """创建HR案件模型"""
    pass


class HrCaseUpdate(BaseModel):
    """更新HR案件模型"""
    status: Optional[HrCaseStatus] = None
    life_status: Optional[HrCaseLifeStatus] = None
    requirement_ratio: Optional[float] = None
    requirement_hours: Optional[float] = None
    seeded_hours: Optional[float] = None
    current_ratio: Optional[float] = None
    entered_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    penalized_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    last_email_notice_at: Optional[datetime] = None
    raw_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class HrCaseInDB(HrCaseBase):
    """数据库中的HR案件模型"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    is_active_hr: bool = Field(False, description="是否为活跃HR状态")
    is_safe: bool = Field(True, description="是否为安全状态")
    hours_remaining: Optional[float] = Field(None, description="HR剩余小时数")
    progress_percentage: Optional[float] = Field(None, description="HR进度百分比")
    
    class Config:
        from_attributes = True


class HrCaseResponse(HrCaseInDB):
    """HR案件响应模型"""
    pass


class HrCaseListResponse(BaseModel):
    """HR案件列表响应"""
    items: List[HrCaseResponse]
    total: int
    page: int
    size: int
    pages: int


class HrCaseStatistics(BaseModel):
    """HR案件统计信息"""
    total_cases: int = 0
    active_hr_cases: int = 0
    safe_cases: int = 0
    violated_cases: int = 0
    deleted_cases: int = 0
    site_breakdown: Dict[str, int] = Field(default_factory=dict)
    urgency_breakdown: Dict[str, int] = Field(default_factory=dict)  # urgent/soon/normal


# 转换函数移至repository模块以避免循环导入
