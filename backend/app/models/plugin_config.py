"""
插件配置模型
PLUGIN-UX-3 实现

存储每个插件的运行时配置数据
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, JSON, Index
from sqlalchemy.sql import func

from app.core.database import Base


class PluginConfig(Base):
    """
    插件配置表
    
    存储每个插件的配置数据。
    配置的 schema 定义在 plugin.json 的 config_schema 字段中。
    """
    __tablename__ = "plugin_configs"
    
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    
    # 插件 ID（关联 Plugin.name）
    plugin_id: str = Column(String(255), nullable=False, index=True, unique=True)
    
    # 配置数据（JSON）
    config: dict = Column(JSON, nullable=False, default=dict)
    
    # 时间戳
    created_at: datetime = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at: datetime = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<PluginConfig {self.plugin_id}>"
