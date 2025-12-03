"""
通知偏好 API
NOTIFY-UX-1 实现

路由前缀：/api/notify/preferences
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.notify_preferences import (
    UserNotifyPreferenceCreate,
    UserNotifyPreferenceUpdate,
    UserNotifyPreferenceRead,
    UserNotifyPreferenceMatrix,
    UserNotifySnoozeUpdate,
    UserNotifySnoozeRead,
    SnoozeRequest,
    MuteNotificationTypeRequest,
)
from app.services import notify_preference_service


router = APIRouter(prefix="/notify/preferences", tags=["notify-preferences"])


# ============== 偏好矩阵 ==============

@router.get("/matrix", response_model=UserNotifyPreferenceMatrix)
async def get_preference_matrix(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取当前用户的完整通知偏好矩阵
    
    包含：
    - 所有偏好配置
    - 静音/Snooze 状态
    - 可用的通知类型列表
    """
    return await notify_preference_service.get_user_matrix(db, current_user.id)


# ============== 偏好 CRUD ==============

@router.put("", response_model=UserNotifyPreferenceRead)
async def upsert_preference(
    data: UserNotifyPreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建或更新通知偏好
    
    唯一键：(notification_type, media_type, target_id)
    - 若存在则更新
    - 不存在则创建
    """
    pref = await notify_preference_service.upsert_preference(db, current_user.id, data)
    return UserNotifyPreferenceRead.model_validate(pref)


@router.delete("/{preference_id}")
async def delete_preference(
    preference_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除通知偏好（恢复默认行为）"""
    success = await notify_preference_service.delete_preference(db, current_user.id, preference_id)
    if not success:
        raise HTTPException(status_code=404, detail="偏好不存在")
    return {"success": True}


# ============== 静音/Snooze ==============

@router.get("/snooze", response_model=Optional[UserNotifySnoozeRead])
async def get_snooze_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的静音/Snooze 状态"""
    snooze = await notify_preference_service.get_user_snooze(db, current_user.id)
    if snooze:
        return UserNotifySnoozeRead.model_validate(snooze)
    return None


@router.put("/snooze", response_model=UserNotifySnoozeRead)
async def update_snooze(
    data: UserNotifySnoozeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新静音/Snooze 状态
    
    支持：
    - muted: 全局静音开关
    - snooze_until: 静音到指定时间
    - allow_critical_only: 静音时仍允许重要通知
    """
    snooze = await notify_preference_service.set_snooze(
        db,
        current_user.id,
        muted=data.muted,
        snooze_until=data.snooze_until,
        allow_critical_only=data.allow_critical_only,
    )
    return UserNotifySnoozeRead.model_validate(snooze)


@router.post("/snooze/quick", response_model=UserNotifySnoozeRead)
async def quick_snooze(
    data: SnoozeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    快速 Snooze
    
    支持：
    - duration_minutes: 静音指定分钟数（5-1440）
    - until: 静音到指定时间
    """
    snooze_until = None
    if data.duration_minutes:
        snooze_until = datetime.utcnow() + timedelta(minutes=data.duration_minutes)
    elif data.until:
        snooze_until = data.until
    
    snooze = await notify_preference_service.set_snooze(
        db,
        current_user.id,
        snooze_until=snooze_until,
        allow_critical_only=data.allow_critical_only,
    )
    return UserNotifySnoozeRead.model_validate(snooze)


@router.delete("/snooze")
async def clear_snooze(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """清除静音/Snooze 状态（恢复正常）"""
    await notify_preference_service.clear_snooze(db, current_user.id)
    return {"success": True}


# ============== 快捷操作 ==============

@router.post("/mute-type")
async def mute_notification_type(
    data: MuteNotificationTypeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    静音某类通知
    
    用于从通知列表中快速静音
    """
    pref_data = UserNotifyPreferenceUpdate(
        notification_type=data.notification_type,
        media_type=data.media_type,
        target_id=data.target_id,
        muted=True,
        enable_web=False,
        enable_telegram=False,
        enable_webhook=False,
        enable_bark=False,
    )
    pref = await notify_preference_service.upsert_preference(db, current_user.id, pref_data)
    return {"success": True, "preference_id": pref.id}


@router.post("/unmute-type")
async def unmute_notification_type(
    data: MuteNotificationTypeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取消静音某类通知
    """
    # 查找并删除对应的静音偏好
    pref = await notify_preference_service.get_preference(
        db,
        current_user.id,
        data.notification_type,
        data.media_type,
        data.target_id,
    )
    
    if pref:
        await notify_preference_service.delete_preference(db, current_user.id, pref.id)
    
    return {"success": True}
