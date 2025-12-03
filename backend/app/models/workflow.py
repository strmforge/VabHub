"""
工作流模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from datetime import datetime
from app.core.database import Base


class Workflow(Base):
    """工作流模型"""
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    trigger_event = Column(String(100), nullable=False)
    conditions = Column(Text, nullable=True)  # JSON字符串
    actions = Column(Text, nullable=False)  # JSON字符串
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WorkflowExecution(Base):
    """工作流执行记录"""
    __tablename__ = "workflow_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, nullable=False)
    status = Column(String(20), default="running")  # running, completed, failed
    result = Column(Text, nullable=True)  # JSON字符串
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

