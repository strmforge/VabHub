"""
音乐中心命令
BOT-EXT-1

/music, /charts 和音乐相关回调
TG-BOT-MUSIC-1: 音乐订阅控制台
"""

from datetime import datetime
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
from app.core.config import settings
from app.models.user_music_subscription import UserMusicSubscription, MusicSubscriptionType
from app.services.music_subscription_service import run_subscription_once


# ============== /music ==============

@router.command("/music")
async def cmd_music(ctx: TelegramUpdateContext) -> None:
    """音乐中心入口"""
    await _show_music_menu(ctx, edit=False)


# ============== /charts ==============

@router.command("/charts")
async def cmd_charts(ctx: TelegramUpdateContext) -> None:
    """音乐榜单命令"""
    await _show_charts_list(ctx, edit=False)


# ============== 音乐回调 ==============

@router.callback("music:")
async def callback_music(ctx: TelegramUpdateContext) -> None:
    """处理音乐相关回调"""
    data = ctx.callback_data
    
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
            await _show_music_menu(ctx, edit=True)
        
        case "charts":
            await _show_charts_list(ctx, edit=True)
        
        case "subscriptions":
            await _show_music_subscriptions(ctx, edit=True)
        
        case "downloads":
            await _show_music_downloads(ctx, edit=True)
        
        case "toggle_sub":
            await _handle_toggle_subscription(ctx, payload)
        
        case "coverage":
            await _handle_show_coverage(ctx, payload)
        
        case _:
            await ctx.answer_callback("功能开发中...")


async def _show_music_menu(ctx: TelegramUpdateContext, edit: bool = False) -> None:
    """显示音乐中心菜单"""
    base_url = getattr(settings, "FRONTEND_URL", "")
    
    text = """
🎵 *音乐中心*

选择你想查看的内容：
"""
    
    buttons = [
        [
            inline_button("📊 音乐榜单", callback_data="music:charts"),
            inline_button("🧩 我的订阅", callback_data="music:subscriptions"),
        ],
        [
            inline_button("⬇️ 最近下载", callback_data="music:downloads"),
        ],
    ]
    
    if base_url:
        buttons.append([
            inline_button("🌐 打开 MusicCenter", url=f"{base_url}/music"),
        ])
    
    buttons.append([inline_button("« 返回主菜单", callback_data="menu:main")])
    
    keyboard = inline_keyboard(buttons)
    
    if edit:
        await ctx.edit_message_text(text, reply_markup=keyboard)
        await ctx.answer_callback()
    else:
        await ctx.reply_text(text, reply_markup=keyboard)


async def _show_charts_list(ctx: TelegramUpdateContext, edit: bool = False) -> None:
    """显示音乐榜单列表"""
    charts = await _get_music_charts(ctx)
    
    if not charts:
        text = "📊 *音乐榜单*\n\n暂无可用的音乐榜单。"
        
        if edit:
            await ctx.edit_message_text(text, reply_markup=build_back_to_menu_button())
            await ctx.answer_callback()
        else:
            await ctx.reply_text(text, reply_markup=build_back_to_menu_button())
        return
    
    text = "📊 *音乐榜单*\n\n"
    buttons = []
    
    for chart in charts[:10]:
        icon = "✅" if chart.get("subscribed") else "📊"
        name = chart.get("name", "未知榜单")
        source = chart.get("source", "")
        new_count = chart.get("new_tracks", 0)
        
        text += f"{icon} *{name}*"
        if source:
            text += f" ({source})"
        if new_count > 0:
            text += f" • 🆕 {new_count}"
        text += "\n"
        
        # 操作按钮
        chart_id = chart.get("id")
        if chart_id:
            payload = {"id": chart_id}
            sub_text = "❌ 取消" if chart.get("subscribed") else "✅ 订阅"
            
            buttons.append([
                inline_button(f"{name[:15]}...", callback_data=callback_data("music:coverage", payload)),
                inline_button(sub_text, callback_data=callback_data("music:toggle_sub", payload)),
            ])
    
    buttons.append([inline_button("« 返回音乐中心", callback_data="music:menu")])
    
    keyboard = inline_keyboard(buttons)
    
    if edit:
        await ctx.edit_message_text(text, reply_markup=keyboard)
        await ctx.answer_callback()
    else:
        await ctx.reply_text(text, reply_markup=keyboard)


