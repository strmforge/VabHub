"""
阅读书架 / 收藏视角 – Telegram 只读控制台 v1 (TG-SHELF-1)

本模块提供 Telegram Bot 的"书架/收藏视角"命令，让用户可以查看自己的收藏内容。

数据来源：
- reading_favorite_service.list_favorites(...) 获取用户收藏列表
- ReadingShelfItem 作为统一的数据结构

与现有阅读命令的关系：
- 进行中视角 (/reading*): 显示当前在读/在听/在看的项目
- 时间线视角 (/reading_recent*): 显示最近的阅读活动记录  
- 书架视角 (/shelf*): 显示收藏的小说/有声书/漫画

所有命令均为只读模式，不会修改收藏状态或阅读进度。
"""

from typing import Optional
from loguru import logger

from app.modules.bots.telegram_router import router
from app.modules.bots.telegram_context import TelegramUpdateContext
from app.modules.bots.telegram_keyboard import build_back_to_menu_button
from app.modules.bots.telegram_bot_state import reading_shelf_cache
from app.services.reading_favorite_service import list_favorites
from app.services.reading_control_service import remove_favorite_by_internal_id, ReadingControlError
from app.models.enums.reading_media_type import ReadingMediaType
from app.schemas.reading_hub import ReadingShelfItem
from app.core.config import settings


# ============== 通用辅助函数 ==============

async def _ensure_user_bound(ctx: TelegramUpdateContext) -> bool:
    """确保用户已绑定账号"""
    if not ctx.is_bound:
        await ctx.reply_text("❌ 请先在 Web UI 生成绑定码，并通过 /bind 绑定账号")
        return False
    return True


def _format_reading_status(status: str, progress_percent: Optional[float] = None) -> str:
    """格式化阅读状态"""
    status_map = {
        "not_started": "未开始",
        "in_progress": "进行中", 
        "finished": "已完成"
    }
    
    status_text = status_map.get(status, status)
    
    if progress_percent is not None and status == "in_progress":
        return f"{status_text} · {progress_percent:.0f}%"
    elif progress_percent is not None and status == "finished":
        return f"{status_text} · 100%"
    else:
        return status_text


