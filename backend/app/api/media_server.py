"""
媒体服务器API
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from loguru import logger

from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.media_server.service import MediaServerService
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response,
    NotFoundResponse
)

router = APIRouter()


class MediaServerCreate(BaseModel):
    """创建媒体服务器请求"""
    name: str
    server_type: str  # plex, jellyfin, emby
    url: str
    api_key: Optional[str] = None
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    user_id: Optional[str] = None
    enabled: bool = True
    sync_enabled: bool = True
    sync_interval: int = 3600
    sync_watched_status: bool = True
    sync_playback_status: bool = True
    sync_metadata: bool = True


class MediaServerUpdate(BaseModel):
    """更新媒体服务器请求"""
    name: Optional[str] = None
    url: Optional[str] = None
    api_key: Optional[str] = None
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    user_id: Optional[str] = None
    enabled: Optional[bool] = None
    sync_enabled: Optional[bool] = None
    sync_interval: Optional[int] = None
    sync_watched_status: Optional[bool] = None
    sync_playback_status: Optional[bool] = None
    sync_metadata: Optional[bool] = None


@router.get("/", response_model=BaseResponse)
async def list_media_servers(
    enabled: Optional[bool] = Query(None, description="是否启用"),
    server_type: Optional[str] = Query(None, description="服务器类型: plex, jellyfin, emby"),
    db: AsyncSession = Depends(get_db)
):
    """获取媒体服务器列表"""
    try:
        service = MediaServerService(db)
        servers = await service.list_media_servers(enabled=enabled, server_type=server_type)
        return success_response(
            data=[{
                "id": s.id,
                "name": s.name,
                "server_type": s.server_type,
                "url": s.url,
                "enabled": s.enabled,
                "status": s.status,
                "last_check": s.last_check.isoformat() if s.last_check else None,
                "last_sync": s.last_sync.isoformat() if s.last_sync else None,
                "total_movies": s.total_movies,
                "total_tv_shows": s.total_tv_shows,
                "total_episodes": s.total_episodes,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat()
            } for s in servers],
            message="获取媒体服务器列表成功"
        )
    except Exception as e:
        logger.error(f"获取媒体服务器列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取媒体服务器列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/{server_id}", response_model=BaseResponse)
async def get_media_server(
    server_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取媒体服务器详情"""
    try:
        service = MediaServerService(db)
        server = await service.get_media_server(server_id)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"媒体服务器不存在 (ID: {server_id})"
                ).model_dump()
            )
        return success_response(
            data={
                "id": server.id,
                "name": server.name,
                "server_type": server.server_type,
                "url": server.url,
                "enabled": server.enabled,
                "sync_enabled": server.sync_enabled,
                "sync_interval": server.sync_interval,
                "status": server.status,
                "last_check": server.last_check.isoformat() if server.last_check else None,
                "last_sync": server.last_sync.isoformat() if server.last_sync else None,
                "next_sync": server.next_sync.isoformat() if server.next_sync else None,
                "error_message": server.error_message,
                "libraries": server.libraries,
                "sync_watched_status": server.sync_watched_status,
                "sync_playback_status": server.sync_playback_status,
                "sync_metadata": server.sync_metadata,
                "total_movies": server.total_movies,
                "total_tv_shows": server.total_tv_shows,
                "total_episodes": server.total_episodes,
                "created_at": server.created_at.isoformat(),
                "updated_at": server.updated_at.isoformat()
            },
            message="获取媒体服务器详情成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取媒体服务器详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取媒体服务器详情时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/", response_model=BaseResponse)
