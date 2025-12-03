"""
Telegram Bot 消息处理器
BOT-TELEGRAM Phase 2

使用 Router 架构处理消息和回调
"""

from typing import Any
from loguru import logger

from app.core.database import async_session_factory
from app.modules.bots.telegram_bot_client import get_telegram_bot_client
from app.modules.bots.telegram_context import TelegramUpdateContext
from app.modules.bots.telegram_router import router
from app.services import user_telegram_service

# 导入所有命令模块以注册处理器
from app.modules.bots import commands  # noqa: F401


async def handle_update(update: dict[str, Any]) -> None:
    """
    处理 Telegram Update（使用新的 Router 架构）
    
    Args:
        update: Telegram Update 对象
    """
    client = get_telegram_bot_client()
    if not client:
        logger.warning("[telegram] bot client not available")
        return
    
    try:
        async with async_session_factory() as session:
            # 创建上下文
            ctx = TelegramUpdateContext(update, session, client)
            
            if not ctx.chat_id:
                return
            
            # 注入绑定的用户
            ctx.app_user = await user_telegram_service.get_user_by_chat_id(
                session, ctx.chat_id
            )
            
            # 通过路由器分发
            await router.dispatch_update(ctx)
            
    except Exception as e:
        logger.error(f"[telegram] handle update error: {e}", exc_info=True)


async def setup_bot_commands() -> bool:
    """设置 Bot 命令列表"""
    client = get_telegram_bot_client()
    if not client:
        return False
    
    commands = [
        {"command": "start", "description": "绑定账号 / 打开主菜单"},
        {"command": "menu", "description": "打开主菜单"},
        {"command": "help", "description": "显示帮助信息"},
        {"command": "search", "description": "搜索影视/漫画/音乐"},
        {"command": "subscriptions", "description": "管理订阅"},
        {"command": "downloads", "description": "下载任务"},
        {"command": "reading", "description": "阅读进度"},
        {"command": "reading_recent", "description": "最近阅读活动"},
        {"command": "shelf", "description": "我的阅读书架"},
        {"command": "reading_done", "description": "标记阅读已完成（会修改状态）"},
        {"command": "reading_fav", "description": "收藏进行中条目（会修改收藏）"},
        {"command": "shelf_unfav", "description": "取消书架收藏（会修改收藏）"},
        {"command": "music", "description": "音乐中心"},
        {"command": "charts", "description": "音乐榜单"},
        {"command": "notify", "description": "通知偏好设置"},
        {"command": "settings", "description": "账号设置"},
        {"command": "admin", "description": "管理员命令（仅管理员）"},
        {"command": "ping", "description": "检查 Bot 状态"},
    ]
    
    return await client.set_my_commands(commands)
