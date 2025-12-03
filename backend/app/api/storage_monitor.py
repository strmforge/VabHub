"""
存储监控API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.core.schemas import success_response, error_response
from app.modules.storage_monitor.service import StorageMonitorService
from loguru import logger

router = APIRouter()


# 请求模型
class StorageDirectoryCreate(BaseModel):
    """创建存储目录请求"""
    name: str = Field(..., description="目录名称")
    path: str = Field(..., description="目录路径")
    enabled: bool = Field(True, description="是否启用监控")
    alert_threshold: float = Field(80.0, description="预警阈值（百分比）", ge=0, le=100)
    description: Optional[str] = Field(None, description="描述")


class StorageDirectoryUpdate(BaseModel):
    """更新存储目录请求"""
    name: Optional[str] = Field(None, description="目录名称")
    enabled: Optional[bool] = Field(None, description="是否启用监控")
    alert_threshold: Optional[float] = Field(None, description="预警阈值（百分比）", ge=0, le=100)
    description: Optional[str] = Field(None, description="描述")


class StorageDirectoryResponse(BaseModel):
    """存储目录响应"""
    id: int
    name: str
    path: str
    enabled: bool
    alert_threshold: float
    description: Optional[str]
    created_at: str
    updated_at: str


class StorageUsageResponse(BaseModel):
    """存储使用情况响应"""
    directory_id: int
    name: str
    path: str
    enabled: bool
    alert_threshold: float
    total_bytes: int
    used_bytes: int
    free_bytes: int
    usage_percent: float


class StorageUsageHistoryResponse(BaseModel):
    """存储使用历史响应"""
    id: int
    directory_id: int
    path: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    usage_percent: float
    recorded_at: str


class StorageAlertResponse(BaseModel):
    """存储预警响应"""
    id: int
    directory_id: int
    path: str
    alert_type: str
    usage_percent: float
    threshold: float
    message: Optional[str]
    resolved: bool
    resolved_at: Optional[str]
    created_at: str


class StorageTrendsResponse(BaseModel):
    """存储使用趋势响应"""
    trends: List[dict]
    days: int
    total_points: int


class StorageStatisticsResponse(BaseModel):
    """存储监控统计响应"""
    total_directories: int
    enabled_directories: int
    unresolved_alerts: int
    total_space_bytes: int
    total_used_bytes: int
    total_free_bytes: int
    total_usage_percent: float
    directories: List[StorageUsageResponse]


@router.post("/directories", response_model=dict)
async def create_directory(
    directory_data: StorageDirectoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建存储目录配置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "创建成功",
        "data": StorageDirectoryResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = StorageMonitorService(db)
        directory = await service.create_directory(
            name=directory_data.name,
            path=directory_data.path,
            enabled=directory_data.enabled,
            alert_threshold=directory_data.alert_threshold,
            description=directory_data.description
        )
        await db.commit()
        
        return success_response(
            data=StorageDirectoryResponse(
                id=directory.id,
                name=directory.name,
                path=directory.path,
                enabled=directory.enabled,
                alert_threshold=directory.alert_threshold,
                description=directory.description,
                created_at=directory.created_at.isoformat(),
                updated_at=directory.updated_at.isoformat()
            ).model_dump(),
            message="创建成功"
        )
    except ValueError as e:
        logger.error(f"创建存储目录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                error_code="INVALID_REQUEST",
                error_message=str(e)
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"创建存储目录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"创建存储目录时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/directories", response_model=dict)
async def list_directories(
    enabled: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取存储目录列表
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [StorageDirectoryResponse, ...],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = StorageMonitorService(db)
        directories = await service.list_directories(enabled)
        
        return success_response(
            data=[StorageDirectoryResponse(
                id=d.id,
                name=d.name,
                path=d.path,
                enabled=d.enabled,
                alert_threshold=d.alert_threshold,
                description=d.description,
                created_at=d.created_at.isoformat(),
                updated_at=d.updated_at.isoformat()
            ).model_dump() for d in directories],
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取存储目录列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取存储目录列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/directories/{directory_id}", response_model=dict)
async def get_directory(
    directory_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取存储目录详情
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": StorageDirectoryResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = StorageMonitorService(db)
        directory = await service.get_directory(directory_id)
        
        if not directory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message=f"存储目录不存在 (ID: {directory_id})"
                ).model_dump()
            )
        
        return success_response(
            data=StorageDirectoryResponse(
                id=directory.id,
                name=directory.name,
                path=directory.path,
                enabled=directory.enabled,
                alert_threshold=directory.alert_threshold,
                description=directory.description,
                created_at=directory.created_at.isoformat(),
                updated_at=directory.updated_at.isoformat()
            ).model_dump(),
            message="获取成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取存储目录详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取存储目录详情时发生错误: {str(e)}"
            ).model_dump()
        )


@router.put("/directories/{directory_id}", response_model=dict)
async def update_directory(
    directory_id: int,
    directory_data: StorageDirectoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    更新存储目录配置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "更新成功",
        "data": StorageDirectoryResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = StorageMonitorService(db)
        directory = await service.update_directory(
            directory_id,
            name=directory_data.name,
            enabled=directory_data.enabled,
            alert_threshold=directory_data.alert_threshold,
            description=directory_data.description
        )
        
        if not directory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message=f"存储目录不存在 (ID: {directory_id})"
                ).model_dump()
            )
        
        await db.commit()
        
        return success_response(
            data=StorageDirectoryResponse(
                id=directory.id,
                name=directory.name,
                path=directory.path,
                enabled=directory.enabled,
                alert_threshold=directory.alert_threshold,
                description=directory.description,
                created_at=directory.created_at.isoformat(),
                updated_at=directory.updated_at.isoformat()
            ).model_dump(),
            message="更新成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新存储目录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新存储目录时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/directories/{directory_id}", response_model=dict)
async def delete_directory(
    directory_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    删除存储目录配置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "删除成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = StorageMonitorService(db)
        success = await service.delete_directory(directory_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message=f"存储目录不存在 (ID: {directory_id})"
                ).model_dump()
            )
        
        await db.commit()
        
        return success_response(data=None, message="删除成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除存储目录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除存储目录时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/directories/{directory_id}/usage", response_model=dict)
async def get_directory_usage(
    directory_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取存储目录使用情况
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": StorageUsageResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = StorageMonitorService(db)
        directory = await service.get_directory(directory_id)
        
        if not directory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message=f"存储目录不存在 (ID: {directory_id})"
                ).model_dump()
            )
        
        usage = await service.get_directory_usage(directory.path)
        if not usage:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_response(
                    error_code="INTERNAL_SERVER_ERROR",
                    error_message="无法获取目录使用情况"
                ).model_dump()
            )
        
        return success_response(
            data=StorageUsageResponse(
                directory_id=directory.id,
                name=directory.name,
                path=directory.path,
                enabled=directory.enabled,
                alert_threshold=directory.alert_threshold,
                **usage
            ).model_dump(),
            message="获取成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取存储目录使用情况失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取存储目录使用情况时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/directories/{directory_id}/trends", response_model=dict)
async def get_directory_trends(
    directory_id: int,
    days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """
    获取存储目录使用趋势
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": StorageTrendsResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = StorageMonitorService(db)
        directory = await service.get_directory(directory_id)
        
        if not directory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message=f"存储目录不存在 (ID: {directory_id})"
                ).model_dump()
            )
        
        trends = await service.get_usage_trends(directory_id=directory_id, days=days)
        
        return success_response(
            data=trends,
            message="获取成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取存储目录使用趋势失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取存储目录使用趋势时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/usage", response_model=dict)
async def get_all_directories_usage(
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有目录的使用情况
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [StorageUsageResponse, ...],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = StorageMonitorService(db)
        usage_list = await service.get_all_directories_usage()
        
        return success_response(
            data=usage_list,
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取所有目录使用情况失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取所有目录使用情况时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/alerts", response_model=dict)
async def get_alerts(
    directory_id: Optional[int] = None,
    resolved: Optional[bool] = None,
    alert_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取存储预警列表
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [StorageAlertResponse, ...],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = StorageMonitorService(db)
        alerts = await service.get_alerts(
            directory_id=directory_id,
            resolved=resolved,
            alert_type=alert_type
        )
        
        return success_response(
            data=[StorageAlertResponse(
                id=a.id,
                directory_id=a.directory_id,
                path=a.path,
                alert_type=a.alert_type,
                usage_percent=a.usage_percent,
                threshold=a.threshold,
                message=a.message,
                resolved=a.resolved,
                resolved_at=a.resolved_at.isoformat() if a.resolved_at else None,
                created_at=a.created_at.isoformat()
            ).model_dump() for a in alerts],
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取存储预警列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取存储预警列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/alerts/{alert_id}/resolve", response_model=dict)
async def resolve_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    解决存储预警
    
    返回统一响应格式：
    {
        "success": true,
        "message": "解决成功",
        "data": StorageAlertResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = StorageMonitorService(db)
        alert = await service.resolve_alert(alert_id)
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message=f"存储预警不存在 (ID: {alert_id})"
                ).model_dump()
            )
        
        await db.commit()
        
        return success_response(
            data=StorageAlertResponse(
                id=alert.id,
                directory_id=alert.directory_id,
                path=alert.path,
                alert_type=alert.alert_type,
                usage_percent=alert.usage_percent,
                threshold=alert.threshold,
                message=alert.message,
                resolved=alert.resolved,
                resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None,
                created_at=alert.created_at.isoformat()
            ).model_dump(),
            message="解决成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解决存储预警失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"解决存储预警时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/statistics", response_model=dict)
async def get_statistics(
    db: AsyncSession = Depends(get_db)
):
    """
    获取存储监控统计信息
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": StorageStatisticsResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = StorageMonitorService(db)
        stats = await service.get_statistics()
        
        return success_response(
            data=stats,
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取存储监控统计信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取存储监控统计信息时发生错误: {str(e)}"
            ).model_dump()
        )

