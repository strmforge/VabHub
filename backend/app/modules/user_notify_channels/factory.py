"""
用户通知渠道适配器工厂
NOTIFY-CORE 实现 + BOT-EXT-2 动作模型集成
"""

from datetime import datetime, timezone
from typing import Any, Optional, Union
from loguru import logger

from app.models.user_notify_channel import UserNotifyChannel
from app.models.enums.user_notify_channel_type import UserNotifyChannelType
from app.schemas.notify_actions import NotificationAction
from app.modules.user_notify_channels.base import (
    get_adapter_for_channel,
    ChannelCapabilities,
)


async def send_user_channel_message(
    channel: UserNotifyChannel,
    message: str,
    title: Optional[str] = None,
    url: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
    actions: Optional[Union[list[dict[str, Any]], list[NotificationAction]]] = None,
    event_type: Optional[str] = None,
    media_type: Optional[str] = None,
    target_id: Optional[int] = None,
) -> bool:
    """
    向用户通知渠道发送消息
    
    Args:
        channel: 用户通知渠道
        message: 消息内容
        title: 消息标题（可选）
        url: 链接 URL（可选）
        extra: 额外数据（可选）
        actions: 操作按钮列表（支持 NotificationAction 或旧格式 dict）
        event_type: 事件类型（可选）
        media_type: 媒体类型（可选）
        target_id: 目标 ID（可选）
        
    Returns:
        是否发送成功
    """
    # 转换动作格式
    normalized_actions = _normalize_actions(actions)
    
    try:
        match channel.channel_type:
            case UserNotifyChannelType.TELEGRAM_BOT:
                return await _send_telegram(channel, message, title, url, normalized_actions)
            case UserNotifyChannelType.WEBHOOK:
                return await _send_webhook(
                    channel, message, title, url, extra,
                    normalized_actions, event_type, media_type, target_id
                )
            case UserNotifyChannelType.BARK:
                return await _send_bark(channel, message, title, url, normalized_actions)
            case _:
                logger.warning(f"[user-notify] unsupported channel type: {channel.channel_type}")
                return False
    except Exception as e:
        logger.error(f"[user-notify] send to channel {channel.id} failed: {e}")
        return False


def _normalize_actions(
    actions: Optional[Union[list[dict[str, Any]], list[NotificationAction]]]
) -> list[NotificationAction]:
    """将动作列表统一转换为 NotificationAction 格式"""
    if not actions:
        return []
    
    result = []
    for action in actions:
        if isinstance(action, NotificationAction):
            result.append(action)
        elif isinstance(action, dict):
            # 旧格式转换
            result.append(_dict_to_action(action))
    
    return result


def _dict_to_action(d: dict[str, Any]) -> NotificationAction:
    """将旧格式 dict 转换为 NotificationAction"""
    from app.schemas.notify_actions import NotificationActionType
    
    action_type = d.get("type", "open")
    
    type_map = {
        "open": NotificationActionType.OPEN_WEB_URL,
        "download": NotificationActionType.DOWNLOAD,
        "mark_read": NotificationActionType.MARK_AS_READ,
        "subscribe": NotificationActionType.SUBSCRIBE,
    }
    
    return NotificationAction(
        id=d.get("id", "action"),
        label=d.get("label", "操作"),
        type=type_map.get(action_type, NotificationActionType.OPEN_WEB_URL),
        url=d.get("url"),
        target_id=d.get("id") if isinstance(d.get("id"), int) else None,
        media_type=d.get("target"),
    )


