"""
告警渠道适配器模块
OPS-2A 实现
"""

from app.modules.alert_channels.base import BaseAlertChannelAdapter
from app.modules.alert_channels.factory import get_alert_channel_adapter

__all__ = ["BaseAlertChannelAdapter", "get_alert_channel_adapter"]
