"""
Local Intel 事件/枚举定义
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class InboxEventType(str, Enum):
    """站内信事件类型"""

    HR_PENALTY = "hr_penalty"          # HR 扣分 / 惩罚
    TORRENT_DELETED = "torrent_deleted"  # 种子被删除
    SITE_THROTTLED = "site_throttled"  # 访问节流 / 功能限制
    OTHER = "other"                    # 未分类事件


@dataclass
class InboxEvent:
    """站内信事件数据结构"""

    site: str
    type: InboxEventType
    raw_subject: str
    raw_body: str

    # 便于展示
    title: Optional[str] = None
    message: Optional[str] = None

    torrent_id: Optional[str] = None
    created_at: Optional[datetime] = None

    # 针对 THROTTLE，可选的解除时间（若能解析）
    throttle_until: Optional[datetime] = None

    # 可选：站点返回的 message id / url
    message_id: Optional[str] = None
    message_url: Optional[str] = None


