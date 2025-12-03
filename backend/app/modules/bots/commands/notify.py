"""
通知偏好命令
BOT-TELEGRAM Phase 2 + NOTIFY-UX-1

/notify 命令：快速管理通知偏好
"""

from loguru import logger

from app.modules.bots.telegram_router import router
from app.modules.bots.telegram_context import TelegramUpdateContext
from app.modules.bots.telegram_keyboard import (
    inline_keyboard,
    inline_button,
    callback_data,
    parse_callback_data,
    build_back_to_menu_button,
)
from app.services import notify_preference_service


# ============== /notify 命令 ==============

@router.command("/notify")
async def cmd_notify(ctx: TelegramUpdateContext) -> None:
    """通知偏好设置命令"""
    await _show_notify_menu(ctx, edit=False)


@router.command("/notifications")
async def cmd_notifications(ctx: TelegramUpdateContext) -> None:
    """通知偏好设置命令（别名）"""
    await _show_notify_menu(ctx, edit=False)


# ============== 回调处理 ==============

@router.callback("npref:")
async def callback_notify_preference(ctx: TelegramUpdateContext) -> None:
    """处理通知偏好回调"""
    data = ctx.callback_data
    
    # 解析 npref:action:payload
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
            payload = {"raw": parts[2]}
    
    match action:
        case "menu":
            await _show_notify_menu(ctx, edit=True)
        
        case "toggle":
            # npref:toggle:group_name
            group = payload.get("raw") or parts[2] if len(parts) > 2 else None
            if group:
                await _toggle_group(ctx, group)
        
        case "snooze":
            await _show_snooze_menu(ctx)
        
        case "snooze_set":
            # npref:snooze_set:minutes
            minutes = int(payload.get("raw") or parts[2]) if len(parts) > 2 else 0
            if minutes > 0:
                await _set_snooze(ctx, minutes)
        
        case "snooze_clear":
            await _clear_snooze(ctx)
        
        case "mute_toggle":
            await _toggle_global_mute(ctx)
        
        case _:
            await ctx.answer_callback("功能开发中...")


async def _show_notify_menu(ctx: TelegramUpdateContext, edit: bool = False) -> None:
    """显示通知偏好菜单"""
    # 获取当前状态
    snooze = await notify_preference_service.get_user_snooze(ctx.session, ctx.app_user.id)
    
    # 获取各分组状态
    manga_enabled = await notify_preference_service.get_group_enabled_status(
        ctx.session, ctx.app_user.id, "manga"
    )
    novel_enabled = await notify_preference_service.get_group_enabled_status(
        ctx.session, ctx.app_user.id, "novel_tts"
    )
    music_enabled = await notify_preference_service.get_group_enabled_status(
        ctx.session, ctx.app_user.id, "music"
    )
    system_enabled = await notify_preference_service.get_group_enabled_status(
        ctx.session, ctx.app_user.id, "system"
    )
    
    # 构建状态文本
    status_icon = "🔔" if not (snooze and snooze.is_snoozed()) else "🔕"
    status_text = "正常" if not (snooze and snooze.is_snoozed()) else "静音中"
    
    if snooze:
        if snooze.muted:
            status_text = "全局静音"
        elif snooze.snooze_until:
            from datetime import datetime
            if datetime.utcnow() < snooze.snooze_until:
                status_text = f"静音到 {snooze.snooze_until.strftime('%H:%M')}"
    
    text = f"""
{status_icon} *通知偏好设置*

*当前状态*: {status_text}

点击下方按钮开关各类通知：
"""
    
    # 构建按钮
    def toggle_icon(enabled: bool) -> str:
        return "✅" if enabled else "❌"
    
    buttons = [
        [
            inline_button(
                f"{toggle_icon(manga_enabled)} 漫画更新",
                callback_data=callback_data("npref:toggle", {"raw": "manga"})
            ),
            inline_button(
                f"{toggle_icon(novel_enabled)} 小说/TTS",
                callback_data=callback_data("npref:toggle", {"raw": "novel_tts"})
            ),
        ],
        [
            inline_button(
                f"{toggle_icon(music_enabled)} 音乐订阅",
                callback_data=callback_data("npref:toggle", {"raw": "music"})
            ),
            inline_button(
                f"{toggle_icon(system_enabled)} 系统通知",
                callback_data=callback_data("npref:toggle", {"raw": "system"})
            ),
        ],
        [
            inline_button("⏰ 临时静音", callback_data="npref:snooze"),
        ],
        [
            inline_button(
                "🔕 全局静音" if not (snooze and snooze.muted) else "🔔 取消静音",
                callback_data="npref:mute_toggle"
            ),
        ],
        [inline_button("« 返回主菜单", callback_data="menu:main")],
    ]
    
    keyboard = inline_keyboard(buttons)
    
    if edit:
        await ctx.edit_message_text(text, reply_markup=keyboard)
        await ctx.answer_callback()
    else:
        await ctx.reply_text(text, reply_markup=keyboard)


