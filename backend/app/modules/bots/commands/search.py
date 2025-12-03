"""
搜索命令
BOT-TELEGRAM Phase 2 + BOT-EXT-1

/search 和纯文本搜索
支持媒体类型过滤和分页
"""

from datetime import datetime, timedelta
from typing import Optional
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
from app.services.global_search_service import search_all
from app.core.config import settings


# 简单限流：记录最近搜索时间
_last_search: dict[int, datetime] = {}
SEARCH_COOLDOWN = 2  # 秒


def _check_rate_limit(chat_id: int) -> bool:
    """检查是否需要限流"""
    now = datetime.utcnow()
    last = _last_search.get(chat_id)
    
    if last and (now - last).total_seconds() < SEARCH_COOLDOWN:
        return False
    
    _last_search[chat_id] = now
    return True


# ============== /search ==============

# 媒体类型映射
MEDIA_TYPE_ALIASES = {
    "movie": "movie",
    "电影": "movie",
    "tv": "tv",
    "剧集": "tv",
    "电视剧": "tv",
    "novel": "novel",
    "小说": "novel",
    "manga": "manga",
    "漫画": "manga",
    "audiobook": "audiobook",
    "有声书": "audiobook",
    "music": "music",
    "音乐": "music",
}


@router.command("/search")
async def cmd_search(ctx: TelegramUpdateContext) -> None:
    """搜索命令
    
    支持格式：
    - /search 关键词
    - /search movie 关键词
    - /search 漫画 关键词
    """
    args = ctx.args.strip()
    
    if not args:
        await ctx.reply_text(
            "🔍 *搜索*\n\n"
            "请输入搜索关键词：\n"
            "`/search 关键词`\n\n"
            "*支持媒体类型过滤：*\n"
            "`/search movie 三体`\n"
            "`/search 漫画 进击的巨人`\n\n"
            "*可用类型：*\n"
            "movie/电影, tv/剧集, novel/小说, manga/漫画, audiobook/有声书, music/音乐\n\n"
            "💡 或直接发送媒体名称进行搜索！"
        )
        return
    
    # 解析媒体类型前缀
    media_type = None
    keyword = args
    
    parts = args.split(maxsplit=1)
    if len(parts) >= 1:
        first_word = parts[0].lower()
        if first_word in MEDIA_TYPE_ALIASES:
            media_type = MEDIA_TYPE_ALIASES[first_word]
            keyword = parts[1] if len(parts) > 1 else ""
    
    if not keyword:
        await ctx.reply_text("请输入搜索关键词")
        return
    
    await _do_search(ctx, keyword, media_type=media_type)


# ============== 纯文本搜索 (fallback) ==============

@router.set_fallback
async def fallback_search(ctx: TelegramUpdateContext) -> None:
    """纯文本作为搜索关键词"""
    text = ctx.text.strip()
    
    # 过滤太短的文本
    if not text or len(text) < 2:
        return
    
    # 过滤一些常见的非搜索文本
    if text.lower() in ("ok", "好", "是", "否", "谢谢", "thanks", "hi", "hello"):
        return
    
    # 限流
    if not _check_rate_limit(ctx.chat_id):
        await ctx.reply_text("⏳ 请稍等片刻再搜索...")
        return
    
    await _do_search(ctx, text)


# ============== 搜索核心逻辑 ==============

