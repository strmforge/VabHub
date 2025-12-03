"""
Telegram Bot 命令模块
BOT-TELEGRAM Phase 2
"""

from app.modules.bots.telegram_router import router

# 导入所有命令模块以注册处理器
from app.modules.bots.commands import (
    basic,
    menu,
    search,
    subscriptions,
    downloads,
    reading,
    shelf,  # 书架/收藏视角命令
    admin,
    notif,
    notify,  # 通知偏好命令
    music,  # 音乐中心命令
)

__all__ = ["router"]
