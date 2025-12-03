"""
电视墙 API

提供作品聚合列表，用于海报墙展示
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func
from loguru import logger

from app.core.database import get_db
from app.api.auth import oauth2_scheme
from app.core.security import decode_access_token
from app.models.user import User
from app.models.media import Media, MediaFile
from app.models.strm import STRMFile
from app.core.schemas import BaseResponse, SuccessResponse, PaginatedResponse
from app.services.player_wall_aggregation_service import PlayerWallAggregationService

router = APIRouter()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户对象"""
    from fastapi import HTTPException, status
    
    payload = decode_access_token(token)
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user = await User.get_by_username(db, username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


@router.get(
    "/wall/list",
    response_model=BaseResponse,
    summary="获取电视墙列表"
)
async def get_player_wall_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键字（按片名模糊搜索）"),
    has_115: Optional[int] = Query(None, description="是否有115源（0/1）"),
    media_type: Optional[str] = Query(None, description="媒体类型（movie/tv/short_drama等）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取电视墙列表
    
    聚合作品信息，包括本地文件、115源、订阅、下载、HR风险、播放进度等状态
    """
    try:
        # 构建查询条件
        conditions = []
        
        # 关键字搜索
        if keyword:
            conditions.append(
                or_(
                    Media.title.ilike(f"%{keyword}%"),
                    Media.original_title.ilike(f"%{keyword}%")
                )
            )
        
        # 媒体类型筛选
        if media_type:
            conditions.append(Media.media_type == media_type)
        
        # 基础查询
        base_query = select(Media)
        if conditions:
            base_query = base_query.where(and_(*conditions))
        
        # 总数查询
        count_query = select(func.count()).select_from(Media)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        # 分页查询
        offset = (page - 1) * page_size
        query = base_query.offset(offset).limit(page_size).order_by(Media.id.desc())
        
        result = await db.execute(query)
        media_list = result.scalars().all()
        
        # 使用聚合服务批量获取状态信息
        try:
            aggregation_service = PlayerWallAggregationService(db)
            aggregated_list = await aggregation_service.aggregate_media_list_with_status(
                media_list, current_user.id
            )
        except Exception as e:
            logger.error(f"状态聚合服务失败，使用降级模式: {e}", exc_info=True)
            # 降级模式：为所有媒体提供空状态信息
            from app.services.player_wall_aggregation_service import MediaStatusInfo
            aggregated_list = [(media, MediaStatusInfo()) for media in media_list]
        
        # 构建返回项
        items = []
        for media, status_info in aggregated_list:
            # 提取源状态
            has_local = status_info.library_status == "in_library"
            has_115_source = status_info.library_status in ["partial", "in_library"]
            
            # 如果指定了 has_115 筛选，进行过滤
            if has_115 is not None:
                if has_115 == 1 and not has_115_source:
                    continue
                elif has_115 == 0 and has_115_source:
                    continue
            
            # 构建返回项
            item = {
                "work": {
                    "id": media.id,
                    "title": media.title,
                    "year": media.year,
                    "media_type": media.media_type,
                    "poster_url": media.poster_url,
                    "overview": media.overview,
                    "tmdb_id": media.tmdb_id
                },
                "source": {
                    "has_local": has_local,
                    "has_115": has_115_source
                },
                "status": {
                    "has_subscription": status_info.has_subscription,
                    "subscription_status": status_info.subscription_status,
                    "has_active_downloads": status_info.has_active_downloads,
                    "download_count": status_info.download_count,
                    "library_status": status_info.library_status,
                    "hr_risk": status_info.hr_risk,
                    "hr_level": status_info.hr_level,
                    "has_progress": status_info.has_progress,
                    "progress_percent": status_info.progress_percent,
                    "is_finished": status_info.is_finished
                }
            }
            items.append(item)
        
        # 如果进行了 has_115 筛选，需要重新计算总数
        if has_115 is not None:
            # 这里简化处理，实际应该用更高效的查询
            total = len(items)
            # 重新分页
            start = (page - 1) * page_size
            end = start + page_size
            items = items[start:end]
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return SuccessResponse(
            data=PaginatedResponse(
                items=items,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            ).model_dump(),
            message="获取电视墙列表成功"
        )
        
    except Exception as e:
        logger.error(f"获取电视墙列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取电视墙列表失败: {str(e)}"
        )

