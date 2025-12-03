"""
简化的RSSHub数据模型（避免复杂的多态关系）
使用临时表名避免与现有表冲突
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, Table
from sqlalchemy.sql import func
from datetime import datetime

from app.core.database import Base


# 组合订阅与源的关联表（临时表名）
rsshub_composite_source_temp = Table(
    'rsshub_composite_source_temp',
    Base.metadata,
    Column('composite_id', String, ForeignKey('rsshub_composite_temp.id', ondelete='CASCADE'), primary_key=True),
    Column('source_id', String, ForeignKey('rsshub_source_temp.id', ondelete='CASCADE'), primary_key=True)
)


class RSSHubSource(Base):
    """RSSHub源表（简化版本，临时表名）"""
    __tablename__ = 'rsshub_source_temp'
    
    id = Column(String, primary_key=True, comment='源ID')
    name = Column(String, nullable=False, comment='源名称')
    url_path = Column(String, nullable=False, comment='RSSHub URL路径')
    type = Column(String, nullable=False, comment='类型: video/tv/variety/anime/music/mixed')
    group = Column(String, nullable=False, comment='分组: rank/update')
    description = Column(Text, comment='描述')
    is_template = Column(Boolean, default=False, nullable=False, comment='是否为模板')
    default_enabled = Column(Boolean, default=False, nullable=False, comment='默认是否启用')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment='更新时间')


class RSSHubComposite(Base):
    """RSSHub组合订阅表（简化版本，临时表名）"""
    __tablename__ = 'rsshub_composite_temp'
    
    id = Column(String, primary_key=True, comment='组合ID')
    name = Column(String, nullable=False, comment='组合名称')
    type = Column(String, nullable=False, comment='类型: video/tv/variety/anime/music/mixed')
    description = Column(Text, comment='描述')
    default_enabled = Column(Boolean, default=False, nullable=False, comment='默认是否启用')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment='更新时间')


class UserRSSHubSubscription(Base):
    """用户RSSHub订阅状态表（简化版本，临时表名）"""
    __tablename__ = 'user_rsshub_subscription_temp'
    
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True, comment='用户ID')
    target_id = Column(String, primary_key=True, comment='目标ID（source_id或composite_id）')
    target_type = Column(String, nullable=False, comment='目标类型: source/composite')
    enabled = Column(Boolean, default=True, nullable=False, comment='是否启用')
    last_checked_at = Column(DateTime, comment='最后检查时间')
    last_item_hash = Column(String, comment='最后一项的哈希值（用于增量更新）')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment='更新时间')
    last_error_code = Column(String(64), nullable=True, comment='最后一次错误编码')
    last_error_message = Column(Text, nullable=True, comment='最后一次错误信息')
    last_error_at = Column(DateTime, nullable=True, comment='最后一次错误时间')