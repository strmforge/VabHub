"""
基础命令
BOT-TELEGRAM Phase 2

/start, /help, /ping, /settings
"""

from loguru import logger
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from app.modules.bots.telegram_router import router
from app.modules.bots.telegram_context import TelegramUpdateContext
from app.modules.bots.telegram_keyboard import build_main_menu_keyboard
from app.services import user_telegram_service
from app.services.home_dashboard_service import get_home_dashboard
from app.models.subscription import Subscription


# ============== 错误处理系统 ==============


def _format_error_message(error_type: str, details: str = "") -> str:
    """格式化统一的错误消息"""
    error_messages = {
        "not_bound": "❌ 请先绑定账号：/start 看说明",
        "invalid_args": "❌ 参数错误，请检查用法",
        "not_found": "❌ 资源不存在",
        "permission_denied": "❌ 权限不足，你只能操作自己的资源",
        "subscription_error": "❌ 订阅操作失败",
        "search_error": "❌ 搜索失败",
        "download_error": "❌ 下载操作失败",
        "system_error": "❌ 系统错误，请稍后重试",
        "tmdb_api_error": "❌ TMDB 搜索暂时不可用",
        "cache_expired": "❌ 搜索结果已过期",
        "no_cache": "❌ 没有找到搜索结果缓存",
        "index_out_of_range": "❌ 选择序号超出范围"
    }
    
    base_msg = error_messages.get(error_type, "❌ 未知错误")
    
    if details:
        return f"{base_msg}\n\n详情：{details}"
    return base_msg


def _format_usage_example(command: str, usage: str, example: str) -> str:
    """格式化用法示例"""
    return f"❌ 用法错误\n\n用法：{usage}\n\n示例：{example}"


# ============== 帮助文本 ==============

HELP_TEXT = """
*VabHub Telegram Bot* 🤖

*基础命令*
/menu - 打开主菜单
/help - 显示帮助信息
/ping - 检查 Bot 状态
/settings - 账号设置

*影视订阅*
/subs - 查看你的影视订阅
/sub_check <id> - 手动检查指定订阅
/sub_toggle <id> - 启用/停用订阅
/sub_search 关键字 - 搜索并创建订阅（安全模式）

*快速下载*
/dl_search 关键字 - 搜索并创建下载任务（安全模式）

*下载任务*
/downloads - 查看最近任务
/downloads failed - 只看失败任务
/downloads active - 进行中任务

*阅读中心*
/reading - 进行中的阅读
/recent - 最近活动

*音乐中心*
/music - 音乐中心入口
/charts - 音乐榜单

*其他功能*
/notify - 通知偏好设置
/search <关键词> - 搜索影视/漫画/音乐

*管理员命令* (仅限管理员)
/admin - 管理员命令帮助
"""

WELCOME_TEXT = """
你已绑定到账户：{username}

🎬 *影视订阅控制*
/subs - 查看你的影视订阅
/sub_check <id> - 手动检查订阅
/sub_search 关键字 - 搜索并创建订阅

⚡ *快速下载*
/dl_search 关键字 - 搜索并创建下载任务

📊 *系统状态*
/status - 系统整体状态
/downloads - 当前下载任务
/reading - 最近阅读/听书
/help - 查看完整帮助
"""

BIND_SUCCESS_TEXT = """
✅ *绑定成功！*

你的 VabHub 账号已成功绑定。

现在你可以：
• 接收通知推送
• 搜索和管理媒体
• 控制下载任务

点击下方按钮开始使用 👇
"""

UNBOUND_TEXT = """
欢迎使用 VabHub 机器人 👋

使用说明：
1️⃣ 请先在 Web 面板中打开「设置 → 通知渠道 → Telegram」
2️⃣ 生成一个绑定验证码（例如：123456）
3️⃣ 回到这里发送：/bind 123456 完成绑定

绑定完成后，你可以使用：
/status 查看系统状态
/downloads 查看当前下载
/reading 查看最近在读/在听
"""


# ============== /start ==============

