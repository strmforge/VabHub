"""
过滤规则组模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Index
from datetime import datetime
from app.core.database import Base


class FilterRuleGroup(Base):
    """过滤规则组模型"""
    __tablename__ = "filter_rule_groups"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # null表示系统级规则组
    name = Column(String(255), nullable=False)  # 规则组名称
    description = Column(Text, nullable=True)  # 描述
    
    # 配置字段
    media_types = Column(JSON, nullable=False, default=["movie", "tv"])  # 适用媒体类型
    priority = Column(Integer, default=100)  # 优先级（数字越小越先应用）
    rules = Column(JSON, nullable=False)  # 规则配置
    enabled = Column(Boolean, default=True)  # 是否启用
    
    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # 索引
    __table_args__ = (
        Index('idx_filter_rule_group_user', 'user_id'),
        Index('idx_filter_rule_group_enabled', 'enabled'),
        Index('idx_filter_rule_group_priority', 'priority'),
    )
    
    def __repr__(self):
        return f"<FilterRuleGroup(id={self.id}, name='{self.name}', user_id={self.user_id})>"
    
    @property
    def is_system(self) -> bool:
        """是否为系统级规则组"""
        return self.user_id is None
    
    @property
    def rule_count(self) -> int:
        """规则数量"""
        if not self.rules or not isinstance(self.rules, dict):
            return 0
        return len(self.rules.get("rules", []))
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "media_types": self.media_types,
            "priority": self.priority,
            "rules": self.rules,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "is_system": self.is_system,
            "rule_count": self.rule_count,
        }