async def _do_search(
    ctx: TelegramUpdateContext,
    keyword: str,
    media_type: Optional[str] = None,
    page: int = 1,
) -> None:
    """执行搜索
    
    Args:
        ctx: 上下文
        keyword: 搜索关键词
        media_type: 媒体类型过滤
        page: 页码
    """
    # 发送搜索中提示
    type_hint = f" ({media_type})" if media_type else ""
    await ctx.reply_text(f"🔍 正在搜索: *{keyword}*{type_hint}...")
    
    try:
        result = await search_all(ctx.session, keyword, limit_per_type=10)
    except Exception as e:
        logger.error(f"[telegram] search error: {e}")
        await ctx.reply_text("❌ 搜索暂时不可用，请稍后再试")
        return
    
    # 过滤媒体类型
    items = result.items
    if media_type:
        items = [i for i in items if i.media_type == media_type]
    
    if not items:
        await ctx.reply_text(
            f"😔 未找到「{keyword}」相关内容\n\n"
            "没有找到相关作品，可以换个关键词试试。",
            reply_markup=build_back_to_menu_button(),
        )
        return
    
    # 分页
    page_size = 5
    total_pages = (len(items) + page_size - 1) // page_size
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * page_size
    page_items = items[start_idx:start_idx + page_size]
    
    # 按类型分组
    grouped: dict[str, list] = {}
    for item in page_items:
        mt = item.media_type
        if mt not in grouped:
            grouped[mt] = []
        grouped[mt].append(item)
    
    # 构建结果消息
    type_icons = {
        "novel": "📖",
        "audiobook": "🎧",
        "manga": "📚",
        "music": "🎵",
        "movie": "🎬",
        "tv": "📺",
    }
    
    type_names = {
        "novel": "小说/电子书",
        "audiobook": "有声书",
        "manga": "漫画",
        "music": "音乐",
        "movie": "电影",
        "tv": "剧集",
    }
    
    # 发送每个类型的结果
    for mt, mt_items in grouped.items():
        icon = type_icons.get(mt, "📄")
        name = type_names.get(mt, mt)
        
        text = f"{icon} *{name}* - 搜索「{keyword}」\n\n"
        buttons = []
        
        for i, item in enumerate(mt_items, 1):
            title = item.title or "未知标题"
            sub = f" - {item.sub_title}" if item.sub_title else ""
            text += f"{i}. *{title}*{sub}\n"
            
            # 构建按钮
            item_buttons = _build_item_buttons(item)
            if item_buttons:
                buttons.extend(item_buttons)
        
        # 分页按钮
        if total_pages > 1:
            page_row = []
            if page > 1:
                page_row.append(inline_button(
                    "« 上一页",
                    callback_data=callback_data("search:page", {"q": keyword, "p": page - 1, "t": media_type or ""})
                ))
            page_row.append(inline_button(f"{page}/{total_pages}", callback_data="noop"))
            if page < total_pages:
                page_row.append(inline_button(
                    "下一页 »",
                    callback_data=callback_data("search:page", {"q": keyword, "p": page + 1, "t": media_type or ""})
                ))
            buttons.append(page_row)
        
        # 添加返回按钮
        buttons.append([inline_button("« 返回主菜单", callback_data="menu:main")])
        
        await ctx.reply_text(text, reply_markup=inline_keyboard(buttons))


def _build_item_buttons(item) -> list[list[dict]]:
    """为单个搜索结果构建按钮"""
    base_url = getattr(settings, "FRONTEND_URL", "")
    
    media_type = item.media_type
    item_id = item.id
    
    payload = {"t": media_type, "id": item_id}
    
    row = []
    
    # 根据类型添加不同按钮
    if media_type == "manga":
        row.append(inline_button("📌 追更", callback_data=callback_data("act:subscribe", payload)))
    elif media_type == "music":
        row.append(inline_button("⬇️ 下载", callback_data=callback_data("act:download", payload)))
    elif media_type in ("novel", "audiobook"):
        row.append(inline_button("📖 阅读", callback_data=callback_data("act:read", payload)))
    
    # 打开网页
    if base_url and item.route_name:
        # 简单构建 URL
        route_params = item.route_params or {}
        if item.route_name == "WorkDetail":
            web_url = f"{base_url}/work/{route_params.get('ebookId', item_id)}"
        elif item.route_name == "MangaReaderPage":
            web_url = f"{base_url}/manga/{route_params.get('series_id', item_id)}"
        else:
            web_url = f"{base_url}"
        
        row.append(inline_button("🌐 网页", url=web_url))
    
    if row:
        return [row]
    return []


