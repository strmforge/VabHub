"""
上传任务管理API端点
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.upload import UploadTask, UploadProgress, UploadTaskStatus
from app.modules.upload.task_manager import UploadTaskManager
from app.core.cloud_storage.providers.cloud_115_api import Cloud115API
from app.core.config import settings
from loguru import logger

router = APIRouter(prefix="/upload", tags=["upload"])

# 全局上传任务管理器（需要在应用启动时初始化）
upload_task_manager: Optional[UploadTaskManager] = None


def get_upload_task_manager() -> UploadTaskManager:
    """获取上传任务管理器"""
    global upload_task_manager
    if upload_task_manager is None:
        # 从配置或数据库获取115网盘API客户端
        # 注意：这里需要根据实际配置获取access_token
        # 暂时使用空字符串，实际使用时需要从配置或数据库获取
        access_token = getattr(settings, 'CLOUD_115_ACCESS_TOKEN', None) or ""
        
        if not access_token:
            logger.warning("115网盘access_token未配置，上传功能可能不可用")
        
        api_client = Cloud115API(access_token=access_token)
        upload_task_manager = UploadTaskManager(
            api_client=api_client,
            max_concurrent=3,
            max_retries=3,
            retry_delay=5.0
        )
        
        # 启动任务管理器
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，创建任务启动
                asyncio.create_task(upload_task_manager.start())
            else:
                # 如果事件循环未运行，直接运行
                loop.run_until_complete(upload_task_manager.start())
        except Exception as e:
            logger.error(f"启动上传任务管理器失败: {e}")
    
    return upload_task_manager


# Pydantic模型
class UploadTaskCreate(BaseModel):
    """创建上传任务请求"""
    file_path: str = Field(..., description="本地文件路径")
    target_parent_id: str = Field(default="0", description="目标目录ID")
    file_name: Optional[str] = Field(None, description="文件名（可选）")
    speed_limit: Optional[int] = Field(None, description="速度限制（字节/秒）")
    user_id: Optional[str] = Field(None, description="用户ID（可选）")


class UploadTaskResponse(BaseModel):
    """上传任务响应"""
    id: str
    file_path: str
    file_name: str
    file_size: int
    status: str
    progress: float
    uploaded_bytes: int
    total_bytes: int
    speed_limit: Optional[int]
    current_speed: Optional[float]
    retry_count: int
    max_retries: int
    created_at: str
    updated_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    
    class Config:
        from_attributes = True


class UploadTaskListResponse(BaseModel):
    """上传任务列表响应"""
    tasks: List[UploadTaskResponse]
    total: int
    offset: int
    limit: int


class UploadProgressResponse(BaseModel):
    """上传进度响应"""
    id: str
    task_id: str
    uploaded_bytes: int
    total_bytes: int
    progress: float
    current_speed: Optional[float]
    average_speed: Optional[float]
    elapsed_time: Optional[float]
    estimated_remaining: Optional[float]
    recorded_at: str
    
    class Config:
        from_attributes = True


@router.post("/tasks", response_model=UploadTaskResponse, summary="添加上传任务")
async def create_upload_task(
    task_data: UploadTaskCreate,
    manager: UploadTaskManager = Depends(get_upload_task_manager)
):
    """
    添加上传任务
    
    - **file_path**: 本地文件路径
    - **target_parent_id**: 目标目录ID（默认0，根目录）
    - **file_name**: 文件名（可选，默认使用本地文件名）
    - **speed_limit**: 速度限制（字节/秒，可选）
    - **user_id**: 用户ID（可选）
    """
    try:
        task_id = await manager.add_task(
            file_path=task_data.file_path,
            target_parent_id=task_data.target_parent_id,
            file_name=task_data.file_name,
            speed_limit=task_data.speed_limit,
            user_id=task_data.user_id
        )
        
        # 获取任务信息
        task_info = await manager.get_task(task_id)
        
        if not task_info:
            raise HTTPException(status_code=404, detail="任务创建失败")
        
        return UploadTaskResponse(**task_info)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=UploadTaskListResponse, summary="列出上传任务")
async def list_upload_tasks(
    status: Optional[str] = Query(None, description="状态过滤"),
    user_id: Optional[str] = Query(None, description="用户ID过滤"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    manager: UploadTaskManager = Depends(get_upload_task_manager)
):
    """
    列出上传任务
    
    - **status**: 状态过滤（可选）
    - **user_id**: 用户ID过滤（可选）
    - **limit**: 限制数量（1-1000，默认100）
    - **offset**: 偏移量（默认0）
    """
    try:
        tasks = await manager.list_tasks(
            status=status,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return UploadTaskListResponse(
            tasks=[UploadTaskResponse(**task) for task in tasks],
            total=len(tasks),
            offset=offset,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=UploadTaskResponse, summary="获取任务详情")
async def get_upload_task(
    task_id: UUID,
    manager: UploadTaskManager = Depends(get_upload_task_manager)
):
    """
    获取上传任务详情
    
    - **task_id**: 任务ID
    """
    try:
        task_info = await manager.get_task(task_id)
        
        if not task_info:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return UploadTaskResponse(**task_info)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/cancel", summary="取消任务")
async def cancel_upload_task(
    task_id: UUID,
    manager: UploadTaskManager = Depends(get_upload_task_manager)
):
    """
    取消上传任务
    
    - **task_id**: 任务ID
    """
    try:
        success = await manager.cancel_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="任务不存在或无法取消")
        
        return {"success": True, "message": "任务已取消"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/pause", summary="暂停任务")
async def pause_upload_task(
    task_id: UUID,
    manager: UploadTaskManager = Depends(get_upload_task_manager)
):
    """
    暂停上传任务
    
    - **task_id**: 任务ID
    """
    try:
        success = await manager.pause_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="任务不存在或无法暂停")
        
        return {"success": True, "message": "任务已暂停"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/resume", summary="恢复任务")
async def resume_upload_task(
    task_id: UUID,
    manager: UploadTaskManager = Depends(get_upload_task_manager)
):
    """
    恢复上传任务
    
    - **task_id**: 任务ID
    """
    try:
        success = await manager.resume_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="任务不存在或无法恢复")
        
        return {"success": True, "message": "任务已恢复"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/progress", response_model=List[UploadProgressResponse], summary="获取任务进度历史")
async def get_upload_task_progress(
    task_id: UUID,
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取上传任务进度历史
    
    - **task_id**: 任务ID
    - **limit**: 限制数量（1-1000，默认100）
    """
    try:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        result = await db.execute(
            select(UploadProgress)
            .where(UploadProgress.task_id == task_id)
            .order_by(UploadProgress.recorded_at.desc())
            .limit(limit)
        )
        progress_records = result.scalars().all()
        
        return [UploadProgressResponse(**record.to_dict()) for record in progress_records]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", summary="获取上传统计信息")
