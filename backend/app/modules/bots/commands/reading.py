"""
阅读 / 听书 / 漫画 - Telegram 远程控制台 v1+v2
TG-BOT-BOOK-1 + TG-BOT-BOOK-2 实现

提供两个主要视角的阅读功能：
1. 进行中阅读列表视角 (ongoing reading) - TG-BOT-BOOK-1
   - /reading, /reading_books, /reading_audio, /reading_manga
   - /reading_detail <index>, /reading_open <index>
2. 最近活动时间线视角 (recent activity timeline) - TG-BOT-BOOK-2  
   - /reading_recent, /reading_recent_open <index>

所有命令均为只读模式，提供阅读进度查看和 Web 跳转功能
"""

from loguru import logger
from datetime import datetime
from typing import Optional

from app.modules.bots.telegram_router import router
from app.modules.bots.telegram_context import TelegramUpdateContext
from app.modules.bots.telegram_keyboard import build_back_to_menu_button
from app.modules.bots.telegram_bot_state import reading_list_cache, reading_activity_cache
from app.services.reading_hub_service import list_ongoing_reading, get_recent_activity
from app.services.reading_control_service import mark_reading_finished, add_favorite_from_reading, ReadingControlError
from app.schemas.reading_hub import ReadingOngoingItem, ReadingActivityItem
from app.schemas.reading_status import ReadingStatusHelper
from app.models.enums.reading_media_type import ReadingMediaType
from app.core.config import settings


# ============== 通用辅助函数 ==============

async def _ensure_user_bound(ctx: TelegramUpdateContext) -> bool:
    """确保用户已绑定账号"""
    if not ctx.is_bound:
        await ctx.reply_text("❌ 请先在 Web UI 生成绑定码，并通过 /bind 绑定账号")
        return False
    return True


def _format_reading_status(status: str, progress_percent: Optional[int]) -> str:
    """格式化阅读状态显示"""
    status_labels = {
        "active": "进行中",
        "not_started": "未开始",
        "finished": "已完成"
    }
    
    label = status_labels.get(status, "未知")
    
    if status == "finished":
        return label
    elif progress_percent and progress_percent > 0:
        return f"{label} · {progress_percent:.0f}%"
    else:
        return label


def _format_reading_item_line(index: int, item: ReadingOngoingItem) -> str:
    """格式化阅读列表条目"""
    # 类型图标
    type_icons = {
        ReadingMediaType.NOVEL: "📖",
        ReadingMediaType.AUDIOBOOK: "🎧", 
        ReadingMediaType.MANGA: "🖼"
    }
    type_names = {
        ReadingMediaType.NOVEL: "小说",
        ReadingMediaType.AUDIOBOOK: "有声书",
        ReadingMediaType.MANGA: "漫画"
    }
    
    icon = type_icons.get(item.media_type, "📚")
    
    # 状态和进度
    status_text = _format_reading_status(
        item.status.value if hasattr(item.status, 'value') else str(item.status),
        item.progress_percent
    )
    
    # 标题（截断避免过长）
    title = item.title
    if len(title) > 30:
        title = title[:27] + "..."
    
    return f"[{index}] {icon}《{title}》 - {status_text}"


def _format_activity_item_line(index: int, item: ReadingActivityItem) -> str:
    """格式化活动时间线条目"""
    # 类型图标
    type_icons = {
        ReadingMediaType.NOVEL: "📖",
        ReadingMediaType.AUDIOBOOK: "🎧", 
        ReadingMediaType.MANGA: "🖼"
    }
    type_names = {
        ReadingMediaType.NOVEL: "小说",
        ReadingMediaType.AUDIOBOOK: "有声书",
        ReadingMediaType.MANGA: "漫画"
    }
    
    icon = type_icons.get(item.media_type, "📚")
    type_name = type_names.get(item.media_type, "未知")
    
    # 标题（截断避免过长）
    title = item.title
    if len(title) > 25:
        title = title[:22] + "..."
    
    # 时间格式化
    time_str = _format_relative_time(item.occurred_at)
    
    # 活动标签
    activity_label = item.activity_label or "未知活动"
    
    return f"[{index}] {icon}《{title}》 · {type_name} · {activity_label} · {time_str}"


def _format_relative_time(occurred_at: Optional[datetime]) -> str:
    """格式化相对时间显示"""
    if not occurred_at:
        return "未知时间"
    
    now = datetime.utcnow()
    delta = now - occurred_at
    
    if delta.days > 0:
        if delta.days == 1:
            return "昨天 " + occurred_at.strftime("%H:%M")
        elif delta.days < 7:
            return f"{delta.days}天前"
        else:
            return occurred_at.strftime("%m-%d")
    elif delta.seconds > 3600:
        hours = delta.seconds // 3600
        if hours == 1:
            return "1小时前"
        else:
            return f"{hours}小时前"
    elif delta.seconds > 60:
        minutes = delta.seconds // 60
        if minutes == 1:
            return "1分钟前"
        else:
            return f"{minutes}分钟前"
    else:
        return "刚刚"


def _build_web_url(settings, item: ReadingOngoingItem) -> str:
    """构建 Web 跳转 URL"""
    base_url = settings.WEB_BASE_URL.rstrip('/')
    
    # 根据路由名称和参数构建 URL
    if item.route_name == "NovelReader":
        return f"{base_url}/novel-center/ebook/{item.route_params.get('ebookId', item.item_id)}"
    elif item.route_name == "WorkDetail":
        return f"{base_url}/audiobook/{item.route_params.get('ebookId', item.item_id)}"
    elif item.route_name == "MangaReaderPage":
        series_id = item.route_params.get('series_id', item.item_id)
        chapter_id = item.route_params.get('chapter_id')
        if chapter_id:
            return f"{base_url}/manga/read/{series_id}/{chapter_id}"
        else:
            return f"{base_url}/manga/read/{series_id}"
    else:
        # 默认回退
        return f"{base_url}/"


def _build_web_url_unified(settings, route_name: str, route_params: dict) -> str:
    """统一的 Web URL 构建函数，支持所有路由类型"""
    base_url = settings.WEB_BASE_URL.rstrip('/')
    
    # 根据路由名称和参数构建 URL
    if route_name == "NovelReader":
        return f"{base_url}/novel-center/ebook/{route_params.get('ebookId', '')}"
    elif route_name == "WorkDetail":
        return f"{base_url}/audiobook/{route_params.get('ebookId', '')}"
    elif route_name == "MangaReaderPage":
        series_id = route_params.get('series_id', '')
        chapter_id = route_params.get('chapter_id')
        if chapter_id:
            return f"{base_url}/manga/read/{series_id}/{chapter_id}"
        else:
            return f"{base_url}/manga/read/{series_id}"
    else:
        # 默认回退
        return f"{base_url}/"


def _get_media_type_label(media_type: ReadingMediaType) -> str:
    """获取媒体类型标签"""
    labels = {
        ReadingMediaType.NOVEL: "小说",
        ReadingMediaType.AUDIOBOOK: "有声书",
        ReadingMediaType.MANGA: "漫画"
    }
    return labels.get(media_type, "未知")


async def _get_reading_items(ctx, item_type: Optional[str] = None, limit: int = 10):
    """获取阅读列表并缓存"""
    user_id = ctx.app_user.id if ctx.app_user else None
    tg_user_id = ctx.from_user_id
    
    if not user_id:
        return []
    
    # 检查缓存
    cached_state = reading_list_cache.get_results(tg_user_id)
    if cached_state and cached_state.item_type == (item_type or "mixed"):
        logger.debug(f"Using cached reading list for user {user_id}")
        return cached_state.items
    
    # 从数据库获取
    try:
        if item_type:
            # 按类型过滤 - 转换小写字符串为枚举
            media_type_map = {
                "novel": ReadingMediaType.NOVEL,
                "audiobook": ReadingMediaType.AUDIOBOOK,
                "manga": ReadingMediaType.MANGA
            }
            media_type = media_type_map.get(item_type.lower())
            if not media_type:
                return []
            
            all_items = await list_ongoing_reading(ctx.session, user_id, limit_per_type=limit)
            filtered_items = [item for item in all_items if item.media_type == media_type]
            items = filtered_items[:limit]
        else:
            # 混合列表
            items = await list_ongoing_reading(ctx.session, user_id, limit_per_type=limit)
            # 按最近更新时间排序并限制总数（处理 None 值）
            items.sort(key=lambda x: x.last_read_at or datetime.min, reverse=True)
            items = items[:limit]
        
        # 缓存结果
        cache_type = item_type or "mixed"
        reading_list_cache.set_results(tg_user_id, user_id, items, cache_type)
        
        return items
        
    except Exception as e:
        logger.error(f"Failed to get reading items for user {user_id}: {e}")
        return []


async def _get_activity_items(ctx, limit: int = 50):
    """获取最近活动列表并缓存"""
    user_id = ctx.app_user.id if ctx.app_user else None
    tg_user_id = ctx.from_user_id
    
    if not user_id:
        return []
    
    # 检查缓存
    cached_state = reading_activity_cache.get_results(tg_user_id)
    if cached_state:
        logger.debug(f"Using cached activity list for user {user_id}")
        return cached_state.items
    
    # 从数据库获取
    try:
        items = await get_recent_activity(ctx.session, user_id, limit=limit)
        
        # 缓存结果
        reading_activity_cache.set_results(tg_user_id, user_id, items)
        
        return items
        
    except Exception as e:
        logger.error(f"Failed to get activity items for user {user_id}: {e}")
        return []


def _parse_index_from_args(ctx: TelegramUpdateContext) -> Optional[int]:
    """从命令参数解析索引"""
    args = ctx.args.strip().split() if ctx.args.strip() else []
    if not args:
        return None
    
    try:
        return int(args[0])
    except (ValueError, IndexError):
        return None


# ============== 命令实现 ==============

@router.command("reading")
async def cmd_reading(ctx: TelegramUpdateContext):
    """显示最近在读/在听/在看的混合列表（进行中阅读列表视角 - 只读）"""
    if not await _ensure_user_bound(ctx):
        return
    
    items = await _get_reading_items(ctx, item_type=None, limit=10)
    
    if not items:
        await ctx.reply_text("📭 当前没有正在进行的阅读/收听/漫画记录")
        return
    
    lines = ["📚 进行中阅读列表（只读模式）："]
    for idx, item in enumerate(items, start=1):
        lines.append(_format_reading_item_line(idx, item))
    
    lines.append("")
    lines.append("👉 查看详情：/reading_detail 1")
    lines.append("👉 打开 Web 阅读：/reading_open 1")
    
    await ctx.reply_text("\n".join(lines), reply_markup=build_back_to_menu_button())


@router.command("reading_recent")
async def cmd_reading_recent(ctx: TelegramUpdateContext):
    """显示最近阅读活动时间线（只读模式）"""
    if not await _ensure_user_bound(ctx):
        return
    
    items = await _get_activity_items(ctx, limit=50)
    
    if not items:
        await ctx.reply_text("📭 目前没有最近的阅读/收听/漫画活动噢~")
        return
    
    lines = ["🕒 最近阅读活动时间线（只读模式）："]
    for idx, item in enumerate(items, start=1):
        lines.append(_format_activity_item_line(idx, item))
    
    lines.append("")
    lines.append("👉 打开 Web 链接：/reading_recent_open 1")
    
    await ctx.reply_text("\n".join(lines), reply_markup=build_back_to_menu_button())


@router.command("reading_books")
async def cmd_reading_books(ctx: TelegramUpdateContext):
    """显示仅小说的最近阅读列表（进行中阅读列表视角 - 只读）"""
    if not await _ensure_user_bound(ctx):
        return
    
    items = await _get_reading_items(ctx, item_type="novel", limit=10)
    
    if not items:
        await ctx.reply_text("📭 当前没有正在阅读的小说")
        return
    
    lines = ["📖 进行中小说列表（只读模式）："]
    for idx, item in enumerate(items, start=1):
        lines.append(_format_reading_item_line(idx, item))
    
    lines.append("")
    lines.append("👉 查看详情：/reading_detail 1")
    lines.append("👉 打开 Web 阅读：/reading_open 1")
    
    await ctx.reply_text("\n".join(lines), reply_markup=build_back_to_menu_button())


@router.command("reading_audio")
async def cmd_reading_audio(ctx: TelegramUpdateContext):
    """显示仅有声书的最近收听列表（进行中阅读列表视角 - 只读）"""
    if not await _ensure_user_bound(ctx):
        return
    
    items = await _get_reading_items(ctx, item_type="audiobook", limit=10)
    
    if not items:
        await ctx.reply_text("📭 当前没有正在收听的有声书")
        return
    
    lines = ["🎧 进行中有声书列表（只读模式）："]
    for idx, item in enumerate(items, start=1):
        lines.append(_format_reading_item_line(idx, item))
    
    lines.append("")
    lines.append("👉 查看详情：/reading_detail 1")
    lines.append("👉 打开 Web 阅读：/reading_open 1")
    
    await ctx.reply_text("\n".join(lines), reply_markup=build_back_to_menu_button())


@router.command("reading_manga")
async def cmd_reading_manga(ctx: TelegramUpdateContext):
    """显示仅漫画的最近阅读列表（进行中阅读列表视角 - 只读）"""
    if not await _ensure_user_bound(ctx):
        return
    
    items = await _get_reading_items(ctx, item_type="manga", limit=10)
    
    if not items:
        await ctx.reply_text("📭 当前没有正在阅读的漫画")
        return
    
    lines = ["🖼 进行中漫画列表（只读模式）："]
    for idx, item in enumerate(items, start=1):
        lines.append(_format_reading_item_line(idx, item))
    
    lines.append("")
    lines.append("👉 查看详情：/reading_detail 1")
    lines.append("👉 打开 Web 阅读：/reading_open 1")
    
    await ctx.reply_text("\n".join(lines), reply_markup=build_back_to_menu_button())


@router.command("reading_detail")
async def cmd_reading_detail(ctx: TelegramUpdateContext):
    """显示某个阅读项的详细信息（进行中阅读列表视角 - 只读）"""
    if not await _ensure_user_bound(ctx):
        return
    
    # 解析索引
    index = _parse_index_from_args(ctx)
    if index is None:
        await ctx.reply_text("❌ 请提供要查看的条目序号\n\n用法：/reading_detail 1")
        return
    
    # 从缓存获取
    item = reading_list_cache.get_item_by_index(ctx.from_user_id, index)
    if not item:
        await ctx.reply_text("❌ 找不到该条目，可能序号超出范围或列表已过期\n\n请先重新发送 /reading 查看最新列表")
        return
    
    # 构建详情信息
    type_name = _get_media_type_label(item.media_type)
    status_text = _format_reading_status(
        item.status.value if hasattr(item.status, 'value') else str(item.status),
        item.progress_percent
    )
    
    lines = [
        f"[{index}] {type_name}《{item.title}》（只读模式）",
        "",
        f"状态：{status_text}",
        f"类型：{type_name}",
        f"最近更新：{item.last_read_at.strftime('%Y-%m-%d %H:%M') if item.last_read_at else '未知'}",
    ]
    
    # 添加进度标签
    if item.progress_label:
        lines.append(f"进度：{item.progress_label}")
    
    # 添加副标题（作者等）
    if item.sub_title:
        lines.append(f"作者：{item.sub_title}")
    
    lines.append("")
    lines.append("👉 打开 Web 继续阅读：")
    
    # 构建并返回 URL
    web_url = _build_web_url(settings, item)
    lines.append(web_url)
    
    await ctx.reply_text("\n".join(lines), reply_markup=build_back_to_menu_button())


@router.command("reading_open")
async def cmd_reading_open(ctx: TelegramUpdateContext):
    """直接返回 Web 跳转链接"""
    if not await _ensure_user_bound(ctx):
        return
    
    # 解析索引
    index = _parse_index_from_args(ctx)
    if index is None:
        await ctx.reply_text("❌ 请提供要打开的条目序号\n\n用法：/reading_open 1")
        return
    
    # 从缓存获取
    item = reading_list_cache.get_item_by_index(ctx.from_user_id, index)
    if not item:
        await ctx.reply_text("❌ 找不到该条目，可能序号超出范围或列表已过期\n\n请先重新发送 /reading 查看最新列表")
        return
    
    # 构建并返回 URL
    web_url = _build_web_url(settings, item)
    
    lines = [
        f"👉 打开 Web 继续阅读：",
        web_url
    ]
    
    await ctx.reply_text("\n".join(lines), reply_markup=build_back_to_menu_button())


@router.command("reading_recent_open")
async def cmd_reading_recent_open(ctx: TelegramUpdateContext):
    """打开最近活动中的某一条对应的 Web 页面"""
    if not await _ensure_user_bound(ctx):
        return
    
    # 解析索引
    index = _parse_index_from_args(ctx)
    if index is None:
        await ctx.reply_text("❌ 请提供要打开的条目序号\n\n用法：/reading_recent_open 1\n示例：/reading_recent_open 2")
        return
    
    # 从缓存获取
    item = reading_activity_cache.get_item(ctx.from_user_id, index)
    if not item:
        await ctx.reply_text("❌ 找不到该条目，可能序号超出范围或列表已过期\n\n请先重新发送 /reading_recent 查看最新列表")
        return
    
    # 构建并返回 URL
    web_url = _build_web_url_unified(settings, item.route_name, item.route_params)
    
    # 获取媒体类型图标
    type_icons = {
        ReadingMediaType.NOVEL: "📖",
        ReadingMediaType.AUDIOBOOK: "🎧", 
        ReadingMediaType.MANGA: "🖼"
    }
    icon = type_icons.get(item.media_type, "📚")
    
    lines = [
        f"已为你打开：",
        f"{icon}《{item.title}》 · {item.activity_label or '继续阅读'}",
        "",
        "Web 链接：",
        web_url
    ]
    
    await ctx.reply_text("\n".join(lines), reply_markup=build_back_to_menu_button())