async def _toggle_group(ctx: TelegramUpdateContext, group: str) -> None:
    """切换分组开关"""
    # 获取当前状态
    current_enabled = await notify_preference_service.get_group_enabled_status(
        ctx.session, ctx.app_user.id, group
    )
    
    # 切换状态
    new_enabled = not current_enabled
    await notify_preference_service.set_group_enabled(
        ctx.session, ctx.app_user.id, group, new_enabled
    )
    
    group_names = {
        "manga": "漫画更新",
        "novel_tts": "小说/TTS",
        "music": "音乐订阅",
        "system": "系统通知",
    }
    group_name = group_names.get(group, group)
    
    status_text = "已开启" if new_enabled else "已关闭"
    await ctx.answer_callback(f"{group_name}通知{status_text}", show_alert=True)
    
    # 刷新菜单
    await _show_notify_menu(ctx, edit=True)


async def _show_snooze_menu(ctx: TelegramUpdateContext) -> None:
    """显示临时静音菜单"""
    text = """
⏰ *临时静音*

选择静音时长：
"""
    
    buttons = [
        [
            inline_button("30 分钟", callback_data="npref:snooze_set:30"),
            inline_button("1 小时", callback_data="npref:snooze_set:60"),
        ],
        [
            inline_button("2 小时", callback_data="npref:snooze_set:120"),
            inline_button("4 小时", callback_data="npref:snooze_set:240"),
        ],
        [
            inline_button("今晚 (23:59)", callback_data="npref:snooze_set:tonight"),
        ],
        [inline_button("« 返回", callback_data="npref:menu")],
    ]
    
    await ctx.edit_message_text(text, reply_markup=inline_keyboard(buttons))
    await ctx.answer_callback()


async def _set_snooze(ctx: TelegramUpdateContext, minutes: int) -> None:
    """设置临时静音"""
    from datetime import datetime, timedelta
    
    # 特殊处理 "tonight"
    if minutes == 0:
        # 计算到今晚 23:59 的分钟数
        now = datetime.utcnow()
        tonight = now.replace(hour=23, minute=59, second=0, microsecond=0)
        if tonight <= now:
            tonight += timedelta(days=1)
        minutes = max(5, int((tonight - now).total_seconds() / 60))
    
    await notify_preference_service.set_snooze(
        ctx.session,
        ctx.app_user.id,
        duration_minutes=minutes,
    )
    
    await ctx.answer_callback(f"已静音 {minutes} 分钟", show_alert=True)
    await _show_notify_menu(ctx, edit=True)


async def _clear_snooze(ctx: TelegramUpdateContext) -> None:
    """清除静音状态"""
    await notify_preference_service.clear_snooze(ctx.session, ctx.app_user.id)
    await ctx.answer_callback("已恢复通知", show_alert=True)
    await _show_notify_menu(ctx, edit=True)


async def _toggle_global_mute(ctx: TelegramUpdateContext) -> None:
    """切换全局静音"""
    snooze = await notify_preference_service.get_user_snooze(ctx.session, ctx.app_user.id)
    
    new_muted = not (snooze and snooze.muted)
    
    await notify_preference_service.set_snooze(
        ctx.session,
        ctx.app_user.id,
        muted=new_muted,
    )
    
    status_text = "已开启全局静音" if new_muted else "已恢复通知"
    await ctx.answer_callback(status_text, show_alert=True)
    await _show_notify_menu(ctx, edit=True)
