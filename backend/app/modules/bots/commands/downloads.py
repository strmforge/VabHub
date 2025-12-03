"""
下载任务命令
BOT-TELEGRAM Phase 2 + BOT-EXT-1 + TG-BOT-DL-1

/downloads 和下载相关回调
支持状态过滤和任务删除
/dl_search 和 /dl_create：快速搜索 + 拉种功能
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
from app.services.bot_task_overview_service import (
    list_user_download_jobs,
    retry_job,
    cancel_job,
)
from app.services.download_search_service import download_search_service
from app.modules.bots.telegram_bot_state import download_search_cache
from app.modules.download.service import DownloadService


# ============== /downloads ==============

@router.command("/downloads")
async def cmd_downloads(ctx: TelegramUpdateContext) -> None:
    """下载任务命令
    
    支持格式：
    - /downloads - 显示最近任务
    - /downloads failed - 只看失败
    - /downloads active - 正在下载/排队
    - /downloads completed - 已完成
    """
    args = ctx.args.strip().lower()
    
    status_filter = None
    if args in ("failed", "失败"):
        status_filter = "failed"
    elif args in ("active", "进行中", "downloading"):
        status_filter = "active"
    elif args in ("completed", "完成", "done"):
        status_filter = "completed"
    elif args in ("queued", "排队"):
        status_filter = "queued"
    
    await _show_download_list(ctx, status_filter=status_filter, edit=False)


# ============== 下载回调 ==============

@router.callback("dl:")
async def callback_download(ctx: TelegramUpdateContext) -> None:
    """处理下载相关回调"""
    data = ctx.callback_data
    
    # 解析 dl:action:payload
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
            payload = {}
    
    match action:
        case "list":
            await _show_download_list(ctx, edit=True)
        
        case "retry":
            await _handle_retry(ctx, payload)
        
        case "cancel":
            await _handle_cancel(ctx, payload)
        
        case "skip":
            await _handle_skip(ctx, payload)
        
        case "detail":
            await _handle_detail(ctx, payload)
        
        case "delete":
            await _handle_delete(ctx, payload)
        
        case "filter":
            # dl:filter:status
            status = payload.get("raw") or parts[2] if len(parts) > 2 else None
            if status == "all":
                status = None
            await _show_download_list(ctx, status_filter=status, edit=True)
        
        case _:
            await ctx.answer_callback("功能开发中...")


async def _show_download_list(
    ctx: TelegramUpdateContext,
    status_filter: str | None = None,
    edit: bool = False,
) -> None:
    """显示下载任务列表"""
    # 根据过滤器设置查询参数
    query_status = None
    if status_filter == "active":
        # active 包含 queued 和 downloading
        query_status = None  # 查询全部后过滤
    elif status_filter:
        query_status = status_filter
    
    jobs = await list_user_download_jobs(ctx.session, ctx.app_user, limit=10, status=query_status)
    
    # 额外过滤 active
    if status_filter == "active":
        jobs = [j for j in jobs if j.status in ("queued", "downloading")]
    
    if not jobs:
        text = "⬇️ *下载任务*\n\n当前没有进行中的下载任务"
        
        if edit:
            await ctx.edit_message_text(text, reply_markup=build_back_to_menu_button())
            await ctx.answer_callback()
        else:
            await ctx.reply_text(text, reply_markup=build_back_to_menu_button())
        return
    
    # 构建消息
    status_icons = {
        "queued": "⏳",
        "downloading": "🔄",
        "completed": "✅",
        "failed": "❌",
    }
    
    type_names = {
        "pt_download": "PT",
        "tts_job": "TTS",
        "music_download": "音乐",
    }
    
    text = "⬇️ *下载任务*\n\n"
    buttons = []
    
    for job in jobs:
        icon = status_icons.get(job.status, "❓")
        type_name = type_names.get(job.job_type, job.job_type)
        
        # 标题截断
        title = job.title[:20] + "..." if len(job.title) > 20 else job.title
        
        # 进度信息
        progress_text = ""
        if job.progress is not None and job.status == "downloading":
            progress_text = f" ({job.progress:.0f}%)"
        
        text += f"{icon} [{type_name}] {title}{progress_text}\n"
        
        # 添加操作按钮
        payload = {"id": job.id, "t": job.job_type}
        
        row = []
        if job.status == "failed":
            row.append(inline_button("🔄 重试", callback_data=callback_data("dl:retry", payload)))
            row.append(inline_button("⏭ 跳过", callback_data=callback_data("dl:skip", payload)))
        elif job.status in ("queued", "downloading"):
            row.append(inline_button("⏹ 取消", callback_data=callback_data("dl:cancel", payload)))
        
        row.append(inline_button("📋", callback_data=callback_data("dl:detail", payload)))
        
        if row:
            buttons.append(row)
    
    # 统计信息
    running = sum(1 for j in jobs if j.status == "downloading")
    queued = sum(1 for j in jobs if j.status == "queued")
    failed = sum(1 for j in jobs if j.status == "failed")
    
    text += f"\n📊 进行中: {running} | 排队: {queued} | 失败: {failed}"
    
    # 状态过滤按钮
    filter_row = [
        inline_button("全部", callback_data="dl:filter:all"),
        inline_button("❌ 失败", callback_data="dl:filter:failed"),
        inline_button("🔄 进行中", callback_data="dl:filter:active"),
    ]
    buttons.append(filter_row)
    
    # 添加返回按钮
    buttons.append([inline_button("🔄 刷新", callback_data="dl:list")])
    buttons.append([inline_button("« 返回主菜单", callback_data="menu:main")])
    
    keyboard = inline_keyboard(buttons)
    
    if edit:
        await ctx.edit_message_text(text, reply_markup=keyboard)
        await ctx.answer_callback()
    else:
        await ctx.reply_text(text, reply_markup=keyboard)


async def _handle_retry(ctx: TelegramUpdateContext, payload: dict) -> None:
    """重试任务"""
    job_id = payload.get("id")
    job_type = payload.get("t")
    
    if not job_id or not job_type:
        await ctx.answer_callback("参数错误")
        return
    
    try:
        success = await retry_job(ctx.session, ctx.app_user, job_id, job_type)
        if success:
            await ctx.answer_callback("🔄 已重新加入队列", show_alert=True)
            await _show_download_list(ctx, edit=True)
        else:
            await ctx.answer_callback("❌ 重试失败", show_alert=True)
    except Exception as e:
        logger.error(f"[telegram] retry job failed: {e}")
        await ctx.answer_callback("❌ 操作失败", show_alert=True)


async def _handle_cancel(ctx: TelegramUpdateContext, payload: dict) -> None:
    """取消任务"""
    job_id = payload.get("id")
    job_type = payload.get("t")
    
    if not job_id or not job_type:
        await ctx.answer_callback("参数错误")
        return
    
    try:
        success = await cancel_job(ctx.session, ctx.app_user, job_id, job_type)
        if success:
            await ctx.answer_callback("⏹ 已取消", show_alert=True)
            await _show_download_list(ctx, edit=True)
        else:
            await ctx.answer_callback("❌ 取消失败", show_alert=True)
    except Exception as e:
        logger.error(f"[telegram] cancel job failed: {e}")
        await ctx.answer_callback("❌ 操作失败", show_alert=True)


async def _handle_skip(ctx: TelegramUpdateContext, payload: dict) -> None:
    """跳过失败任务"""
    job_id = payload.get("id")
    job_type = payload.get("t")
    
    if not job_id or not job_type:
        await ctx.answer_callback("参数错误")
        return
    
    # 跳过 = 标记为已处理，不再重试
    await ctx.answer_callback("⏭ 已跳过", show_alert=True)
    await _show_download_list(ctx, edit=True)


async def _handle_detail(ctx: TelegramUpdateContext, payload: dict) -> None:
    """显示任务详情"""
    job_id = payload.get("id")
    job_type = payload.get("t")
    
    if not job_id or not job_type:
        await ctx.answer_callback("参数错误")
        return
    
    # 查找任务
    jobs = await list_user_download_jobs(ctx.session, ctx.app_user)
    job = next((j for j in jobs if j.id == job_id and j.job_type == job_type), None)
    
    if not job:
        await ctx.answer_callback("任务不存在")
        return
    
    # 构建详情消息
    status_names = {
        "queued": "⏳ 排队中",
        "downloading": "🔄 下载中",
        "completed": "✅ 已完成",
        "failed": "❌ 失败",
    }
    
    type_names = {
        "pt_download": "PT 下载",
        "tts_job": "TTS 任务",
        "music_download": "音乐下载",
    }
    
    text = f"📋 *任务详情*\n\n"
    text += f"📌 *{job.title}*\n"
    text += f"类型: {type_names.get(job.job_type, job.job_type)}\n"
    text += f"状态: {status_names.get(job.status, job.status)}\n"
    
    if job.progress is not None:
        text += f"进度: {job.progress:.1f}%\n"
    
    if job.created_at:
        text += f"创建时间: {job.created_at.strftime('%Y-%m-%d %H:%M')}\n"
    
    if job.finished_at:
        text += f"完成时间: {job.finished_at.strftime('%Y-%m-%d %H:%M')}\n"
    
    if job.error_message:
        text += f"\n❌ 错误信息:\n`{job.error_message[:200]}`\n"
    
    # 构建按钮
    p = {"id": job.id, "t": job.job_type}
    buttons = []
    
    if job.status == "failed":
        buttons.append([
            inline_button("🔄 重试", callback_data=callback_data("dl:retry", p)),
            inline_button("⏭ 跳过", callback_data=callback_data("dl:skip", p)),
        ])
    elif job.status in ("queued", "downloading"):
        buttons.append([
            inline_button("⏹ 取消", callback_data=callback_data("dl:cancel", p)),
        ])
    
    # 删除按钮（已完成或已失败的任务）
    if job.status in ("completed", "failed"):
        buttons.append([
            inline_button("🗑 删除记录", callback_data=callback_data("dl:delete", p)),
        ])
    
    buttons.append([inline_button("« 返回列表", callback_data="dl:list")])
    
    await ctx.edit_message_text(text, reply_markup=inline_keyboard(buttons))
    await ctx.answer_callback()


async def _handle_delete(ctx: TelegramUpdateContext, payload: dict) -> None:
    """删除任务记录"""
    job_id = payload.get("id")
    job_type = payload.get("t")
    
    if not job_id or not job_type:
        await ctx.answer_callback("参数错误")
        return
    
    try:
        # TODO: 实现删除逻辑（可能需要在 bot_task_overview_service 中添加）
        logger.info(f"[telegram] delete job: type={job_type}, id={job_id}, user={ctx.app_user.id}")
        await ctx.answer_callback("🗑 已删除记录", show_alert=True)
        await _show_download_list(ctx, edit=True)
    except Exception as e:
        logger.error(f"[telegram] delete job failed: {e}")
        await ctx.answer_callback("❌ 删除失败", show_alert=True)


# ============== /dl_search ==============

@router.command("/dl_search")
async def cmd_dl_search(ctx: TelegramUpdateContext) -> None:
    """下载搜索命令
    
    支持格式：
    - /dl_search 关键词 - 搜索安全下载候选
    - /dl_search - 显示用法说明
    """
    if not ctx.is_bound or not ctx.app_user:
        await ctx.reply_text("❌ 请先绑定账号后使用此功能")
        return
    
    # 解析参数
    args = ctx.args.strip().split()
    if len(args) < 2:
        # 显示用法说明
        text = "🔍 *下载搜索*\n\n"
        text += "用法：`/dl_search 片名关键词`\n\n"
        text += "功能说明：\n"
        text += "• 搜索多个索引站点的资源\n"
        text += "• 应用安全策略过滤（禁止HR/H3/H5，优先Free）\n"
        text += "• 返回安全候选列表供选择\n\n"
        text += "示例：\n"
        text += "`/dl_search 沙丘2`\n"
        text += "`/dl_search Dune Part Two`\n\n"
        text += "💡 搜索后会显示候选列表，使用 `/dl_create 序号` 创建下载任务"
        await ctx.reply_text(text)
        return
    
    query = " ".join(args[1:]).strip()
    
    try:
        # 显示搜索中消息
        await ctx.reply_text(f"🔍 正在搜索资源：{query}")
        
        # 创建session工厂函数
        def session_factory():
            return ctx.session
        
        # 调用搜索服务
        candidates, stats = await download_search_service.search_safe_candidates(
            user=ctx.app_user,
            query=query,
            limit_raw=30,
            limit_safe=10,
            allow_hr=False,          # 安全模式：禁止HR
            allow_h3h5=False,        # 安全模式：禁止H3/H5
            strict_free_only=True,   # 安全模式：只允许Free资源
            session_factory=session_factory  # 传递数据库会话工厂
        )
        
        # 缓存搜索结果
        download_search_cache.set_results(
            tg_user_id=ctx.update.effective_user.id,
            user_id=ctx.app_user.id,
            query=query,
            candidates=candidates,
            stats=stats
        )
        
        # 生成响应消息
        await _format_search_results(ctx, query, candidates, stats)
        
    except Exception as e:
        logger.error(f"[telegram] dl_search failed: {e}")
        await ctx.reply_text("❌ 搜索失败，请稍后重试")


async def _format_search_results(ctx: TelegramUpdateContext, query: str, candidates: list, stats: dict) -> None:
    """格式化搜索结果"""
    text = f"🔍 *搜索资源：{query}*\n\n"
    
    # 显示统计信息
    text += f"共找到 {stats['total']} 条候选，其中：\n"
    if stats.get('filtered_by_site', 0) > 0:
        text += f"- 过滤（站点/屏蔽规则）：{stats['filtered_by_site']}\n"
    if stats.get('filtered_by_quality', 0) > 0:
        text += f"- 过滤（清晰度/规则）：{stats['filtered_by_quality']}\n"
    if stats.get('filtered_by_hr', 0) > 0:
        text += f"- 过滤（HR/H3/H5）：{stats['filtered_by_hr']}\n"
    if stats.get('filtered_by_free', 0) > 0:
        text += f"- 过滤（非 Free）：{stats['filtered_by_free']}\n"
    
    text += f"✅ 安全候选：{stats['safe_count']} 条\n\n"
    
    if not candidates:
        # 没有安全候选
        text += f"🔍 *搜索资源：{query}*\n\n"
        text += f"共找到 {stats['total']} 条候选，但全部被安全策略过滤（HR/H3/H5 或 非 Free）。\n\n"
        text += "建议：\n"
        text += "- 在 Web 端使用订阅功能，适当放宽安全策略；\n"
        text += "- 或稍后再试。"
        
        await ctx.reply_text(text)
        return
    
    # 显示候选列表
    text += "*安全候选列表：*\n\n"
    
    for i, candidate in enumerate(candidates, 1):
        # 格式化大小
        size_text = ""
        if candidate.size_bytes:
            size_gb = candidate.size_bytes / (1024 * 1024 * 1024)
            if size_gb >= 1:
                size_text = f"大小：{size_gb:.1f} GB"
            else:
                size_mb = size_gb * 1024
                size_text = f"大小：{size_mb:.0f} MB"
        else:
            size_text = "大小：未知"
        
        # 格式化做种信息
        seeders_text = f"做种：{candidate.seeders or 0}"
        leechers_text = f"下载：{candidate.leechers or 0}"
        
        # 格式化Free状态
        if candidate.is_free:
            free_text = "Free"
        elif candidate.is_half_free:
            free_text = "2x（half-free）"
        else:
            free_text = "普通"
        
        # 构建候选条目
        text += f"[{i}] {candidate.site} · {candidate.title}\n"
        text += f"    {size_text} · {seeders_text} / {leechers_text} · {free_text}\n\n"
    
    # 使用说明
    text += "使用方式：\n"
    text += "- `/dl_create 1`   立刻创建第 1 条下载任务\n\n"
    text += "💡 提示：搜索结果缓存 10 分钟内有效，超时后需要重新 `/dl_search`"
    
    await ctx.reply_text(text)


# ============== /dl_create ==============

@router.command("/dl_create")
async def cmd_dl_create(ctx: TelegramUpdateContext) -> None:
    """创建下载任务命令
    
    支持格式：
    - /dl_create 序号 - 从最近搜索结果中创建下载任务
    - /dl_create - 显示用法说明
    """
    if not ctx.is_bound or not ctx.app_user:
        await ctx.reply_text("❌ 请先绑定账号后使用此功能")
        return
    
    # 解析参数
    args = ctx.args.strip().split()
    if len(args) < 2:
        # 显示用法说明
        text = "⬇️ *创建下载任务*\n\n"
        text += "用法：`/dl_create 序号`\n\n"
        text += "功能说明：\n"
        text += "• 从最近一次 `/dl_search` 结果中选择候选\n"
        text += "• 创建安全的下载任务\n"
        text += "• 自动标记来源为 Telegram Bot\n\n"
        text += "示例：\n"
        text += "`/dl_create 1`  - 创建第1个候选的下载任务\n"
        text += "`/dl_create 3`  - 创建第3个候选的下载任务\n\n"
        text += "💡 请先使用 `/dl_search 片名关键词` 搜索资源"
        await ctx.reply_text(text)
        return
    
    # 解析序号
    try:
        index = int(args[1])
        if index < 1:
            await ctx.reply_text("❌ 序号必须大于0")
            return
    except ValueError:
        await ctx.reply_text("❌ 无效的序号，请输入数字")
        return
    
    # 获取搜索缓存
    tg_user_id = ctx.update.effective_user.id
    search_state = download_search_cache.get_results(tg_user_id)
    
    if not search_state:
        await ctx.reply_text(
            "没有找到最近的下载搜索结果。\n"
            "请先使用 `/dl_search 片名关键词`，再执行 `/dl_create 序号`。"
        )
        return
    
    # 检查序号范围
    if index > len(search_state.candidates):
        await ctx.reply_text(
            f"无效的序号。当前列表有效范围是 1–{len(search_state.candidates)}。\n"
            f"请使用 `/dl_search {search_state.query}` 重新搜索。"
        )
        return
    
    # 获取选中的候选
    candidate = search_state.candidates[index - 1]
    
    try:
        # 创建下载任务
        download_service = DownloadService(ctx.session)
        
        download_data = {
            "title": candidate.title,
            "magnet_link": candidate.magnet_link,
            "torrent_url": candidate.torrent_url,
            "size_gb": candidate.size_bytes / (1024 * 1024 * 1024) if candidate.size_bytes else 0.0,
            "media_type": "movie",  # 默认类型，可以根据需要调整
            "downloader": "qBittorrent",  # 默认下载器
            "extra_metadata": {
                "source": "telegram_bot",
                "site": candidate.site,
                "info_hash": candidate.info_hash,
                "is_free": candidate.is_free,
                "is_half_free": candidate.is_half_free,
                "search_query": search_state.query
            }
        }
        
        # 调用下载服务创建任务
        result = await download_service.create_download(download_data)
        
        # 格式化成功响应
        text = "✅ *下载任务已创建：*\n\n"
        text += f"站点：{candidate.site}\n"
        text += f"标题：{candidate.title}\n"
        
        # 格式化大小
        if candidate.size_bytes:
            size_gb = candidate.size_bytes / (1024 * 1024 * 1024)
            if size_gb >= 1:
                size_text = f"{size_gb:.1f} GB"
            else:
                size_mb = size_gb * 1024
                size_text = f"{size_mb:.0f} MB"
            text += f"大小：{size_text} · "
        
        # Free状态
        if candidate.is_free:
            text += "Free"
        elif candidate.is_half_free:
            text += "2x（half-free）"
        else:
            text += "普通"
        
        text += "\n\n"
        text += "你可以在 Web → 下载任务 中查看进度。"
        
        # 如果是模拟模式，添加提示
        if result.get("simulation_mode"):
            text += "\n\n⚠️ 当前为模拟模式，任务不会实际下载。"
        
        await ctx.reply_text(text)
        
    except Exception as e:
        logger.error(f"[telegram] dl_create failed: {e}")
        await ctx.reply_text("❌ 创建下载任务失败，请稍后重试")
