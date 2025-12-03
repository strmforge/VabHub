"""
通知测试 API
BOT-EXT-2 实现

多渠道通知测试与预览
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from loguru import logger

from app.core.database import get_session
from app.core.auth import get_current_user
from app.models.user import User
from app.models.enums.notification_type import NotificationType
from app.schemas.notify_actions import (
    NotificationAction,
    NotificationActionType,
    action_open_manga,
    action_mark_read,
    action_open_url,
)
from app.modules.user_notify_channels.base import (
    get_capabilities_for_channel_type,
    ChannelCapabilities,
)
from app.services.notify_user_service import notify_user
from app.services.user_notify_channel_service import get_enabled_channels_for_user
from app.core.config import settings


router = APIRouter(prefix="/notify/test", tags=["notify-test"])


# ============== 请求/响应模型 ==============

class SendSampleRequest(BaseModel):
    """发送样例通知请求"""
    user_id: Optional[int] = None  # 不填则使用当前用户
    event_type: str = "MANGA_UPDATED"
    channels: list[str] = ["telegram", "webhook", "bark"]


class SendSampleResponse(BaseModel):
    """发送样例通知响应"""
    success: bool
    results: dict[str, dict]  # {"telegram": {"ok": true}, ...}


class PreviewResponse(BaseModel):
    """预览响应"""
    base: dict
    per_channel: dict


class ChannelCapabilitiesResponse(BaseModel):
    """渠道能力响应"""
    channel_type: str
    capabilities: dict


# ============== 样例通知构建 ==============

def build_sample_notification(event_type: str) -> dict:
    """构建样例通知数据"""
    base_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    
    samples = {
        "MANGA_UPDATED": {
            "title": "《海贼王》有新章节",
            "message": "站点: CopyManga\n最新: 第 1100 话\n\n这是一条测试通知，用于验证多渠道通知功能。",
            "event_type": NotificationType.MANGA_UPDATED,
            "media_type": "manga",
            "target_id": 1,
            "url": f"{base_url}/manga/1",
            "actions": [
                action_open_manga(1, "打开漫画"),
                action_mark_read(target_id=1, media_type="manga"),
            ],
        },
        "NOVEL_NEW_CHAPTER": {
            "title": "《三体》有新章节",
            "message": "第 10 章: 黑暗森林\n\n这是一条测试通知。",
            "event_type": NotificationType.NOVEL_NEW_CHAPTER,
            "media_type": "novel",
            "target_id": 1,
            "url": f"{base_url}/work/1",
            "actions": [
                action_open_url(f"{base_url}/work/1", "打开小说", primary=True),
            ],
        },
        "TTS_JOB_COMPLETED": {
            "title": "TTS 任务完成",
            "message": "《三体》有声书已生成完毕\n时长: 约 12 小时\n\n这是一条测试通知。",
            "event_type": NotificationType.TTS_JOB_COMPLETED,
            "media_type": "audiobook",
            "target_id": 1,
            "url": f"{base_url}/audiobook/1",
            "actions": [
                action_open_url(f"{base_url}/audiobook/1", "打开有声书", primary=True),
            ],
        },
        "AUDIOBOOK_READY": {
            "title": "有声书就绪",
            "message": "《流浪地球》有声书已准备好\n\n这是一条测试通知。",
            "event_type": NotificationType.AUDIOBOOK_READY,
            "media_type": "audiobook",
            "target_id": 1,
            "url": f"{base_url}/audiobook/1",
            "actions": [
                action_open_url(f"{base_url}/audiobook/1", "开始收听", primary=True),
            ],
        },
        "SYSTEM_ALERT": {
            "title": "系统告警测试",
            "message": "这是一条系统告警测试通知\n严重程度: 警告\n\n用于验证告警通知渠道。",
            "event_type": NotificationType.SYSTEM_MESSAGE,
            "media_type": None,
            "target_id": None,
            "url": f"{base_url}/admin/system",
            "actions": [
                action_open_url(f"{base_url}/admin/system", "查看系统状态", primary=True),
            ],
        },
    }
    
    return samples.get(event_type, samples["MANGA_UPDATED"])


# ============== API 端点 ==============

@router.post("/send_sample", response_model=SendSampleResponse)
async def send_sample_notification(
    request: SendSampleRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    发送样例通知到指定渠道
    
    仅管理员可用
    """
    # 确定目标用户
    target_user_id = request.user_id or current_user.id
    
    from sqlalchemy import select
    result = await session.execute(
        select(User).where(User.id == target_user_id)
    )
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 构建样例通知
    sample = build_sample_notification(request.event_type)
    
    # 发送通知
    results = {}
    
    try:
        await notify_user(
            session,
            target_user,
            title=sample["title"],
            message=sample["message"],
            event_type=sample["event_type"],
            media_type=sample["media_type"],
            target_id=sample["target_id"],
            url=sample["url"],
            actions=sample["actions"],
            skip_web=False,
        )
        results["all"] = {"ok": True, "message": "通知已发送"}
    except Exception as e:
        logger.error(f"[notify-test] send sample failed: {e}")
        results["all"] = {"ok": False, "error": str(e)}
    
    return SendSampleResponse(
        success=results.get("all", {}).get("ok", False),
        results=results,
    )


