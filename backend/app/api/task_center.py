"""
任务中心 API
TASK-1 实现
"""
import logging
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.task_center import TaskCenterListResponse
from app.schemas.response import BaseResponse, success_response
from app.services.task_center_service import list_tasks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/task_center", tags=["任务中心"])


@router.get("/tasks", response_model=BaseResponse, summary="获取任务列表")
async def get_tasks(
    media_type: str | None = Query(None, description="媒体类型过滤"),
    kind: str | None = Query(None, description="任务类型过滤"),
    status: str | None = Query(None, description="状态过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取任务列表
    
    聚合 TTS 任务、音乐下载任务等
    
    - media_type: movie/series/novel/audiobook/manga/music/other
    - kind: download/tts/import/subscription/other
    - status: pending/running/success/failed/skipped
    """
    try:
        data = await list_tasks(
            db,
            media_type=media_type,
            kind=kind,
            status=status,
            page=page,
            page_size=page_size,
        )
        return success_response(
            data=data.model_dump(),
            message="获取任务列表成功"
        )
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务列表失败: {str(e)}"
        )
