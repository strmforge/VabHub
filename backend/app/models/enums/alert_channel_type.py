"""
告警渠道类型枚举
OPS-2A 实现
"""

from enum import Enum


class AlertChannelType(str, Enum):
    """告警渠道类型"""
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    BARK = "bark"
    # 预留扩展
    # SLACK = "slack"
    # DISCORD = "discord"
