"""
搜索API（Chain模式版本）
使用Chain模式的搜索API实现
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from pydantic import BaseModel
from loguru import logger

from app.chain import get_search_chain

router = APIRouter()


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str
    media_type: Optional[str] = None
    year: Optional[int] = None
    quality: Optional[str] = None
    resolution: Optional[str] = None
    min_size: Optional[float] = None
    max_size: Optional[float] = None
    min_seeders: Optional[int] = None
    max_seeders: Optional[int] = None
    include: Optional[str] = None
    exclude: Optional[str] = None
    sites: Optional[List[str]] = None
    sort_by: str = "seeders"
    sort_order: str = "desc"
    save_history: bool = True
    user_id: Optional[int] = None


class SearchResponse(BaseModel):
    """搜索响应"""
    results: List[dict]
    total: int
    query: str


@router.post("", response_model=SearchResponse)
async def search(request: SearchRequest):
    """执行搜索（Chain模式）"""
    try:
        chain = get_search_chain()
        results = await chain.search(
            query=request.query,
            media_type=request.media_type,
            year=request.year,
            quality=request.quality,
            resolution=request.resolution,
            min_size=request.min_size,
            max_size=request.max_size,
            min_seeders=request.min_seeders,
            max_seeders=request.max_seeders,
            include=request.include,
            exclude=request.exclude,
            sites=request.sites,
            sort_by=request.sort_by,
            sort_order=request.sort_order,
            save_history=request.save_history,
            user_id=request.user_id
        )
        
        return SearchResponse(
            results=results,
            total=len(results),
            query=request.query
        )
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索失败: {str(e)}"
        )


@router.get("/history", response_model=List[dict])
async def get_search_history(
    user_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    """获取搜索历史（Chain模式）"""
    try:
        chain = get_search_chain()
        history = await chain.get_search_history(user_id=user_id, limit=limit)
        return history
    except Exception as e:
        logger.error(f"获取搜索历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取搜索历史失败: {str(e)}"
        )


@router.get("/suggestions", response_model=List[str])
async def get_suggestions(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50)
):
    """获取搜索建议（Chain模式）"""
    try:
        chain = get_search_chain()
        suggestions = await chain.get_suggestions(query=query, limit=limit)
        return suggestions
    except Exception as e:
        logger.error(f"获取搜索建议失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取搜索建议失败: {str(e)}"
        )


@router.delete("/history/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_search_history(history_id: int):
    """删除搜索历史（Chain模式）"""
    try:
        chain = get_search_chain()
        success = await chain.delete_search_history(history_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="搜索历史不存在"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除搜索历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除搜索历史失败: {str(e)}"
        )


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
async def clear_search_history(user_id: Optional[int] = Query(None)):
    """清除搜索历史（Chain模式）"""
    try:
        chain = get_search_chain()
        await chain.clear_search_history(user_id=user_id)
    except Exception as e:
        logger.error(f"清除搜索历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清除搜索历史失败: {str(e)}"
        )

