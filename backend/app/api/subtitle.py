"""
字幕相关API
使用统一响应模型
"""

from fastapi import APIRouter, Depends, HTTPException, status as http_status, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from loguru import logger

from app.core.database import get_db
from app.modules.subtitle.service import SubtitleService
from app.core.schemas import (
    BaseResponse,
    PaginatedResponse,
    NotFoundResponse,
    success_response,
    error_response
)

router = APIRouter()


class SubtitleResponse(BaseModel):
    """字幕响应"""
    id: int
    media_file_path: str
    media_type: str
    media_title: str
    media_year: Optional[int] = None
    season: Optional[int] = None
    episode: Optional[int] = None
    subtitle_path: str
    language: str
    language_code: str
    format: str
    source: str
    source_id: Optional[str] = None
    download_url: Optional[str] = None
    file_size: Optional[int] = None
    rating: Optional[int] = None
    downloads: Optional[int] = None
    is_embedded: bool
    is_external: bool
    is_forced: bool
    is_hearing_impaired: bool
    downloaded_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SubtitleInfoResponse(BaseModel):
    """字幕信息响应（搜索结果）"""
    title: str
    language: str
    language_code: str
    format: str
    download_url: str
    file_size: int
    rating: Optional[int] = None
    downloads: Optional[int] = None
    source: str
    source_id: str
    is_forced: bool
    is_hearing_impaired: bool


@router.post("/download", response_model=BaseResponse)
async def download_subtitle(
    media_file_path: str = Query(..., description="媒体文件路径"),
    language: str = Query("zh", description="语言"),
    save_path: Optional[str] = Query(None, description="保存路径（可选）"),
    force_download: bool = Query(True, description="是否强制下载（忽略自动下载设置）"),
    db = Depends(get_db)
):
    """
    下载字幕
    
    返回统一响应格式：
    {
        "success": true,
        "message": "下载成功",
        "data": {
            "subtitle_path": "/path/to/subtitle.srt"
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SubtitleService(db)
        subtitle_path = await service.download_subtitle(
            media_file_path,
            language,
            save_path,
            force_download=force_download
        )
        
        if not subtitle_path:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="SUBTITLE_NOT_FOUND",
                    error_message="未找到匹配的字幕"
                ).model_dump(mode='json')
            )
        
        return success_response(
            data={"subtitle_path": subtitle_path},
            message="下载成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载字幕失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"下载字幕时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


@router.get("/search", response_model=BaseResponse)
async def search_subtitles(
    media_file_path: str = Query(..., description="媒体文件路径"),
    language: str = Query("zh", description="语言"),
    db = Depends(get_db)
):
    """
    搜索字幕（不下载）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "搜索成功",
        "data": [SubtitleInfoResponse, ...],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SubtitleService(db)
        subtitles = await service.search_subtitles(media_file_path, language)
        
        # 转换为响应格式
        subtitle_responses = [
            SubtitleInfoResponse(
                title=subtitle.title,
                language=subtitle.language,
                language_code=subtitle.language_code,
                format=subtitle.format,
                download_url=subtitle.download_url,
                file_size=subtitle.file_size,
                rating=subtitle.rating,
                downloads=subtitle.downloads,
                source=subtitle.source,
                source_id=subtitle.source_id,
                is_forced=subtitle.is_forced,
                is_hearing_impaired=subtitle.is_hearing_impaired
            ) for subtitle in subtitles
        ]
        
        return success_response(
            data=[subtitle.model_dump() for subtitle in subtitle_responses],
            message=f"找到 {len(subtitle_responses)} 个字幕"
        )
    except Exception as e:
        logger.error(f"搜索字幕失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"搜索字幕时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


@router.get("/", response_model=BaseResponse)
async def list_subtitles(
    media_file_path: Optional[str] = Query(None, description="媒体文件路径过滤"),
    language: Optional[str] = Query(None, description="语言过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db = Depends(get_db)
):
    """
    获取字幕列表（支持分页）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "items": [SubtitleResponse, ...],
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SubtitleService(db)
        subtitles = await service.list_subtitles(media_file_path, language)
        
        # 计算分页
        total = len(subtitles)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_items = subtitles[start:end]
        
        # 转换为响应格式
        subtitle_responses = [
            SubtitleResponse.model_validate(item) for item in paginated_items
        ]
        
        # 使用PaginatedResponse
        paginated_data = PaginatedResponse.create(
            items=[item.model_dump() for item in subtitle_responses],
            total=total,
            page=page,
            page_size=page_size
        )
        
        return success_response(data=paginated_data.model_dump(), message="获取成功")
    except Exception as e:
        logger.error(f"获取字幕列表失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取字幕列表时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


@router.get("/{subtitle_id}", response_model=BaseResponse)
async def get_subtitle(
    subtitle_id: int,
    db = Depends(get_db)
):
    """
    获取字幕详情
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": SubtitleResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SubtitleService(db)
        subtitle = await service.get_subtitle(subtitle_id)
        if not subtitle:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"字幕不存在 (ID: {subtitle_id})"
                ).model_dump(mode='json')
            )
        
        # 转换为响应格式
        subtitle_response = SubtitleResponse.model_validate(subtitle)
        return success_response(data=subtitle_response.model_dump(), message="获取成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取字幕详情失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取字幕详情时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


@router.delete("/{subtitle_id}", response_model=BaseResponse)
async def delete_subtitle(
    subtitle_id: int,
    db = Depends(get_db)
):
    """
    删除字幕
    
    返回统一响应格式：
    {
        "success": true,
        "message": "删除成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = SubtitleService(db)
        success = await service.delete_subtitle(subtitle_id)
        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"字幕不存在 (ID: {subtitle_id})"
                ).model_dump(mode='json')
            )
        
        return success_response(data=None, message="删除成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除字幕失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除字幕时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )

