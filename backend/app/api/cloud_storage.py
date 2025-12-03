"""
云存储API
使用统一响应模型
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db
from app.modules.cloud_storage.service import CloudStorageService
from app.models.cloud_storage import CloudStorage
from app.core.schemas import (
    BaseResponse,
    PaginatedResponse,
    NotFoundResponse,
    success_response,
    error_response
)


router = APIRouter()


# 请求模型
class CloudStorageCreate(BaseModel):
    """创建云存储配置请求"""
    name: str
    provider: str  # 115, rclone, openlist
    enabled: bool = True
    rclone_remote_name: Optional[str] = None
    rclone_config_path: Optional[str] = None
    openlist_server_url: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class CloudStorageUpdate(BaseModel):
    """更新云存储配置请求"""
    name: Optional[str] = None
    enabled: Optional[bool] = None
    rclone_remote_name: Optional[str] = None
    rclone_config_path: Optional[str] = None
    openlist_server_url: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


# 响应模型
class CloudStorageResponse(BaseModel):
    """云存储配置响应"""
    id: int
    name: str
    provider: str
    enabled: bool
    app_id: Optional[str] = None
    rclone_remote_name: Optional[str] = None
    rclone_config_path: Optional[str] = None
    openlist_server_url: Optional[str] = None
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class QRCodeResponse(BaseModel):
    """二维码响应"""
    qr_content: str
    qr_url: str
    message: str


class QRStatusResponse(BaseModel):
    """二维码状态响应"""
    status: int  # 0=未扫码, 1=已扫码, 2=已确认, -1=已过期/失败
    message: str
    token_data: Optional[Dict[str, Any]] = None


class FileListResponse(BaseModel):
    """文件列表响应"""
    files: List[Dict[str, Any]]
    total: int


class StorageUsageResponse(BaseModel):
    """存储使用情况响应"""
    total: int
    used: int
    available: int
    percentage: float


@router.post("", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_storage(
    storage_data: CloudStorageCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建云存储配置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "创建成功",
        "data": CloudStorageResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = CloudStorageService(db)
        storage = await service.create_storage(storage_data.dict())
        
        if not storage:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="CREATE_FAILED",
                    error_message="创建云存储配置失败"
                ).model_dump()
            )
        
        storage_response = CloudStorageResponse(
            id=storage.id,
            name=storage.name,
            provider=storage.provider,
            enabled=storage.enabled,
            app_id=storage.app_id,
            rclone_remote_name=storage.rclone_remote_name,
            rclone_config_path=storage.rclone_config_path,
            openlist_server_url=storage.openlist_server_url,
            user_id=storage.user_id,
            user_name=storage.user_name,
            config=storage.config,
            created_at=storage.created_at.isoformat(),
            updated_at=storage.updated_at.isoformat()
        )
        
        return success_response(data=storage_response.model_dump(), message="创建成功")
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(
                error_code="VALIDATION_ERROR",
                error_message=str(e)
            ).model_dump()
        )
    except Exception as e:
        logger.error(f"创建云存储配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"创建云存储配置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("", response_model=BaseResponse)
async def list_storages(
    provider: Optional[str] = Query(None, description="提供商过滤: 115, rclone, openlist"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    列出云存储配置（支持分页）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "items": [CloudStorageResponse, ...],
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = CloudStorageService(db)
        storages = await service.list_storages(provider)
        
        storage_responses = [CloudStorageResponse(
            id=storage.id,
            name=storage.name,
            provider=storage.provider,
            enabled=storage.enabled,
            app_id=storage.app_id,
            rclone_remote_name=storage.rclone_remote_name,
            rclone_config_path=storage.rclone_config_path,
            openlist_server_url=storage.openlist_server_url,
            user_id=storage.user_id,
            user_name=storage.user_name,
            config=storage.config,
            created_at=storage.created_at.isoformat(),
            updated_at=storage.updated_at.isoformat()
        ).model_dump() for storage in storages]
        
        # 计算分页
        total = len(storage_responses)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_items = storage_responses[start:end]
        
        # 使用PaginatedResponse
        paginated_data = PaginatedResponse.create(
            items=paginated_items,
            total=total,
            page=page,
            page_size=page_size
        )
        
        return success_response(data=paginated_data.model_dump(), message="获取成功")
    except Exception as e:
        logger.error(f"列出云存储配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"列出云存储配置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/{storage_id}", response_model=BaseResponse)
async def get_storage(
    storage_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取云存储配置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": CloudStorageResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = CloudStorageService(db)
        storage = await service.get_storage(storage_id)
        
        if not storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"云存储配置不存在 (ID: {storage_id})"
                ).model_dump()
            )
        
        storage_response = CloudStorageResponse(
            id=storage.id,
            name=storage.name,
            provider=storage.provider,
            enabled=storage.enabled,
            app_id=storage.app_id,
            rclone_remote_name=storage.rclone_remote_name,
            rclone_config_path=storage.rclone_config_path,
            openlist_server_url=storage.openlist_server_url,
            user_id=storage.user_id,
            user_name=storage.user_name,
            config=storage.config,
            created_at=storage.created_at.isoformat(),
            updated_at=storage.updated_at.isoformat()
        )
        
        return success_response(data=storage_response.model_dump(), message="获取成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取云存储配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取云存储配置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.put("/{storage_id}", response_model=BaseResponse)
async def update_storage(
    storage_id: int,
    storage_data: CloudStorageUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    更新云存储配置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "更新成功",
        "data": CloudStorageResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = CloudStorageService(db)
        storage = await service.update_storage(storage_id, storage_data.dict(exclude_unset=True))
        
        if not storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"云存储配置不存在 (ID: {storage_id})"
                ).model_dump()
            )
        
        storage_response = CloudStorageResponse(
            id=storage.id,
            name=storage.name,
            provider=storage.provider,
            enabled=storage.enabled,
            app_id=storage.app_id,
            rclone_remote_name=storage.rclone_remote_name,
            rclone_config_path=storage.rclone_config_path,
            openlist_server_url=storage.openlist_server_url,
            user_id=storage.user_id,
            user_name=storage.user_name,
            config=storage.config,
            created_at=storage.created_at.isoformat(),
            updated_at=storage.updated_at.isoformat()
        )
        
        return success_response(data=storage_response.model_dump(), message="更新成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新云存储配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新云存储配置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/{storage_id}", response_model=BaseResponse)
async def delete_storage(
    storage_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    删除云存储配置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "删除成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = CloudStorageService(db)
        success = await service.delete_storage(storage_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"云存储配置不存在 (ID: {storage_id})"
                ).model_dump()
            )
        
        return success_response(message="删除成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除云存储配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除云存储配置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/{storage_id}/qr-code", response_model=BaseResponse)
async def generate_qr_code(
    storage_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    生成二维码（115网盘）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "二维码生成成功，请使用115网盘App扫描",
        "data": {
            "qr_content": "...",
            "qr_url": "..."
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = CloudStorageService(db)
        qr_content, qr_url, error = await service.generate_qr_code(storage_id)
        
        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="QR_GENERATE_FAILED",
                    error_message=error
                ).model_dump()
            )
        
        return success_response(
            data={
                "qr_content": qr_content,
                "qr_url": qr_url
            },
            message="二维码生成成功，请使用115网盘App扫描"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成二维码失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"生成二维码时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/{storage_id}/qr-status", response_model=BaseResponse)
async def check_qr_status(
    storage_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    检查二维码登录状态（115网盘）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "状态消息",
        "data": {
            "status": 0,  // 0=未扫码, 1=已扫码, 2=已确认, -1=已过期/失败
            "token_data": {...}
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = CloudStorageService(db)
        status_code, message, token_data = await service.check_qr_status(storage_id)
        
        if status_code is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="QR_STATUS_CHECK_FAILED",
                    error_message=message or "检查状态失败"
                ).model_dump()
            )
        
        return success_response(
            data={
                "status": status_code,
                "token_data": token_data
            },
            message=message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检查二维码状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"检查二维码状态时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/{storage_id}/files", response_model=BaseResponse)
async def list_files(
    storage_id: int,
    path: str = Query("/", description="文件路径"),
    recursive: bool = Query(False, description="是否递归列出"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    列出文件（支持分页）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "items": [FileInfo, ...],
            "total": 100,
            "page": 1,
            "page_size": 50,
            "total_pages": 2
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = CloudStorageService(db)
        files = await service.list_files(storage_id, path, recursive)
        
        # 计算分页
        total = len(files)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_items = files[start:end]
        
        # 使用PaginatedResponse
        paginated_data = PaginatedResponse.create(
            items=paginated_items,
            total=total,
            page=page,
            page_size=page_size
        )
        
        return success_response(data=paginated_data.model_dump(), message="获取成功")
    except Exception as e:
        logger.error(f"列出文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"列出文件时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/{storage_id}/usage", response_model=BaseResponse)
async def get_storage_usage(
    storage_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取存储使用情况
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": StorageUsageResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = CloudStorageService(db)
        usage = await service.get_storage_usage(storage_id)
        
        if not usage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message="无法获取存储使用情况"
                ).model_dump()
            )
        
        return success_response(data=StorageUsageResponse(**usage).model_dump(), message="获取成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取存储使用情况失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取存储使用情况时发生错误: {str(e)}"
            ).model_dump()
        )

