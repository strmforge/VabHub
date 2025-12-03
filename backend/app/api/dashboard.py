"""
仪表盘相关API
使用统一响应模型
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from loguru import logger

from app.core.database import get_db
from app.modules.dashboard.service import DashboardService
from app.modules.dashboard.layout_service import DashboardLayoutService
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)
from app.core.cache import get_cache
from app.core.cache_decorator import cache_key_builder

router = APIRouter()


class SystemStats(BaseModel):
    """系统统计"""
    cpu_usage: float
    memory_usage: float
    memory_total_gb: float
    memory_used_gb: float
    disk_usage: float
    disk_total_gb: float
    disk_used_gb: float
    disk_free_gb: float
    network_sent: int
    network_recv: int


class MediaStats(BaseModel):
    """媒体统计"""
    total_movies: int
    total_tv_shows: int
    total_anime: int
    total_episodes: int
    total_size_gb: float
    by_quality: Dict[str, int]


class DownloadStats(BaseModel):
    """下载统计"""
    active: int
    paused: int
    completed: int
    failed: int
    total_speed_mbps: float
    total_size_gb: float
    downloaded_gb: float


class TTSStats(BaseModel):
    """TTS统计"""
    pending_jobs: int
    running_jobs: int
    completed_last_24h: int


class PluginStats(BaseModel):
    """插件统计"""
    total_plugins: int
    active_plugins: int
    quarantined_plugins: int


class ReadingStats(BaseModel):
    """阅读统计"""
    active_novels: int
    active_audiobooks: int
    active_manga: int


class RecentEvent(BaseModel):
    """最近活动事件"""
    type: str
    title: str
    time: Optional[str]
    message: str
    media_type: Optional[str] = None
    ebook_id: Optional[int] = None
    plugin_name: Optional[str] = None


class DashboardResponse(BaseModel):
    """仪表盘响应"""
    system_stats: SystemStats
    media_stats: MediaStats
    download_stats: DownloadStats
    active_downloads: int
    active_subscriptions: int
    # 新增字段
    tts_stats: TTSStats
    plugin_stats: PluginStats
    reading_stats: ReadingStats
    recent_events: List[RecentEvent]


@router.get("/", response_model=BaseResponse)
async def get_dashboard(
    db = Depends(get_db)
):
    """
    获取仪表盘数据（综合）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": DashboardResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        # 尝试从缓存获取（30秒TTL）
        cache = get_cache()
        cache_key = "dashboard:main"
        cached_data = await cache.get(cache_key)
        if cached_data is not None:
            return success_response(data=cached_data, message="获取成功（缓存）")
        
        service = DashboardService(db)
        dashboard_data = await service.get_dashboard_data()
        
        # 存储到缓存
        await cache.set(cache_key, dashboard_data, ttl=30)
        
        return success_response(data=dashboard_data, message="获取成功")
    except Exception as e:
        logger.error(f"获取仪表盘数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取仪表盘数据时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/system-resources-history", response_model=BaseResponse)
async def get_system_resources_history(
    hours: int = Query(24, ge=1, le=168, description="查询最近N小时的数据"),
    interval_minutes: int = Query(5, ge=1, le=60, description="数据点间隔（分钟）"),
    db = Depends(get_db)
):
    """
    获取系统资源历史数据（用于图表）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "cpu": [{"timestamp": "...", "value": 50.5}, ...],
            "memory": [{"timestamp": "...", "value": 60.2}, ...],
            "disk": [{"timestamp": "...", "value": 70.1}, ...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DashboardService(db)
        history_data = await service.get_system_resources_history(
            hours=hours,
            interval_minutes=interval_minutes
        )
        return success_response(data=history_data, message="获取成功")
    except Exception as e:
        logger.error(f"获取系统资源历史数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取系统资源历史数据时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/downloader-status", response_model=BaseResponse)
async def get_downloader_status(
    db = Depends(get_db)
):
    """
    获取下载器状态
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "qBittorrent": {
                "connected": true,
                "status": "online",
                "dl_info_speed": 1000000,
                "up_info_speed": 500000,
                ...
            },
            "Transmission": {
                "connected": true,
                "status": "online",
                "downloadSpeed": 1000000,
                "uploadSpeed": 500000,
                ...
            }
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DashboardService(db)
        downloader_status = await service.get_downloader_status()
        return success_response(data=downloader_status, message="获取成功")
    except Exception as e:
        logger.error(f"获取下载器状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取下载器状态时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/music-stats", response_model=BaseResponse)
async def get_music_stats(
    db = Depends(get_db)
):
    """
    获取音乐统计
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "total_tracks": 1000,
            "total_albums": 100,
            "total_artists": 50,
            "total_playlists": 10,
            "total_size_gb": 50.5
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DashboardService(db)
        music_stats = await service.get_music_stats()
        return success_response(data=music_stats, message="获取成功")
    except Exception as e:
        logger.error(f"获取音乐统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取音乐统计时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/system-stats", response_model=BaseResponse)
async def get_system_stats():
    """
    获取系统统计
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": SystemStats,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        # 尝试从缓存获取（10秒TTL，系统资源变化较快）
        cache = get_cache()
        cache_key = "dashboard:system-stats"
        cached_data = await cache.get(cache_key)
        if cached_data is not None:
            return success_response(data=cached_data, message="获取成功（缓存）")
        
        service = DashboardService(None)
        stats = await service.get_system_stats()
        
        # 存储到缓存
        await cache.set(cache_key, stats, ttl=10)
        
        return success_response(data=stats, message="获取成功")
    except Exception as e:
        logger.error(f"获取系统统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取系统统计时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/media-stats", response_model=BaseResponse)
