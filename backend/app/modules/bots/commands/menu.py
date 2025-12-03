"""
主菜单命令
BOT-TELEGRAM Phase 2

/menu 和菜单回调处理
"""

from app.modules.bots.telegram_router import router
from app.modules.bots.telegram_context import TelegramUpdateContext
from app.modules.bots.telegram_keyboard import (
    build_main_menu_keyboard,
    build_back_to_menu_button,
    inline_keyboard,
    inline_button,
    parse_callback_data,
)


# ============== /menu ==============

@router.command("/menu")
async def cmd_menu(ctx: TelegramUpdateContext) -> None:
    """显示主菜单"""
    await ctx.reply_text(
        "📱 *VabHub 主菜单*\n\n选择一个功能开始：",
        reply_markup=build_main_menu_keyboard(),
    )


# ============== 菜单回调 ==============

@router.callback("menu:")
async def callback_menu(ctx: TelegramUpdateContext) -> None:
    """处理菜单回调"""
    action = ctx.callback_data.replace("menu:", "")
    
    match action:
        case "main":
            await _show_main_menu(ctx)
        case "reading":
            await _show_reading_menu(ctx)
        case "movies":
            await _show_movies_menu(ctx)
        case "novels":
            await _show_novels_menu(ctx)
        case "manga":
            await _show_manga_menu(ctx)
        case "music":
            await _show_music_menu(ctx)
        case "search":
            await _show_search_prompt(ctx)
        case "subscriptions":
            await _show_subscriptions_menu(ctx)
        case "downloads":
            await _show_downloads_menu(ctx)
        case "settings":
            await _show_settings_menu(ctx)
        case _:
            await ctx.answer_callback("功能开发中...")


async def _show_main_menu(ctx: TelegramUpdateContext) -> None:
    """显示主菜单"""
    await ctx.edit_message_text(
        "📱 *VabHub 主菜单*\n\n选择一个功能开始：",
        reply_markup=build_main_menu_keyboard(),
    )
    await ctx.answer_callback()


async def _show_reading_menu(ctx: TelegramUpdateContext) -> None:
    """阅读中心菜单"""
    text = """
📚 *阅读中心*

查看你的阅读进度、最近活动和收藏书架。

**只读视角：**
- 进行中视角：查看你当前在读/在听/在看的进度（只读）
- 时间线视角：查看最近的阅读/收听/更新活动（只读）
- 书架视角：查看你收藏的小说/有声书/漫画（只读）

**交互操作（⚠️ 会修改状态）：**
- /reading_done <编号>：标记某条为已完成
- /reading_fav <编号>：将某条加入书架
- /shelf_unfav <编号>：取消收藏

快捷命令：
/reading - 进行中
/reading_recent - 最近活动
/shelf - 我的书架
"""
    keyboard = inline_keyboard([
        [
            inline_button("📖 进行中", callback_data="reading:ongoing"),
            inline_button("📋 最近活动", callback_data="reading:recent"),
        ],
        [
            inline_button("📚 我的书架", callback_data="reading:shelf"),
        ],
        [inline_button("« 返回主菜单", callback_data="menu:main")],
    ])
    
    await ctx.edit_message_text(text, reply_markup=keyboard)
    await ctx.answer_callback()


async def _show_movies_menu(ctx: TelegramUpdateContext) -> None:
    """影视中心菜单"""
    text = """
📺 *影视中心*

搜索电影和电视剧，添加到下载队列。

直接发送影视名称开始搜索！
"""
    keyboard = inline_keyboard([
        [inline_button("🔍 搜索影视", callback_data="menu:search")],
        [inline_button("⬇️ 下载队列", callback_data="menu:downloads")],
        [inline_button("« 返回主菜单", callback_data="menu:main")],
    ])
    
    await ctx.edit_message_text(text, reply_markup=keyboard)
    await ctx.answer_callback()


async def _show_novels_menu(ctx: TelegramUpdateContext) -> None:
    """小说/有声书菜单"""
    text = """
📖 *小说 & 有声书*

管理你的电子书和有声书库。

发送书名搜索，或查看阅读进度。
"""
    keyboard = inline_keyboard([
        [inline_button("🔍 搜索书籍", callback_data="menu:search")],
        [inline_button("📖 阅读进度", callback_data="reading:ongoing")],
        [inline_button("« 返回主菜单", callback_data="menu:main")],
    ])
    
    await ctx.edit_message_text(text, reply_markup=keyboard)
    await ctx.answer_callback()


async def _show_manga_menu(ctx: TelegramUpdateContext) -> None:
    """漫画中心菜单"""
    text = """
📚 *漫画中心*

搜索漫画，管理追更订阅。

发送漫画名称搜索，点击"追更"订阅更新。
"""
    keyboard = inline_keyboard([
        [inline_button("🔍 搜索漫画", callback_data="menu:search")],
        [inline_button("📌 我的追更", callback_data="sub:list:manga")],
        [inline_button("« 返回主菜单", callback_data="menu:main")],
    ])
    
    await ctx.edit_message_text(text, reply_markup=keyboard)
    await ctx.answer_callback()


