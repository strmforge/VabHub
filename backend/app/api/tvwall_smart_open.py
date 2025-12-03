"""
电视墙智能打开 API 端点

提供 POST /api/tvwall/smart-open 接口，根据网络环境和媒体库配置
决定电视墙海报点击后的跳转目标（媒体库详情页或 VabHub 详情页）
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Literal
from loguru import logger

from app.core.config import Settings, get_settings
from app.core.network_context import resolve_network_context, NetworkContext
from app.services.media_library_jump import build_media_library_jump, MediaLibraryJump
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.media import Media


router = APIRouter(prefix="/api/tvwall", tags=["tvwall"])


class SmartOpenRequest(BaseModel):
    """智能打开请求体"""
    media_id: str = Field(..., description="VabHub 内部的媒体 ID 或 key")
    media_type: Literal["movie", "tv", "short_drama", "other"] = Field(
        default="movie", 
        description="媒体类型，帮助判断处理逻辑"
    )


class SmartOpenDecision(BaseModel):
    """智能打开决策结果"""
    kind: Literal["media_library", "vabhub_detail"] = Field(
        ..., 
        description="决策类型：media_library 表示跳转媒体库，vabhub_detail 表示跳转 VabHub 详情页"
    )
    url: Optional[str] = Field(None, description="目标 URL（媒体库跳转时使用）")
    route_name: Optional[str] = Field(None, description="前端路由名称（VabHub 详情页时使用）")
    route_params: Optional[dict] = Field(None, description="路由参数")
    reason: Optional[str] = Field(None, description="决策原因或失败原因")
    fallback_available: bool = Field(True, description="是否有 VabHub 详情页作为回退选项")


class SmartOpenResponse(BaseModel):
    """智能打开响应"""
    network_context: Literal["lan", "wan", "unknown"] = Field(..., description="网络上下文")
    decision: SmartOpenDecision = Field(..., description="跳转决策")


@router.post("/smart-open", response_model=SmartOpenResponse)
async def smart_open(
    request: SmartOpenRequest,
    http_request: Request,
    config: Settings = Depends(get_settings),
    db: AsyncSession = Depends(get_db)
):
    """
    电视墙海报点击智能决策接口
    
    根据网络环境（LAN/WAN）和媒体库配置，决定海报点击后的跳转目标：
    - LAN + 有媒体库配置 → 跳转媒体库详情/搜索页
    - LAN + 无媒体库配置 → 跳转 VabHub 详情页
    - WAN → 统一跳转 VabHub 详情页
    
    Args:
        request: 智能打开请求
        http_request: HTTP 请求对象（用于网络环境检测）
        config: 应用配置
        
    Returns:
        SmartOpenResponse: 包含网络上下文和跳转决策的响应
        
    Raises:
        HTTPException: 当 media_id 无效时返回 404
    """
    
    try:
        # 1. 检测网络环境
        network_context = resolve_network_context(http_request, config)
        logger.info(f"Smart open request for media {request.media_id}, network: {network_context}")
        
        # 2. 获取媒体基本信息
        media_info = await _get_media_info(request.media_id, db)
        if not media_info:
            decision = SmartOpenDecision(
                kind="vabhub_detail",
                url=None,
                route_name=None,
                route_params=None,
                reason="media not found",
                fallback_available=False
            )
            return SmartOpenResponse(
                network_context=network_context.value,
                decision=decision
            )
        
        # 3. 根据网络环境做决策
        if network_context == NetworkContext.LAN:
            # 内网：尝试媒体库跳转
            library_jump = build_media_library_jump(
                media_title=media_info.get('title', ''),
                media_year=media_info.get('year'),
                media_season=media_info.get('season'),
                media_type=request.media_type,
                config=config
            )
            
            if library_jump.enabled and library_jump.url:
                # 内网 + 有媒体库配置 → 跳转媒体库
                decision = SmartOpenDecision(
                    kind="media_library",
                    url=library_jump.url,
                    route_name=None,
                    route_params=None,
                    reason=None,
                    fallback_available=True  # VabHub 详情页始终可用作回退
                )
            else:
                # 内网 + 无媒体库配置 → 跳转 VabHub 详情页
                decision = SmartOpenDecision(
                    kind="vabhub_detail",
                    url=None,
                    route_name="MediaDetail" if media_info.get("tmdb_id") else None,
                    route_params={
                        "type": media_info.get("media_type") or request.media_type,
                        "tmdbId": media_info.get("tmdb_id")
                    } if media_info.get("tmdb_id") else None,
                    reason=library_jump.reason or "media library not available",
                    fallback_available=bool(media_info.get("tmdb_id"))
                )
        else:
            # 外网：统一跳转 VabHub 详情页
            decision = SmartOpenDecision(
                kind="vabhub_detail",
                url=None,
                route_name="MediaDetail" if media_info.get("tmdb_id") else None,
                route_params={
                    "type": media_info.get("media_type") or request.media_type,
                    "tmdbId": media_info.get("tmdb_id")
                } if media_info.get("tmdb_id") else None,
                reason="wan access - use vabhub detail",
                fallback_available=bool(media_info.get("tmdb_id"))
            )
        
        return SmartOpenResponse(
            network_context=network_context.value,
            decision=decision
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Smart open failed for media {request.media_id}: {e}")
        # 发生异常时回退到 VabHub 详情页，确保用户不会"点了没响应"
        decision = SmartOpenDecision(
            kind="vabhub_detail",
            url=None,
            route_name=None,
            route_params=None,
            reason=f"fallback due to error: {str(e)}",
            fallback_available=False
        )
        
        return SmartOpenResponse(
            network_context="unknown",
            decision=decision
        )


async def _get_media_info(media_id: str, db: AsyncSession) -> Optional[dict]:
    """
    获取媒体基本信息
    
    TODO: 根据实际数据模型实现，从数据库查询媒体详情
    当前返回模拟数据用于测试
    
    Args:
        media_id: 媒体 ID
        config: 配置对象
        
    Returns:
        dict | None: 媒体信息字典，包含 title, year, season 等字段
    """
    
    try:
        media_pk = int(media_id)
    except (TypeError, ValueError):
        return None

    media = await db.get(Media, media_pk)
    if not media:
        return None

    return {
        "id": media.id,
        "title": media.title,
        "year": media.year,
        "season": None,
        "media_type": media.media_type,
        "tmdb_id": media.tmdb_id
    }


# TODO: 在实际项目中，需要在这里添加真实的数据库查询逻辑
# 例如：
# async def _get_media_info(media_id: str, config: Settings) -> Optional[dict]:
#     from app.db.session import get_db_session
#     from app.models.media import Media
#     
#     async with get_db_session() as session:
#         media = await session.get(Media, media_id)
#         if not media:
#             return None
#         
#         return {
#             "title": media.title,
#             "year": media.year,
#             "season": media.season,
#             "type": media.type
#         }