async def _show_music_subscriptions(ctx: TelegramUpdateContext, edit: bool = False) -> None:
    """显示我的音乐订阅"""
    subs = await _get_user_music_subscriptions(ctx)
    
    if not subs:
        text = "🧩 *我的音乐订阅*\n\n暂无订阅。"
        
        if edit:
            await ctx.edit_message_text(text, reply_markup=build_back_to_menu_button())
            await ctx.answer_callback()
        else:
            await ctx.reply_text(text, reply_markup=build_back_to_menu_button())
        return
    
    text = "🧩 *我的音乐订阅*\n\n"
    buttons = []
    
    for sub in subs[:10]:
        name = sub.get("name", "未知订阅")
        status = "✅ 启用" if sub.get("enabled") else "⏸ 暂停"
        coverage = sub.get("coverage")
        
        text += f"• *{name}*\n"
        text += f"   状态: {status}"
        if coverage is not None:
            text += f" | 覆盖率: {coverage:.0f}%"
        text += "\n"
        
        sub_id = sub.get("id")
        if sub_id:
            payload = {"id": sub_id}
            toggle_text = "⏸" if sub.get("enabled") else "▶️"
            
            buttons.append([
                inline_button(name[:20], callback_data=callback_data("music:coverage", payload)),
                inline_button(toggle_text, callback_data=callback_data("music:toggle_sub", payload)),
            ])
    
    buttons.append([inline_button("« 返回音乐中心", callback_data="music:menu")])
    
    keyboard = inline_keyboard(buttons)
    
    if edit:
        await ctx.edit_message_text(text, reply_markup=keyboard)
        await ctx.answer_callback()
    else:
        await ctx.reply_text(text, reply_markup=keyboard)


async def _show_music_downloads(ctx: TelegramUpdateContext, edit: bool = False) -> None:
    """显示音乐下载任务"""
    jobs = await _get_music_download_jobs(ctx)
    
    if not jobs:
        text = "⬇️ *音乐下载*\n\n暂无下载任务。"
        
        if edit:
            await ctx.edit_message_text(text, reply_markup=build_back_to_menu_button())
            await ctx.answer_callback()
        else:
            await ctx.reply_text(text, reply_markup=build_back_to_menu_button())
        return
    
    status_icons = {
        "queued": "⏳",
        "downloading": "🔄",
        "completed": "✅",
        "failed": "❌",
    }
    
    text = "⬇️ *音乐下载*\n\n"
    
    for job in jobs[:10]:
        icon = status_icons.get(job.get("status", ""), "❓")
        title = job.get("title", "未知")[:25]
        text += f"{icon} {title}\n"
    
    text += "\n使用 /downloads 查看更多任务"
    
    buttons = [
        [inline_button("⬇️ 所有下载任务", callback_data="dl:list")],
        [inline_button("« 返回音乐中心", callback_data="music:menu")],
    ]
    
    keyboard = inline_keyboard(buttons)
    
    if edit:
        await ctx.edit_message_text(text, reply_markup=keyboard)
        await ctx.answer_callback()
    else:
        await ctx.reply_text(text, reply_markup=keyboard)


async def _handle_toggle_subscription(ctx: TelegramUpdateContext, payload: dict) -> None:
    """切换音乐订阅状态"""
    chart_id = payload.get("id")
    
    if not chart_id:
        await ctx.answer_callback("参数错误")
        return
    
    try:
        # 尝试切换订阅
        from app.services.user_subscription_overview_service import toggle_subscription
        
        new_status = await toggle_subscription(ctx.session, ctx.app_user, "music_chart", chart_id)
        status_text = "已订阅" if new_status else "已取消订阅"
        await ctx.answer_callback(f"✅ {status_text}", show_alert=True)
        await _show_charts_list(ctx, edit=True)
        
    except ValueError as e:
        await ctx.answer_callback(f"❌ {str(e)}", show_alert=True)
    except Exception as e:
        logger.error(f"[telegram] toggle music subscription failed: {e}")
        await ctx.answer_callback("❌ 操作失败", show_alert=True)


