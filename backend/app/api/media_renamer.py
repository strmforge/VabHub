"""
媒体文件重命名和整理API
使用统一响应模型
"""

from fastapi import APIRouter, Depends, HTTPException, status as http_status, Query, File, UploadFile
from typing import List, Optional
from pydantic import BaseModel
from loguru import logger

from app.core.database import get_db
from app.modules.media_renamer.identifier import MediaIdentifier
from app.modules.media_renamer.renamer import MediaRenamer
from app.modules.media_renamer.organizer import MediaOrganizer
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)
from app.core.config import settings

router = APIRouter()


class MediaInfoResponse(BaseModel):
    """媒体信息响应"""
    title: str
    year: Optional[int] = None
    media_type: str
    season: Optional[int] = None
    episode: Optional[int] = None
    episode_name: Optional[str] = None
    quality: Optional[str] = None
    resolution: Optional[str] = None
    codec: Optional[str] = None
    source: Optional[str] = None
    group: Optional[str] = None
    language: Optional[str] = None
    subtitle: Optional[str] = None
    raw_title: str = ""


class OrganizeRequest(BaseModel):
    """整理请求"""
    source_path: str
    target_base_dir: str
    rename_template: Optional[str] = None
    move_file: bool = True
    media_extensions: Optional[List[str]] = None
    download_subtitle: bool = False  # 是否下载字幕
    subtitle_language: str = "zh"  # 字幕语言
    use_classification: bool = True  # 是否使用分类规则


class OrganizeResultResponse(BaseModel):
    """整理结果响应"""
    original_path: str
    new_path: Optional[str] = None
    success: bool
    error: Optional[str] = None
    media_info: Optional[MediaInfoResponse] = None


