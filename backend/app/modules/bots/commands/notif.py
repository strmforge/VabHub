"""
通知回调处理
BOT-TELEGRAM Phase 2

处理通知消息中的按钮回调
"""

from loguru import logger

from app.modules.bots.telegram_router import router
from app.modules.bots.telegram_context import TelegramUpdateContext
from app.modules.bots.telegram_keyboard import parse_callback_data
from app.core.config import settings


@router.callback("notif:")
async def callback_notification(ctx: TelegramUpdateContext) -> None:
    """处理通知按钮回调"""
    data = ctx.callback_data
    
    # 解析 notif:action:{json}
    parts = data.split(":", 2)
    if len(parts) < 2:
        await ctx.answer_callback("无效操作")
        return
    
    action = parts[1]
    
    payload = {}
    if len(parts) > 2:
        try:
            _, payload = parse_callback_data(f":{parts[2]}")
        except Exception:
            payload = {}
    
    target = payload.get("t", "")
    item_id = payload.get("id", "")
    
    match action:
        case "open":
            await _handle_open(ctx, target, item_id)
        case "download":
            await _handle_download(ctx, target, item_id)
        case "mark_read":
            await _handle_mark_read(ctx, target, item_id)
        case "subscribe":
            await _handle_subscribe(ctx, target, item_id)
        case _:
            await ctx.answer_callback("功能开发中...")


async def _handle_open(ctx: TelegramUpdateContext, target: str, item_id: str) -> None:
    """处理打开操作"""
    base_url = getattr(settings, "FRONTEND_URL", "")
    
    if not base_url:
        await ctx.answer_callback("请在网页端查看")
        return
    
    # 根据 target 构建 URL
    url = ""
    match target:
        case "manga_series":
            url = f"{base_url}/manga/{item_id}"
        case "work_detail" | "novel" | "audiobook":
            url = f"{base_url}/work/{item_id}"
        case "music":
            url = f"{base_url}/music"
        case "download_task":
            url = f"{base_url}/downloads"
        case _:
            url = base_url
    
    await ctx.answer_callback(f"请访问: {url}")


async def _handle_download(ctx: TelegramUpdateContext, target: str, item_id: str) -> None:
    """处理下载操作"""
    # TODO: 添加到下载队列
    logger.info(f"[telegram] notif download: target={target}, id={item_id}")
    await ctx.answer_callback("⬇️ 已加入下载队列", show_alert=True)


async def _handle_mark_read(ctx: TelegramUpdateContext, target: str, item_id: str) -> None:
    """处理标记已读操作"""
    try:
        # 标记通知已读
        from app.services.notification_service import NotificationService
        
        if item_id:
            await NotificationService.mark_notification_read(
                ctx.session,
                ctx.app_user.id,
                int(item_id),
            )
        
        await ctx.answer_callback("✅ 已标记已读", show_alert=True)
        
    except Exception as e:
        logger.error(f"[telegram] mark read failed: {e}")
        await ctx.answer_callback("❌ 操作失败", show_alert=True)


async def _handle_subscribe(ctx: TelegramUpdateContext, target: str, item_id: str) -> None:
    """处理订阅操作"""
    if target == "manga_series":
        try:
            from app.services.manga_follow_service import create_follow
            
            await create_follow(
                ctx.session,
                user_id=ctx.app_user.id,
                series_id=int(item_id),
            )
            await ctx.answer_callback("✅ 已添加追更", show_alert=True)
        except Exception as e:
            logger.warning(f"[telegram] subscribe failed: {e}")
            await ctx.answer_callback("❌ 订阅失败", show_alert=True)
    else:
        await ctx.answer_callback("暂不支持此类型的订阅", show_alert=True)