@router.command("/start", require_bind=False)
async def cmd_start(ctx: TelegramUpdateContext) -> None:
    """处理 /start 命令"""
    code = ctx.args.strip()
    
    if not code:
        # 无绑定码，检查绑定状态
        binding = await user_telegram_service.get_binding_by_chat_id(ctx.session, ctx.chat_id)
        if binding:
            # 已绑定，显示欢迎 + 主菜单
            username = binding.telegram_username or f"用户#{binding.user_id}"
            welcome_msg = WELCOME_TEXT.format(username=username)
            await ctx.reply_text(welcome_msg, reply_markup=build_main_menu_keyboard())
        else:
            await ctx.reply_text(UNBOUND_TEXT)
        return
    
    # 白名单校验
    if not user_telegram_service.is_user_allowed(ctx.chat_id, ctx.username):
        await ctx.reply_text("❌ 抱歉，本 Bot 仅限授权用户使用")
        return
    
    # 尝试绑定
    binding = await user_telegram_service.bind_user_with_code(
        ctx.session,
        code=code,
        telegram_chat_id=ctx.chat_id,
        username=ctx.username,
        first_name=ctx.first_name,
        last_name=ctx.last_name,
        language_code=ctx.language_code,
    )
    
    if binding:
        logger.info(f"[telegram] user bound: chat_id={ctx.chat_id}")
        await ctx.reply_text(BIND_SUCCESS_TEXT, reply_markup=build_main_menu_keyboard())
    else:
        await ctx.reply_text("❌ 绑定失败：绑定码无效或已过期\n\n请重新获取绑定码")


# ============== /help ==============

@router.command("/help", require_bind=False)
async def cmd_help(ctx: TelegramUpdateContext) -> None:
    """显示帮助信息"""
    await ctx.reply_text(HELP_TEXT)


# ============== /ping ==============

@router.command("/ping", require_bind=False)
async def cmd_ping(ctx: TelegramUpdateContext) -> None:
    """健康检查"""
    status = "✅ 已绑定" if ctx.is_bound else "⚠️ 未绑定"
    await ctx.reply_text(f"🏓 *VabHub Bot* 运行正常！\n\n账号状态: {status}")


# ============== /status ==============

@router.command("/status")
async def cmd_status(ctx: TelegramUpdateContext) -> None:
    """显示系统状态概览"""
    if not ctx.is_bound or not ctx.app_user:
        await ctx.reply_text(_format_error_message("not_bound"))
        return
    
    try:
        # 获取Dashboard数据
        dashboard = await get_home_dashboard(ctx.app_user, ctx.session)
        
        # 格式化状态消息
        status_msg = f"""📊 VabHub 状态

下载任务：进行中 {dashboard.task_summary.running} / 今日完成 {dashboard.task_summary.completed_today} / 失败 {dashboard.task_summary.failed}
TTS 队列：等待 {dashboard.task_summary.tts_pending} / 进行中 {dashboard.task_summary.tts_running}
阅读活跃：小说 {dashboard.task_summary.reading_novel} / 有声书 {dashboard.task_summary.reading_audio} / 漫画 {dashboard.task_summary.reading_manga}
插件：启用 {dashboard.task_summary.plugin_active} / 隔离 {dashboard.task_summary.plugin_quarantined}"""
        
        await ctx.reply_text(status_msg)
        
    except Exception as e:
        logger.error(f"[telegram] failed to get status: {e}")
        await ctx.reply_text("暂时无法获取状态，请稍后再试")


# ============== /settings ==============

@router.command("/settings")
async def cmd_settings(ctx: TelegramUpdateContext) -> None:
    """账号设置"""
    from app.core.config import settings
    
    # 获取绑定信息
    binding = await user_telegram_service.get_binding_by_chat_id(ctx.session, ctx.chat_id)
    
    text = "*⚙️ 账号设置*\n\n"
    
    if binding:
        text += f"📱 *Telegram*: @{binding.telegram_username or '未设置'}\n"
        text += f"👤 *VabHub 用户*: {ctx.app_user.username if ctx.app_user else '未知'}\n"
        text += f"📅 *绑定时间*: {binding.created_at.strftime('%Y-%m-%d %H:%M')}\n"
    
    text += "\n更多设置请访问 VabHub 网页端。"
    
    # 构建按钮
    from app.modules.bots.telegram_keyboard import inline_keyboard, inline_button
    
    base_url = getattr(settings, "FRONTEND_URL", "")
    keyboard = inline_keyboard([
        [inline_button("🌐 打开网页设置", url=f"{base_url}/settings/notify-channels")] if base_url else [],
        [inline_button("« 返回主菜单", callback_data="menu:main")],
    ])
    
    await ctx.reply_text(text, reply_markup=keyboard)