@router.get("/preview", response_model=PreviewResponse)
async def preview_notification(
    event_type: str = "MANGA_UPDATED",
    current_user: User = Depends(require_admin),
):
    """
    预览样例通知在各渠道的表现
    
    仅管理员可用
    """
    base_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    sample = build_sample_notification(event_type)
    
    # 基础数据
    base = {
        "title": sample["title"],
        "message": sample["message"],
        "event_type": sample["event_type"].value if sample["event_type"] else None,
        "media_type": sample["media_type"],
        "target_id": sample["target_id"],
        "url": sample["url"],
        "actions": [
            {
                "id": a.id,
                "label": a.label,
                "type": a.type.value,
                "url": a.to_url(base_url),
            }
            for a in sample["actions"]
        ],
    }
    
    # 各渠道渲染预览
    per_channel = {}
    
    # Telegram 预览
    telegram_caps = get_capabilities_for_channel_type("telegram")
    telegram_text = f"*{sample['title']}*\n\n{sample['message']}"
    if sample["url"]:
        telegram_text += f"\n\n🔗 [查看详情]({sample['url']})"
    
    telegram_buttons = []
    for action in sample["actions"][:telegram_caps.max_button_count]:
        action_url = action.to_url(base_url)
        telegram_buttons.append({
            "text": action.label,
            "url": action_url,
        })
    
    per_channel["telegram"] = {
        "capabilities": telegram_caps.model_dump(),
        "rendered_text": telegram_text,
        "keyboard": telegram_buttons,
    }
    
    # Webhook 预览
    webhook_caps = get_capabilities_for_channel_type("webhook")
    webhook_payload = {
        "source": "vabhub",
        "event_type": sample["event_type"].value if sample["event_type"] else "NOTIFICATION",
        "severity": "info",
        "title": sample["title"],
        "message": sample["message"],
        "media_type": sample["media_type"],
        "target_id": sample["target_id"],
        "web_url": sample["url"],
        "actions": [
            {
                "id": a.id,
                "label": a.label,
                "type": a.type.value,
                "url": a.to_url(base_url),
            }
            for a in sample["actions"]
        ],
    }
    
    per_channel["webhook"] = {
        "capabilities": webhook_caps.model_dump(),
        "payload": webhook_payload,
    }
    
    # Bark 预览
    bark_caps = get_capabilities_for_channel_type("bark")
    bark_body = sample["message"]
    
    # 降级：其他动作变成文本提示
    if len(sample["actions"]) > 1:
        other_actions = [a.label for a in sample["actions"][1:]]
        bark_body += f"\n\n其他操作（请在 Web 端进行）：\n• " + "\n• ".join(other_actions)
    
    if len(bark_body) > 1024:
        bark_body = bark_body[:1020] + "..."
    
    primary_url = sample["url"]
    if sample["actions"]:
        primary_url = sample["actions"][0].to_url(base_url) or sample["url"]
    
    per_channel["bark"] = {
        "capabilities": bark_caps.model_dump(),
        "title": sample["title"],
        "body": bark_body,
        "url": primary_url,
    }
    
    return PreviewResponse(base=base, per_channel=per_channel)


@router.get("/capabilities/{channel_type}", response_model=ChannelCapabilitiesResponse)
async def get_channel_capabilities(
    channel_type: str,
    current_user: User = Depends(get_current_user),
):
    """获取指定渠道的能力声明"""
    caps = get_capabilities_for_channel_type(channel_type)
    
    return ChannelCapabilitiesResponse(
        channel_type=channel_type,
        capabilities=caps.model_dump(),
    )


@router.get("/my_channels")
async def get_my_channels(
    db: DbSessionDep,
    current_user: CurrentUserDep,
):
    """获取当前用户已配置的通知渠道"""
    channels = await get_enabled_channels_for_user(db, current_user.id)
    
    return {
        "channels": [
            {
                "id": c.id,
                "type": c.channel_type.value,
                "name": c.name,
                "enabled": c.enabled,
            }
            for c in channels
        ]
    }
