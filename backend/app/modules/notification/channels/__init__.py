"""
通知渠道模块
"""
from .telegram import TelegramChannel
from .wechat import WeChatChannel
from .base import NotificationChannelBase

# 注意：NotificationChannelManager在app/modules/notification/channels.py中
# 由于文件名冲突（channels.py和channels/目录），需要从父模块导入
# 但这里只导出渠道类，不导出Manager，避免循环导入

__all__ = [
    "TelegramChannel",
    "WeChatChannel",
    "NotificationChannelBase"
]