# ============== TG-BOT-2 新命令占位符 ==============
# 这些命令将在后续P2-P5中实现具体功能

@router.command("/subs")
async def cmd_subs(ctx: TelegramUpdateContext) -> None:
    """查看影视订阅"""
    if not ctx.is_bound or not ctx.app_user:
        await ctx.reply_text(_format_error_message("not_bound"))
        return
    
    try:
        # 直接查询Subscription模型获取用户影视订阅
        from app.models.subscription import Subscription
        from sqlalchemy import select
        
        stmt = (
            select(Subscription)
            .where(Subscription.user_id == ctx.app_user.id)
            .where(Subscription.media_type.in_(["movie", "tv"]))  # 只显示影视订阅
            .order_by(Subscription.created_at.desc())
            .limit(10)
        )
        
        result = await ctx.session.execute(stmt)
        subscriptions = result.scalars().all()
        
        if not subscriptions:
            await ctx.reply_text(
                "📽️ 你还没有影视订阅\n\n"
                "💡 使用 /sub_search 关键字 来创建你的第一个订阅\n"
                "例如：/sub_search 沙丘2"
            )
            return
        
        # 格式化订阅列表
        text = "📽️ *你的影视订阅（最多显示 10 条）：*\n\n"
        
        for sub in subscriptions:
            # 基本信息
            media_type_text = "电影" if sub.media_type == "movie" else "美剧"
            status_text = "启用" if sub.status == "active" else "停用"
            
            text += f"#{sub.id} {media_type_text}《{sub.title}》 ({status_text})\n"
            
            # 站点信息
            if sub.sites:
                sites_text = ", ".join([str(site_id) for site_id in sub.sites[:3]])  # 最多显示3个
                if len(sub.sites) > 3:
                    sites_text += f" 等{len(sub.sites)}个"
                text += f"- 站点：{sites_text}\n"
            
            # 清晰度信息
            quality_parts = []
            if sub.quality:
                quality_parts.append(sub.quality)
            if sub.resolution:
                quality_parts.append(sub.resolution)
            if quality_parts:
                text += f"- 清晰度：{'-'.join(quality_parts)}\n"
            
            # 安全策略信息
            security_text = _format_security_policy(sub)
            text += f"- 安全策略：{security_text}\n"
            
            # 上次检查时间
            if sub.last_check_at:
                check_time = sub.last_check_at.strftime("%Y-%m-%d %H:%M")
                text += f"- 上次检查：{check_time}\n"
            
            text += "\n"
        
        # 添加操作提示
        text += "💡 *快速操作：*\n"
        text += "- /sub_check <id>  手动检查指定订阅\n"
        text += "- /sub_toggle <id>  启用/停用订阅\n"
        text += "- /sub_search 关键字  搜索并创建新订阅"
        
        await ctx.reply_text(text)
        
    except Exception as e:
        logger.error(f"[telegram] /subs command failed: {e}")
        await ctx.reply_text("❌ 获取订阅列表失败，请稍后重试")


def _format_security_policy(subscription: Subscription) -> str:
    """格式化安全策略为用户友好的中文描述"""
    if subscription.strict_free_only:
        return "安全模式（禁止 HR/H3/H5，只下载 Free）"
    elif subscription.allow_hr or subscription.allow_h3h5:
        risks = []
        if subscription.allow_hr:
            risks.append("HR")
        if subscription.allow_h3h5:
            risks.append("H3/H5")
        return f"允许风险（{', '.join(risks)}）"
    else:
        return "标准模式（禁止 HR/H3/H5，允许非 Free）"


