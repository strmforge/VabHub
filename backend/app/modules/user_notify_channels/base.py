"""
用户通知渠道适配器基类
BOT-EXT-2 实现

定义渠道能力声明与动作降级策略。
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel

from app.models.user_notify_channel import UserNotifyChannel
from app.schemas.notify_actions import NotificationAction, NotificationActionType


class ChannelCapabilities(BaseModel):
    """渠道能力声明"""
    
    # 内容能力
    supports_markdown: bool = False
    supports_html: bool = False
    supports_long_text: bool = True
    max_text_length: int = 4096
    
    # 交互能力
    supports_buttons: bool = False
    max_button_count: int = 0
    supports_inline_buttons: bool = False
    
    # 链接能力
    supports_deep_link: bool = False
    supports_click_url: bool = True
    
    # 其他
    supports_image: bool = False
    supports_file: bool = False


class BaseUserNotifyChannelAdapter(ABC):
    """用户通知渠道适配器基类"""
    
    def __init__(self, channel: UserNotifyChannel):
        self.channel = channel
    
    @abstractmethod
    def get_capabilities(self) -> ChannelCapabilities:
        """获取渠道能力声明"""
        return ChannelCapabilities()
    
    @abstractmethod
    async def send(
        self,
        message: str,
        title: Optional[str] = None,
        url: Optional[str] = None,
        actions: Optional[list[NotificationAction]] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> bool:
        """发送消息"""
        pass
    
    def degrade_actions(
        self,
        actions: list[NotificationAction],
        base_url: str = "",
    ) -> tuple[list[NotificationAction], Optional[str], Optional[str]]:
        """
        根据渠道能力降级动作
        
        Args:
            actions: 原始动作列表
            base_url: 前端基础 URL
            
        Returns:
            (降级后的动作列表, 主 URL, 附加文本提示)
        """
        caps = self.get_capabilities()
        
        if not actions:
            return [], None, None
        
        # 按 primary 排序，主要动作优先
        sorted_actions = sorted(actions, key=lambda a: not a.primary)
        
        # 支持按钮的渠道
        if caps.supports_buttons:
            # 截断到最大按钮数
            truncated = sorted_actions[:caps.max_button_count] if caps.max_button_count else sorted_actions
            return truncated, None, None
        
        # 不支持按钮但支持 deep link
        if caps.supports_deep_link or caps.supports_click_url:
            # 选择第一个可转 URL 的动作作为主 URL
            primary_url = None
            for action in sorted_actions:
                url = action.to_url(base_url)
                if url:
                    primary_url = url
                    break
            
            # 生成其他动作的文本提示
            other_actions = [a for a in sorted_actions if a.to_url(base_url) != primary_url]
            hint_text = None
            if other_actions:
                hints = [f"• {a.label}" for a in other_actions[:3]]
                hint_text = "其他操作（请在 Web 端进行）：\n" + "\n".join(hints)
            
            return [], primary_url, hint_text
        
        # 完全不支持交互
        hint_parts = [f"• {a.label}" for a in sorted_actions[:3]]
        hint_text = "可用操作（请登录 Web 端）：\n" + "\n".join(hint_parts)
        return [], None, hint_text


class TelegramUserNotifyAdapter(BaseUserNotifyChannelAdapter):
    """Telegram 渠道适配器"""
    
    def get_capabilities(self) -> ChannelCapabilities:
        return ChannelCapabilities(
            supports_markdown=True,
            supports_long_text=True,
            max_text_length=4096,
            supports_buttons=True,
            max_button_count=8,
            supports_inline_buttons=True,
            supports_deep_link=True,
            supports_click_url=True,
        )
    
    async def send(
        self,
        message: str,
        title: Optional[str] = None,
        url: Optional[str] = None,
        actions: Optional[list[NotificationAction]] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> bool:
        """通过 Telegram Bot 发送"""
        # 实现在 factory.py 中
        raise NotImplementedError("Use factory._send_telegram instead")


class WebhookUserNotifyAdapter(BaseUserNotifyChannelAdapter):
    """Webhook 渠道适配器"""
    
    def get_capabilities(self) -> ChannelCapabilities:
        return ChannelCapabilities(
            supports_markdown=True,
            supports_long_text=True,
            max_text_length=65535,
            supports_buttons=False,  # 由接收端自行处理 JSON
            max_button_count=0,
            supports_inline_buttons=False,
            supports_deep_link=True,
            supports_click_url=True,
        )
    
    async def send(
        self,
        message: str,
        title: Optional[str] = None,
        url: Optional[str] = None,
        actions: Optional[list[NotificationAction]] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> bool:
        """通过 Webhook 发送"""
        raise NotImplementedError("Use factory._send_webhook instead")


class BarkUserNotifyAdapter(BaseUserNotifyChannelAdapter):
    """Bark 渠道适配器"""
    
    def get_capabilities(self) -> ChannelCapabilities:
        return ChannelCapabilities(
            supports_markdown=False,
            supports_long_text=False,
            max_text_length=1024,
            supports_buttons=False,
            max_button_count=0,
            supports_inline_buttons=False,
            supports_deep_link=True,
            supports_click_url=True,  # 点击通知可打开 URL
        )
    
    async def send(
        self,
        message: str,
        title: Optional[str] = None,
        url: Optional[str] = None,
        actions: Optional[list[NotificationAction]] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> bool:
        """通过 Bark 发送"""
        raise NotImplementedError("Use factory._send_bark instead")


def get_adapter_for_channel(channel: UserNotifyChannel) -> BaseUserNotifyChannelAdapter:
    """获取渠道对应的适配器"""
    from app.models.enums.user_notify_channel_type import UserNotifyChannelType
    
    adapters = {
        UserNotifyChannelType.TELEGRAM_BOT: TelegramUserNotifyAdapter,
        UserNotifyChannelType.WEBHOOK: WebhookUserNotifyAdapter,
        UserNotifyChannelType.BARK: BarkUserNotifyAdapter,
    }
    
    adapter_class = adapters.get(channel.channel_type, BaseUserNotifyChannelAdapter)
    return adapter_class(channel)


def get_capabilities_for_channel_type(channel_type: str) -> ChannelCapabilities:
    """获取渠道类型的能力声明（用于预览）"""
    from app.models.enums.user_notify_channel_type import UserNotifyChannelType
    
    caps_map = {
        UserNotifyChannelType.TELEGRAM_BOT.value: TelegramUserNotifyAdapter(None).get_capabilities(),
        UserNotifyChannelType.WEBHOOK.value: WebhookUserNotifyAdapter(None).get_capabilities(),
        UserNotifyChannelType.BARK.value: BarkUserNotifyAdapter(None).get_capabilities(),
        "telegram": TelegramUserNotifyAdapter(None).get_capabilities(),
        "webhook": WebhookUserNotifyAdapter(None).get_capabilities(),
        "bark": BarkUserNotifyAdapter(None).get_capabilities(),
    }
    
    return caps_map.get(channel_type, ChannelCapabilities())
