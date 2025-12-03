"""
RSSHub数据模型
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, Table, and_
from sqlalchemy.orm import relationship, foreign
from sqlalchemy.sql import func
from datetime import datetime

from app.core.database import Base


# 组合订阅与源的关联表
rsshub_composite_source = Table(
    'rsshub_composite_source',
    Base.metadata,
    Column('composite_id', String, ForeignKey('rsshub_composite.id', ondelete='CASCADE'), primary_key=True),
    Column('source_id', String, ForeignKey('rsshub_source.id', ondelete='CASCADE'), primary_key=True)
)


class RSSHubSource(Base):
    """RSSHub源表"""
    __tablename__ = 'rsshub_source'
    
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
    
    # 关系
    composite_sources = relationship(
        'RSSHubComposite',
        secondary=rsshub_composite_source,
        back_populates='sources'
    )
    # 简化关系配置，避免复杂的多态关系
    # user_subscriptions = relationship(
    #     'UserRSSHubSubscription',
    #     primaryjoin="RSSHubSource.id == UserRSSHubSubscription.target_id",
    #     foreign_keys="[UserRSSHubSubscription.target_id]",
    #     back_populates='source'
    # )


class RSSHubComposite(Base):
    """RSSHub组合订阅表"""
    __tablename__ = 'rsshub_composite'
    
    id = Column(String, primary_key=True, comment='组合ID')
    name = Column(String, nullable=False, comment='组合名称')
    type = Column(String, nullable=False, comment='类型: video/tv/variety/anime/music/mixed')
    description = Column(Text, comment='描述')
    default_enabled = Column(Boolean, default=False, nullable=False, comment='默认是否启用')
    created_at = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment='更新时间')
    
    # 关系
    sources = relationship(
        'RSSHubSource',
        secondary=rsshub_composite_source,
        back_populates='composite_sources'
    )
    # 简化关系配置，避免复杂的多态关系
    # user_subscriptions = relationship(
    #     'UserRSSHubSubscription',
    #     primaryjoin="RSSHubComposite.id == UserRSSHubSubscription.target_id",
    #     foreign_keys="[UserRSSHubSubscription.target_id]",
    #     back_populates='composite'
    # )


class UserRSSHubSubscription(Base):
    """用户RSSHub订阅状态表"""
    __tablename__ = 'user_rsshub_subscription'
    
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
    
    # 关系
    user = relationship('User', backref='rsshub_subscriptions')
    # 简化关系配置，避免复杂的多态关系
    # source = relationship(
    #     'RSSHubSource',
    #     primaryjoin='and_(UserRSSHubSubscription.target_id == RSSHubSource.id, '
    #                 'UserRSSHubSubscription.target_type == "source")',
    #     back_populates='user_subscriptions',
    #     overlaps="composite,user_subscriptions",
    # )
    # composite = relationship(
    #     'RSSHubComposite',
    #     primaryjoin='and_(UserRSSHubSubscription.target_id == RSSHubComposite.id, '
    #                 'UserRSSHubSubscription.target_type == "composite")',
    #     back_populates='user_subscriptions',
    #     overlaps="source,user_subscriptions",
    # )