def _format_shelf_item_line(index: int, item: ReadingShelfItem) -> str:
    """格式化书架条目行"""
    # 类型图标
    type_icons = {
        ReadingMediaType.NOVEL: "📖",
        ReadingMediaType.AUDIOBOOK: "🎧",
        ReadingMediaType.MANGA: "🖼"
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
    
    # 构建基础行
    line = f"[{index}] {icon}《{title}》 - {status_text}"
    
    # 添加位置标签（如果有）
    if item.last_position_label:
        line += f" · {item.last_position_label}"
    
    return line


async def _get_shelf_items(
    ctx: TelegramUpdateContext,
    item_type: Optional[str],  # "novel" / "audiobook" / "manga" / None
    limit: int = 20,
) -> list[ReadingShelfItem]:
    """获取书架列表并缓存"""
    user_id = ctx.app_user.id if ctx.app_user else None
    tg_user_id = ctx.from_user_id
    
    if not user_id:
        return []
    
    # 确定媒体类型
    media_type = None
    if item_type:
        type_map = {
            "novel": ReadingMediaType.NOVEL,
            "audiobook": ReadingMediaType.AUDIOBOOK,
            "manga": ReadingMediaType.MANGA,
        }
        media_type = type_map.get(item_type)
    
    # 确定缓存类型
    cache_type = item_type or "mixed"
    
    # 检查缓存
    cached_state = reading_shelf_cache.get_results(tg_user_id, cache_type)
    if cached_state:
        logger.debug(f"Using cached shelf list for user {user_id}, type: {cache_type}")
        return cached_state.items
    
    # 从数据库获取
    try:
        items = await list_favorites(
            session=ctx.session,
            user_id=user_id,
            media_type=media_type,
            limit=limit,
            offset=0
        )
        
        # 缓存结果
        reading_shelf_cache.set_results(tg_user_id, user_id, items, cache_type)
        
        return items
        
    except Exception as e:
        logger.error(f"Failed to get shelf items for user {user_id}: {e}")
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

@router.command("shelf")
async def cmd_shelf(ctx: TelegramUpdateContext):
    """显示我的书架混合列表（只读模式）"""
    if not await _ensure_user_bound(ctx):
        return
    
    items = await _get_shelf_items(ctx, item_type=None, limit=20)
    
    if not items:
        await ctx.reply_text("📭 你的书架里还没有任何收藏（只读模式）")
        return
    
    lines = ["📚 我的书架（只读模式）"]
    for idx, item in enumerate(items, start=1):
        lines.append(_format_shelf_item_line(idx, item))
    
    lines.append("")
    lines.append("👉 查看详情：/shelf_detail 1")
    lines.append("👉 打开 Web 页面：/shelf_open 1")
    
    await ctx.reply_text("\n".join(lines), reply_markup=build_back_to_menu_button())


@router.command("shelf_books")
async def cmd_shelf_books(ctx: TelegramUpdateContext):
    """显示我收藏的小说（只读模式）"""
    if not await _ensure_user_bound(ctx):
        return
    
    items = await _get_shelf_items(ctx, item_type="novel", limit=20)
    
    if not items:
        await ctx.reply_text("📭 你的书架里还没有收藏的小说（只读模式）")
        return
    
    lines = ["📚 我的书架 - 小说（只读模式）"]
    for idx, item in enumerate(items, start=1):
        lines.append(_format_shelf_item_line(idx, item))
    
    lines.append("")
    lines.append("👉 查看详情：/shelf_detail 1")
    lines.append("👉 打开 Web 页面：/shelf_open 1")
    
    await ctx.reply_text("\n".join(lines), reply_markup=build_back_to_menu_button())


@router.command("shelf_audio")
async def cmd_shelf_audio(ctx: TelegramUpdateContext):
    """显示我收藏的有声书（只读模式）"""
    if not await _ensure_user_bound(ctx):
        return
    
    items = await _get_shelf_items(ctx, item_type="audiobook", limit=20)
    
    if not items:
        await ctx.reply_text("📭 你的书架里还没有收藏的有声书（只读模式）")
        return
    
    lines = ["📚 我的书架 - 有声书（只读模式）"]
    for idx, item in enumerate(items, start=1):
        lines.append(_format_shelf_item_line(idx, item))
    
    lines.append("")
    lines.append("👉 查看详情：/shelf_detail 1")
    lines.append("👉 打开 Web 页面：/shelf_open 1")
    
    await ctx.reply_text("\n".join(lines), reply_markup=build_back_to_menu_button())


@router.command("shelf_manga")
async def cmd_shelf_manga(ctx: TelegramUpdateContext):
    """显示我收藏的漫画（只读模式）"""
    if not await _ensure_user_bound(ctx):
        return
    
    items = await _get_shelf_items(ctx, item_type="manga", limit=20)
    
    if not items:
        await ctx.reply_text("📭 你的书架里还没有收藏的漫画（只读模式）")
        return
    
    lines = ["📚 我的书架 - 漫画（只读模式）"]
    for idx, item in enumerate(items, start=1):
        lines.append(_format_shelf_item_line(idx, item))
    
    lines.append("")
    lines.append("👉 查看详情：/shelf_detail 1")
    lines.append("👉 打开 Web 页面：/shelf_open 1")
    
    await ctx.reply_text("\n".join(lines), reply_markup=build_back_to_menu_button())


def _build_web_url_for_shelf(settings, item: ReadingShelfItem) -> str:
    """构建书架项的 Web 跳转 URL"""
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
            return f"{base_url}/manga/{series_id}/chapter/{chapter_id}"
        else:
            return f"{base_url}/manga/{series_id}"
    else:
        # 默认回退
        return f"{base_url}/"


def _get_media_type_label(media_type: ReadingMediaType) -> str:
    """获取媒体类型标签"""
    type_labels = {
        ReadingMediaType.NOVEL: "小说",
        ReadingMediaType.AUDIOBOOK: "有声书",
        ReadingMediaType.MANGA: "漫画"
    }
    return type_labels.get(media_type, "未知")


@router.command("shelf_detail")
async def cmd_shelf_detail(ctx: TelegramUpdateContext):
    """显示书架条目详情（只读模式）"""
    if not await _ensure_user_bound(ctx):
        return
    
    # 解析索引
    index = _parse_index_from_args(ctx)
    if index is None:
        await ctx.reply_text("❌ 请提供要查看的书架条目序号\n\n用法：/shelf_detail 1")
        return
    
    # 从缓存获取
    item = reading_shelf_cache.get_item_by_index(ctx.from_user_id, index)
    if not item:
        await ctx.reply_text("❌ 找不到该条目，可能序号超出范围或列表已过期\n\n请先重新发送 /shelf 查看最新列表")
        return
    
    # 构建详情信息
    type_name = _get_media_type_label(item.media_type)
    status_text = _format_reading_status(
        item.status.value if hasattr(item.status, 'value') else str(item.status),
        item.progress_percent
    )
    
    lines = [
        f"📚 书架条目详情（只读模式）",
        "",
        f"{_get_media_type_label(item.media_type)}《{item.title}》",
        "",
        f"类型：{type_name}",
        f"状态：{status_text}",
    ]
    
    # 添加来源标签
    if item.source_label:
        lines.append(f"来源：{item.source_label}")
    
    # 添加位置标签
    if item.last_position_label:
        lines.append(f"最近阅读位置：{item.last_position_label}")
    
    # 添加副标题（作者等）
    if item.sub_title:
        lines.append(f"作者：{item.sub_title}")
    
    # 添加最近阅读时间
    if item.last_read_at:
        lines.append(f"最近阅读时间：{item.last_read_at.strftime('%Y-%m-%d %H:%M')}")
    
    lines.append("")
    lines.append("👉 打开 Web 页面：")
    
    # 构建并返回 URL
    web_url = _build_web_url_for_shelf(settings, item)
    lines.append(web_url)
    
    await ctx.reply_text("\n".join(lines), reply_markup=build_back_to_menu_button())


@router.command("shelf_open")
async def cmd_shelf_open(ctx: TelegramUpdateContext):
    """直接返回 Web 跳转链接"""
    if not await _ensure_user_bound(ctx):
        return
    
    # 解析索引
    index = _parse_index_from_args(ctx)
    if index is None:
        await ctx.reply_text("❌ 请提供要打开的书架条目序号\n\n用法：/shelf_open 1")
        return
    
    # 从缓存获取
    item = reading_shelf_cache.get_item_by_index(ctx.from_user_id, index)
    if not item:
        await ctx.reply_text("❌ 找不到该条目，可能序号超出范围或列表已过期\n\n请先重新发送 /shelf 查看最新列表")
        return
    
    # 构建并返回 URL
    web_url = _build_web_url_for_shelf(settings, item)
    
    lines = [
        f"👉 打开 Web 页面：",
        web_url
    ]
    
    await ctx.reply_text("\n".join(lines), reply_markup=build_back_to_menu_button())


@router.command("shelf_unfav", help_text="取消书架收藏（⚠️ 会修改收藏状态）")
async def cmd_shelf_unfav(ctx: TelegramUpdateContext):
    """从书架视角中取消收藏"""
    if not await _ensure_user_bound(ctx):
        return
    
    # 解析索引
    index = _parse_index_from_args(ctx)
    if index is None:
        await ctx.reply_text("❌ 请提供要取消收藏的条目序号\n\n用法：/shelf_unfav <编号>\n示例：/shelf_unfav 1")
        return
    
    # 从缓存获取对应条目
    item = reading_shelf_cache.get_item_by_index(ctx.from_user_id, index)
    if not item:
        await ctx.reply_text("❌ 找不到该条目，可能序号超出范围或列表已过期\n\n请先重新发送 /shelf 查看最新列表")
        return
    
    # 调用 Service 层执行取消收藏操作
    try:
        removed = await remove_favorite_by_internal_id(
            session=ctx.session,
            user_id=ctx.user_id,
            media_type=item.media_type,
            internal_id=item.item_id,
        )
        
        # 缓存失效处理
        reading_shelf_cache.clear_user(ctx.from_user_id)
        # 可选：失效其他缓存（如果书架状态会影响进行中展示）
        # reading_list_cache.clear_user(ctx.from_user_id)
        
        # 构建成功反馈
        type_name = _get_media_type_label(item.media_type)
        
        if removed:
            lines = [
                "✅ 已取消收藏（会修改你的收藏状态）",
                "",
                f"{type_name}《{item.title}》已从你的书架中移除。"
            ]
        else:
            lines = [
                "ℹ️ 该条目目前不在你的书架中，无需取消。",
                "",
                f"{type_name}《{item.title}》"
            ]
        
        await ctx.reply_text("\n".join(lines), reply_markup=build_back_to_menu_button())
        
    except ReadingControlError as e:
        logger.error(f"Failed to remove favorite: user_id={ctx.user_id}, error={e}")
        await ctx.reply_text(f"❌ 操作失败：{str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error removing favorite: user_id={ctx.user_id}, error={e}")
        await ctx.reply_text("❌ 操作失败，请稍后重试")