@router.post("/identify", response_model=BaseResponse)
async def identify_media_file(
    file_path: str = Query(..., description="文件路径"),
    db = Depends(get_db)
):
    """
    识别媒体文件信息
    
    返回统一响应格式：
    {
        "success": true,
        "message": "识别成功",
        "data": MediaInfoResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        # 获取TMDB API密钥（从设置中）
        tmdb_api_key = getattr(settings, 'TMDB_API_KEY', None)
        
        identifier = MediaIdentifier(tmdb_api_key)
        media_info = await identifier.identify(file_path)
        
        # 转换为响应格式
        media_info_response = MediaInfoResponse(
            title=media_info.title,
            year=media_info.year,
            media_type=media_info.media_type,
            season=media_info.season,
            episode=media_info.episode,
            episode_name=media_info.episode_name,
            quality=media_info.quality,
            resolution=media_info.resolution,
            codec=media_info.codec,
            source=media_info.source,
            group=media_info.group,
            language=media_info.language,
            subtitle=media_info.subtitle,
            raw_title=media_info.raw_title
        )
        
        return success_response(
            data=media_info_response.model_dump(),
            message="识别成功"
        )
    except Exception as e:
        logger.error(f"识别媒体文件失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"识别媒体文件时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


@router.post("/identify/batch", response_model=BaseResponse)
async def batch_identify_media_files(
    file_paths: List[str],
    db = Depends(get_db)
):
    """
    批量识别媒体文件
    
    返回统一响应格式：
    {
        "success": true,
        "message": "识别成功",
        "data": [MediaInfoResponse, ...],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        # 获取TMDB API密钥
        tmdb_api_key = getattr(settings, 'TMDB_API_KEY', None)
        
        identifier = MediaIdentifier(tmdb_api_key)
        media_infos = await identifier.identify_batch(file_paths)
        
        # 转换为响应格式
        media_info_responses = [
            MediaInfoResponse(
                title=info.title,
                year=info.year,
                media_type=info.media_type,
                season=info.season,
                episode=info.episode,
                episode_name=info.episode_name,
                quality=info.quality,
                resolution=info.resolution,
                codec=info.codec,
                source=info.source,
                group=info.group,
                language=info.language,
                subtitle=info.subtitle,
                raw_title=info.raw_title
            ) for info in media_infos
        ]
        
        return success_response(
            data=[info.model_dump() for info in media_info_responses],
            message=f"成功识别 {len(media_info_responses)} 个文件"
        )
    except Exception as e:
        logger.error(f"批量识别媒体文件失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"批量识别媒体文件时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


@router.post("/organize", response_model=BaseResponse)
async def organize_media_file(
    request: OrganizeRequest,
    db = Depends(get_db)
):
    """
    整理媒体文件（识别、重命名、移动）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "整理成功",
        "data": OrganizeResultResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        # 获取TMDB API密钥
        tmdb_api_key = getattr(settings, 'TMDB_API_KEY', None)
        
        organizer = MediaOrganizer(tmdb_api_key)
        result = await organizer.organize_file(
            request.source_path,
            request.target_base_dir,
            request.rename_template,
            request.move_file,
            request.download_subtitle,
            request.subtitle_language,
            request.use_classification
        )
        
        # 转换为响应格式
        result_response = OrganizeResultResponse(
            original_path=result.original_path,
            new_path=result.new_path,
            success=result.success,
            error=result.error,
            media_info=MediaInfoResponse(
                title=result.media_info.title,
                year=result.media_info.year,
                media_type=result.media_info.media_type,
                season=result.media_info.season,
                episode=result.media_info.episode,
                episode_name=result.media_info.episode_name,
                quality=result.media_info.quality,
                resolution=result.media_info.resolution,
                codec=result.media_info.codec,
                source=result.media_info.source,
                group=result.media_info.group,
                language=result.media_info.language,
                subtitle=result.media_info.subtitle,
                raw_title=result.media_info.raw_title
            ) if result.media_info else None
        )
        
        return success_response(
            data=result_response.model_dump(),
            message="整理成功" if result.success else "整理失败"
        )
    except Exception as e:
        logger.error(f"整理媒体文件失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"整理媒体文件时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


@router.post("/organize/directory", response_model=BaseResponse)
async def organize_directory(
    request: OrganizeRequest,
    db = Depends(get_db)
):
    """
    整理目录中的所有媒体文件
    
    返回统一响应格式：
    {
        "success": true,
        "message": "整理完成",
        "data": {
            "total": 10,
            "success": 8,
            "failed": 2,
            "results": [OrganizeResultResponse, ...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        # 获取TMDB API密钥
        tmdb_api_key = getattr(settings, 'TMDB_API_KEY', None)
        
        organizer = MediaOrganizer(tmdb_api_key)
        results = await organizer.organize_directory(
            request.source_path,
            request.target_base_dir,
            request.rename_template,
            request.move_file,
            request.media_extensions,
            request.download_subtitle,
            request.subtitle_language,
            request.use_classification
        )
        
        # 转换为响应格式
        result_responses = []
        for result in results:
            result_response = OrganizeResultResponse(
                original_path=result.original_path,
                new_path=result.new_path,
                success=result.success,
                error=result.error,
                media_info=MediaInfoResponse(
                    title=result.media_info.title,
                    year=result.media_info.year,
                    media_type=result.media_info.media_type,
                    season=result.media_info.season,
                    episode=result.media_info.episode,
                    episode_name=result.media_info.episode_name,
                    quality=result.media_info.quality,
                    resolution=result.media_info.resolution,
                    codec=result.media_info.codec,
                    source=result.media_info.source,
                    group=result.media_info.group,
                    language=result.media_info.language,
                    subtitle=result.media_info.subtitle,
                    raw_title=result.media_info.raw_title
                ) if result.media_info else None
            )
            result_responses.append(result_response)
        
        success_count = sum(1 for r in results if r.success)
        failed_count = len(results) - success_count
        
        return success_response(
            data={
                "total": len(results),
                "success": success_count,
                "failed": failed_count,
                "results": [r.model_dump() for r in result_responses]
            },
            message=f"整理完成：成功 {success_count} 个，失败 {failed_count} 个"
        )
    except Exception as e:
        logger.error(f"整理目录失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"整理目录时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )

