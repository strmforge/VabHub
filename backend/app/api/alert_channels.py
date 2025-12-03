"""
告警渠道管理 API
OPS-2A 实现
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.dependencies import get_current_admin_user
from app.models.user import User
from app.schemas.alert_channel import (
    AlertChannelCreate,
    AlertChannelRead,
    AlertChannelUpdate,
    AlertChannelTestRequest,
)
from app.services import alert_channel_service

router = APIRouter(prefix="/api/admin/alert_channels", tags=["告警渠道"])


@router.get("", response_model=List[AlertChannelRead])
async def list_alert_channels(
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_admin_user),
):
    """获取所有告警渠道"""
    return await alert_channel_service.list_channels(session)


@router.post("", response_model=AlertChannelRead)
async def create_alert_channel(
    data: AlertChannelCreate,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_admin_user),
):
    """创建告警渠道"""
    return await alert_channel_service.create_channel(session, data)


@router.get("/{channel_id}", response_model=AlertChannelRead)
async def get_alert_channel(
    channel_id: int,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_admin_user),
):
    """获取单个告警渠道"""
    channel = await alert_channel_service.get_channel(session, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="告警渠道不存在")
    return channel


@router.put("/{channel_id}", response_model=AlertChannelRead)
async def update_alert_channel(
    channel_id: int,
    data: AlertChannelUpdate,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_admin_user),
):
    """更新告警渠道"""
    channel = await alert_channel_service.update_channel(session, channel_id, data)
    if not channel:
        raise HTTPException(status_code=404, detail="告警渠道不存在")
    return channel


@router.delete("/{channel_id}")
async def delete_alert_channel(
    channel_id: int,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_admin_user),
):
    """删除告警渠道"""
    success = await alert_channel_service.delete_channel(session, channel_id)
    if not success:
        raise HTTPException(status_code=404, detail="告警渠道不存在")
    return {"message": "删除成功"}


@router.post("/{channel_id}/test")
async def test_alert_channel(
    channel_id: int,
    data: AlertChannelTestRequest = AlertChannelTestRequest(),
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_admin_user),
):
    """发送测试告警"""
    success = await alert_channel_service.send_test_message(
        session, channel_id, data.message
    )
    if not success:
        raise HTTPException(status_code=400, detail="发送测试消息失败")
    return {"message": "测试消息已发送"}
