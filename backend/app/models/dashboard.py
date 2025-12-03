"""
仪表盘布局模型
支持可拖拽布局和个性化配置
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from datetime import datetime
from app.core.database import Base


class DashboardLayout(Base):
    """仪表盘布局模型"""
    __tablename__ = "dashboard_layouts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)  # 用户ID（单用户系统可为空）
    name = Column(String(100), nullable=False)  # 布局名称
    description = Column(Text, nullable=True)  # 布局描述
    breakpoint = Column(String(20), default="lg")  # 布局断点（xs, sm, md, lg, xl）
    cols = Column(Integer, default=12)  # 网格列数
    row_height = Column(Integer, default=30)  # 行高
    margin = Column(JSON, nullable=True)  # 边距 [x, y]
    layouts = Column(JSON, nullable=True)  # 不同断点的布局配置
    widgets = Column(JSON, nullable=True)  # 组件列表
    is_default = Column(Boolean, default=False)  # 是否为默认布局
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DashboardWidget(Base):
    """仪表盘组件模型"""
    __tablename__ = "dashboard_widgets"
    
    id = Column(Integer, primary_key=True, index=True)
    widget_id = Column(String(100), unique=True, nullable=False, index=True)  # 组件ID
    name = Column(String(100), nullable=False)  # 组件名称
    type = Column(String(50), nullable=False)  # 组件类型（chart, stats, list, alert, custom）
    description = Column(Text, nullable=True)  # 组件描述
    component = Column(String(100), nullable=False)  # Vue组件名称
    config = Column(JSON, nullable=True)  # 组件配置
    enabled = Column(Boolean, default=True)  # 是否启用
    configurable = Column(Boolean, default=True)  # 是否可配置
    refresh_interval = Column(Integer, default=30)  # 刷新间隔（秒）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

