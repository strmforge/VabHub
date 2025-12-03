"""
用户通知渠道类型枚举
NOTIFY-CORE 实现
"""

from enum import Enum


class UserNotifyChannelType(str, Enum):
    """用户通知渠道类型"""
    TELEGRAM_BOT = "telegram_bot"   # Telegram Bot 绑定
    WEBHOOK = "webhook"             # 自定义 Webhook
    BARK = "bark"                   # Bark iOS 推送
    # 预留位：以后可以加 wecom/feishu/discord 等
