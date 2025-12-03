"""
Telegram Bot 键盘构建器
BOT-TELEGRAM Phase 2

提供 Inline Keyboard 构建工具
"""

import json
from typing import Any, Optional


def inline_keyboard(rows: list[list[dict]]) -> dict:
    """
    构建 InlineKeyboardMarkup
    
    Args:
        rows: 按钮行列表，每行是按钮列表
        
    Returns:
        InlineKeyboardMarkup dict
    """
    return {"inline_keyboard": rows}


def inline_button(
    text: str,
    callback_data: Optional[str] = None,
    url: Optional[str] = None,
) -> dict:
    """
    构建单个 InlineKeyboardButton
    
    Args:
        text: 按钮文本
        callback_data: 回调数据
        url: 跳转链接
    """
    button = {"text": text}
    if callback_data:
        button["callback_data"] = callback_data
    elif url:
        button["url"] = url
    return button


def callback_data(action: str, payload: Optional[dict] = None) -> str:
    """
    构建回调数据字符串
    
    格式: action:json_payload
    
    Args:
        action: 动作标识
        payload: 载荷数据（会 JSON 序列化）
    """
    if payload:
        return f"{action}:{json.dumps(payload, separators=(',', ':'), ensure_ascii=False)}"
    return action


def parse_callback_data(data: str) -> tuple[str, dict]:
    """
    解析回调数据
    
    Returns:
        (action, payload_dict)
    """
    if ":" not in data:
        return data, {}
    
    action, rest = data.split(":", 1)
    try:
        payload = json.loads(rest)
    except json.JSONDecodeError:
        payload = {"raw": rest}
    
    return action, payload


# ============== 预定义键盘 ==============

def build_main_menu_keyboard() -> dict:
    """构建主菜单键盘"""
    return inline_keyboard([
        [
            inline_button("📚 阅读中心", callback_data="menu:reading"),
            inline_button("📺 影视中心", callback_data="menu:movies"),
        ],
        [
            inline_button("📖 小说/有声书", callback_data="menu:novels"),
            inline_button("📚 漫画中心", callback_data="menu:manga"),
        ],
        [
            inline_button("🎵 音乐中心", callback_data="menu:music"),
        ],
        [
            inline_button("🔍 搜索", callback_data="menu:search"),
            inline_button("🧩 订阅管理", callback_data="menu:subscriptions"),
        ],
        [
            inline_button("⬇️ 下载任务", callback_data="menu:downloads"),
            inline_button("⚙️ 设置", callback_data="menu:settings"),
        ],
    ])


def build_back_button(to: str = "menu:main") -> dict:
    """构建返回按钮"""
    return inline_keyboard([
        [inline_button("« 返回", callback_data=to)]
    ])


def build_back_to_menu_button() -> dict:
    """返回主菜单按钮"""
    return build_back_button("menu:main")


def build_confirm_keyboard(
    confirm_callback: str,
    cancel_callback: str = "cancel",
    confirm_text: str = "✅ 确认",
    cancel_text: str = "❌ 取消",
) -> dict:
    """构建确认/取消键盘"""
    return inline_keyboard([
        [
            inline_button(confirm_text, callback_data=confirm_callback),
            inline_button(cancel_text, callback_data=cancel_callback),
        ]
    ])


def build_pagination_keyboard(
    current_page: int,
    total_pages: int,
    callback_prefix: str,
    extra_buttons: Optional[list[dict]] = None,
) -> dict:
    """
    构建分页键盘
    
    Args:
        current_page: 当前页（从 1 开始）
        total_pages: 总页数
        callback_prefix: 回调前缀，会拼接 :page={n}
        extra_buttons: 额外的按钮行
    """
    buttons = []
    
    # 分页行
    page_row = []
    if current_page > 1:
        page_row.append(inline_button("« 上一页", callback_data=f"{callback_prefix}:page={current_page - 1}"))
    
    page_row.append(inline_button(f"{current_page}/{total_pages}", callback_data="noop"))
    
    if current_page < total_pages:
        page_row.append(inline_button("下一页 »", callback_data=f"{callback_prefix}:page={current_page + 1}"))
    
    if page_row:
        buttons.append(page_row)
    
    # 额外按钮
    if extra_buttons:
        buttons.extend(extra_buttons)
    
    # 返回按钮
    buttons.append([inline_button("« 返回主菜单", callback_data="menu:main")])
    
    return inline_keyboard(buttons)


