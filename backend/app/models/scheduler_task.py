"""
调度器任务模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text, Float, Index
from datetime import datetime
from app.core.database import Base


class SchedulerTask(Base):
    """调度器任务模型"""
    __tablename__ = "scheduler_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(255), nullable=False, unique=True, index=True)  # 任务ID
    name = Column(String(255), nullable=False)  # 任务名称
    task_type = Column(String(50), nullable=False, index=True)  # 任务类型
    status = Column(String(50), default="pending", index=True)  # 状态: pending, running, completed, failed, disabled
    trigger_type = Column(String(50), nullable=False)  # 触发器类型: interval, cron, date
    trigger_config = Column(JSON, nullable=True)  # 触发器配置
    next_run_time = Column(DateTime, nullable=True, index=True)  # 下次运行时间
    last_run_time = Column(DateTime, nullable=True, index=True)  # 最后运行时间
    run_count = Column(Integer, default=0)  # 运行次数
    success_count = Column(Integer, default=0)  # 成功次数
    fail_count = Column(Integer, default=0)  # 失败次数
    enabled = Column(Boolean, default=True, index=True)  # 是否启用
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_scheduler_task_status_enabled', 'status', 'enabled'),
    )


class SchedulerTaskExecution(Base):
    """调度器任务执行历史"""
    __tablename__ = "scheduler_task_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, nullable=False, index=True)  # 任务ID
    job_id = Column(String(255), nullable=False, index=True)  # 任务ID（冗余字段，方便查询）
    status = Column(String(50), nullable=False, index=True)  # 状态: running, completed, failed
    started_at = Column(DateTime, default=datetime.utcnow, index=True)  # 开始时间
    completed_at = Column(DateTime, nullable=True)  # 完成时间
    duration = Column(Float, nullable=True)  # 执行耗时（秒）
    result = Column(JSON, nullable=True)  # 执行结果
    error_message = Column(Text, nullable=True)  # 错误信息
    error_traceback = Column(Text, nullable=True)  # 错误堆栈
    
    __table_args__ = (
        Index('idx_scheduler_task_execution_task_ts', 'task_id', 'started_at'),
        Index('idx_scheduler_task_execution_job_ts', 'job_id', 'started_at'),
    )

