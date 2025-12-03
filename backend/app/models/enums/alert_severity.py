"""
告警严重级别枚举
OPS-2A 实现
"""

from enum import Enum


class AlertSeverity(str, Enum):
    """告警严重级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
