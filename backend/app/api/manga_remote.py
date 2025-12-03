"""
远程漫画浏览 API（只读，普通用户可访问）
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db
from app.core.schemas import BaseResponse, success_response
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.manga_remote_service import (
    list_enabled_sources,
    search_series,
    get_series_detail,
    list_chapters,
    list_series_by_library,
    list_libraries_for_source,
    aggregated_search_series,
    build_external_url,
)

router = APIRouter(prefix="/api/manga/remote", tags=["远程漫画"])


@router.get("/sources", response_model=BaseResponse, summary="列出可用源")
async def list_sources(
    only_enabled: bool = Query(True, description="是否只返回启用的源"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    列出可用的漫画源（只读）
    
    不暴露敏感信息（如 api_key、password）
    """
    try:
        sources = await list_enabled_sources(db)
        if not only_enabled:
            # 如果需要所有源，可以扩展 service
            pass
        
        return success_response(
            data=[s.model_dump() for s in sources],
            message="获取源列表成功"
        )
    except Exception as e:
        logger.error(f"获取源列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取源列表失败: {str(e)}"
        )


@router.get(
    "/sources/{source_id}/libraries",
    response_model=BaseResponse,
    summary="列出指定源下的库/书架",
)
async def list_source_libraries(
    source_id: int = Path(..., description="源 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出指定源下的库/书架列表，供前端选择按库浏览使用。"""
    try:
        libraries = await list_libraries_for_source(db, source_id)
        return success_response(
            data=[lib.model_dump() for lib in libraries],
            message="获取库列表成功",
        )
    except Exception as e:
        logger.error(f"获取源库列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取库列表失败: {str(e)}",
        )


@router.get("/search", response_model=BaseResponse, summary="搜索漫画")
async def search_manga(
    q: str = Query(..., min_length=1, description="搜索关键字"),
    source_id: Optional[int] = Query(None, description="源 ID（可选，默认首个启用源）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    搜索远程漫画
    
    支持在指定源或默认源中搜索
    """
    try:
        result = await search_series(
            session=db,
            query=q,
            source_id=source_id,
            page=page,
            page_size=page_size,
        )
        
        return success_response(
            data=result.model_dump(),
            message="搜索成功"
        )
    except Exception as e:
        logger.error(f"搜索漫画失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索失败: {str(e)}"
        )


@router.get("/series/{source_id}/{remote_series_id}", response_model=BaseResponse, summary="获取漫画详情")
async def get_manga_detail(
    source_id: int = Path(..., description="源 ID"),
    remote_series_id: str = Path(..., description="远程漫画 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取漫画详情
    
    包括基本信息、封面、简介、作者、标签等
    """
    try:
        series = await get_series_detail(
            session=db,
            source_id=source_id,
            remote_series_id=remote_series_id,
        )
        
        if not series:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="漫画不存在或源不可用"
            )
        
        return success_response(
            data=series.model_dump(),
            message="获取详情成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取漫画详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取详情失败: {str(e)}"
        )


@router.get("/series/{source_id}/{remote_series_id}/chapters", response_model=BaseResponse, summary="获取章节列表")
async def get_manga_chapters(
    source_id: int = Path(..., description="源 ID"),
    remote_series_id: str = Path(..., description="远程漫画 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取漫画章节列表
    
    仅用于展示，不涉及下载
    """
    try:
        chapters = await list_chapters(
            session=db,
            source_id=source_id,
            remote_series_id=remote_series_id,
        )
        
        return success_response(
            data=[ch.model_dump() for ch in chapters],
            message="获取章节列表成功"
        )
    except Exception as e:
        logger.error(f"获取章节列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取章节列表失败: {str(e)}"
        )


@router.get(
    "/sources/{source_id}/libraries/{library_id}/series",
    response_model=BaseResponse,
    summary="按库浏览远程漫画系列",
)
async def browse_manga_by_library(
    source_id: int = Path(..., description="源 ID"),
    library_id: str = Path(..., description="库/书架 ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """按库/书架浏览远程漫画系列。

    若目标源不支持按库浏览，将返回空结果，前端可据此提示用户。
    """
    try:
        result = await list_series_by_library(
            session=db,
            source_id=source_id,
            library_id=library_id,
            page=page,
            page_size=page_size,
        )
        return success_response(
            data=result.model_dump(),
            message="获取库下漫画列表成功",
        )
    except Exception as e:
        logger.error(f"按库浏览远程漫画失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"按库浏览失败: {str(e)}",
        )


@router.get("/aggregated-search", response_model=BaseResponse, summary="聚合搜索漫画")
async def aggregated_search_manga(
    q: str = Query(..., min_length=1, description="搜索关键字"),
    sources: Optional[str] = Query(None, description="源ID列表，逗号分隔，不传则搜索所有启用源"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    timeout_per_source: int = Query(10, ge=5, le=30, description="每个源的超时时间（秒）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    聚合搜索远程漫画
    
    并发调用多个启用源的搜索，合并结果按源分组返回
    """
    try:
        # 解析源ID列表
        source_ids = None
        if sources:
            try:
                source_ids = [int(s.strip()) for s in sources.split(',') if s.strip()]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="源ID格式错误，应为逗号分隔的数字"
                )
        
        result = await aggregated_search_series(
            session=db,
            query=q,
            source_ids=source_ids,
            page=page,
            page_size=page_size,
            timeout_per_source=timeout_per_source,
        )
        
        return success_response(
            data=result.model_dump(),
            message="聚合搜索成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"聚合搜索漫画失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"聚合搜索失败: {str(e)}"
        )


@router.get(
    "/series/{source_id}/{remote_series_id}/external-url",
    response_model=BaseResponse,
    summary="获取外部阅读URL",
)
async def get_external_reading_url(
    source_id: int = Path(..., description="源 ID"),
    remote_series_id: str = Path(..., description="远程漫画 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取外部阅读URL
    
    返回在原站打开漫画的URL，用于"在原站打开"功能
    """
    try:
        external_url = await build_external_url(
            session=db,
            source_id=source_id,
            remote_series_id=remote_series_id,
        )
        
        if not external_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="无法构建外部URL或源不支持此功能"
            )
        
        return success_response(
            data={"external_url": external_url},
            message="获取外部URL成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取外部URL失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取外部URL失败: {str(e)}"
        )

