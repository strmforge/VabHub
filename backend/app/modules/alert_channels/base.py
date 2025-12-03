"""
告警渠道适配器基类
OPS-2A 实现
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.alert_channel import AlertChannel


class BaseAlertChannelAdapter(ABC):
    """告警渠道适配器基类"""

    def __init__(self, channel: "AlertChannel"):
        self.channel = channel

    @abstractmethod
    async def send(self, title: str, body: str) -> None:
        """
        发送告警消息
        
        Args:
            title: 告警标题
            body: 告警内容
        """
        ...

    def get_config(self, key: str, default=None):
        """获取渠道配置"""
        return self.channel.config.get(key, default)
