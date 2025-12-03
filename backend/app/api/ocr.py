"""
OCR API端点
提供OCR统计、配置、状态查询等功能
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, timedelta
from loguru import logger

from app.core.database import get_db
from app.core.ocr import OcrHelper
from app.modules.ocr.statistics import OCRStatisticsService
from app.core.schemas import success_response, error_response
from app.core.config import settings

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.get("/status")
async def get_ocr_status():
    """
    获取OCR引擎状态
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "external_service": {...},
            "paddleocr": {...},
            "preferred_engine": "..."
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        ocr_helper = OcrHelper()
        status = ocr_helper.get_engine_status()
        
        return success_response(
            data=status,
            message="获取OCR状态成功"
        )
    except Exception as e:
        logger.error(f"获取OCR状态失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取OCR状态失败: {str(e)}"
            ).model_dump()
        )


@router.get("/statistics")
async def get_ocr_statistics(
    site_name: Optional[str] = Query(None, description="站点名称过滤"),
    engine: Optional[str] = Query(None, description="OCR引擎过滤"),
    days: int = Query(30, ge=1, le=365, description="统计最近N天的数据"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取OCR统计信息
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "total": 100,
            "success": 85,
            "failed": 15,
            "success_rate": 85.0,
            "avg_duration_ms": 250.5,
            "avg_confidence": 0.9,
            "by_site": {...},
            "by_engine": {...}
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        stats_service = OCRStatisticsService(db)
        
        start_date = datetime.utcnow() - timedelta(days=days)
        statistics = await stats_service.get_statistics(
            site_name=site_name,
            engine=engine,
            start_date=start_date
        )
        
        return success_response(
            data=statistics,
            message="获取OCR统计成功"
        )
    except Exception as e:
        logger.error(f"获取OCR统计失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取OCR统计失败: {str(e)}"
            ).model_dump()
        )


@router.get("/records")
async def get_ocr_records(
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    site_name: Optional[str] = Query(None, description="站点名称过滤"),
    success_only: Optional[bool] = Query(None, description="是否只返回成功的记录"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取OCR识别记录
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [
            {
                "id": 1,
                "site_name": "OpenCD",
                "image_hash": "...",
                "cleaned_text": "ABC123",
                "success": true,
                "engine": "paddleocr",
                "duration_ms": 250,
                "created_at": "2025-01-XX..."
            },
            ...
        ],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        stats_service = OCRStatisticsService(db)
        records = await stats_service.get_recent_records(
            limit=limit,
            site_name=site_name,
            success_only=success_only
        )
        
        # 转换为字典列表
        records_data = [
            {
                "id": r.id,
                "site_name": r.site_name,
                "site_url": r.site_url,
                "image_hash": r.image_hash,
                "image_url": r.image_url,
                "original_text": r.original_text,
                "cleaned_text": r.cleaned_text,
                "expected_length": r.expected_length,
                "success": r.success,
                "confidence": r.confidence,
                "engine": r.engine,
                "retry_count": r.retry_count,
                "duration_ms": r.duration_ms,
                "error_message": r.error_message,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in records
        ]
        
        return success_response(
            data=records_data,
            message="获取OCR记录成功"
        )
    except Exception as e:
        logger.error(f"获取OCR记录失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取OCR记录失败: {str(e)}"
            ).model_dump()
        )


@router.post("/cleanup")
async def cleanup_ocr_records(
    days: int = Query(30, ge=1, le=365, description="保留最近N天的记录"),
    db: AsyncSession = Depends(get_db)
):
    """
    清理旧的OCR记录
    
    返回统一响应格式：
    {
        "success": true,
        "message": "清理成功",
        "data": {
            "deleted_count": 100
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        stats_service = OCRStatisticsService(db)
        deleted_count = await stats_service.cleanup_old_records(days=days)
        
        return success_response(
            data={"deleted_count": deleted_count},
            message=f"清理成功，删除了 {deleted_count} 条记录"
        )
    except Exception as e:
        logger.error(f"清理OCR记录失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"清理OCR记录失败: {str(e)}"
            ).model_dump()
        )


@router.get("/config")
async def get_ocr_config():
    """
    获取OCR配置信息
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "ocr_host": "...",
            "use_local_ocr": false,
            "preferred_engine": "..."
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        ocr_helper = OcrHelper()
        status = ocr_helper.get_engine_status()
        
        config = {
            "ocr_host": getattr(settings, 'OCR_HOST', None) or "https://movie-pilot.org",
            "use_local_ocr": getattr(settings, 'OCR_USE_LOCAL', False),
            "preferred_engine": status.get("preferred_engine", "external_service"),
            "external_service_available": status.get("external_service", {}).get("available", True),
            "paddleocr_available": status.get("paddleocr", {}).get("available", False)
        }
        
        return success_response(
            data=config,
            message="获取OCR配置成功"
        )
    except Exception as e:
        logger.error(f"获取OCR配置失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取OCR配置失败: {str(e)}"
            ).model_dump()
        )

