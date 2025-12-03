"""
订阅管理命令
BOT-TELEGRAM Phase 2

/subscriptions 和订阅相关回调
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
from app.services.user_subscription_overview_service import (
    list_user_subscriptions,
    toggle_subscription,
    run_subscription_once,
    remove_subscription,
)
from app.core.config import settings


# ============== /subscriptions ==============

@router.command("/subscriptions")
async def cmd_subscriptions(ctx: TelegramUpdateContext) -> None:
    """订阅管理命令"""
    await _show_subscription_list(ctx, kind=None, edit=False)


# ============== 订阅列表回调 ==============

@router.callback("sub:")
async def callback_subscription(ctx: TelegramUpdateContext) -> None:
    """处理订阅相关回调"""
    data = ctx.callback_data
    
    # 解析 sub:action:payload
    parts = data.split(":", 2)
    if len(parts) < 2:
        await ctx.answer_callback("无效操作")
        return
    
    action = parts[1]
    
    # 解析 payload
    payload = {}
    if len(parts) > 2:
        try:
            _, payload = parse_callback_data(f":{parts[2]}")
        except Exception:
            payload = {"raw": parts[2]}
    
    match action:
        case "list":
            # sub:list:manga / sub:list:music / sub:list:all
            kind = payload.get("raw") or parts[2] if len(parts) > 2 else None
            if kind == "all":
                kind = None
            await _show_subscription_list(ctx, kind=kind, edit=True)
        
        case "toggle":
            await _handle_toggle(ctx, payload)
        
        case "run":
            await _handle_run_once(ctx, payload)
        
        case "open":
            await _handle_open_web(ctx, payload)
        
        case "detail":
            await _handle_detail(ctx, payload)
        
        case "remove":
            await _handle_remove(ctx, payload)
        
        case _:
            await ctx.answer_callback("功能开发中...")


async def _show_subscription_list(
    ctx: TelegramUpdateContext,
    kind: str | None = None,
    edit: bool = False,
) -> None:
    """显示订阅列表"""
    items = await list_user_subscriptions(ctx.session, ctx.app_user, kind=kind)
    
    if not items:
        kind_name = {
            "manga": "漫画追更",
            "music": "音乐榜单",
        }.get(kind, "订阅")
        
        text = f"📋 *{kind_name}*\n\n暂无订阅内容。"
        
        if edit:
            await ctx.edit_message_text(text, reply_markup=build_back_to_menu_button())
            await ctx.answer_callback()
        else:
            await ctx.reply_text(text, reply_markup=build_back_to_menu_button())
        return
    
    # 分类型显示
    kind_icons = {
        "manga_follow": "📚",
        "music_chart": "🎵",
        "rss": "📡",
    }
    
    kind_names = {
        "manga_follow": "漫画追更",
        "music_chart": "音乐榜单",
        "rss": "RSS 订阅",
    }
    
    # 按类型分组
    grouped: dict[str, list] = {}
    for item in items:
        if item.kind not in grouped:
            grouped[item.kind] = []
        grouped[item.kind].append(item)
    
    # 构建消息
    text = "🧩 *我的订阅*\n\n"
    buttons = []
    
    for item_kind, kind_items in grouped.items():
        icon = kind_icons.get(item_kind, "📌")
        name = kind_names.get(item_kind, item_kind)
        
        text += f"{icon} *{name}* ({len(kind_items)})\n"
        
        for item in kind_items[:5]:  # 每类最多显示5个
            status_icon = "✅" if item.status == "enabled" else "⏸"
            text += f"  {status_icon} {item.title}\n"
            
            # 添加操作按钮
            payload = {"id": item.id, "k": item.kind}
            toggle_text = "⏸ 暂停" if item.status == "enabled" else "▶️ 启用"
            
            buttons.append([
                inline_button(f"{item.title[:15]}...", callback_data=callback_data("sub:detail", payload)),
                inline_button(toggle_text, callback_data=callback_data("sub:toggle", payload)),
            ])
        
        if len(kind_items) > 5:
            text += f"  ... 还有 {len(kind_items) - 5} 个\n"
        
        text += "\n"
    
    # 添加返回按钮
    buttons.append([inline_button("« 返回主菜单", callback_data="menu:main")])
    
    keyboard = inline_keyboard(buttons)
    
    if edit:
        await ctx.edit_message_text(text, reply_markup=keyboard)
        await ctx.answer_callback()
    else:
        await ctx.reply_text(text, reply_markup=keyboard)


async def _handle_toggle(ctx: TelegramUpdateContext, payload: dict) -> None:
    """切换订阅状态"""
    sub_id = payload.get("id")
    kind = payload.get("k")
    
    if not sub_id or not kind:
        await ctx.answer_callback("参数错误")
        return
    
    try:
        new_status = await toggle_subscription(ctx.session, ctx.app_user, kind, sub_id)
        status_text = "已启用" if new_status else "已暂停"
        await ctx.answer_callback(f"✅ {status_text}", show_alert=True)
        
        # 刷新列表
        await _show_subscription_list(ctx, kind=None, edit=True)
        
    except ValueError as e:
        await ctx.answer_callback(f"❌ {str(e)}", show_alert=True)
    except Exception as e:
        logger.error(f"[telegram] toggle subscription failed: {e}")
        await ctx.answer_callback("❌ 操作失败", show_alert=True)


async def _handle_run_once(ctx: TelegramUpdateContext, payload: dict) -> None:
    """立即执行一次"""
    sub_id = payload.get("id")
    kind = payload.get("k")
    
    if not sub_id or not kind:
        await ctx.answer_callback("参数错误")
        return
    
    try:
        success = await run_subscription_once(ctx.session, ctx.app_user, kind, sub_id)
        if success:
            await ctx.answer_callback("🔄 已触发同步，请稍后查看结果", show_alert=True)
        else:
            await ctx.answer_callback("❌ 触发失败", show_alert=True)
    except Exception as e:
        logger.error(f"[telegram] run subscription failed: {e}")
        await ctx.answer_callback("❌ 操作失败", show_alert=True)


async def _handle_open_web(ctx: TelegramUpdateContext, payload: dict) -> None:
    """打开网页"""
    base_url = getattr(settings, "FRONTEND_URL", "")
    
    if not base_url:
        await ctx.answer_callback("请在网页端查看")
        return
    
    kind = payload.get("k")
    sub_id = payload.get("id")
    
    # 构建 URL
    if kind == "manga_follow":
        url = f"{base_url}/manga/{payload.get('series_id', sub_id)}"
    elif kind == "music_chart":
        url = f"{base_url}/music"
    else:
        url = base_url
    
    await ctx.answer_callback(f"请访问: {url}")


async def _handle_detail(ctx: TelegramUpdateContext, payload: dict) -> None:
    """显示订阅详情"""
    sub_id = payload.get("id")
    kind = payload.get("k")
    
    # 查找订阅
    items = await list_user_subscriptions(ctx.session, ctx.app_user, kind=kind.replace("_follow", "").replace("_chart", ""))
    item = next((i for i in items if i.id == sub_id), None)
    
    if not item:
        await ctx.answer_callback("订阅不存在")
        return
    
    # 构建详情消息
    kind_names = {
        "manga_follow": "漫画追更",
        "music_chart": "音乐榜单",
    }
    
    status_text = "✅ 启用" if item.status == "enabled" else "⏸ 暂停"
    
    text = f"📋 *订阅详情*\n\n"
    text += f"📌 *{item.title}*\n"
    text += f"类型: {kind_names.get(item.kind, item.kind)}\n"
    text += f"状态: {status_text}\n"
    
    if item.last_run_at:
        text += f"上次同步: {item.last_run_at.strftime('%Y-%m-%d %H:%M')}\n"
    if item.last_result:
        result_icon = "✅" if item.last_result == "success" else "❌"
        text += f"同步结果: {result_icon}\n"
    
    # 构建按钮
    p = {"id": item.id, "k": item.kind}
    toggle_text = "⏸ 暂停" if item.status == "enabled" else "▶️ 启用"
    
    keyboard = inline_keyboard([
        [
            inline_button(toggle_text, callback_data=callback_data("sub:toggle", p)),
            inline_button("🔄 立即执行", callback_data=callback_data("sub:run", p)),
        ],
        [
            inline_button("🗑 取消订阅", callback_data=callback_data("sub:remove", p)),
        ],
        [inline_button("« 返回列表", callback_data="sub:list:all")],
    ])
    
    await ctx.edit_message_text(text, reply_markup=keyboard)
    await ctx.answer_callback()


async def _handle_remove(ctx: TelegramUpdateContext, payload: dict) -> None:
    """删除订阅"""
    sub_id = payload.get("id")
    kind = payload.get("k")
    
    if not sub_id or not kind:
        await ctx.answer_callback("参数错误")
        return
    
    try:
        await remove_subscription(ctx.session, ctx.app_user, kind, sub_id)
        await ctx.answer_callback("✅ 已取消订阅", show_alert=True)
        
        # 刷新列表
        await _show_subscription_list(ctx, kind=None, edit=True)
        
    except ValueError as e:
        await ctx.answer_callback(f"❌ {str(e)}", show_alert=True)
    except Exception as e:
        logger.error(f"[telegram] remove subscription failed: {e}")
        await ctx.answer_callback("❌ 操作失败", show_alert=True)
