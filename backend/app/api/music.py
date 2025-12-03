"""
音乐相关API - VabHub特色功能
使用统一响应模型
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from loguru import logger

from app.core.database import get_db
from app.modules.music.service import MusicService
from app.core.schemas import (
    BaseResponse,
    PaginatedResponse,
    NotFoundResponse,
    success_response,
    error_response
)

router = APIRouter()


class MusicSearchRequest(BaseModel):
    """音乐搜索请求"""
    query: str = Field(..., description="搜索关键词")
    type: str = Field("all", description="搜索类型: song, album, artist, all")
    platform: Optional[str] = Field(None, description="指定平台: spotify, apple_music, qq_music, netease")
    limit: int = Field(20, ge=1, le=100, description="返回数量")


class MusicItem(BaseModel):
    """音乐项"""
    id: str
    title: str
    artist: str
    album: Optional[str] = None
    duration: Optional[int] = None  # 秒
    release_date: Optional[str] = None
    genre: List[str] = []
    platform: str
    external_url: Optional[str] = None
    preview_url: Optional[str] = None
    cover_url: Optional[str] = None
    popularity: Optional[float] = None


class MusicSubscriptionCreate(BaseModel):
    """创建音乐订阅请求"""
    name: str
    type: str = Field(..., description="订阅类型: artist, album, playlist, genre, track")
    platform: str = Field(..., description="平台: spotify, apple_music, qq_music, netease")
    target_id: str = Field(..., description="目标ID（艺术家ID、专辑ID等）")
    target_name: Optional[str] = Field(None, description="目标名称（可选）")
    auto_download: bool = True
    quality: Optional[str] = Field(None, description="音质要求: flac, mp3_320, mp3_128")
    sites: Optional[List[str]] = Field(None, description="可选的订阅站点列表")
    downloader: Optional[str] = Field(None, description="下载器")
    save_path: Optional[str] = Field(None, description="保存路径")
    min_seeders: Optional[int] = Field(2, ge=1, description="最小做种数")
    include: Optional[str] = Field(None, description="包含关键字")
    exclude: Optional[str] = Field(None, description="排除关键字")
    search_keywords: Optional[List[str]] = Field(
        default=None, description="自定义PT搜索关键字"
    )
    chart_entry: Optional[Dict[str, Any]] = Field(
        default=None, description="榜单条目原始信息"
    )


class MusicSubscriptionResponse(BaseModel):
    """音乐订阅响应"""
    id: int
    name: str
    type: str
    platform: str
    status: str
    auto_download: bool
    created_at: datetime
    subscription_id: Optional[int] = None
    target_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class ChartRequest(BaseModel):
    """榜单请求"""
    platform: str = Field(..., description="榜单平台: qq_music, netease, tme_youni, billboard_china")
    chart_type: str = Field("hot", description="榜单类型: hot, new, trending")
    region: str = Field("CN", description="地区代码")
    limit: int = Field(50, ge=1, le=100, description="返回数量")


class MusicAutoDownloadRequest(BaseModel):
    """音乐自动下载请求"""
    subscription_id: int = Field(..., description="音乐订阅ID")
    preview_only: bool = Field(False, description="仅预览搜索结果")
    limit: int = Field(5, ge=1, le=20, description="最多返回的预览关键字数量")


@router.post("/search", response_model=BaseResponse)
async def search_music(
    request: MusicSearchRequest,
    db = Depends(get_db)
):
    """
    搜索音乐
    
    返回统一响应格式：
    {
        "success": true,
        "message": "搜索成功",
        "data": [MusicItem, ...],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = MusicService(db)
        results = await service.search_music(
            query=request.query,
            search_type=request.type,
            platform=request.platform,
            limit=request.limit
        )
        return success_response(data=results, message="搜索成功")
    except Exception as e:
        logger.error(f"搜索音乐失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"搜索音乐时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/charts/platforms", response_model=BaseResponse)
async def get_chart_platforms():
    """
    获取支持的音乐榜单平台
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "platforms": [...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        platforms = [
            {"id": "qq_music", "name": "QQ音乐"},
            {"id": "netease", "name": "网易云音乐"},
            {"id": "tme_youni", "name": "TME由你音乐榜"},
            {"id": "billboard_china", "name": "Billboard中国"},
            {"id": "spotify", "name": "Spotify"},
            {"id": "apple_music", "name": "Apple Music"}
        ]
        return success_response(data={"platforms": platforms}, message="获取成功")
    except Exception as e:
        logger.error(f"获取榜单平台失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取榜单平台时发生错误: {str(e)}"
            ).model_dump()
        )


async def _build_chart_response(
    *,
    platform: str,
    chart_type: str,
    region: str,
    limit: int,
    db
):
    """
    获取音乐榜单
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "platform": "...",
            "chart_type": "...",
            "region": "...",
            "total": 50,
            "charts": [...],
            "updated_at": "..."
        },
        "timestamp": "2025-01-XX..."
    }
    """
    service = MusicService(db)
    charts = await service.get_charts(
        platform=platform,
        chart_type=chart_type,
        region=region,
        limit=limit
    )
    return success_response(
        data={
            "platform": platform,
            "chart_type": chart_type,
            "region": region,
            "total": len(charts),
            "charts": charts,
            "updated_at": datetime.now().isoformat()
        },
        message="获取成功"
    )


@router.get("/charts", response_model=BaseResponse)
async def get_music_charts_v2(
    platform: str = Query(..., description="榜单平台"),
    chart_type: str = Query("hot", description="榜单类型"),
    region: str = Query("CN", description="地区"),
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
    db = Depends(get_db)
):
    try:
        return await _build_chart_response(
            platform=platform,
            chart_type=chart_type,
            region=region,
            limit=limit,
            db=db
        )
    except Exception as e:
        logger.error(f"获取音乐榜单失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取音乐榜单时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/charts", response_model=BaseResponse)
async def get_music_charts(
    request: ChartRequest,
    db = Depends(get_db)
):
    try:
        return await _build_chart_response(
            platform=request.platform,
            chart_type=request.chart_type,
            region=request.region,
            limit=request.limit,
            db=db
        )
    except Exception as e:
        logger.error(f"获取音乐榜单失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取音乐榜单时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/charts/history", response_model=BaseResponse)
async def get_music_chart_history(
    platform: Optional[str] = Query(None, description="榜单平台（可选）"),
    chart_type: Optional[str] = Query(None, description="榜单类型（可选）"),
    region: Optional[str] = Query(None, description="地区代码（可选）"),
    batches: int = Query(3, ge=1, le=10, description="返回最近多少批记录"),
    db = Depends(get_db)
):
    """
    获取最近的榜单历史（持久化记录）
    """
    try:
        service = MusicService(db)
        history = await service.get_chart_history(
            platform=platform,
            chart_type=chart_type,
            region=region,
            batches=batches
        )
        serialized = []
        for batch in history:
            serialized.append({
                "batch_id": batch.get("batch_id"),
                "captured_at": batch.get("captured_at").isoformat() if batch.get("captured_at") else None,
                "platform": batch.get("platform"),
                "chart_type": batch.get("chart_type"),
                "region": batch.get("region"),
                "entries": [
                    {
                        **entry,
                        "captured_at": entry.get("captured_at").isoformat() if entry.get("captured_at") else None,
                    }
                    for entry in batch.get("entries", [])
                ]
            })
        return success_response(
            data={
                "platform": platform,
                "chart_type": chart_type,
                "region": region,
                "batches": serialized
            },
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取音乐榜单历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取音乐榜单历史时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/tracks/{track_id}", response_model=BaseResponse)
async def get_track_detail(
    track_id: int,
    db = Depends(get_db)
):
    """
    获取音乐曲目详情
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "id": 1,
            "title": "...",
            "artist": "...",
            "album": "...",
            "duration": 180,
            "release_date": "2024-01-01",
            "genre": ["Pop", "Rock"],
            "platform": "spotify",
            "platform_id": "...",
            "external_url": "...",
            "preview_url": "...",
            "cover_url": "...",
            "popularity": 0.8,
            "file_path": "...",
            "file_size_mb": 5.2,
            "quality": "flac",
            "created_at": "...",
            "updated_at": "..."
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import select
        from app.models.music import MusicTrack
        import json
        
        result = await db.execute(
            select(MusicTrack).where(MusicTrack.id == track_id)
        )
        track = result.scalar_one_or_none()
        
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"音乐曲目不存在 (ID: {track_id})"
                ).model_dump()
            )
        
        # 解析genre（如果是JSON字符串）
        genre = track.genre
        if isinstance(genre, str):
            try:
                genre = json.loads(genre)
            except:
                genre = [genre] if genre else []
        
        track_data = {
            "id": track.id,
            "title": track.title,
            "artist": track.artist,
            "album": track.album,
            "duration": track.duration,
            "release_date": track.release_date.isoformat() if track.release_date else None,
            "genre": genre,
            "platform": track.platform,
            "platform_id": track.platform_id,
            "external_url": track.external_url,
            "preview_url": track.preview_url,
            "cover_url": track.cover_url,
            "popularity": track.popularity,
            "file_path": track.file_path,
            "file_size_mb": track.file_size_mb,
            "quality": track.quality,
            "created_at": track.created_at.isoformat() if track.created_at else "",
            "updated_at": track.updated_at.isoformat() if track.updated_at else ""
        }
        
        return success_response(
            data=track_data,
            message="获取成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取音乐曲目详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取音乐曲目详情时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/trending", response_model=BaseResponse)