async def get_media_stats(
    db = Depends(get_db)
):
    """
    获取媒体统计
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": MediaStats,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        # 尝试从缓存获取（60秒TTL，媒体统计变化较慢）
        cache = get_cache()
        cache_key = "dashboard:media-stats"
        cached_data = await cache.get(cache_key)
        if cached_data is not None:
            return success_response(data=cached_data, message="获取成功（缓存）")
        
        service = DashboardService(db)
        stats = await service.get_media_stats()
        
        # 存储到缓存
        await cache.set(cache_key, stats, ttl=60)
        
        return success_response(data=stats, message="获取成功")
    except Exception as e:
        logger.error(f"获取媒体统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取媒体统计时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/download-stats", response_model=BaseResponse)
async def get_download_stats(
    db = Depends(get_db)
):
    """
    获取下载统计
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": DownloadStats,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DashboardService(db)
        stats = await service.get_download_stats()
        return success_response(data=stats, message="获取成功")
    except Exception as e:
        logger.error(f"获取下载统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取下载统计时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/storage-stats", response_model=BaseResponse)
async def get_storage_stats(
    db = Depends(get_db)
):
    """
    获取存储统计
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": StorageStats,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DashboardService(db)
        stats = await service.get_storage_stats()
        return success_response(data=stats, message="获取成功")
    except Exception as e:
        logger.error(f"获取存储统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取存储统计时发生错误: {str(e)}"
            ).model_dump()
        )


# 可拖拽布局相关API
class LayoutRequest(BaseModel):
    """布局请求"""
    name: str
    breakpoint: str = "lg"
    cols: int = 12
    row_height: int = 30
    margin: list = [10, 10]
    layouts: Dict[str, Any]
    widgets: list
    is_default: bool = False


@router.get("/layout", response_model=BaseResponse)
async def get_layout(
    layout_id: Optional[int] = None,
    db = Depends(get_db)
):
    """
    获取仪表盘布局
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {...},
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DashboardLayoutService(db)
        layout = await service.get_layout(layout_id=layout_id)
        
        if not layout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message="布局不存在"
                ).model_dump()
            )
        
        return success_response(data=layout, message="获取布局成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取布局失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取布局时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/layout", response_model=BaseResponse)
async def save_layout(
    layout: LayoutRequest,
    layout_id: Optional[int] = None,
    db = Depends(get_db)
):
    """
    保存仪表盘布局
    
    返回统一响应格式：
    {
        "success": true,
        "message": "保存成功",
        "data": {"layout_id": 1},
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DashboardLayoutService(db)
        saved_layout_id = await service.save_layout(
            name=layout.name,
            breakpoint=layout.breakpoint,
            cols=layout.cols,
            row_height=layout.row_height,
            margin=layout.margin,
            layouts=layout.layouts,
            widgets=layout.widgets,
            layout_id=layout_id,
            is_default=layout.is_default
        )
        
        if not saved_layout_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="BAD_REQUEST",
                    error_message="保存布局失败"
                ).model_dump()
            )
        
        return success_response(
            data={"layout_id": saved_layout_id},
            message="保存布局成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存布局失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"保存布局时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/layouts", response_model=BaseResponse)
async def list_layouts(
    db = Depends(get_db)
):
    """
    列出所有布局
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [...],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DashboardLayoutService(db)
        layouts = await service.list_layouts()
        return success_response(data=layouts, message="获取布局列表成功")
    except Exception as e:
        logger.error(f"获取布局列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取布局列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/layout/{layout_id}", response_model=BaseResponse)
async def delete_layout(
    layout_id: int,
    db = Depends(get_db)
):
    """
    删除布局
    
    返回统一响应格式：
    {
        "success": true,
        "message": "删除成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DashboardLayoutService(db)
        success = await service.delete_layout(layout_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message="布局不存在"
                ).model_dump()
            )
        
        return success_response(message="删除布局成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除布局失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除布局时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/widgets", response_model=BaseResponse)
async def list_widgets(
    db = Depends(get_db)
):
    """
    列出所有组件
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [...],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = DashboardLayoutService(db)
        widgets = await service.list_widgets()
        return success_response(data=widgets, message="获取组件列表成功")
    except Exception as e:
        logger.error(f"获取组件列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取组件列表时发生错误: {str(e)}"
            ).model_dump()
        )


# 别名端点（兼容前端期望的路径格式）
@router.get("/stats/system", response_model=BaseResponse)
async def get_system_stats_alias():
    """
    获取系统统计（别名端点）
    
    映射到 /system-stats
    """
    return await get_system_stats()


@router.get("/stats/media", response_model=BaseResponse)
async def get_media_stats_alias(
    db = Depends(get_db)
):
    """
    获取媒体统计（别名端点）
    
    映射到 /media-stats
    """
    return await get_media_stats(db)