@router.command("/sub_check")
async def cmd_sub_check(ctx: TelegramUpdateContext) -> None:
    """手动检查订阅"""
    if not ctx.is_bound or not ctx.app_user:
        await ctx.reply_text(_format_error_message("not_bound"))
        return
    
    # 解析订阅ID
    args = ctx.message_text.strip().split()
    if len(args) < 2:
        await ctx.reply_text(_format_usage_example(
            "/sub_check", 
            "/sub_check <订阅ID>", 
            "/sub_check 12"
        ))
        return
    
    try:
        subscription_id = int(args[1])
    except ValueError:
        await ctx.reply_text(_format_error_message("invalid_args", "订阅ID必须是数字"))
    
    try:
        # 查询订阅并检查权限
        stmt = select(Subscription).where(Subscription.id == subscription_id)
        result = await ctx.session.execute(stmt)
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            await ctx.reply_text(_format_error_message("not_found", f"订阅 #{subscription_id} 不存在"))
            return
        
        if subscription.user_id != ctx.app_user.id:
            await ctx.reply_text(_format_error_message("permission_denied"))
            return
        
        # 执行订阅检查（试运行模式）
        from app.runners.subscription_checker import run_single_subscription_check
        
        await ctx.reply_text(f"🔍 正在检查订阅 #{subscription_id}《{subscription.title}》...")
        
        check_result = await run_single_subscription_check(
            db=ctx.session,
            subscription_id=subscription_id,
            dry_run=True  # 试运行，不实际创建下载任务
        )
        
        # 格式化检查结果
        text = f"📊 *订阅 #{subscription_id}《{subscription.title}》检查结果：*\n\n"
        
        if check_result.succeeded_checks > 0:
            text += "✅ 检查成功\n\n"
            
            # 这里需要从实际的搜索结果中获取详细信息
            # 由于run_single_subscription_check返回的是批量结果，我们需要获取更详细的信息
            # 暂时使用简化的格式，后续可以优化
            text += f"- 候选总数：{check_result.checked_subscriptions}\n"
            text += f"- 将会创建下载任务：{check_result.created_tasks}\n"
            text += f"- 检查状态：{'成功' if check_result.succeeded_checks > 0 else '失败'}\n"
            
            # 显示安全策略信息
            security_text = _format_security_policy(subscription)
            text += f"- 安全策略：{security_text}\n"
            
        else:
            text += "❌ 检查失败\n\n"
            text += "可能的原因：\n"
            text += "- 网络连接问题\n"
            text += "- 站点访问异常\n"
            text += "- 搜索规则过于严格\n"
        
        text += "\n💡 *提示：*\n"
        text += "- 这次是「试运行」，并未实际创建任务\n"
        text += "- 如要真正创建任务，请等待定时任务自动执行\n"
        text += "- 或在 Web 端检查规则后手动触发"
        
        await ctx.reply_text(text)
        
    except Exception as e:
        logger.error(f"[telegram] /sub_check command failed: {e}")
        await ctx.reply_text(_format_error_message("subscription_error"))


@router.command("/sub_toggle")
async def cmd_sub_toggle(ctx: TelegramUpdateContext) -> None:
    """启用/停用订阅"""
    if not ctx.is_bound or not ctx.app_user:
        await ctx.reply_text(_format_error_message("not_bound"))
        return
    
    # 解析订阅ID
    args = ctx.message_text.strip().split()
    if len(args) < 2:
        await ctx.reply_text(_format_usage_example(
            "/sub_toggle", 
            "/sub_toggle <订阅ID>", 
            "/sub_toggle 12"
        ))
        return
    
    try:
        subscription_id = int(args[1])
    except ValueError:
        await ctx.reply_text(_format_error_message("invalid_args", "订阅ID必须是数字"))
        return
    
    try:
        # 查询订阅并检查权限
        stmt = select(Subscription).where(Subscription.id == subscription_id)
        result = await ctx.session.execute(stmt)
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            await ctx.reply_text(_format_error_message("not_found", f"订阅 #{subscription_id} 不存在"))
            return
        
        if subscription.user_id != ctx.app_user.id:
            await ctx.reply_text(_format_error_message("permission_denied"))
            return
        
        # 切换状态
        old_status = subscription.status
        if subscription.status == "active":
            subscription.status = "paused"
            new_status_text = "停用"
        elif subscription.status == "paused":
            subscription.status = "active"
            new_status_text = "启用"
        else:
            # 如果是其他状态（如completed），统一切换到active
            subscription.status = "active"
            new_status_text = "启用"
        
        # 保存到数据库
        await ctx.session.commit()
        
        # 格式化响应
        media_type_text = "电影" if subscription.media_type == "movie" else "美剧"
        
        text = f"✅ *订阅状态更新成功*\n\n"
        text += f"#{subscription_id} {media_type_text}《{subscription.title}》\n"
        text += f"状态已切换为：【{new_status_text}】"
        
        await ctx.reply_text(text)
        
    except Exception as e:
        logger.error(f"[telegram] /sub_toggle command failed: {e}")
        await ctx.reply_text(_format_error_message("subscription_error"))


