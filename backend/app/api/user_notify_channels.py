"""
用户通知渠道 API
NOTIFY-CORE 实现
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.user_notify_channel import (
    UserNotifyChannelCreate,
    UserNotifyChannelRead,
    UserNotifyChannelUpdate,
    UserNotifyChannelTestResponse,
)
from app.services import user_notify_channel_service

router = APIRouter(prefix="/api/notify/channels", tags=["用户通知渠道"])


@router.get("", response_model=List[UserNotifyChannelRead])
async def list_user_notify_channels(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的通知渠道列表"""
    return await user_notify_channel_service.list_channels_for_user(session, current_user)


@router.post("", response_model=UserNotifyChannelRead)
async def create_user_notify_channel(
    data: UserNotifyChannelCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """创建通知渠道"""
    return await user_notify_channel_service.create_channel_for_user(session, current_user, data)


@router.get("/{channel_id}", response_model=UserNotifyChannelRead)
async def get_user_notify_channel(
    channel_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """获取单个通知渠道"""
    channel = await user_notify_channel_service.get_channel_for_user(session, current_user, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="通知渠道不存在")
    return channel


@router.put("/{channel_id}", response_model=UserNotifyChannelRead)
async def update_user_notify_channel(
    channel_id: int,
    data: UserNotifyChannelUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """更新通知渠道"""
    channel = await user_notify_channel_service.update_channel_for_user(
        session, current_user, channel_id, data
    )
    if not channel:
        raise HTTPException(status_code=404, detail="通知渠道不存在")
    return channel


@router.delete("/{channel_id}")
async def delete_user_notify_channel(
    channel_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """删除通知渠道"""
    success = await user_notify_channel_service.delete_channel_for_user(
        session, current_user, channel_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="通知渠道不存在")
    return {"message": "删除成功"}


@router.post("/{channel_id}/test", response_model=UserNotifyChannelTestResponse)
async def test_user_notify_channel(
    channel_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """测试通知渠道"""
    channel = await user_notify_channel_service.get_channel_for_user(session, current_user, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="通知渠道不存在")
    
    success = await user_notify_channel_service.test_channel(session, channel)
    
    return UserNotifyChannelTestResponse(
        success=success,
        message="测试消息已发送" if success else "发送失败，请检查配置",
    )