async def create_media_server(
    server_data: MediaServerCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建媒体服务器"""
    try:
        service = MediaServerService(db)
        server = await service.create_media_server(
            name=server_data.name,
            server_type=server_data.server_type,
            url=server_data.url,
            api_key=server_data.api_key,
            token=server_data.token,
            username=server_data.username,
            password=server_data.password,
            user_id=server_data.user_id,
            enabled=server_data.enabled
        )
        await db.commit()
        return success_response(
            data={
                "id": server.id,
                "name": server.name,
                "server_type": server.server_type,
                "url": server.url,
                "enabled": server.enabled,
                "status": server.status,
                "created_at": server.created_at.isoformat()
            },
            message="创建媒体服务器成功"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"创建媒体服务器失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"创建媒体服务器时发生错误: {str(e)}"
            ).model_dump()
        )


@router.put("/{server_id}", response_model=BaseResponse)
async def update_media_server(
    server_id: int,
    server_data: MediaServerUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新媒体服务器"""
    try:
        service = MediaServerService(db)
        update_data = server_data.model_dump(exclude_unset=True)
        server = await service.update_media_server(server_id, **update_data)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"媒体服务器不存在 (ID: {server_id})"
                ).model_dump()
            )
        await db.commit()
        return success_response(
            data={
                "id": server.id,
                "name": server.name,
                "server_type": server.server_type,
                "url": server.url,
                "enabled": server.enabled,
                "status": server.status,
                "updated_at": server.updated_at.isoformat()
            },
            message="更新媒体服务器成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"更新媒体服务器失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新媒体服务器时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/{server_id}", response_model=BaseResponse)
async def delete_media_server(
    server_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除媒体服务器"""
    try:
        service = MediaServerService(db)
        success = await service.delete_media_server(server_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"媒体服务器不存在 (ID: {server_id})"
                ).model_dump()
            )
        await db.commit()
        return success_response(message="删除媒体服务器成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"删除媒体服务器失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除媒体服务器时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/{server_id}/check", response_model=BaseResponse)
async def check_server_status(
    server_id: int,
    db: AsyncSession = Depends(get_db)
):
    """检查服务器状态"""
    try:
        service = MediaServerService(db)
        result = await service.check_server_status(server_id)
        await db.commit()
        return success_response(data=result, message="检查服务器状态成功")
    except Exception as e:
        await db.rollback()
        logger.error(f"检查服务器状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"检查服务器状态时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/{server_id}/sync/libraries", response_model=BaseResponse)
async def sync_libraries(
    server_id: int,
    db: AsyncSession = Depends(get_db)
):
    """同步媒体库"""
    try:
        service = MediaServerService(db)
        result = await service.sync_libraries(server_id)
        await db.commit()
        return success_response(data=result, message="同步媒体库成功")
    except Exception as e:
        await db.rollback()
        logger.error(f"同步媒体库失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"同步媒体库时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/{server_id}/sync/metadata", response_model=BaseResponse)
async def sync_metadata(
    server_id: int,
    item_id: Optional[str] = Query(None, description="媒体项ID，如果不提供则同步所有"),
    db: AsyncSession = Depends(get_db)
):
    """同步元数据"""
    try:
        service = MediaServerService(db)
        result = await service.sync_metadata(server_id, item_id)
        await db.commit()
        return success_response(data=result, message="同步元数据成功")
    except Exception as e:
        await db.rollback()
        logger.error(f"同步元数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"同步元数据时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/{server_id}/playback-sessions", response_model=BaseResponse)
async def get_playback_sessions(
    server_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取播放会话"""
    try:
        service = MediaServerService(db)
        sessions = await service.get_playback_sessions(server_id)
        await db.commit()
        return success_response(data=sessions, message="获取播放会话成功")
    except Exception as e:
        await db.rollback()
        logger.error(f"获取播放会话失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取播放会话时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/{server_id}/sync-history", response_model=BaseResponse)
async def get_sync_history(
    server_id: int,
    limit: int = Query(100, ge=1, le=1000, description="返回记录数限制"),
    db: AsyncSession = Depends(get_db)
):
    """获取同步历史"""
    try:
        service = MediaServerService(db)
        history = await service.get_sync_history(server_id=server_id, limit=limit)
        return success_response(
            data=[{
                "id": h.id,
                "media_server_id": h.media_server_id,
                "sync_type": h.sync_type,
                "status": h.status,
                "items_synced": h.items_synced,
                "items_failed": h.items_failed,
                "duration": h.duration,
                "error_message": h.error_message,
                "started_at": h.started_at.isoformat(),
                "completed_at": h.completed_at.isoformat() if h.completed_at else None
            } for h in history],
            message="获取同步历史成功"
        )
    except Exception as e:
        logger.error(f"获取同步历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取同步历史时发生错误: {str(e)}"
            ).model_dump()
        )

