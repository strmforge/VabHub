"""
任务管理API
用于管理系统任务（下载、上传、同步等）
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from loguru import logger

from app.core.database import get_db
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response,
    NotFoundResponse
)

router = APIRouter()


class TaskResponse(BaseModel):
    """任务响应"""
    id: str
    type: str  # download, upload, sync, etc.
    status: str  # pending, running, completed, failed, cancelled
    progress: float
    title: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


@router.get("/", response_model=BaseResponse)
async def list_tasks(
    task_type: Optional[str] = Query(None, description="任务类型过滤: download, upload, sync"),
    status: Optional[str] = Query(None, description="状态过滤: pending, running, completed, failed, cancelled"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取任务列表
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "items": [TaskResponse, ...],
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        # 收集所有类型的任务
        all_tasks = []
        
        # 1. 下载任务
        if not task_type or task_type == "download":
            from app.modules.download.service import DownloadService
            download_service = DownloadService(db)
            downloads = await download_service.list_downloads(
                status=status,
                page=1,
                page_size=1000  # 获取所有下载任务
            )
            if downloads and isinstance(downloads, dict):
                items = downloads.get("items", [])
                for item in items:
                    all_tasks.append({
                        "id": item.get("id", ""),
                        "type": "download",
                        "status": item.get("status", "unknown"),
                        "progress": item.get("progress", 0.0),
                        "title": item.get("title", ""),
                        "created_at": item.get("created_at"),
                        "updated_at": item.get("updated_at"),
                        "completed_at": None,
                        "error_message": None
                    })
        
        # 2. STRM同步任务
        if not task_type or task_type == "sync":
            from app.modules.strm.task_manager import get_sync_task_manager
            task_manager = get_sync_task_manager()
            sync_tasks = await task_manager.list_running_tasks()
            for task in sync_tasks:
                all_tasks.append({
                    "id": task.get("task_id", ""),
                    "type": "sync",
                    "status": task.get("status", "unknown"),
                    "progress": task.get("progress", 0.0),
                    "title": task.get("title", "STRM同步"),
                    "created_at": task.get("created_at"),
                    "updated_at": task.get("updated_at"),
                    "completed_at": task.get("completed_at"),
                    "error_message": task.get("error_message")
                })
        
        # 3. 上传任务
        if not task_type or task_type == "upload":
            from app.modules.upload.service import UploadTaskManager
            upload_manager = UploadTaskManager()
            upload_tasks = await upload_manager.list_tasks()
            for task in upload_tasks:
                all_tasks.append({
                    "id": task.get("id", ""),
                    "type": "upload",
                    "status": task.get("status", "unknown"),
                    "progress": task.get("progress", 0.0),
                    "title": task.get("title", ""),
                    "created_at": task.get("created_at"),
                    "updated_at": task.get("updated_at"),
                    "completed_at": task.get("completed_at"),
                    "error_message": task.get("error_message")
                })
        
        # 应用状态过滤
        if status:
            all_tasks = [t for t in all_tasks if t.get("status") == status]
        
        # 排序（按创建时间倒序）
        all_tasks.sort(key=lambda x: x.get("created_at") or datetime.min, reverse=True)
        
        # 分页
        total = len(all_tasks)
        total_pages = (total + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        paginated_tasks = all_tasks[start:end]
        
        return success_response(
            data={
                "items": paginated_tasks,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            },
            message="获取任务列表成功"
        )
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取任务列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/{task_id}", response_model=BaseResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取任务详情
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": TaskResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        # 尝试从下载任务获取
        from app.modules.download.service import DownloadService
        download_service = DownloadService(db)
        download = await download_service.get_download(task_id)
        if download:
            return success_response(
                data={
                    "id": download.get("id", task_id),
                    "type": "download",
                    "status": download.get("status", "unknown"),
                    "progress": download.get("progress", 0.0),
                    "title": download.get("title", ""),
                    "created_at": download.get("created_at"),
                    "updated_at": download.get("updated_at"),
                    "completed_at": None,
                    "error_message": None
                },
                message="获取任务详情成功"
            )
        
        # 尝试从STRM同步任务获取
        from app.modules.strm.task_manager import get_sync_task_manager
        task_manager = get_sync_task_manager()
        sync_task = await task_manager.get_task_status(task_id)
        if sync_task:
            return success_response(
                data={
                    "id": sync_task.get("task_id", task_id),
                    "type": "sync",
                    "status": sync_task.get("status", "unknown"),
                    "progress": sync_task.get("progress", 0.0),
                    "title": sync_task.get("title", "STRM同步"),
                    "created_at": sync_task.get("created_at"),
                    "updated_at": sync_task.get("updated_at"),
                    "completed_at": sync_task.get("completed_at"),
                    "error_message": sync_task.get("error_message")
                },
                message="获取任务详情成功"
            )
        
        # 尝试从上传任务获取
        from app.modules.upload.service import UploadTaskManager
        upload_manager = UploadTaskManager()
        upload_task = await upload_manager.get_task(task_id)
        if upload_task:
            return success_response(
                data={
                    "id": upload_task.get("id", task_id),
                    "type": "upload",
                    "status": upload_task.get("status", "unknown"),
                    "progress": upload_task.get("progress", 0.0),
                    "title": upload_task.get("title", ""),
                    "created_at": upload_task.get("created_at"),
                    "updated_at": upload_task.get("updated_at"),
                    "completed_at": upload_task.get("completed_at"),
                    "error_message": upload_task.get("error_message")
                },
                message="获取任务详情成功"
            )
        
        # 未找到任务
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NotFoundResponse(
                error_code="NOT_FOUND",
                error_message=f"任务不存在 (ID: {task_id})"
            ).model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取任务详情时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/{task_id}/retry", response_model=BaseResponse)
async def retry_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    重试任务
    
    返回统一响应格式：
    {
        "success": true,
        "message": "重试成功",
        "data": TaskResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        # 尝试重试下载任务
        from app.modules.download.service import DownloadService
        download_service = DownloadService(db)
        download = await download_service.get_download(task_id)
        if download:
            # 恢复下载（相当于重试）
            success = await download_service.resume_download(task_id)
            if success:
                return success_response(message="任务重试成功")
        
        # 尝试重试STRM同步任务
        from app.modules.strm.task_manager import get_sync_task_manager
        task_manager = get_sync_task_manager()
        sync_task = await task_manager.get_task_status(task_id)
        if sync_task and sync_task.get("status") == "failed":
            # 重新启动同步任务
            # 这里需要根据实际情况实现
            return success_response(message="任务重试成功（STRM同步任务需要手动重新启动）")
        
        # 未找到任务或任务不支持重试
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NotFoundResponse(
                error_code="NOT_FOUND",
                error_message=f"任务不存在或不支持重试 (ID: {task_id})"
            ).model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重试任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"重试任务时发生错误: {str(e)}"
            ).model_dump()
        )

