"""
系统运维状态 API
ADMIN-1 实现
"""
import logging
import os
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.ebook import EBook
from app.models.music import Music, MusicFile
from app.models.manga_series_local import MangaSeriesLocal
from app.models.manga_source import MangaSource
from app.models.music_chart_source import MusicChartSource
from app.schemas.response import BaseResponse, success_response
from app.schemas.home_dashboard import HomeRunnerStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["系统运维"])


class StorageInfo(BaseModel):
    """存储信息"""
    name: str
    path: Optional[str] = None
    total_items: int = 0
    size_description: Optional[str] = None
    status: str = "unknown"  # ok / warning / error / unknown


class ExternalSourceStatus(BaseModel):
    """外部源状态"""
    name: str
    type: str  # manga / music / indexer
    url: Optional[str] = None
    last_check_at: Optional[datetime] = None
    last_status: str = "unknown"  # ok / error / unknown
    message: Optional[str] = None


class AdminDashboardResponse(BaseModel):
    """管理控制台响应"""
    runners: List[HomeRunnerStatus]
    external_sources: List[ExternalSourceStatus]
    storage: List[StorageInfo]


@router.get("/runners", response_model=BaseResponse, summary="获取 Runner 状态")
async def get_runners(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取后台 Runner 服务状态"""
    # 目前没有 runner 心跳表，返回预定义列表
    runners = [
        HomeRunnerStatus(
            name="TTS 生成服务",
            key="tts_worker",
            last_run_at=None,
            last_status="unknown",
            last_message="systemd: python -m app.runners.tts_worker"
        ),
        HomeRunnerStatus(
            name="TTS 清理服务",
            key="tts_cleanup",
            last_run_at=None,
            last_status="unknown",
            last_message="systemd: python -m app.runners.tts_cleanup"
        ),
        HomeRunnerStatus(
            name="漫画追更同步",
            key="manga_follow",
            last_run_at=None,
            last_status="unknown",
            last_message="systemd: python -m app.runners.manga_follow_sync"
        ),
        HomeRunnerStatus(
            name="音乐榜单同步",
            key="music_chart_sync",
            last_run_at=None,
            last_status="unknown",
            last_message="systemd: python -m app.runners.music_chart_sync"
        ),
        HomeRunnerStatus(
            name="音乐下载服务",
            key="music_download",
            last_run_at=None,
            last_status="unknown",
            last_message="systemd: python -m app.runners.music_download_worker"
        ),
        HomeRunnerStatus(
            name="音乐状态同步",
            key="music_status_sync",
            last_run_at=None,
            last_status="unknown",
            last_message="systemd: python -m app.runners.music_status_sync"
        ),
    ]
    
    return success_response(
        data=[r.model_dump() for r in runners],
        message="获取 Runner 状态成功"
    )


@router.get("/external_sources", response_model=BaseResponse, summary="获取外部源状态")
async def get_external_sources(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取外部源（漫画源、音乐榜单源等）状态"""
    sources: List[ExternalSourceStatus] = []
    
    try:
        # 漫画源
        result = await db.execute(select(MangaSource))
        manga_sources = result.scalars().all()
        for src in manga_sources:
            sources.append(ExternalSourceStatus(
                name=src.name,
                type="manga",
                url=src.base_url if hasattr(src, 'base_url') else None,
                last_check_at=src.updated_at if hasattr(src, 'updated_at') else None,
                last_status="ok" if src.is_enabled else "disabled",
                message=f"类型: {src.source_type}" if hasattr(src, 'source_type') else None
            ))
    except Exception as e:
        logger.warning(f"获取漫画源失败: {e}")
    
    try:
        # 音乐榜单源
        result = await db.execute(select(MusicChartSource))
        chart_sources = result.scalars().all()
        for src in chart_sources:
            sources.append(ExternalSourceStatus(
                name=src.name,
                type="music",
                url=None,
                last_check_at=src.last_sync_at if hasattr(src, 'last_sync_at') else None,
                last_status="ok" if src.is_enabled else "disabled",
                message=f"平台: {src.platform}" if hasattr(src, 'platform') else None
            ))
    except Exception as e:
        logger.warning(f"获取音乐榜单源失败: {e}")
    
    return success_response(
        data=[s.model_dump() for s in sources],
        message="获取外部源状态成功"
    )


@router.get("/storage", response_model=BaseResponse, summary="获取存储概览")
async def get_storage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取存储概览"""
    storage_info: List[StorageInfo] = []
    
    try:
        # 小说/电子书
        result = await db.execute(select(func.count()).select_from(EBook))
        ebook_count = result.scalar() or 0
        storage_info.append(StorageInfo(
            name="小说/电子书库",
            total_items=ebook_count,
            status="ok" if ebook_count > 0 else "empty"
        ))
    except Exception as e:
        logger.warning(f"获取电子书统计失败: {e}")
        storage_info.append(StorageInfo(name="小说/电子书库", status="error"))
    
    try:
        # 漫画
        result = await db.execute(select(func.count()).select_from(MangaSeriesLocal))
        manga_count = result.scalar() or 0
        storage_info.append(StorageInfo(
            name="漫画库",
            total_items=manga_count,
            status="ok" if manga_count > 0 else "empty"
        ))
    except Exception as e:
        logger.warning(f"获取漫画统计失败: {e}")
        storage_info.append(StorageInfo(name="漫画库", status="error"))
    
    try:
        # 音乐
        result = await db.execute(select(func.count()).select_from(Music))
        music_count = result.scalar() or 0
        result = await db.execute(select(func.count()).select_from(MusicFile))
        music_file_count = result.scalar() or 0
        storage_info.append(StorageInfo(
            name="音乐库",
            total_items=music_count,
            size_description=f"{music_file_count} 个文件",
            status="ok" if music_count > 0 else "empty"
        ))
    except Exception as e:
        logger.warning(f"获取音乐统计失败: {e}")
        storage_info.append(StorageInfo(name="音乐库", status="error"))
    
    # TTS 存储（尝试读取配置路径）
    tts_path = os.environ.get("TTS_OUTPUT_DIR", "./data/tts_output")
    storage_info.append(StorageInfo(
        name="TTS 存储",
        path=tts_path,
        status="unknown",
        size_description="请查看 TTS 存储管理页面"
    ))
    
    return success_response(
        data=[s.model_dump() for s in storage_info],
        message="获取存储概览成功"
    )


@router.get("/dashboard", response_model=BaseResponse, summary="获取管理控制台数据")
async def get_admin_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取管理控制台汇总数据"""
    try:
        # 获取各部分数据
        runners_resp = await get_runners(db=db, current_user=current_user)
        sources_resp = await get_external_sources(db=db, current_user=current_user)
        storage_resp = await get_storage(db=db, current_user=current_user)
        
        return success_response(
            data={
                "runners": runners_resp.data,
                "external_sources": sources_resp.data,
                "storage": storage_resp.data,
            },
            message="获取管理控制台数据成功"
        )
    except Exception as e:
        logger.error(f"获取管理控制台数据失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取管理控制台数据失败: {str(e)}"
        )
