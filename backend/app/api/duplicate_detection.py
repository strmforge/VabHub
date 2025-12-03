"""
重复文件检测API
使用统一响应模型
"""

from fastapi import APIRouter, Depends, HTTPException, status as http_status, Query
from typing import List, Optional
from pydantic import BaseModel
from loguru import logger

from app.core.database import get_db
from app.modules.media_renamer.duplicate_detector import DuplicateDetector, DuplicateFile
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)

router = APIRouter()


class DuplicateFileResponse(BaseModel):
    """重复文件响应"""
    file_path: str
    file_size: int
    file_hash: str
    group_id: int


class DuplicateGroupResponse(BaseModel):
    """重复文件组响应"""
    group_id: int
    files: List[DuplicateFileResponse]
    total_size: int
    recommended_keep: str  # 推荐保留的文件路径


@router.post("/detect", response_model=BaseResponse)
async def detect_duplicates(
    directory: str = Query(..., description="要检测的目录路径"),
    extensions: Optional[List[str]] = Query(None, description="文件扩展名列表（如 .mp4, .mkv）"),
    use_hash: bool = Query(True, description="是否使用哈希值检测（更精确但更慢）"),
    db = Depends(get_db)
):
    """
    检测重复文件
    
    返回统一响应格式：
    {
        "success": true,
        "message": "检测完成",
        "data": {
            "total_groups": 10,
            "total_files": 25,
            "groups": [DuplicateGroupResponse, ...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        detector = DuplicateDetector()
        duplicate_groups = detector.detect_duplicates(directory, extensions, use_hash)
        
        # 转换为响应格式
        groups_response = []
        total_files = 0
        
        for group in duplicate_groups:
            group_response = {
                "group_id": group[0].group_id,
                "files": [
                    {
                        "file_path": file.file_path,
                        "file_size": file.file_size,
                        "file_hash": file.file_hash,
                        "group_id": file.group_id
                    }
                    for file in group
                ],
                "total_size": sum(file.file_size for file in group),
                "recommended_keep": group[0].file_path  # 简单推荐：保留第一个文件
            }
            groups_response.append(group_response)
            total_files += len(group)
        
        return success_response(
            data={
                "total_groups": len(duplicate_groups),
                "total_files": total_files,
                "groups": groups_response
            },
            message=f"检测完成：找到 {len(duplicate_groups)} 组重复文件，共 {total_files} 个文件"
        )
    except Exception as e:
        logger.error(f"检测重复文件失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"检测重复文件时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )


@router.post("/compare", response_model=BaseResponse)
async def compare_duplicates(
    file_paths: List[str],
    db = Depends(get_db)
):
    """
    比较重复文件的质量，推荐保留的文件
    
    返回统一响应格式：
    {
        "success": true,
        "message": "比较完成",
        "data": {
            "files": [QualityInfo, ...],
            "recommended_keep": QualityInfo
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.media_renamer.quality_comparator import QualityComparator
        
        comparator = QualityComparator()
        quality_infos = comparator.compare_files(file_paths)
        best_quality = comparator.get_best_quality_file(file_paths)
        
        return success_response(
            data={
                "files": [
                    {
                        "file_path": info.file_path,
                        "file_size": info.file_size,
                        "resolution": info.resolution,
                        "codec": info.codec,
                        "quality_score": info.quality_score
                    }
                    for info in quality_infos
                ],
                "recommended_keep": {
                    "file_path": best_quality.file_path,
                    "file_size": best_quality.file_size,
                    "resolution": best_quality.resolution,
                    "codec": best_quality.codec,
                    "quality_score": best_quality.quality_score
                } if best_quality else None
            },
            message="比较完成"
        )
    except Exception as e:
        logger.error(f"比较重复文件失败: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"比较重复文件时发生错误: {str(e)}"
            ).model_dump(mode='json')
        )