async def get_trending_music(
    platform: str = Query("all", description="平台: all, qq_music, netease, spotify"),
    region: str = Query("CN", description="地区代码"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db = Depends(get_db)
):
    """
    获取热门音乐
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "platform": "...",
            "region": "...",
            "trending": [...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = MusicService(db)
        trending = await service.get_trending_music(
            platform=platform,
            region=region,
            limit=limit
        )
        return success_response(
            data={
                "platform": platform,
                "region": region,
                "trending": trending
            },
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取热门音乐失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取热门音乐时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/subscriptions", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_music_subscription(
    subscription: MusicSubscriptionCreate,
    db = Depends(get_db)
):
    """
    创建音乐订阅
    
    返回统一响应格式：
    {
        "success": true,
        "message": "创建成功",
        "data": MusicSubscriptionResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = MusicService(db)
        result = await service.create_subscription(subscription.model_dump())
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="CREATE_FAILED",
                    error_message="创建音乐订阅失败"
                ).model_dump()
            )
        # 将SQLAlchemy对象转换为Pydantic模型
        subscription_response = MusicSubscriptionResponse.model_validate(result)
        return success_response(data=subscription_response.model_dump(), message="创建成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建音乐订阅失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"创建音乐订阅时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/subscriptions", response_model=BaseResponse)
async def list_music_subscriptions(
    platform: Optional[str] = Query(None, description="平台过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db = Depends(get_db)
):
    """
    获取音乐订阅列表（支持分页）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "items": [MusicSubscriptionResponse, ...],
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = MusicService(db)
        subscriptions = await service.list_subscriptions(
            platform=platform,
            status=status
        )
        
        # 将SQLAlchemy对象转换为Pydantic模型
        subscription_responses = [
            MusicSubscriptionResponse.model_validate(sub) for sub in subscriptions
        ]
        
        # 计算分页
        total = len(subscription_responses)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_items = subscription_responses[start:end]
        
        # 使用PaginatedResponse
        paginated_data = PaginatedResponse.create(
            items=[item.model_dump() for item in paginated_items],
            total=total,
            page=page,
            page_size=page_size
        )
        
        return success_response(data=paginated_data.model_dump(), message="获取成功")
    except Exception as e:
        logger.error(f"获取音乐订阅列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取音乐订阅列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/subscriptions/{subscription_id}", response_model=BaseResponse)
async def get_music_subscription(
    subscription_id: int,
    db = Depends(get_db)
):
    """
    获取音乐订阅详情
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": MusicSubscriptionResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = MusicService(db)
        subscription = await service.get_subscription(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"音乐订阅不存在 (ID: {subscription_id})"
                ).model_dump()
            )
        # 将SQLAlchemy对象转换为Pydantic模型
        subscription_response = MusicSubscriptionResponse.model_validate(subscription)
        return success_response(data=subscription_response.model_dump(), message="获取成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取音乐订阅详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取音乐订阅详情时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/subscriptions/{subscription_id}", response_model=BaseResponse)
async def delete_music_subscription(
    subscription_id: int,
    db = Depends(get_db)
):
    """
    删除音乐订阅
    
    返回统一响应格式：
    {
        "success": true,
        "message": "删除成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = MusicService(db)
        success = await service.delete_subscription(subscription_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"音乐订阅不存在 (ID: {subscription_id})"
                ).model_dump()
            )
        return success_response(message="删除成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除音乐订阅失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除音乐订阅时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/autodownload", response_model=BaseResponse)
async def auto_download_music_subscription(
    request: MusicAutoDownloadRequest,
    db = Depends(get_db)
):
    """
    触发音乐订阅自动下载/预览
    """
    try:
        service = MusicService(db)
        result = await service.auto_download_subscription(
            request.subscription_id,
            preview_only=request.preview_only,
            limit=request.limit
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="AUTO_DOWNLOAD_FAILED",
                    error_message=result.get("message", "自动下载失败"),
                    details=result
                ).model_dump()
            )
        
        message = "预览完成" if request.preview_only else "自动下载任务已触发"
        return success_response(data=result, message=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"音乐自动下载失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"音乐自动下载时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/library/stats", response_model=BaseResponse)
async def get_music_library_stats(
    db = Depends(get_db)
):
    """
    获取音乐库统计
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {stats_dict},
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = MusicService(db)
        stats = await service.get_library_stats()
        return success_response(data=stats, message="获取成功")
    except Exception as e:
        logger.error(f"获取音乐库统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取音乐库统计时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/library/scan", response_model=BaseResponse)
async def scan_music_library(
    path: str = Body(..., description="扫描路径"),
    recursive: bool = Body(True, description="递归扫描"),
    db = Depends(get_db)
):
    """
    扫描音乐库
    
    返回统一响应格式：
    {
        "success": true,
        "message": "扫描成功",
        "data": {scan_result},
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = MusicService(db)
        scan_result = await service.scan_music_library(path, recursive)
        return success_response(data=scan_result, message="扫描成功")
    except Exception as e:
        logger.error(f"扫描音乐库失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"扫描音乐库时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/recommendations/{user_id}", response_model=BaseResponse)
async def get_music_recommendations(
    user_id: str,
    count: int = Query(20, ge=1, le=50, description="推荐数量"),
    algorithm: str = Query("hybrid", description="推荐算法: collaborative, content, hybrid"),
    db = Depends(get_db)
):
    """
    获取音乐推荐
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "user_id": "...",
            "algorithm": "...",
            "recommendations": [...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = MusicService(db)
        recommendations = await service.get_recommendations(
            user_id=user_id,
            count=count,
            algorithm=algorithm
        )
        return success_response(
            data={
                "user_id": user_id,
                "algorithm": algorithm,
                "recommendations": recommendations
            },
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取音乐推荐失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取音乐推荐时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/lyrics", response_model=BaseResponse)
async def get_lyrics(
    title: str = Query(..., description="歌曲标题"),
    artist: str = Query(..., description="艺术家"),
    platform: Optional[str] = Query(None, description="指定平台: netease, qq_music"),
    db = Depends(get_db)
):
    """
    获取歌词
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "lyrics": "...",
            "translation": "...",
            "source": "...",
            "platform_id": "..."
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = MusicService(db)
        lyrics_data = await service.get_lyrics(title, artist, platform)
        if not lyrics_data:
            return success_response(
                data=None,
                message="未找到歌词"
            )
        return success_response(data=lyrics_data, message="获取成功")
    except Exception as e:
        logger.error(f"获取歌词失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取歌词时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/cover/download", response_model=BaseResponse)
async def download_cover(
    title: str = Body(..., description="歌曲标题"),
    artist: str = Body(..., description="艺术家"),
    album: Optional[str] = Body(None, description="专辑名称"),
    platform: Optional[str] = Body(None, description="指定平台: netease, qq_music"),
    save_path: Optional[str] = Body(None, description="保存路径（可选）"),
    db = Depends(get_db)
):
    """
    下载专辑封面
    
    返回统一响应格式：
    {
        "success": true,
        "message": "下载成功",
        "data": {
            "cover_path": "..."
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = MusicService(db)
        cover_path = await service.download_cover(
            title, artist, album, platform, save_path
        )
        if not cover_path:
            return success_response(
                data=None,
                message="未找到封面"
            )
        return success_response(
            data={"cover_path": cover_path},
            message="下载成功"
        )
    except Exception as e:
        logger.error(f"下载封面失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"下载封面时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/scrape", response_model=BaseResponse)
async def scrape_music_file(
    file_path: str = Body(..., description="音乐文件路径"),
    db = Depends(get_db)
):
    """
    刮削音乐文件元数据
    
    返回统一响应格式：
    {
        "success": true,
        "message": "刮削成功",
        "data": {metadata_dict},
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        import os
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="FILE_NOT_FOUND",
                    error_message=f"文件不存在: {file_path}"
                ).model_dump()
            )
        
        service = MusicService(db)
        metadata = await service.scrape_music_file(file_path)
        return success_response(data=metadata, message="刮削成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刮削音乐文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"刮削音乐文件时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/metadata/extract", response_model=BaseResponse)
async def extract_metadata(
    file_path: str = Body(..., description="音乐文件路径"),
    db = Depends(get_db)
):
    """
    提取音乐文件元数据
    
    返回统一响应格式：
    {
        "success": true,
        "message": "提取成功",
        "data": {metadata_dict},
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        import os
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="FILE_NOT_FOUND",
                    error_message=f"文件不存在: {file_path}"
                ).model_dump()
            )
        
        service = MusicService(db)
        metadata = await service.extract_metadata(file_path)
        return success_response(data=metadata, message="提取成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提取元数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"提取元数据时发生错误: {str(e)}"
            ).model_dump()
        )


# ========== 本地音乐库浏览 API ==========

@router.get("/library/albums", response_model=BaseResponse)
async def list_albums(
    keyword: Optional[str] = Query(None, description="搜索关键字"),
    artist: Optional[str] = Query(None, description="艺术家筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db = Depends(get_db)
):
    """
    获取本地音乐库专辑列表
    """
    try:
        from sqlalchemy import select, func, distinct
        from app.models.music import Music, MusicFile
        
        # 基础查询：按 artist + album 分组
        query = select(
            Music.artist,
            Music.album,
            Music.year,
            Music.genre,
            func.count(distinct(MusicFile.id)).label('track_count'),
            func.sum(MusicFile.duration_seconds).label('total_duration'),
            func.min(Music.id).label('id')
        ).outerjoin(MusicFile, Music.id == MusicFile.music_id)
        
        # 筛选条件
        if keyword:
            query = query.where(
                (Music.title.ilike(f"%{keyword}%")) |
                (Music.artist.ilike(f"%{keyword}%")) |
                (Music.album.ilike(f"%{keyword}%"))
            )
        if artist:
            query = query.where(Music.artist.ilike(f"%{artist}%"))
        
        query = query.where(Music.album.isnot(None))
        query = query.group_by(Music.artist, Music.album, Music.year, Music.genre)
        
        # 计算总数
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0
        
        # 分页
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        rows = result.all()
        
        albums = []
        for row in rows:
            albums.append({
                "id": row.id,
                "title": row.album,
                "artist_name": row.artist,
                "year": row.year,
                "genre": row.genre,
                "track_count": row.track_count or 0,
                "total_duration_seconds": row.total_duration
            })
        
        total_pages = (total + page_size - 1) // page_size
        
        return success_response(
            data={
                "items": albums,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            },
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取专辑列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取专辑列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/library/albums/{album_id}", response_model=BaseResponse)
async def get_album_detail(
    album_id: int,
    db = Depends(get_db)
):
    """
    获取专辑详情（包含曲目列表）
    """
    try:
        from sqlalchemy import select
        from app.models.music import Music, MusicFile
        
        # 获取专辑信息
        result = await db.execute(
            select(Music).where(Music.id == album_id)
        )
        music = result.scalar_one_or_none()
        
        if not music:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"专辑不存在 (ID: {album_id})"
                ).model_dump()
            )
        
        # 获取同专辑的所有曲目
        tracks_result = await db.execute(
            select(Music, MusicFile)
            .outerjoin(MusicFile, Music.id == MusicFile.music_id)
            .where(Music.artist == music.artist)
            .where(Music.album == music.album)
            .order_by(MusicFile.disc_number, MusicFile.track_number)
        )
        tracks_rows = tracks_result.all()
        
        tracks = []
        total_duration = 0
        for row in tracks_rows:
            m, mf = row
            track = {
                "id": m.id,
                "title": m.title,
                "artist_name": m.artist,
                "track_number": mf.track_number if mf else None,
                "disc_number": mf.disc_number if mf else None,
                "duration_seconds": mf.duration_seconds if mf else None,
                "bitrate_kbps": mf.bitrate_kbps if mf else None,
                "format": mf.format if mf else None,
                "file_id": mf.id if mf else None
            }
            tracks.append(track)
            if mf and mf.duration_seconds:
                total_duration += mf.duration_seconds
        
        album_detail = {
            "id": music.id,
            "title": music.album,
            "artist_name": music.artist,
            "album_artist": music.album_artist,
            "year": music.year,
            "genre": music.genre,
            "track_count": len(tracks),
            "total_duration_seconds": total_duration,
            "tracks": tracks
        }
        
        return success_response(data=album_detail, message="获取成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取专辑详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取专辑详情时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/library/artists", response_model=BaseResponse)
async def list_artists(
    keyword: Optional[str] = Query(None, description="搜索关键字"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db = Depends(get_db)
):
    """
    获取本地音乐库艺术家列表
    """
    try:
        from sqlalchemy import select, func, distinct
        from app.models.music import Music, MusicFile
        
        # 按艺术家分组统计
        query = select(
            Music.artist,
            func.count(distinct(Music.album)).label('album_count'),
            func.count(distinct(MusicFile.id)).label('track_count')
        ).outerjoin(MusicFile, Music.id == MusicFile.music_id)
        
        if keyword:
            query = query.where(Music.artist.ilike(f"%{keyword}%"))
        
        query = query.group_by(Music.artist)
        
        # 计算总数
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0
        
        # 分页
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        rows = result.all()
        
        artists = []
        for i, row in enumerate(rows):
            artists.append({
                "id": i + 1 + (page - 1) * page_size,  # 虚拟 ID
                "name": row.artist,
                "album_count": row.album_count or 0,
                "track_count": row.track_count or 0
            })
        
        total_pages = (total + page_size - 1) // page_size
        
        return success_response(
            data={
                "items": artists,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            },
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取艺术家列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取艺术家列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/library/tracks", response_model=BaseResponse)
async def list_tracks(
    keyword: Optional[str] = Query(None, description="搜索关键字"),
    artist: Optional[str] = Query(None, description="艺术家筛选"),
    album: Optional[str] = Query(None, description="专辑筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db = Depends(get_db)
):
    """
    获取本地音乐库曲目列表
    """
    try:
        from sqlalchemy import select, func
        from app.models.music import Music, MusicFile
        
        query = select(Music, MusicFile).outerjoin(MusicFile, Music.id == MusicFile.music_id)
        
        if keyword:
            query = query.where(
                (Music.title.ilike(f"%{keyword}%")) |
                (Music.artist.ilike(f"%{keyword}%"))
            )
        if artist:
            query = query.where(Music.artist.ilike(f"%{artist}%"))
        if album:
            query = query.where(Music.album.ilike(f"%{album}%"))
        
        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        # 分页
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        rows = result.all()
        
        tracks = []
        for row in rows:
            m, mf = row
            tracks.append({
                "id": m.id,
                "title": m.title,
                "artist_name": m.artist,
                "album_title": m.album,
                "track_number": mf.track_number if mf else None,
                "disc_number": mf.disc_number if mf else None,
                "duration_seconds": mf.duration_seconds if mf else None,
                "bitrate_kbps": mf.bitrate_kbps if mf else None,
                "format": mf.format if mf else None,
                "file_id": mf.id if mf else None
            })
        
        total_pages = (total + page_size - 1) // page_size
        
        return success_response(
            data={
                "items": tracks,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            },
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取曲目列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取曲目列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/library/stream/{file_id}")
async def stream_music_file(
    file_id: int,
    db = Depends(get_db)
):
    """
    流式播放音乐文件
    """
    try:
        from fastapi.responses import FileResponse
        from sqlalchemy import select
        from app.models.music import MusicFile
        import os
        
        result = await db.execute(
            select(MusicFile).where(MusicFile.id == file_id)
        )
        music_file = result.scalar_one_or_none()
        
        if not music_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="音乐文件不存在"
            )
        
        if not os.path.exists(music_file.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="音乐文件不存在于磁盘"
            )
        
        # 根据格式设置 MIME 类型
        mime_types = {
            "mp3": "audio/mpeg",
            "flac": "audio/flac",
            "m4a": "audio/mp4",
            "aac": "audio/aac",
            "ogg": "audio/ogg",
            "wav": "audio/wav"
        }
        media_type = mime_types.get(music_file.format.lower(), "audio/mpeg")
        
        return FileResponse(
            music_file.file_path,
            media_type=media_type,
            filename=os.path.basename(music_file.file_path)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"流式播放失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"流式播放时发生错误: {str(e)}"
        )

