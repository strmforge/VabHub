"""
时间工具模块
"""

from datetime import datetime
from typing import Optional


def utcnow() -> datetime:
    """获取当前UTC时间"""
    return datetime.utcnow()


def format_datetime(dt: Optional[datetime] = None) -> str:
    """格式化时间为字符串"""
    if dt is None:
        dt = utcnow()
    return dt.isoformat()