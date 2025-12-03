"""
全局搜索 API
SEARCH-1 实现
"""
import logging
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.global_search import GlobalSearchResponse
from app.schemas.response import BaseResponse, success_response
from app.services.global_search_service import search_all

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["全局搜索"])


@router.get("/global", response_model=BaseResponse, summary="全局搜索")
async def global_search(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    limit_per_type: int = Query(5, ge=1, le=20, description="每种类型最多返回数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    全局搜索
    
    跨媒体类型搜索小说、漫画、音乐等
    """
    try:
        data = await search_all(db, query=q, limit_per_type=limit_per_type)
        return success_response(
            data=data.model_dump(),
            message="搜索成功"
        )
    except Exception as e:
        logger.error(f"全局搜索失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索失败: {str(e)}"
        )