async def _send_telegram(
    channel: UserNotifyChannel,
    message: str,
    title: Optional[str] = None,
    url: Optional[str] = None,
    actions: Optional[list[NotificationAction]] = None,
) -> bool:
    """通过 Telegram Bot 发送消息（支持操作按钮）"""
    from app.schemas.notify_actions import NotificationActionType
    
    try:
        from app.modules.bots.telegram_bot_client import get_telegram_bot_client
        from app.modules.bots.telegram_keyboard import inline_keyboard, inline_button, callback_data
        from app.core.config import settings
        
        client = get_telegram_bot_client()
        if not client:
            logger.warning("[user-notify] telegram bot not configured")
            return False
        
        chat_id = channel.config.get("chat_id")
        if not chat_id:
            logger.warning(f"[user-notify] channel {channel.id} missing chat_id")
            return False
        
        # 获取渠道能力并降级动作
        adapter = get_adapter_for_channel(channel)
        base_url = getattr(settings, "FRONTEND_URL", "")
        degraded_actions, primary_url, hint_text = adapter.degrade_actions(actions or [], base_url)
        
        # 组装消息
        text = ""
        if title:
            text = f"*{title}*\n\n"
        text += message
        
        # 添加主 URL（如果有）
        if url:
            text += f"\n\n🔗 [查看详情]({url})"
        elif primary_url:
            text += f"\n\n🔗 [查看详情]({primary_url})"
        
        # 添加动作提示文本
        if hint_text:
            text += f"\n\n{hint_text}"
        
        # 构建操作按钮
        reply_markup = None
        if degraded_actions:
            buttons = []
            for action in degraded_actions[:8]:  # Telegram 最多 8 个按钮
                payload = {"t": action.media_type or "", "id": action.target_id or ""}
                
                match action.type:
                    case NotificationActionType.OPEN_WEB_URL:
                        if action.url:
                            buttons.append([inline_button(action.label or "🌐 打开", url=action.url)])
                        else:
                            buttons.append([inline_button(action.label or "📋 查看", callback_data=callback_data("notif:open", payload))])
                    
                    case NotificationActionType.OPEN_WEB_ROUTE:
                        action_url = action.to_url(base_url)
                        if action_url:
                            buttons.append([inline_button(action.label or "📋 查看", url=action_url)])
                        else:
                            buttons.append([inline_button(action.label or "📋 查看", callback_data=callback_data("notif:open", payload))])
                    
                    case NotificationActionType.OPEN_MANGA | NotificationActionType.OPEN_NOVEL | NotificationActionType.OPEN_AUDIOBOOK:
                        action_url = action.to_url(base_url)
                        if action_url:
                            buttons.append([inline_button(action.label, url=action_url)])
                        else:
                            buttons.append([inline_button(action.label, callback_data=callback_data("notif:open", payload))])
                    
                    case NotificationActionType.DOWNLOAD:
                        buttons.append([inline_button(action.label or "⬇️ 下载", callback_data=callback_data("notif:download", payload))])
                    
                    case NotificationActionType.MARK_AS_READ:
                        buttons.append([inline_button(action.label or "✅ 标记已读", callback_data=callback_data("notif:mark_read", payload))])
                    
                    case NotificationActionType.SUBSCRIBE:
                        buttons.append([inline_button(action.label or "📌 订阅", callback_data=callback_data("notif:subscribe", payload))])
                    
                    case NotificationActionType.RETRY:
                        buttons.append([inline_button(action.label or "🔄 重试", callback_data=callback_data("notif:retry", payload))])
                    
                    case _:
                        # 默认使用 URL 或回调
                        action_url = action.to_url(base_url)
                        if action_url:
                            buttons.append([inline_button(action.label, url=action_url)])
            
            if buttons:
                reply_markup = inline_keyboard(buttons)
        
        return await client.send_message(chat_id, text, parse_mode="Markdown", reply_markup=reply_markup)
        
    except ImportError:
        logger.warning("[user-notify] telegram bot client not available, using fallback")
        return await _send_telegram_fallback(channel, message, title, url)


async def _send_telegram_fallback(
    channel: UserNotifyChannel,
    message: str,
    title: Optional[str] = None,
    url: Optional[str] = None,
) -> bool:
    """Telegram 回退实现（直接调用 API）"""
    import httpx
    from app.core.config import settings
    
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    if not bot_token:
        logger.warning("[user-notify] TELEGRAM_BOT_TOKEN not configured")
        return False
    
    chat_id = channel.config.get("chat_id")
    if not chat_id:
        return False
    
    text = ""
    if title:
        text = f"*{title}*\n\n"
    text += message
    if url:
        text += f"\n\n🔗 [查看详情]({url})"
    
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(api_url, json=payload)
            resp.raise_for_status()
            logger.info(f"[user-notify] sent telegram message to {chat_id}")
            return True
    except httpx.HTTPError as e:
        logger.error(f"[user-notify] telegram send failed: {e}")
        return False


