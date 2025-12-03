"""
云存储API（Chain模式版本）
这是使用Chain模式的示例实现
可以作为现有API的替代方案
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from loguru import logger

from app.chain.storage import StorageChain

router = APIRouter()


# 请求模型（复用现有的）
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


@router.get("", response_model=List[CloudStorageResponse])
async def list_storages(provider: Optional[str] = None):
    """列出云存储配置（Chain模式）"""
    try:
        chain = StorageChain()
        storages = await chain.list_storages(provider)
        return [CloudStorageResponse(**storage) for storage in storages]
    except Exception as e:
        logger.error(f"列出云存储配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出失败: {str(e)}"
        )


@router.get("/{storage_id}", response_model=CloudStorageResponse)
async def get_storage(storage_id: int):
    """获取云存储配置（Chain模式）"""
    try:
        chain = StorageChain()
        storage = await chain.get_storage(storage_id)
        
        if not storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="云存储配置不存在"
            )
        
        return CloudStorageResponse(**storage)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取云存储配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )


@router.get("/{storage_id}/files", response_model=FileListResponse)
async def list_files(
    storage_id: int,
    path: str = "/",
    recursive: bool = False
):
    """列出文件（Chain模式）"""
    try:
        chain = StorageChain()
        files = await chain.list_files(storage_id, path, recursive)
        
        return FileListResponse(
            files=files,
            total=len(files)
        )
    except Exception as e:
        logger.error(f"列出文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出文件失败: {str(e)}"
        )


@router.get("/{storage_id}/usage", response_model=StorageUsageResponse)
async def get_storage_usage(storage_id: int):
    """获取存储使用情况（Chain模式）"""
    try:
        chain = StorageChain()
        usage = await chain.get_storage_usage(storage_id)
        
        if not usage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="无法获取存储使用情况"
            )
        
        return StorageUsageResponse(**usage)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取存储使用情况失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )


@router.post("/{storage_id}/qr-code", response_model=QRCodeResponse)
async def generate_qr_code(storage_id: int):
    """生成二维码（115网盘，Chain模式）"""
    try:
        chain = StorageChain()
        qr_content, qr_url, error = await chain.generate_qr_code(storage_id)
        
        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        return QRCodeResponse(
            qr_content=qr_content,
            qr_url=qr_url,
            message="二维码生成成功，请使用115网盘App扫描"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成二维码失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成失败: {str(e)}"
        )


@router.get("/{storage_id}/qr-status", response_model=QRStatusResponse)
async def check_qr_status(storage_id: int):
    """检查二维码登录状态（115网盘，Chain模式）"""
    try:
        chain = StorageChain()
        status_code, message, token_data = await chain.check_qr_status(storage_id)
        
        if status_code is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message or "检查状态失败"
            )
        
        return QRStatusResponse(
            status=status_code,
            message=message or "",
            token_data=token_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检查二维码状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查失败: {str(e)}"
        )