# ============== 搜索结果按钮 ==============

def build_search_result_buttons(
    media_type: str,
    item_id: int,
    title: str,
    web_url: Optional[str] = None,
) -> dict:
    """
    构建搜索结果操作按钮
    
    Args:
        media_type: 媒体类型 (movie/tv/manga/music/novel/audiobook)
        item_id: 项目 ID
        title: 标题（用于显示）
        web_url: Web 详情页 URL
    """
    payload = {"t": media_type, "id": item_id}
    
    buttons = []
    
    # 第一行：详情 + 订阅/下载
    row1 = [inline_button("📋 详情", callback_data=callback_data("act:detail", payload))]
    
    if media_type in ("movie", "tv", "music"):
        row1.append(inline_button("⬇️ 下载", callback_data=callback_data("act:download", payload)))
    elif media_type == "manga":
        row1.append(inline_button("📌 追更", callback_data=callback_data("act:subscribe", payload)))
    elif media_type in ("novel", "audiobook"):
        row1.append(inline_button("📖 阅读", callback_data=callback_data("act:read", payload)))
    
    buttons.append(row1)
    
    # 第二行：打开网页
    if web_url:
        buttons.append([inline_button("🌐 打开网页", url=web_url)])
    
    return inline_keyboard(buttons)


# ============== 订阅管理按钮 ==============

def build_subscription_buttons(
    sub_id: int,
    sub_kind: str,
    is_enabled: bool,
) -> dict:
    """
    构建订阅管理按钮
    
    Args:
        sub_id: 订阅 ID
        sub_kind: 订阅类型
        is_enabled: 是否启用
    """
    payload = {"id": sub_id, "k": sub_kind}
    
    toggle_text = "⏸ 暂停" if is_enabled else "▶️ 启用"
    
    return inline_keyboard([
        [
            inline_button(toggle_text, callback_data=callback_data("sub:toggle", payload)),
            inline_button("🔄 立即执行", callback_data=callback_data("sub:run", payload)),
        ],
        [
            inline_button("🌐 打开网页", callback_data=callback_data("sub:open", payload)),
        ],
    ])


# ============== 下载任务按钮 ==============

def build_download_buttons(
    job_id: int,
    status: str,
) -> dict:
    """
    构建下载任务按钮
    
    Args:
        job_id: 任务 ID
        status: 任务状态
    """
    payload = {"id": job_id}
    buttons = []
    
    if status == "failed":
        buttons.append([
            inline_button("🔄 重试", callback_data=callback_data("dl:retry", payload)),
            inline_button("⏭ 跳过", callback_data=callback_data("dl:skip", payload)),
        ])
    elif status in ("queued", "downloading"):
        buttons.append([
            inline_button("⏹ 取消", callback_data=callback_data("dl:cancel", payload)),
        ])
    
    buttons.append([
        inline_button("📋 详情", callback_data=callback_data("dl:detail", payload)),
    ])
    
    return inline_keyboard(buttons)


# ============== 阅读进度按钮 ==============

def build_reading_buttons(
    media_type: str,
    item_id: int,
    web_url: Optional[str] = None,
) -> dict:
    """构建阅读进度按钮"""
    payload = {"t": media_type, "id": item_id}
    
    buttons = []
    
    row = []
    if web_url:
        row.append(inline_button("📖 继续阅读", url=web_url))
    row.append(inline_button("✅ 标记完成", callback_data=callback_data("read:finish", payload)))
    buttons.append(row)
    
    return inline_keyboard(buttons)
