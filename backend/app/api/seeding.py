"""
做种管理API
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from pydantic import BaseModel, Field
from loguru import logger

from app.core.database import get_db
from app.modules.seeding.service import SeedingService
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)

router = APIRouter()


class SeedingTaskResponse(BaseModel):
    """做种任务响应"""
    hash: str
    title: str
    downloader: str
    size: int
    uploaded: int
    downloaded: int
    ratio: float
    upload_speed: int
    download_speed: int
    peers: int
    seeds: int
    status: str


class SeedingStatisticsResponse(BaseModel):
    """做种统计响应"""
    total_tasks: int
    total_size: int
    total_uploaded: int
    total_downloaded: int
    total_upload_speed: int
    total_download_speed: int
    total_peers: int
    total_seeds: int
    average_ratio: float
    tasks_by_downloader: dict


@router.get("/tasks", response_model=BaseResponse)
async def get_seeding_tasks(
    downloader: Optional[str] = Query(None, description="下载器名称"),
    status: Optional[str] = Query(None, description="状态"),
    limit: Optional[int] = Query(None, description="限制数量"),
    db = Depends(get_db)
):
    """获取做种任务列表"""
    try:
        service = SeedingService(db)
        tasks = await service.get_seeding_tasks(
            downloader=downloader,
            status=status,
            limit=limit
        )
        return success_response(data=tasks, message="获取做种任务列表成功")
    except Exception as e:
        logger.error(f"获取做种任务列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取做种任务列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/statistics", response_model=BaseResponse)
async def get_seeding_statistics(
    downloader: Optional[str] = Query(None, description="下载器名称"),
    db = Depends(get_db)
):
    """获取做种统计信息"""
    try:
        service = SeedingService(db)
        statistics = await service.get_seeding_statistics(downloader=downloader)
        return success_response(data=statistics, message="获取做种统计信息成功")
    except Exception as e:
        logger.error(f"获取做种统计信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取做种统计信息时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/history", response_model=BaseResponse)
async def get_seeding_history(
    downloader: Optional[str] = Query(None, description="下载器名称"),
    days: int = Query(7, ge=1, le=30, description="查询天数"),
    limit: Optional[int] = Query(None, description="限制数量"),
    db = Depends(get_db)
):
    """获取做种历史记录"""
    try:
        service = SeedingService(db)
        history = await service.get_seeding_history(
            downloader=downloader,
            days=days,
            limit=limit
        )
        return success_response(data=history, message="获取做种历史记录成功")
    except Exception as e:
        logger.error(f"获取做种历史记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取做种历史记录时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/pause", response_model=BaseResponse)
async def pause_seeding(
    downloader: str = Query(..., description="下载器名称"),
    torrent_hash: str = Query(..., description="种子哈希"),
    db = Depends(get_db)
):
    """暂停做种"""
    try:
        service = SeedingService(db)
        success = await service.pause_seeding(downloader, torrent_hash)
        if success:
            return success_response(message="暂停做种成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="OPERATION_FAILED",
                    error_message="暂停做种失败"
                ).model_dump()
            )
    except Exception as e:
        logger.error(f"暂停做种失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"暂停做种时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/resume", response_model=BaseResponse)
async def resume_seeding(
    downloader: str = Query(..., description="下载器名称"),
    torrent_hash: str = Query(..., description="种子哈希"),
    db = Depends(get_db)
):
    """恢复做种"""
    try:
        service = SeedingService(db)
        success = await service.resume_seeding(downloader, torrent_hash)
        if success:
            return success_response(message="恢复做种成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="OPERATION_FAILED",
                    error_message="恢复做种失败"
                ).model_dump()
            )
    except Exception as e:
        logger.error(f"恢复做种失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"恢复做种时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/delete", response_model=BaseResponse)
async def delete_seeding(
    downloader: str = Query(..., description="下载器名称"),
    torrent_hash: str = Query(..., description="种子哈希"),
    delete_files: bool = Query(False, description="是否删除文件"),
    db = Depends(get_db)
):
    """删除做种任务"""
    try:
        service = SeedingService(db)
        success = await service.delete_seeding(downloader, torrent_hash, delete_files)
        if success:
            return success_response(message="删除做种任务成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="OPERATION_FAILED",
                    error_message="删除做种任务失败"
                ).model_dump()
            )
    except Exception as e:
        logger.error(f"删除做种任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除做种任务时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/daily-statistics", response_model=BaseResponse)
async def get_daily_statistics(
    days: int = Query(7, ge=1, le=30, description="查询天数"),
    db = Depends(get_db)
):
    """获取每日做种统计"""
    try:
        service = SeedingService(db)
        statistics = await service.statistics.get_daily_statistics(days=days)
        return success_response(data=statistics, message="获取每日做种统计成功")
    except Exception as e:
        logger.error(f"获取每日做种统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取每日做种统计时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/hnr-statistics", response_model=BaseResponse)
async def get_hnr_statistics(
    days: int = Query(7, ge=1, le=30, description="查询天数"),
    db = Depends(get_db)
):
    """获取HNR相关做种统计"""
    try:
        service = SeedingService(db)
        statistics = await service.statistics.get_hnr_statistics(days=days)
        return success_response(data=statistics, message="获取HNR做种统计成功")
    except Exception as e:
        logger.error(f"获取HNR做种统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取HNR做种统计时发生错误: {str(e)}"
            ).model_dump()
        )