@router.command("/sub_search")
async def cmd_sub_search(ctx: TelegramUpdateContext) -> None:
    """搜索并创建订阅（支持TMDB ID和关键词双模式）"""
    if not ctx.is_bound or not ctx.app_user:
        await ctx.reply_text(_format_error_message("not_bound"))
        return
    
    # 解析搜索关键词
    args = ctx.message_text.strip().split(maxsplit=1)
    if len(args) < 2:
        await ctx.reply_text(
            "❌ 用法错误\n\n"
            "用法1：/sub_search 沙丘2      # 关键词搜索 TMDB\n"
            "用法2：/sub_search 123456     # 使用 TMDB ID 直接创建订阅\n\n"
            "示例：\n"
            "/sub_search 沙丘2  # 搜索并显示结果列表\n"
            "/sub_search 123456  # 直接创建订阅"
        )
        return
    
    query = args[1].strip()
    
    try:
        # 判断是TMDB ID还是关键词搜索
        if query.isdigit():
            # TMDB ID模式：直接创建订阅（兼容旧行为）
            tmdb_id = int(query)
            await _create_subscription_from_tmdb_id_with_details(ctx, tmdb_id)
        else:
            # 关键词搜索模式：调用TMDB API搜索
            await _handle_keyword_search(ctx, query)
            
    except Exception as e:
        logger.error(f"[telegram] /sub_search command failed: {e}")
        await ctx.reply_text(_format_error_message("search_error"))


async def _handle_keyword_search(ctx: TelegramUpdateContext, query: str) -> None:
    """处理关键词搜索"""
    from app.services.tmdb_search_service import search_tmdb
    from app.modules.bots.telegram_bot_state import tmdb_search_cache
    
    await ctx.reply_text(f"🔍 正在搜索 TMDB：{query}")
    
    try:
        # 调用TMDB搜索服务
        search_results = await search_tmdb(
            query=query,
            media_type="multi",
            limit=5
        )
        
        if not search_results:
            await ctx.reply_text(
                "❌ 未找到匹配的影视内容\n\n"
                "建议：\n"
                "• 尝试使用更精确的关键词\n"
                "• 或使用 TMDB ID 直接创建：/sub_search 123456\n\n"
                "示例：/sub_search 沙丘2"
            )
            return
        
        # 缓存搜索结果
        tmdb_search_cache.set_results(
            tg_user_id=ctx.update.effective_user.id,
            user_id=ctx.app_user.id,
            items=search_results
        )
        
        # 格式化搜索结果
        text = f"📺 *找到 {len(search_results)} 个 TMDB 结果：*\n\n"
        
        for i, item in enumerate(search_results, 1):
            media_type_text = "电影" if item.media_type == "movie" else "剧集"
            year_text = f" ({item.year})" if item.year else ""
            original_title_text = f"\n    原名：{item.original_title}" if item.original_title and item.original_title != item.title else ""
            overview_text = f"\n    {item.overview}" if item.overview else ""
            
            text += f"[{i}] {media_type_text}《{item.title}》{year_text}{original_title_text}{overview_text}\n\n"
        
        text += "💡 *创建订阅：*\n"
        text += f"/sub_create 1  # 以第 1 条结果创建订阅（安全模式）\n"
        text += f"/sub_create 2  # 以第 2 条结果创建订阅\n"
        text += "...\n\n"
        text += "⏰ 搜索结果缓存 10 分钟，请及时选择"
        
        await ctx.reply_text(text)
        
    except ValueError as e:
        # TMDB API key未配置
        logger.error(f"[telegram] TMDB API key not configured: {e}")
        await ctx.reply_text(
            "❌ TMDB API 未配置\n\n"
            "请联系管理员配置 TMDB_API_KEY\n\n"
            "临时解决方案：\n"
            "• 使用 TMDB ID 直接创建：/sub_search 123456\n"
            "• 在 Web 端手动添加订阅"
        )
    except Exception as e:
        logger.error(f"[telegram] TMDB search failed for query '{query}': {e}")
        await ctx.reply_text(
            _format_error_message("tmdb_api_error", 
                "TMDB 搜索暂时不可用，请稍后再试\n\n"
                "或者：\n"
                "• 使用 TMDB ID 直接创建：/sub_search 123456\n"
                "• 在 Web 端手动添加订阅"
            )
        )




