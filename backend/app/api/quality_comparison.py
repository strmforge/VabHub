"""
文件质量比较API
使用统一响应模型
"""

from fastapi import APIRouter, Depends, HTTPException, status as http_status, Query
from typing import List, Optional
from pydantic import BaseModel
from loguru import logger

from app.core.database import get_db
from app.modules.media_renamer.quality_comparator import QualityComparator, QualityInfo
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)

router = APIRouter()


class QualityInfoResponse(BaseModel):
    """质量信息响应"""
    file_path: str
    file_size: int
    resolution: Optional[str] = None
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None
    codec: Optional[str] = None
    bitrate: Optional[int] = None
    quality_score: float


@router.post("/compare", response_model=BaseResponse)
async def compare_quality(
    file_paths: List[str],
    db = Depends(get_db)
):
    """
    比较多个文件的质量
    
    返回统一响应格式：
    {
        "success": true,
        "message": "比较完成",
        "data": {
            "files": [QualityInfoResponse, ...],
            "best_quality": QualityInfoResponse
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        comparator = QualityComparator()
        quality_infos = await comparator.compare_files(file_paths)
        best_quality = await comparator.get_best_quality_file(file_paths)
        
        return success_response(
            data={
                "files": [
                    {
                        "file_path": info.file_path,
                        "file_size": info.file_size,
                        "resolution": info.resolution,
                        "resolution_width": info.resolution_width,
                        "resolution_height": info.resolution_height,
                        "codec": info.codec,
                        "bitrate": info.bitrate,
                        "quality_score": info.quality_score
                    }
                    for info in quality_infos
                ],
                "best_quality": {
                    "file_path": best_quality.file_path,
                    "file_size": best_quality.file_size,
                    "resolution": best_quality.resolution,
                    "resolution_width": best_quality.resolution_width,
                    "resolution_height": best_quality.resolution_height,
                    "codec": best_quality.codec,
                    "bitrate": best_quality.bitrate,
                    "quality_score": best_quality.quality_score
                } if best_quality else None
            },
            message="比较完成"
        )
    except Exception as e:
        logger.error(f"比较文件质量失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"比较文件质量时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


@router.post("/analyze", response_model=BaseResponse)
async def analyze_quality(
    file_path: str = Query(..., description="文件路径"),
    db = Depends(get_db)
):
    """
    分析单个文件的质量
    
    返回统一响应格式：
    {
        "success": true,
        "message": "分析完成",
        "data": QualityInfoResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        comparator = QualityComparator()
        quality_info = await comparator.get_quality_info(file_path)
        
        return success_response(
            data={
                "file_path": quality_info.file_path,
                "file_size": quality_info.file_size,
                "resolution": quality_info.resolution,
                "resolution_width": quality_info.resolution_width,
                "resolution_height": quality_info.resolution_height,
                "codec": quality_info.codec,
                "bitrate": quality_info.bitrate,
                "quality_score": quality_info.quality_score
            },
            message="分析完成"
        )
    except Exception as e:
        logger.error(f"分析文件质量失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"分析文件质量时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )

