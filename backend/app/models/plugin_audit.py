"""
插件审计日志模型
PLUGIN-SAFETY-1 实现

记录插件的关键操作，用于安全审计和问题排查
"""

from datetime import datetime
from typing import Optional, Any

from sqlalchemy import Column, Integer, String, DateTime, Index, JSON
from sqlalchemy.sql import func

from app.core.database import Base


class PluginAuditLog(Base):
    """
    插件审计日志
    
    记录插件的关键操作，如下载任务、媒体访问、云存储操作等。
    这些日志不需要永久保存，会定期清理。
    """
    __tablename__ = "plugin_audit_logs"
    
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    
    # 插件 ID（关联到 Plugin.name）
    plugin_id: str = Column(String(255), nullable=False, index=True)
    
    # 操作类型（如 "download.add_task", "media.read", "cloud115.task"）
    action: str = Column(String(100), nullable=False, index=True)
    
    # 操作参数（JSON 格式，记录关键信息）
    # 注意：不记录敏感信息如密码、token 等
    payload: Optional[dict[str, Any]] = Column(JSON, nullable=True)
    
    # 创建时间（带索引便于清理）
    created_at: datetime = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # ============== 索引优化 ==============
    # 复合索引：按插件和操作类型查询
    __table_args__ = (
        Index('idx_plugin_action', 'plugin_id', 'action'),
        Index('idx_created_cleanup', 'created_at'),  # 用于清理旧记录
    )
    
    def __repr__(self) -> str:
        return f"<PluginAuditLog {self.plugin_id}:{self.action} at {self.created_at}>"