async def get_upload_stats(
    user_id: Optional[str] = Query(None, description="用户ID过滤"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取上传统计信息
    
    - **user_id**: 用户ID过滤（可选）
    """
    try:
        from sqlalchemy import select, func
        from sqlalchemy import and_
        
        query = select(UploadTask)
        conditions = []
        
        if user_id:
            conditions.append(UploadTask.user_id == user_id)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 统计各状态的任务数
        status_counts = {}
        for status in UploadTaskStatus:
            count_query = select(func.count(UploadTask.id)).where(UploadTask.status == status.value)
            if conditions:
                count_query = count_query.where(and_(*conditions))
            result = await db.execute(count_query)
            status_counts[status.value] = result.scalar()
        
        # 统计总上传字节数
        total_uploaded = select(func.sum(UploadTask.uploaded_bytes))
        if conditions:
            total_uploaded = total_uploaded.where(and_(*conditions))
        result = await db.execute(total_uploaded)
        total_uploaded_bytes = result.scalar() or 0
        
        # 统计总文件大小
        total_size = select(func.sum(UploadTask.total_bytes))
        if conditions:
            total_size = total_size.where(and_(*conditions))
        result = await db.execute(total_size)
        total_bytes = result.scalar() or 0
        
        return {
            "status_counts": status_counts,
            "total_uploaded_bytes": total_uploaded_bytes,
            "total_bytes": total_bytes,
            "total_tasks": sum(status_counts.values())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