@router.command("/sub_create")
async def cmd_sub_create(ctx: TelegramUpdateContext) -> None:
    """创建订阅（支持index选择和TMDB ID双模式）"""
    if not ctx.is_bound or not ctx.app_user:
        await ctx.reply_text(_format_error_message("not_bound"))
        return
    
    # 解析参数
    args = ctx.message_text.strip().split(maxsplit=1)
    if len(args) < 2:
        await ctx.reply_text(
            "❌ 用法错误\n\n"
            "用法1：/sub_create 1           # 使用最近一次搜索结果中的第 1 条\n"
            "用法2：/sub_create 123456      # 直接用 TMDB ID 123456 创建订阅\n\n"
            "💡 搜索结果缓存 10 分钟，请及时选择"
        )
        return
    
    token = args[1].strip()
    
    # 验证输入必须是数字
    if not token.isdigit():
        await ctx.reply_text(_format_error_message("invalid_args", "必须是数字"))
        return
    
    try:
        value = int(token)
        
        # 尝试index模式（优先）
        from app.modules.bots.telegram_bot_state import tmdb_search_cache
        
        cached_state = tmdb_search_cache.get_results(ctx.update.effective_user.id)
        
        if cached_state and 1 <= value <= len(cached_state.items):
            # index模式：从缓存获取真实TMDB数据
            await _create_subscription_from_cached_item(ctx, cached_state.items[value - 1])
        else:
            # 检查是否有缓存但index超出范围
            if cached_state and value > len(cached_state.items):
                await ctx.reply_text(
                    f"❌ 索引超出范围\n\n"
                    f"最近搜索结果只有 {len(cached_state.items)} 条\n"
                    f"请选择 1-{len(cached_state.items)} 之间的数字\n\n"
                    f"💡 如果你想使用 TMDB ID {value}，请使用：/sub_search {value}"
                )
                return
            
            # tmdb_id模式：直接使用TMDB ID
            await _create_subscription_from_tmdb_id_with_details(ctx, value)
            
    except Exception as e:
        logger.error(f"[telegram] /sub_create command failed: {e}")
        await ctx.reply_text(_format_error_message("subscription_error"))


async def _create_subscription_from_cached_item(ctx: TelegramUpdateContext, item) -> None:
    """从缓存的TMDB项目创建订阅"""
    try:
        # 使用真实的TMDB数据
        subscription_data = {
            "title": item.title,
            "media_type": item.media_type,
            "tmdb_id": item.tmdb_id,
            "year": item.year,
            "poster": None,
            "backdrop": None,
            
            # 默认设置
            "quality": "1080p",
            "resolution": "2160p,1080p",
            "sites": [],  # 使用所有可用站点
            "downloader": "default",
            "min_seeders": 5,
            "auto_download": True,
            
            # VIDEO-AUTOLOOP-1 安全策略（默认安全模式）
            "allow_hr": False,
            "allow_h3h5": False,
            "strict_free_only": True
        }
        
        # 调用订阅服务创建订阅
        from app.modules.subscription.service import SubscriptionService
        subscription_service = SubscriptionService(ctx.session)
        
        new_subscription = await subscription_service.create_subscription(subscription_data)
        
        # 设置用户ID
        new_subscription.user_id = ctx.app_user.id
        await ctx.session.commit()
        
        # 格式化成功响应
        media_type_text = "电影" if item.media_type == "movie" else "剧集"
        year_text = f" ({item.year})" if item.year else ""
        
        text = f"✅ *订阅创建成功*\n\n"
        text += f"订阅ID：#{new_subscription.id}\n"
        text += f"目标：{media_type_text}《{item.title}》{year_text}\n"
        text += f"TMDB ID：{item.tmdb_id}\n"
        text += f"清晰度：{new_subscription.resolution or '1080p'}\n"
        text += f"安全策略：安全模式（只下载 Free 资源）\n\n"
        text += "💡 你可以在 Web → 影视订阅中心 中查看并调整详细规则"
        
        await ctx.reply_text(text)
        
    except Exception as e:
        logger.error(f"[telegram] create subscription from cached item failed: {e}")
        await ctx.reply_text(_format_error_message("subscription_error"))