async def _handle_show_coverage(ctx: TelegramUpdateContext, payload: dict) -> None:
    """显示榜单覆盖率详情"""
    chart_id = payload.get("id")
    
    if not chart_id:
        await ctx.answer_callback("参数错误")
        return
    
    # TODO: 实现覆盖率详情展示
    await ctx.answer_callback("覆盖率详情功能开发中...", show_alert=True)


# ============== 辅助函数 ==============

async def _get_music_charts(ctx: TelegramUpdateContext) -> list[dict]:
    """获取音乐榜单列表"""
    charts = []
    
    try:
        from app.services.music_chart_service import list_charts
        
        result = await list_charts(ctx.session, ctx.app_user.id)
        
        for chart in result:
            charts.append({
                "id": chart.id,
                "name": chart.name,
                "source": getattr(chart, "source", None),
                "subscribed": getattr(chart, "is_subscribed", False),
                "new_tracks": getattr(chart, "new_tracks_count", 0),
            })
    except ImportError:
        logger.debug("[telegram] music_chart_service not available")
    except Exception as e:
        logger.warning(f"[telegram] get music charts failed: {e}")
    
    return charts


async def _get_user_music_subscriptions(ctx: TelegramUpdateContext) -> list[dict]:
    """获取用户音乐订阅"""
    subs = []
    
    try:
        from app.services.user_subscription_overview_service import list_user_subscriptions
        
        items = await list_user_subscriptions(ctx.session, ctx.app_user, kind="music")
        
        for item in items:
            subs.append({
                "id": item.id,
                "name": item.title,
                "enabled": item.status == "enabled",
                "coverage": None,
            })
    except ImportError:
        logger.debug("[telegram] subscription service not available")
    except Exception as e:
        logger.warning(f"[telegram] get music subscriptions failed: {e}")
    
    return subs


async def _get_music_download_jobs(ctx: TelegramUpdateContext) -> list[dict]:
    """获取音乐下载任务"""
    jobs = []
    
    try:
        from app.services.bot_task_overview_service import list_user_download_jobs
        
        items = await list_user_download_jobs(ctx.session, ctx.app_user, limit=10)
        
        for job in items:
            if job.job_type == "music_download":
                jobs.append({
                    "id": job.id,
                    "title": job.title,
                    "status": job.status,
                })
    except ImportError:
        logger.debug("[telegram] bot task service not available")
    except Exception as e:
        logger.warning(f"[telegram] get music downloads failed: {e}")
    
    return jobs


# ========== TG-BOT-MUSIC-1: 音乐订阅控制台 ==========

def format_music_security_policy(sub: UserMusicSubscription) -> str:
    """格式化音乐订阅安全策略"""
    policies = []
    
    if not sub.allow_hr and not sub.allow_h3h5 and sub.strict_free_only:
        policies.append("[严格安全]")
        desc = "不下 HR/H3H5，只下 Free/半 Free"
    elif not sub.allow_hr and not sub.allow_h3h5:
        policies.append("[标准模式]")
        desc = "过滤 HR/H3H5，允许非 Free"
    elif sub.allow_hr or sub.allow_h3h5:
        policies.append("[风险自担]")
        if sub.allow_hr and sub.allow_h3h5:
            desc = "允许 HR/H3H5，Free 不限制"
        elif sub.allow_hr:
            desc = "允许 HR，过滤 H3H5"
        else:
            desc = "允许 H3H5，过滤 HR"
    else:
        policies.append("[宽松模式]")
        desc = "基本不过滤"
    
    return f"{policies[0]} {desc}"


async def _ensure_user_bound(ctx: TelegramUpdateContext) -> bool:
    """确保用户已绑定"""
    if not ctx.is_bound:
        await ctx.reply_text(
            "❌ 请先在 Web UI 生成绑定码，并通过 /bind 绑定账号"
        )
        return False
    return True