async def _send_webhook(
    channel: UserNotifyChannel,
    message: str,
    title: Optional[str] = None,
    url: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
    actions: Optional[list[NotificationAction]] = None,
    event_type: Optional[str] = None,
    media_type: Optional[str] = None,
    target_id: Optional[int] = None,
) -> bool:
    """通过 Webhook 发送消息（标准化 payload）"""
    import httpx
    from app.core.config import settings
    
    webhook_url = channel.config.get("url")
    if not webhook_url:
        logger.warning(f"[user-notify] channel {channel.id} missing webhook url")
        return False
    
    method = channel.config.get("method", "POST").upper()
    headers = channel.config.get("headers", {})
    secret = channel.config.get("secret")
    base_url = getattr(settings, "FRONTEND_URL", "")
    
    # 构建标准化 payload
    payload = {
        "source": "vabhub",
        "event_type": event_type or "NOTIFICATION",
        "severity": "info",
        "title": title or "VabHub 通知",
        "message": message,
        "media_type": media_type,
        "target_id": target_id,
        "time": datetime.now(timezone.utc).isoformat(),
        "web_url": url,
        "actions": [],
        "raw_payload": extra,
    }
    
    # 序列化动作
    if actions:
        for action in actions:
            action_dict = {
                "id": action.id,
                "label": action.label,
                "type": action.type.value,
            }
            
            # 添加 URL
            action_url = action.to_url(base_url)
            if action_url:
                action_dict["url"] = action_url
            
            # API 调用信息
            if action.api_path:
                action_dict["api_path"] = action.api_path
                action_dict["api_method"] = action.api_method
                if action.api_body:
                    action_dict["api_body"] = action.api_body
            
            payload["actions"].append(action_dict)
    
    if secret:
        headers["X-Webhook-Secret"] = secret
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            if method == "GET":
                resp = await client.get(webhook_url, params={"data": str(payload)}, headers=headers)
            else:
                resp = await client.post(webhook_url, json=payload, headers=headers)
            resp.raise_for_status()
            logger.info(f"[user-notify] sent webhook to {webhook_url}")
            return True
    except httpx.HTTPError as e:
        logger.error(f"[user-notify] webhook send failed: {e}")
        return False


async def _send_bark(
    channel: UserNotifyChannel,
    message: str,
    title: Optional[str] = None,
    url: Optional[str] = None,
    actions: Optional[list[NotificationAction]] = None,
) -> bool:
    """通过 Bark 发送消息（动作降级到 URL）"""
    import httpx
    from app.core.config import settings
    
    server = channel.config.get("server", "").rstrip("/")
    if not server:
        logger.warning(f"[user-notify] channel {channel.id} missing bark server")
        return False
    
    sound = channel.config.get("sound", "alarm")
    group = channel.config.get("group", "VabHub")
    base_url = getattr(settings, "FRONTEND_URL", "")
    
    # 获取渠道能力并降级动作
    adapter = get_adapter_for_channel(channel)
    _, primary_url, hint_text = adapter.degrade_actions(actions or [], base_url)
    
    # 构建消息体
    body = message
    
    # 添加动作提示
    if hint_text:
        body += f"\n\n{hint_text}"
    
    # 限制长度
    if len(body) > 1024:
        body = body[:1020] + "..."
    
    bark_url = f"{server}/push"
    payload = {
        "title": title or "VabHub 通知",
        "body": body,
        "sound": sound,
        "group": group,
    }
    
    # 设置点击 URL（优先使用传入的 url，其次是动作降级的 primary_url）
    if url:
        payload["url"] = url
    elif primary_url:
        payload["url"] = primary_url
    elif base_url:
        payload["url"] = base_url
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(bark_url, json=payload)
            resp.raise_for_status()
            logger.info(f"[user-notify] sent bark notification")
            return True
    except httpx.HTTPError as e:
        logger.error(f"[user-notify] bark send failed: {e}")
        return False