@router.command("reading_done", help_text="标记进行中的阅读为已完成（⚠️ 会修改状态）")
async def cmd_reading_done(ctx: TelegramUpdateContext):
    """标记进行中列表中的某条为已完成"""
    if not await _ensure_user_bound(ctx):
        return
    
    # 解析索引
    index = _parse_index_from_args(ctx)
    if index is None:
        await ctx.reply_text("❌ 请提供要标记完成的条目序号\n\n用法：/reading_done <编号>\n示例：/reading_done 1")
        return
    
    # 从缓存获取对应条目
    item = reading_list_cache.get_item_by_index(ctx.from_user_id, index)
    if not item:
        await ctx.reply_text("❌ 找不到该条目，可能序号超出范围或列表已过期\n\n请先重新发送 /reading 查看最新列表")
        return
    
    # 调用 Service 层执行标记完成
    try:
        await mark_reading_finished(
            session=ctx.session,
            user_id=ctx.user_id,
            media_type=item.media_type,
            internal_id=item.item_id,
        )
        
        # 缓存失效处理
        reading_list_cache.clear_user(ctx.from_user_id)
        reading_activity_cache.clear_user(ctx.from_user_id)
        
        # 构建成功反馈（使用原始缓存项，但更新状态显示）
        type_name = _get_media_type_label(item.media_type)
        
        # 手动构建已完成状态显示
        lines = [
            "✅ 已标记为已完成（会影响你的阅读进度）",
            "",
            f"{type_name}《{item.title}》",
            f"类型：{type_name}",
            "当前状态：已完成 · 100%",
            "",
            "如需继续查看进行中列表，可发送：",
            "/reading"
        ]
        
        await ctx.reply_text("\n".join(lines), reply_markup=build_back_to_menu_button())
        
    except ReadingControlError as e:
        logger.error(f"Failed to mark reading finished: user_id={ctx.user_id}, error={e}")
        await ctx.reply_text(f"❌ 操作失败：{str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error marking reading finished: user_id={ctx.user_id}, error={e}")
        await ctx.reply_text("❌ 操作失败，请稍后重试")


@router.command("reading_fav", help_text="将进行中的条目加入书架收藏（⚠️ 会修改收藏状态）")
async def cmd_reading_fav(ctx: TelegramUpdateContext):
    """从进行中列表把条目加入书架收藏"""
    if not await _ensure_user_bound(ctx):
        return
    
    # 解析索引
    index = _parse_index_from_args(ctx)
    if index is None:
        await ctx.reply_text("❌ 请提供要收藏的条目序号\n\n用法：/reading_fav <编号>\n示例：/reading_fav 1")
        return
    
    # 从缓存获取对应条目
    item = reading_list_cache.get_item_by_index(ctx.from_user_id, index)
    if not item:
        await ctx.reply_text("❌ 找不到该条目，可能序号超出范围或列表已过期\n\n请先重新发送 /reading 查看最新列表")
        return
    
    # 调用 Service 层执行收藏操作
    try:
        shelf_item = await add_favorite_from_reading(
            session=ctx.session,
            user_id=ctx.user_id,
            reading_item=item,
        )
        
        # 缓存失效处理
        from app.modules.bots.telegram_bot_state import reading_shelf_cache
        reading_shelf_cache.clear_user(ctx.from_user_id)
        # 可选：失效其他缓存（如果书架状态会影响进行中展示）
        # reading_list_cache.clear_user(ctx.from_user_id)
        
        # 构建成功反馈
        type_name = _get_media_type_label(item.media_type)
        
        lines = [
            "⭐ 已加入书架收藏（会修改你的收藏状态）",
            "",
            f"{type_name}《{item.title}》已添加到你的书架。",
            "",
            "你可以通过 /shelf 查看。"
        ]
        
        await ctx.reply_text("\n".join(lines), reply_markup=build_back_to_menu_button())
        
    except ReadingControlError as e:
        logger.error(f"Failed to add favorite: user_id={ctx.user_id}, error={e}")
        await ctx.reply_text(f"❌ 操作失败：{str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error adding favorite: user_id={ctx.user_id}, error={e}")
        await ctx.reply_text("❌ 操作失败，请稍后重试")