def _format_datetime(dt: datetime) -> str:
    """格式化日期时间"""
    if not dt:
        return "无"
    return dt.strftime("%Y-%m-%d %H:%M")


async def _get_user_music_subscriptions(ctx: TelegramUpdateContext, limit: int = 10) -> list[UserMusicSubscription]:
    """获取用户音乐订阅列表"""
    from sqlalchemy import select
    
    result = await ctx.session.execute(
        select(UserMusicSubscription)
        .where(UserMusicSubscription.user_id == ctx.app_user.id)
        .order_by(UserMusicSubscription.id.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def _get_music_subscription_by_id(ctx: TelegramUpdateContext, sub_id: int) -> UserMusicSubscription | None:
    """根据ID获取用户音乐订阅"""
    from sqlalchemy import select
    
    result = await ctx.session.execute(
        select(UserMusicSubscription)
        .where(
            UserMusicSubscription.id == sub_id,
            UserMusicSubscription.user_id == ctx.app_user.id
        )
    )
    return result.scalar_one_or_none()


# ============== /music_subs ==============

@router.command("/music_subs")
async def cmd_music_subs(ctx: TelegramUpdateContext) -> None:
    """列出音乐订阅"""
    # 检查用户绑定
    if not await _ensure_user_bound(ctx):
        return
    
    try:
        subscriptions = await _get_user_music_subscriptions(ctx, 10)
        
        if not subscriptions:
            await ctx.reply_text(
                "🎵 *音乐订阅*\n\n"
                "你还没有任何音乐订阅。\n"
                "可以在 Web 端「音乐订阅」页创建。",
                reply_markup=build_back_to_menu_button()
            )
            return
        
        # 构建订阅列表
        text = "🎵 *我的音乐订阅*\n\n"
        
        for sub in subscriptions:
            # 类型图标
            type_icon = "📊" if sub.subscription_type == MusicSubscriptionType.CHART else "🔍"
            type_name = "榜单" if sub.subscription_type == MusicSubscriptionType.CHART else "关键字"
            
            # 状态图标
            status_icon = "✅" if sub.status == "active" else "⏸"
            status_name = "激活" if sub.status == "active" else "暂停"
            
            # 目标信息
            if sub.subscription_type == MusicSubscriptionType.CHART and sub.chart_id:
                target = f"榜单 #{sub.chart_id}"
            elif sub.music_query:
                target = sub.music_query
            else:
                target = "未设置"
            
            # 站点信息
            site = sub.music_site or "全部站点"
            
            # 质量信息
            quality = sub.music_quality or "任意"
            
            # 安全策略
            security = format_music_security_policy(sub)
            
            text += f"{status_icon} *#{sub.id}* {type_icon}{type_name}\n"
            text += f"   目标: {target}\n"
            text += f"   站点: {site} | 质量: {quality}\n"
            text += f"   状态: {status_name} | {security}\n\n"
        
        # 添加帮助提示
        text += "💡 *操作示例:*\n"
        text += "- 查看详情: `/music_sub <ID>`\n"
        text += "- 试运行: `/music_sub_check <ID>`\n"
        text += "- 真实执行: `/music_sub_run <ID>`\n"
        text += "- 切换状态: `/music_sub_toggle <ID>`"
        
        await ctx.reply_text(text, reply_markup=build_back_to_menu_button())
        
    except Exception as e:
        logger.error(f"[telegram] music_subs failed: {e}")
        await ctx.reply_text("❌ 查询订阅时出错，请稍后重试")


# ============== /music_sub ==============

@router.command("/music_sub")
async def cmd_music_sub(ctx: TelegramUpdateContext) -> None:
    """查看音乐订阅详情"""
    # 检查用户绑定
    if not await _ensure_user_bound(ctx):
        return
    
    # 解析参数
    if not ctx.args:
        await ctx.reply_text(
            "用法: `/music_sub 订阅ID`\n"
            "示例: `/music_sub 12`"
        )
        return
    
    try:
        sub_id = int(ctx.args.strip())
    except ValueError:
        await ctx.reply_text("❌ 订阅ID必须是数字")
        return
    
    try:
        # 获取订阅
        sub = await _get_music_subscription_by_id(ctx, sub_id)
        if not sub:
            await ctx.reply_text("❌ 找不到该订阅，可能不存在或不属于你")
            return
        
        # 类型信息
        type_name = "榜单订阅" if sub.subscription_type == MusicSubscriptionType.CHART else "关键字订阅"
        
        # 目标信息
        if sub.subscription_type == MusicSubscriptionType.CHART and sub.chart_id:
            target = f"榜单 #{sub.chart_id}"
        elif sub.music_query:
            target = f"关键字: {sub.music_query}"
        else:
            target = "未设置"
        
        # 站点和质量
        site = sub.music_site or "全部站点"
        quality = sub.music_quality or "任意"
        
        # 状态信息
        status_name = "激活" if sub.status == "active" else "暂停"
        status_icon = "✅" if sub.status == "active" else "⏸"
        
        # 安全策略
        security = format_music_security_policy(sub)
        
        # 构建详情文本
        text = f"🎵 *音乐订阅详情*\n\n"
        text += f"ID: *#{sub.id}*\n"
        text += f"类型: {type_name}\n"
        text += f"目标: {target}\n"
        text += f"站点: {site}\n"
        text += f"质量: {quality}\n\n"
        text += f"状态: {status_icon} {status_name}\n"
        text += f"安全策略: {security}\n\n"
        text += f"📊 *最近运行:*\n"
        text += f"- 最近运行: {_format_datetime(sub.last_run_at)}\n"
        text += f"- 新增曲目: {sub.last_run_new_count or 0}\n"
        text += f"- 搜索数量: {sub.last_run_search_count or 0}\n"
        text += f"- 下载任务: {sub.last_run_download_count or 0}\n\n"
        text += f"🔧 *操作:*\n"
        text += f"- 试运行: `/music_sub_check {sub.id}`\n"
        text += f"- 真实执行: `/music_sub_run {sub.id}`\n"
        text += f"- 切换状态: `/music_sub_toggle {sub.id}`"
        
        await ctx.reply_text(text, reply_markup=build_back_to_menu_button())
        
    except Exception as e:
        logger.error(f"[telegram] music_sub failed: {e}")
        await ctx.reply_text("❌ 查询订阅详情时出错，请稍后重试")


# ============== /music_sub_check ==============

@router.command("/music_sub_check")
async def cmd_music_sub_check(ctx: TelegramUpdateContext) -> None:
    """试运行音乐订阅"""
    # 检查用户绑定
    if not await _ensure_user_bound(ctx):
        return
    
    # 解析参数
    if not ctx.args:
        await ctx.reply_text(
            "用法: `/music_sub_check 订阅ID`\n"
            "示例: `/music_sub_check 12`"
        )
        return
    
    try:
        sub_id = int(ctx.args.strip())
    except ValueError:
        await ctx.reply_text("❌ 订阅ID必须是数字")
        return
    
    try:
        # 获取订阅
        sub = await _get_music_subscription_by_id(ctx, sub_id)
        if not sub:
            await ctx.reply_text("❌ 找不到该订阅，可能不存在或不属于你")
            return
        
        # 类型信息
        type_name = "榜单" if sub.subscription_type == MusicSubscriptionType.CHART else "关键字"
        
        # 目标信息
        if sub.subscription_type == MusicSubscriptionType.CHART and sub.chart_id:
            target = f"榜单 #{sub.chart_id}"
        elif sub.music_query:
            target = sub.music_query
        else:
            target = "未设置"
        
        # 状态信息
        status_name = "激活" if sub.status == "active" else "暂停"
        status_icon = "✅" if sub.status == "active" else "⏸"
        
        # 安全策略
        security = format_music_security_policy(sub)
        
        # 发送处理中消息
        processing_msg = await ctx.reply_text("🔄 正在试运行订阅...")
        
        # 执行试运行
        result = await run_subscription_once(ctx.session, sub, auto_download=False)
        
        # 构建统计信息
        filtered_total = sum(result.filtered_out.values()) if result.filtered_out else 0
        available = result.found_total - filtered_total - result.skipped_existing
        
        # 构建结果文本
        text = f"✅ *试运行完成*（不会创建真实下载任务）\n\n"
        text += f"订阅: *#{sub.id}* [{type_name}] {target}\n"
        text += f"当前状态: {status_icon} {status_name}\n"
        text += f"安全策略: {security}\n\n"
        text += f"📊 *本次统计:*\n"
        text += f"- 原始候选: {result.found_total}\n"
        text += f"- 过滤: "
        
        if result.filtered_out:
            filter_parts = []
            for key, count in result.filtered_out.items():
                if key == "hr":
                    filter_parts.append(f"HR={count}")
                elif key == "h3h5":
                    filter_parts.append(f"H3/H5={count}")
                elif key == "non_free":
                    filter_parts.append(f"非Free={count}")
                elif key == "duplicate":
                    filter_parts.append(f"重复={count}")
                else:
                    filter_parts.append(f"{key}={count}")
            text += ", ".join(filter_parts)
        else:
            text += "无"
        
        text += f"\n- 理论可下载: {available}"
        
        if result.errors:
            text += f"\n\n⚠️ 错误: {len(result.errors)}个"
            for error in result.errors[:2]:  # 只显示前2个错误
                text += f"\n• {error}"
        
        text += f"\n\n💡 如需创建真实下载任务，可执行:\n`/music_sub_run {sub_id}`"
        
        # 更新消息
        await ctx.edit_message_text(text, reply_markup=build_back_to_menu_button())
        
    except Exception as e:
        logger.error(f"[telegram] music_sub_check failed: {e}")
        await ctx.reply_text("❌ 试运行失败，请稍后重试")


# ============== /music_sub_run ==============

@router.command("/music_sub_run")
async def cmd_music_sub_run(ctx: TelegramUpdateContext) -> None:
    """真实运行音乐订阅"""
    # 检查用户绑定
    if not await _ensure_user_bound(ctx):
        return
    
    # 解析参数
    if not ctx.args:
        await ctx.reply_text(
            "用法: `/music_sub_run 订阅ID`\n"
            "示例: `/music_sub_run 12`"
        )
        return
    
    try:
        sub_id = int(ctx.args.strip())
    except ValueError:
        await ctx.reply_text("❌ 订阅ID必须是数字")
        return
    
    try:
        # 获取订阅
        sub = await _get_music_subscription_by_id(ctx, sub_id)
        if not sub:
            await ctx.reply_text("❌ 找不到该订阅，可能不存在或不属于你")
            return
        
        # 检查订阅状态
        if sub.status != "active":
            await ctx.reply_text(
                f"⏸ 当前订阅 #{sub.id} 已暂停，如需自动下载请先使用:\n"
                f"`/music_sub_toggle {sub_id}`\n\n"
                f"然后再执行:\n"
                f"`/music_sub_run {sub_id}`"
            )
            return
        
        # 类型信息
        type_name = "榜单" if sub.subscription_type == MusicSubscriptionType.CHART else "关键字"
        
        # 目标信息
        if sub.subscription_type == MusicSubscriptionType.CHART and sub.chart_id:
            target = f"榜单 #{sub.chart_id}"
        elif sub.music_query:
            target = sub.music_query
        else:
            target = "未设置"
        
        # 安全策略
        security = format_music_security_policy(sub)
        
        # 发送处理中消息
        processing_msg = await ctx.reply_text("🔄 正在执行订阅...")
        
        # 执行真实运行
        result = await run_subscription_once(ctx.session, sub, auto_download=True)
        
        # 构建统计信息
        filtered_total = sum(result.filtered_out.values()) if result.filtered_out else 0
        
        # 构建结果文本
        text = f"✅ *订阅执行完成*\n\n"
        text += f"订阅: *#{sub.id}* [{type_name}] {target}\n"
        text += f"安全策略: {security}\n\n"
        text += f"📊 *本次统计:*\n"
        text += f"- 原始候选: {result.found_total}\n"
        text += f"- 过滤: "
        
        if result.filtered_out:
            filter_parts = []
            for key, count in result.filtered_out.items():
                if key == "hr":
                    filter_parts.append(f"HR={count}")
                elif key == "h3h5":
                    filter_parts.append(f"H3/H5={count}")
                elif key == "non_free":
                    filter_parts.append(f"非Free={count}")
                elif key == "duplicate":
                    filter_parts.append(f"重复={count}")
                else:
                    filter_parts.append(f"{key}={count}")
            text += ", ".join(filter_parts)
        else:
            text += "无"
        
        text += f"\n- 创建下载任务: {result.created_tasks}"
        
        if result.errors:
            text += f"\n\n⚠️ 错误: {len(result.errors)}个"
            for error in result.errors[:2]:  # 只显示前2个错误
                text += f"\n• {error}"
        
        if result.created_tasks > 0:
            text += f"\n\n💡 你可以在 Web 端的「下载任务」中查看详细进度。"
        
        # 更新消息
        await ctx.edit_message_text(text, reply_markup=build_back_to_menu_button())
        
        # 更新订阅运行时间
        from datetime import datetime
        sub.last_run_at = datetime.utcnow()
        if not result.errors:
            sub.last_success_at = datetime.utcnow()
            sub.last_error = None
        else:
            sub.last_error = "; ".join(result.errors[:1])  # 只保存第一个错误
        
        await ctx.session.commit()
        
    except Exception as e:
        logger.error(f"[telegram] music_sub_run failed: {e}")
        await ctx.reply_text("❌ 执行失败，请稍后重试")


# ============== /music_sub_toggle ==============

@router.command("/music_sub_toggle")
async def cmd_music_sub_toggle(ctx: TelegramUpdateContext) -> None:
    """切换音乐订阅状态"""
    # 检查用户绑定
    if not await _ensure_user_bound(ctx):
        return
    
    # 解析参数
    if not ctx.args:
        await ctx.reply_text(
            "用法: `/music_sub_toggle 订阅ID`\n"
            "示例: `/music_sub_toggle 12`"
        )
        return
    
    try:
        sub_id = int(ctx.args.strip())
    except ValueError:
        await ctx.reply_text("❌ 订阅ID必须是数字")
        return
    
    try:
        # 获取订阅
        sub = await _get_music_subscription_by_id(ctx, sub_id)
        if not sub:
            await ctx.reply_text("❌ 找不到该订阅，可能不存在或不属于你")
            return
        
        # 类型信息
        type_name = "榜单" if sub.subscription_type == MusicSubscriptionType.CHART else "关键字"
        
        # 目标信息
        if sub.subscription_type == MusicSubscriptionType.CHART and sub.chart_id:
            target = f"榜单 #{sub.chart_id}"
        elif sub.music_query:
            target = sub.music_query
        else:
            target = "未设置"
        
        # 切换状态
        old_status = sub.status
        sub.status = "paused" if sub.status == "active" else "active"
        
        # 保存变更
        await ctx.session.commit()
        
        # 构建结果文本
        new_status_name = "已激活" if sub.status == "active" else "已暂停"
        new_status_icon = "✅" if sub.status == "active" else "⏸"
        
        text = f"✅ *已切换订阅状态*\n\n"
        text += f"订阅: *#{sub.id}* [{type_name}] {target}\n"
        text += f"新状态: {new_status_icon} {new_status_name}\n\n"
        text += f"📝 *说明:*\n"
        text += f"- 激活时: 系统会根据你的设置自动参与音乐订阅执行\n"
        text += f"- 暂停时: 不会再自动执行，但你仍然可以用 `/music_sub_check {sub_id}` 试运行"
        
        await ctx.reply_text(text, reply_markup=build_back_to_menu_button())
        
    except Exception as e:
        logger.error(f"[telegram] music_sub_toggle failed: {e}")
        await ctx.reply_text("❌ 切换状态失败，请稍后重试")