# ============== 搜索分页回调 ==============

@router.callback("search:")
async def callback_search(ctx: TelegramUpdateContext) -> None:
    """处理搜索相关回调"""
    data = ctx.callback_data
    
    parts = data.split(":", 2)
    if len(parts) < 2:
        await ctx.answer_callback("无效操作")
        return
    
    action = parts[1]
    
    if action == "page":
        # 分页回调
        payload = {}
        if len(parts) > 2:
            _, payload = parse_callback_data(f":{parts[2]}")
        
        keyword = payload.get("q", "")
        page = payload.get("p", 1)
        media_type = payload.get("t") or None
        
        if keyword:
            await ctx.answer_callback()
            await _do_search(ctx, keyword, media_type=media_type, page=page)
        else:
            await ctx.answer_callback("搜索参数错误")
    else:
        await ctx.answer_callback("功能开发中...")


# ============== 搜索结果操作回调 ==============

@router.callback("act:")
async def callback_action(ctx: TelegramUpdateContext) -> None:
    """处理搜索结果操作"""
    data = ctx.callback_data
    
    # 解析 act:xxx:{json}
    parts = data.split(":", 2)
    if len(parts) < 2:
        await ctx.answer_callback("无效操作")
        return
    
    action = parts[1]
    payload = {}
    if len(parts) > 2:
        _, payload = parse_callback_data(f":{parts[2]}")
    
    media_type = payload.get("t", "")
    item_id = payload.get("id", "")
    
    match action:
        case "subscribe":
            await _handle_subscribe(ctx, media_type, item_id)
        case "download":
            await _handle_download(ctx, media_type, item_id)
        case "read":
            await _handle_read(ctx, media_type, item_id)
        case "detail":
            await _handle_detail(ctx, media_type, item_id)
        case _:
            await ctx.answer_callback("功能开发中...")


async def _handle_subscribe(ctx: TelegramUpdateContext, media_type: str, item_id: str) -> None:
    """处理订阅操作"""
    if media_type == "manga":
        try:
            from app.services.manga_follow_service import create_follow
            
            await create_follow(
                ctx.session,
                user_id=ctx.app_user.id,
                series_id=int(item_id),
            )
            await ctx.answer_callback("✅ 已添加追更！", show_alert=True)
        except Exception as e:
            logger.warning(f"[telegram] subscribe manga failed: {e}")
            if "已经在追更" in str(e) or "already" in str(e).lower():
                await ctx.answer_callback("你已经在追更这部漫画了", show_alert=True)
            else:
                await ctx.answer_callback("❌ 添加失败，请稍后重试", show_alert=True)
    else:
        await ctx.answer_callback("暂不支持此类型的订阅", show_alert=True)


async def _handle_download(ctx: TelegramUpdateContext, media_type: str, item_id: str) -> None:
    """处理下载操作"""
    # TODO: 实现下载队列添加
    await ctx.answer_callback("⬇️ 下载功能开发中...", show_alert=True)


async def _handle_read(ctx: TelegramUpdateContext, media_type: str, item_id: str) -> None:
    """处理阅读操作"""
    base_url = getattr(settings, "FRONTEND_URL", "")
    
    if base_url:
        if media_type in ("novel", "audiobook"):
            url = f"{base_url}/work/{item_id}"
            await ctx.answer_callback(f"请在浏览器中打开: {url}")
        else:
            await ctx.answer_callback("暂不支持此类型")
    else:
        await ctx.answer_callback("请在网页端阅读")


async def _handle_detail(ctx: TelegramUpdateContext, media_type: str, item_id: str) -> None:
    """处理详情操作"""
    # 返回更多信息
    await ctx.answer_callback("详情功能开发中...")
