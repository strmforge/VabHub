"""
HNR检测相关API
使用统一响应模型
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from pydantic import BaseModel, Field
from loguru import logger

from app.core.database import get_db
from app.modules.hnr.service import HNRService
from app.core.schemas import (
    BaseResponse,
    PaginatedResponse,
    NotFoundResponse,
    success_response,
    error_response
)

router = APIRouter()


class HNRDetectionRequest(BaseModel):
    """HNR检测请求"""
    title: str = Field(..., description="资源标题")
    subtitle: str = Field("", description="副标题")
    badges_text: str = Field("", description="标签文本")
    list_html: str = Field("", description="列表HTML")
    site_id: Optional[int] = Field(None, description="站点ID")
    site_name: Optional[str] = Field(None, description="站点名称")
    download_task_id: Optional[int] = Field(None, description="下载任务ID")


class HNRTaskCreate(BaseModel):
    """创建HNR监控任务请求"""
    download_task_id: int = Field(..., description="下载任务ID")
    title: str = Field(..., description="任务标题")
    site_id: Optional[int] = Field(None, description="站点ID")
    site_name: Optional[str] = Field(None, description="站点名称")
    required_ratio: float = Field(1.0, description="要求分享率")
    required_seed_time_hours: float = Field(0.0, description="要求做种时间（小时）")


class HNRTaskUpdate(BaseModel):
    """更新HNR任务请求"""
    current_ratio: Optional[float] = None
    seed_time_hours: Optional[float] = None
    downloaded_gb: Optional[float] = None
    uploaded_gb: Optional[float] = None


@router.post("/signatures/reload", response_model=BaseResponse)
async def reload_signatures(
    db = Depends(get_db)
):
    """
    重新加载签名包（热更新）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "签名包已重新加载",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = HNRService(db)
        success = service.reload_signatures()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_response(
                    error_code="RELOAD_FAILED",
                    error_message="签名包重新加载失败"
                ).model_dump()
            )
        return success_response(message="签名包已重新加载")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新加载签名包失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"重新加载签名包时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/signatures", response_model=BaseResponse)