async def _show_music_menu(ctx: TelegramUpdateContext) -> None:
    """音乐中心菜单"""
    text = """
🎵 *音乐中心*

搜索音乐，管理榜单订阅。

发送歌曲/歌手名称搜索。
"""
    keyboard = inline_keyboard([
        [inline_button("🔍 搜索音乐", callback_data="menu:search")],
        [inline_button("📊 我的订阅榜单", callback_data="sub:list:music")],
        [inline_button("« 返回主菜单", callback_data="menu:main")],
    ])
    
    await ctx.edit_message_text(text, reply_markup=keyboard)
    await ctx.answer_callback()


async def _show_search_prompt(ctx: TelegramUpdateContext) -> None:
    """搜索提示"""
    text = """
🔍 *搜索*

直接发送你想搜索的内容：
• 电影/剧集名称
• 小说/有声书名
• 漫画名称
• 歌曲/歌手名

例如：`三体`、`周杰伦`、`进击的巨人`
"""
    await ctx.edit_message_text(text, reply_markup=build_back_to_menu_button())
    await ctx.answer_callback()


async def _show_subscriptions_menu(ctx: TelegramUpdateContext) -> None:
    """订阅管理菜单"""
    text = """
🧩 *订阅管理*

管理你的各类订阅。

发送 `/subscriptions` 查看完整列表。
"""
    keyboard = inline_keyboard([
        [
            inline_button("📚 漫画追更", callback_data="sub:list:manga"),
            inline_button("🎵 音乐榜单", callback_data="sub:list:music"),
        ],
        [inline_button("📋 全部订阅", callback_data="sub:list:all")],
        [inline_button("« 返回主菜单", callback_data="menu:main")],
    ])
    
    await ctx.edit_message_text(text, reply_markup=keyboard)
    await ctx.answer_callback()


async def _show_downloads_menu(ctx: TelegramUpdateContext) -> None:
    """下载任务菜单"""
    text = """
⬇️ *下载任务*

查看和管理下载任务。

发送 `/downloads` 查看完整列表。
"""
    keyboard = inline_keyboard([
        [inline_button("📋 查看任务", callback_data="dl:list")],
        [inline_button("« 返回主菜单", callback_data="menu:main")],
    ])
    
    await ctx.edit_message_text(text, reply_markup=keyboard)
    await ctx.answer_callback()


async def _show_settings_menu(ctx: TelegramUpdateContext) -> None:
    """设置菜单"""
    from app.core.config import settings
    
    text = f"""
⚙️ *设置*

👤 *账号*: {ctx.app_user.username if ctx.app_user else '未知'}
📱 *Telegram*: @{ctx.username or '未设置'}

更多设置请访问网页端。
"""
    base_url = getattr(settings, "FRONTEND_URL", "")
    buttons = []
    if base_url:
        buttons.append([inline_button("🌐 打开网页设置", url=f"{base_url}/settings/notify-channels")])
    buttons.append([inline_button("« 返回主菜单", callback_data="menu:main")])
    
    await ctx.edit_message_text(text, reply_markup=inline_keyboard(buttons))
    await ctx.answer_callback()


# ============== 阅读中心回调 ==============

@router.callback("reading:")
async def callback_reading(ctx: TelegramUpdateContext) -> None:
    """处理阅读中心回调"""
    action = ctx.callback_data.replace("reading:", "")
    
    match action:
        case "ongoing":
            await ctx.reply_text(
                "📖 进行中阅读（只读模式）\n\n"
                "发送 `/reading` 查看进行中的阅读列表\n"
                "发送 `/reading_books` 查看小说\n"
                "发送 `/reading_audio` 查看有声书\n"
                "发送 `/reading_manga` 查看漫画",
                reply_markup=build_back_to_menu_button()
            )
        case "recent":
            await ctx.reply_text(
                "📋 最近阅读活动（只读模式）\n\n"
                "发送 `/reading_recent` 查看最近活动时间线\n"
                "发送 `/reading_recent_open 1` 打开对应页面",
                reply_markup=build_back_to_menu_button()
            )
        case "shelf":
            await ctx.reply_text(
                "📚 我的书架（只读模式）\n\n"
                "发送 `/shelf` 查看混合书架列表\n"
                "发送 `/shelf_books` 查看我收藏的小说\n"
                "发送 `/shelf_audio` 查看我收藏的有声书\n"
                "发送 `/shelf_manga` 查看我收藏的漫画",
                reply_markup=build_back_to_menu_button()
            )
            await ctx.answer_callback()
        case _:
            await ctx.answer_callback("功能开发中...")


# ============== noop 回调 ==============

@router.callback("noop")
async def callback_noop(ctx: TelegramUpdateContext) -> None:
    """空操作"""
    await ctx.answer_callback()


@router.callback("cancel")
async def callback_cancel(ctx: TelegramUpdateContext) -> None:
    """取消操作"""
    await ctx.answer_callback("已取消")
    await ctx.edit_message_text("操作已取消", reply_markup=build_back_to_menu_button())
