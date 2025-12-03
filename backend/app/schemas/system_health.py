"""
系统健康检查 Schema
OPS-1A 实现
"""

from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel


# 类型定义
HealthStatus = Literal["ok", "warning", "error", "unknown"]
CheckType = Literal["db", "service", "external", "disk", "queue", "runner", "other"]
RunnerType = Literal["scheduled", "manual", "critical", "optional"]


class SystemHealthCheckRead(BaseModel):
    """健康检查读取 Schema"""
    key: str
    check_type: str
    status: HealthStatus
    last_checked_at: Optional[datetime] = None
    last_duration_ms: Optional[int] = None
    last_error: Optional[str] = None
    meta: Optional[dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class SystemRunnerStatusRead(BaseModel):
    """Runner 状态读取 Schema"""
    name: str
    runner_type: str
    last_started_at: Optional[datetime] = None
    last_finished_at: Optional[datetime] = None
    last_exit_code: Optional[int] = None
    last_duration_ms: Optional[int] = None
    last_error: Optional[str] = None
    recommended_interval_min: Optional[int] = None
    # OPS-2C: 成功/失败统计
    success_count: int = 0
    failure_count: int = 0
    
    class Config:
        from_attributes = True


class RunnerStatsRead(BaseModel):
    """Runner 统计信息（OPS-2C）"""
    name: str
    runner_type: str
    last_started_at: Optional[str] = None
    last_finished_at: Optional[str] = None
    last_exit_code: Optional[int] = None
    last_duration_ms: Optional[int] = None
    last_error: Optional[str] = None
    recommended_interval_min: Optional[int] = None
    success_count: int = 0
    failure_count: int = 0
    total_runs: int = 0
    success_rate: float = 0.0


class SystemHealthSummary(BaseModel):
    """系统健康汇总"""
    overall_status: HealthStatus
    total_checks: int = 0
    ok_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    unknown_count: int = 0
    checks: list[SystemHealthCheckRead] = []
    runners: list[SystemRunnerStatusRead] = []
    last_check_time: Optional[datetime] = None


class HealthCheckResult(BaseModel):
    """单项健康检查结果"""
    status: HealthStatus
    duration_ms: int
    error: Optional[str] = None
    meta: Optional[dict[str, Any]] = None