async def _create_subscription_from_tmdb_id_with_details(ctx: TelegramUpdateContext, tmdb_id: int) -> None:
    """使用TMDB ID创建订阅（获取真实详情）"""
    try:
        # 尝试获取TMDB详细信息
        from app.services.tmdb_search_service import get_tmdb_details
        
        # 先尝试movie类型，如果失败再尝试tv类型
        details = await get_tmdb_details(tmdb_id, "movie")
        media_type = "movie"
        
        if not details or not details.get("title"):
            # 如果movie失败，尝试tv
            details = await get_tmdb_details(tmdb_id, "tv")
            media_type = "tv"
        
        if details and (details.get("title") or details.get("name")):
            # 使用真实TMDB数据
            title = details.get("title") if media_type == "movie" else details.get("name")
            release_date = details.get("release_date") if media_type == "movie" else details.get("first_air_date")
            year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None
            
            subscription_data = {
                "title": title,
                "media_type": media_type,
                "tmdb_id": tmdb_id,
                "year": year,
                "poster": None,
                "backdrop": None,
                
                # 默认设置
                "quality": "1080p",
                "resolution": "2160p,1080p",
                "sites": [],
                "downloader": "default",
                "min_seeders": 5,
                "auto_download": True,
                
                # 安全策略
                "allow_hr": False,
                "allow_h3h5": False,
                "strict_free_only": True
            }
        else:
            # TMDB API失败，使用mock数据fallback
            subscription_data = {
                "title": f"TMDB-{tmdb_id} 影片",
                "media_type": "movie",
                "tmdb_id": tmdb_id,
                "year": 2024,
                "poster": None,
                "backdrop": None,
                
                # 默认设置
                "quality": "1080p",
                "resolution": "2160p,1080p",
                "sites": [],
                "downloader": "default",
                "min_seeders": 5,
                "auto_download": True,
                
                # 安全策略
                "allow_hr": False,
                "allow_h3h5": False,
                "strict_free_only": True
            }
            
            # 创建订阅
            from app.modules.subscription.service import SubscriptionService
            subscription_service = SubscriptionService(ctx.session)
            
            new_subscription = await subscription_service.create_subscription(subscription_data)
            new_subscription.user_id = ctx.app_user.id
            await ctx.session.commit()
            
            # 格式化响应
            text = f"✅ *订阅创建成功*\n\n"
            text += f"订阅ID：#{new_subscription.id}\n"
            text += f"目标：{new_subscription.title}\n"
            text += f"TMDB ID：{tmdb_id}\n"
            text += f"清晰度：{new_subscription.resolution or '1080p'}\n"
            text += f"安全策略：安全模式（只下载 Free 资源）\n\n"
            text += "💡 你可以在 Web → 影视订阅中心 中查看并调整详细规则"
            
            await ctx.reply_text(text)
            return
        
        # 创建订阅
        from app.modules.subscription.service import SubscriptionService
        subscription_service = SubscriptionService(ctx.session)
        
        new_subscription = await subscription_service.create_subscription(subscription_data)
        new_subscription.user_id = ctx.app_user.id
        await ctx.session.commit()
        
        # 格式化响应
        media_type_text = "电影" if media_type == "movie" else "剧集"
        year_text = f" ({year})" if year else ""
        
        text = f"✅ *订阅创建成功*\n\n"
        text += f"订阅ID：#{new_subscription.id}\n"
        text += f"目标：{media_type_text}《{title}》{year_text}\n"
        text += f"TMDB ID：{tmdb_id}\n"
        text += f"清晰度：{new_subscription.resolution or '1080p'}\n"
        text += f"安全策略：安全模式（只下载 Free 资源）\n\n"
        text += "💡 你可以在 Web → 影视订阅中心 中查看并调整详细规则"
        
        await ctx.reply_text(text)
        
    except Exception as e:
        logger.error(f"[telegram] create subscription from tmdb_id with details failed: {e}")
        # 如果获取详情失败，使用mock数据fallback
        subscription_data = {
            "title": f"TMDB-{tmdb_id} 影片",
            "media_type": "movie",
            "tmdb_id": tmdb_id,
            "year": 2024,
            "poster": None,
            "backdrop": None,
            
            # 默认设置
            "quality": "1080p",
            "resolution": "2160p,1080p",
            "sites": [],
            "downloader": "default",
            "min_seeders": 5,
            "auto_download": True,
            
            # 安全策略
            "allow_hr": False,
            "allow_h3h5": False,
            "strict_free_only": True
        }
        
        # 创建订阅
        from app.modules.subscription.service import SubscriptionService
        subscription_service = SubscriptionService(ctx.session)
        
        new_subscription = await subscription_service.create_subscription(subscription_data)
        new_subscription.user_id = ctx.app_user.id
        await ctx.session.commit()
        
        # 格式化响应
        text = f"✅ *订阅创建成功*\n\n"
        text += f"订阅ID：#{new_subscription.id}\n"
        text += f"目标：{new_subscription.title}\n"
        text += f"TMDB ID：{tmdb_id}\n"
        text += f"清晰度：{new_subscription.resolution or '1080p'}\n"
        text += f"安全策略：安全模式（只下载 Free 资源）\n\n"
        text += "💡 你可以在 Web → 影视订阅中心 中查看并调整详细规则"
        
        await ctx.reply_text(text)