async def get_signatures(
    db = Depends(get_db)
):
    """
    获取所有签名
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "version": 1,
            "signatures": [...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = HNRService(db)
        signatures = service.detector.sigpack.get_signatures()
        return success_response(
            data={
                "version": service.detector.sigpack.pack.version if service.detector.sigpack.pack else 0,
                "signatures": [
                    {
                        "id": sig.id,
                        "name": sig.name,
                        "category": sig.category,
                        "confidence": sig.confidence,
                        "penalties": sig.penalties
                    }
                    for sig in signatures
                ]
            },
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取签名失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取签名时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/detect", response_model=BaseResponse)
async def detect_hnr(
    request: HNRDetectionRequest,
    db = Depends(get_db)
):
    """
    执行HNR检测
    
    返回统一响应格式：
    {
        "success": true,
        "message": "检测完成",
        "data": {
            "id": 1,
            "verdict": "...",
            "confidence": 0.95,
            "matched_rules": [...],
            "category": "...",
            "message": "...",
            "detected_at": "..."
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = HNRService(db)
        detection = await service.detect_hnr(
            title=request.title,
            subtitle=request.subtitle,
            badges_text=request.badges_text,
            list_html=request.list_html,
            site_id=request.site_id,
            site_name=request.site_name,
            download_task_id=request.download_task_id
        )
        
        return success_response(
            data={
                "id": detection.id,
                "verdict": detection.verdict,
                "confidence": detection.confidence,
                "matched_rules": detection.matched_rules,
                "category": detection.category,
                "message": detection.message,
                "detected_at": detection.detected_at.isoformat() if detection.detected_at else None
            },
            message="检测完成"
        )
    except Exception as e:
        logger.error(f"执行HNR检测失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"执行HNR检测时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/tasks", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_hnr_task(
    task: HNRTaskCreate,
    db = Depends(get_db)
):
    """
    创建HNR监控任务
    
    返回统一响应格式：
    {
        "success": true,
        "message": "创建成功",
        "data": HNRTaskResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = HNRService(db)
        hnr_task = await service.create_monitoring_task(
            download_task_id=task.download_task_id,
            title=task.title,
            site_id=task.site_id,
            site_name=task.site_name,
            required_ratio=task.required_ratio,
            required_seed_time_hours=task.required_seed_time_hours
        )
        
        if not hnr_task:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="CREATE_FAILED",
                    error_message="创建HNR监控任务失败"
                ).model_dump()
            )
        
        return success_response(
            data={
                "id": hnr_task.id,
                "download_task_id": hnr_task.download_task_id,
                "title": hnr_task.title,
                "status": hnr_task.status,
                "risk_score": hnr_task.risk_score,
                "current_ratio": hnr_task.current_ratio,
                "required_ratio": hnr_task.required_ratio,
                "seed_time_hours": hnr_task.seed_time_hours,
                "required_seed_time_hours": hnr_task.required_seed_time_hours,
                "created_at": hnr_task.created_at.isoformat() if hnr_task.created_at else None
            },
            message="创建成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建HNR监控任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"创建HNR监控任务时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/tasks", response_model=BaseResponse)
async def list_hnr_tasks(
    status: Optional[str] = Query(None, description="任务状态"),
    min_risk_score: Optional[float] = Query(None, description="最小风险评分"),
    site_id: Optional[int] = Query(None, description="站点ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db = Depends(get_db)
):
    """
    获取HNR监控任务列表（支持分页）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "items": [HNRTaskResponse, ...],
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = HNRService(db)
        tasks = await service.list_tasks(
            status=status,
            min_risk_score=min_risk_score,
            site_id=site_id
        )
        
        task_responses = [
            {
                "id": task.id,
                "download_task_id": task.download_task_id,
                "title": task.title,
                "site_id": task.site_id,
                "site_name": task.site_name,
                "status": task.status,
                "risk_score": task.risk_score,
                "current_ratio": task.current_ratio,
                "required_ratio": task.required_ratio,
                "seed_time_hours": task.seed_time_hours,
                "required_seed_time_hours": task.required_seed_time_hours,
                "downloaded_gb": task.downloaded_gb,
                "uploaded_gb": task.uploaded_gb,
                "last_check": task.last_check.isoformat() if task.last_check else None,
                "next_check": task.next_check.isoformat() if task.next_check else None,
                "created_at": task.created_at.isoformat() if task.created_at else None
            }
            for task in tasks
        ]
        
        # 计算分页
        total = len(task_responses)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_items = task_responses[start:end]
        
        # 使用PaginatedResponse
        paginated_data = PaginatedResponse.create(
            items=paginated_items,
            total=total,
            page=page,
            page_size=page_size
        )
        
        return success_response(data=paginated_data.model_dump(), message="获取成功")
    except Exception as e:
        logger.error(f"获取HNR监控任务列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取HNR监控任务列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/tasks/{task_id}", response_model=BaseResponse)
async def get_hnr_task(
    task_id: int,
    db = Depends(get_db)
):
    """
    获取HNR监控任务详情
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": HNRTaskResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = HNRService(db)
        task = await service.get_task(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"HNR监控任务不存在 (ID: {task_id})"
                ).model_dump()
            )
        
        return success_response(
            data={
                "id": task.id,
                "download_task_id": task.download_task_id,
                "title": task.title,
                "site_id": task.site_id,
                "site_name": task.site_name,
                "status": task.status,
                "risk_score": task.risk_score,
                "current_ratio": task.current_ratio,
                "required_ratio": task.required_ratio,
                "seed_time_hours": task.seed_time_hours,
                "required_seed_time_hours": task.required_seed_time_hours,
                "downloaded_gb": task.downloaded_gb,
                "uploaded_gb": task.uploaded_gb,
                "last_check": task.last_check.isoformat() if task.last_check else None,
                "next_check": task.next_check.isoformat() if task.next_check else None,
                "created_at": task.created_at.isoformat() if task.created_at else None
            },
            message="获取成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取HNR监控任务详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取HNR监控任务详情时发生错误: {str(e)}"
            ).model_dump()
        )


@router.put("/tasks/{task_id}", response_model=BaseResponse)
async def update_hnr_task(
    task_id: int,
    update: HNRTaskUpdate,
    db = Depends(get_db)
):
    """
    更新HNR监控任务
    
    返回统一响应格式：
    {
        "success": true,
        "message": "更新成功",
        "data": HNRTaskResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = HNRService(db)
        task = await service.update_task_metrics(
            task_id=task_id,
            current_ratio=update.current_ratio,
            seed_time_hours=update.seed_time_hours,
            downloaded_gb=update.downloaded_gb,
            uploaded_gb=update.uploaded_gb
        )
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"HNR监控任务不存在 (ID: {task_id})"
                ).model_dump()
            )
        
        return success_response(
            data={
                "id": task.id,
                "risk_score": task.risk_score,
                "current_ratio": task.current_ratio,
                "seed_time_hours": task.seed_time_hours,
                "downloaded_gb": task.downloaded_gb,
                "uploaded_gb": task.uploaded_gb
            },
            message="更新成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新HNR监控任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新HNR监控任务时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/tasks/{task_id}", response_model=BaseResponse)
async def delete_hnr_task(
    task_id: int,
    db = Depends(get_db)
):
    """
    删除HNR监控任务
    
    返回统一响应格式：
    {
        "success": true,
        "message": "删除成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = HNRService(db)
        success = await service.delete_task(task_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"HNR监控任务不存在 (ID: {task_id})"
                ).model_dump()
            )
        return success_response(message="删除成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除HNR监控任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除HNR监控任务时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/stats", response_model=BaseResponse)
async def get_hnr_stats(db = Depends(get_db)):
    """
    获取HNR风险统计
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {stats_dict},
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = HNRService(db)
        stats = await service.get_risk_stats()
        return success_response(data=stats, message="获取成功")
    except Exception as e:
        logger.error(f"获取HNR风险统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取HNR风险统计时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/detections", response_model=BaseResponse)
async def get_recent_detections(
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    verdict: Optional[str] = Query(None, description="判定结果过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db = Depends(get_db)
):
    """
    获取最近的检测记录（支持分页）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "items": [DetectionResponse, ...],
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = HNRService(db)
        detections = await service.get_recent_detections(limit=limit, verdict=verdict)
        
        detection_responses = [
            {
                "id": detection.id,
                "download_task_id": detection.download_task_id,
                "title": detection.title,
                "site_name": detection.site_name,
                "verdict": detection.verdict,
                "confidence": detection.confidence,
                "matched_rules": detection.matched_rules,
                "category": detection.category,
                "message": detection.message,
                "detected_at": detection.detected_at.isoformat() if detection.detected_at else None
            }
            for detection in detections
        ]
        
        # 计算分页
        total = len(detection_responses)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_items = detection_responses[start:end]
        
        # 使用PaginatedResponse
        paginated_data = PaginatedResponse.create(
            items=paginated_items,
            total=total,
            page=page,
            page_size=page_size
        )
        
        return success_response(data=paginated_data.model_dump(), message="获取成功")
    except Exception as e:
        logger.error(f"获取检测记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取检测记录时发生错误: {str(e)}"
            ).model_dump()
        )

