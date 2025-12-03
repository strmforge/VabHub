"""
告警渠道适配器工厂
OPS-2A 实现
"""

from typing import TYPE_CHECKING

from app.models.enums.alert_channel_type import AlertChannelType
from app.modules.alert_channels.base import BaseAlertChannelAdapter
from app.modules.alert_channels.telegram import TelegramAlertAdapter
from app.modules.alert_channels.webhook import WebhookAlertAdapter
from app.modules.alert_channels.bark import BarkAlertAdapter

if TYPE_CHECKING:
    from app.models.alert_channel import AlertChannel


def get_alert_channel_adapter(channel: "AlertChannel") -> BaseAlertChannelAdapter:
    """
    根据渠道类型获取对应的适配器实例
    
    Args:
        channel: 告警渠道模型实例
        
    Returns:
        对应类型的适配器实例
        
    Raises:
        ValueError: 不支持的渠道类型
    """
    match channel.channel_type:
        case AlertChannelType.TELEGRAM:
            return TelegramAlertAdapter(channel)
        case AlertChannelType.WEBHOOK:
            return WebhookAlertAdapter(channel)
        case AlertChannelType.BARK:
            return BarkAlertAdapter(channel)
        case _:
            raise ValueError(f"Unsupported channel type: {channel.channel_type}")