@router.command("/dl_search")
async def cmd_dl_search(ctx: TelegramUpdateContext) -> None:
    """快速下载搜索（占位符）"""
    if not ctx.is_bound or not ctx.app_user:
        await ctx.reply_text(_format_error_message("not_bound"))
        return
    
    # 解析搜索关键词
    args = ctx.message_text.strip().split(maxsplit=1)
    if len(args) < 2:
        await ctx.reply_text(
            "❌ 用法错误\n\n"
            "用法：/dl_search <搜索关键词>\n\n"
            "示例：/dl_search 沙丘2"
        )
        return
    
    query = args[1].strip()
    
    # 简化实现：引导用户使用Web界面
    text = f"🔍 *快速下载功能*\n\n"
    text += f"搜索关键词：{query}\n\n"
    text += "⚠️ *此功能正在开发中*\n\n"
    text += "目前建议使用以下方式：\n\n"
    text += "🌐 **Web界面**（推荐）\n"
    text += "1. 访问 VabHub Web 端\n"
    text += "2. 进入「下载中心」\n"
    text += "3. 使用高级搜索功能\n"
    text += "4. 一键创建下载任务\n\n"
    text += "📱 **Telegram订阅**\n"
    text += f"使用 /sub_search {query} 创建订阅，系统会自动下载\n\n"
    text += "💡 快速下载功能将在后续版本中完善，敬请期待！"
    
    await ctx.reply_text(text)


@router.command("/dl_create")
async def cmd_dl_create(ctx: TelegramUpdateContext) -> None:
    """创建下载任务（占位符）"""
    if not ctx.is_bound or not ctx.app_user:
        await ctx.reply_text(_format_error_message("not_bound"))
        return
    
    # 解析参数
    args = ctx.message_text.strip().split(maxsplit=1)
    if len(args) < 2:
        await ctx.reply_text(
            "❌ 用法错误\n\n"
            "用法：/dl_create <搜索结果索引>\n\n"
            "示例：/dl_create 1\n\n"
            "💡 此命令需要先使用 /dl_search 搜索"
        )
        return
    
    try:
        index = int(args[1].strip())
    except ValueError:
        await ctx.reply_text("❌ 索引必须是数字\n\n例如：/dl_create 1")
        return
    
    # 简化实现：引导用户使用Web界面
    text = f"⚡ *创建下载任务*\n\n"
    text += f"选择索引：{index}\n\n"
    text += "⚠️ *此功能正在开发中*\n\n"
    text += "目前建议使用以下方式：\n\n"
    text += "🌐 **Web界面**（推荐）\n"
    text += "1. 访问 VabHub Web 端\n"
    text += "2. 进入「下载中心」\n"
    text += "3. 搜索并选择资源\n"
    text += "4. 一键创建下载任务\n\n"
    text += "📱 **Telegram订阅**\n"
    text += "使用 /sub_search <TMDB_ID> 创建订阅，系统会自动下载\n\n"
    text += "💡 快速下载功能将在后续版本中完善，敬请期待！"
    
    await ctx.reply_text(text)
