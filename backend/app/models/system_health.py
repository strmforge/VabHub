"""
系统健康检查模型
OPS-1A 实现
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from app.core.database import Base


class SystemHealthCheck(Base):
    """系统健康检查记录"""
    __tablename__ = "system_health_check"

    id = Column(Integer, primary_key=True, index=True)
    
    # 检查项唯一 key，如 "db.default", "service.download_client", "external.pt_indexer"
    key = Column(String(128), unique=True, index=True, nullable=False)
    
    # 类型：db / service / external / disk / queue / runner / other
    check_type = Column(String(32), nullable=False)
    
    # 最近一次状态：ok / warning / error / unknown
    status = Column(String(16), nullable=False, default="unknown")
    
    # 最近一次检查时间
    last_checked_at = Column(DateTime, nullable=True)
    
    # 最近一次耗时（毫秒）
    last_duration_ms = Column(Integer, nullable=True)
    
    # 最近一次错误信息
    last_error = Column(Text, nullable=True)
    
    # 额外元数据（JSON）
    meta = Column(JSON, nullable=True)
    
    # 上次通知状态（用于降频）
    last_notified_status = Column(String(16), nullable=True)


class SystemRunnerStatus(Base):
    """Runner 运行状态记录"""
    __tablename__ = "system_runner_status"

    id = Column(Integer, primary_key=True, index=True)
    
    # Runner 名称，如 "manga_follow_sync", "music_chart_sync"
    name = Column(String(128), unique=True, index=True, nullable=False)
    
    # Runner 类型: scheduled / manual / critical / optional
    runner_type = Column(String(32), nullable=False, default="scheduled")
    
    # 上次开始时间
    last_started_at = Column(DateTime, nullable=True)
    
    # 上次结束时间
    last_finished_at = Column(DateTime, nullable=True)
    
    # 上次 exit_code（0 成功，非 0 失败）
    last_exit_code = Column(Integer, nullable=True)
    
    # 上次运行时长（毫秒）
    last_duration_ms = Column(Integer, nullable=True)
    
    # 最近一次错误摘要
    last_error = Column(Text, nullable=True)
    
    # 推荐运行间隔（分钟）
    recommended_interval_min = Column(Integer, nullable=True)
    
    # OPS-2C: 成功/失败次数统计
    success_count = Column(Integer, default=0, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
