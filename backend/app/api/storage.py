"""
本地存储API
用于列出本地目录和文件，支持路径选择功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel
from pathlib import Path
import os
from loguru import logger

from app.core.database import get_db
from app.core.schemas import success_response, error_response, BaseResponse
from app.modules.settings.service import SettingsService
from app.modules.storage_monitor.service import StorageMonitorService
from app.modules.cloud_storage.service import CloudStorageService
from fastapi import status
from fastapi.responses import JSONResponse

router = APIRouter()


class ManualStorageOption(BaseModel):
    """手动整理存储选项"""
    key: str  # 存储标识符，如 "local", "115", "rclone", "openlist"
    label: str  # 显示名称，如 "本地", "115网盘"
    kind: str  # 存储类型，如 "local", "pan115", "rclone", "openlist"


class FileItem(BaseModel):
    """文件/目录项"""
    name: str
    path: str
    type: str  # 'dir' 或 'file'
    size: Optional[int] = None
    basename: str
    storage: str = 'local'


@router.post("/list", response_model=dict)
async def list_storage(
    path: str = Query('/', description="目录路径"),
    storage: str = Query('local', description="存储类型: local/115/123"),
    recursive: bool = Query(False, description="是否递归列出")
):
    """
    列出存储目录下的文件和文件夹
    
    用于路径选择器组件，支持：
    - 本地存储（local）：列出本地文件系统目录
    - 云存储（115/123）：通过云存储API列出（需要storage_id）
    
    Args:
        path: 目录路径
        storage: 存储类型（local/115/123）
        recursive: 是否递归列出
    
    Returns:
        文件列表
    """
    try:
        if storage == 'local':
            # 列出本地目录
            return await _list_local_directory(path, recursive)
        else:
            # 云存储需要通过云存储API
            # 这里暂时返回空列表，实际使用时需要传入storage_id
            logger.warning(f"云存储路径选择需要storage_id，当前storage={storage}")
            return success_response(data=[], message="云存储路径选择需要storage_id")
            
    except Exception as e:
        logger.error(f"列出存储目录失败: {e}")
        return error_response(message=f"列出目录失败: {str(e)}")


async def _list_local_directory(path: str, recursive: bool = False) -> dict:
    """
    列出本地目录
    
    Args:
        path: 目录路径
        recursive: 是否递归
    
    Returns:
        文件列表
    """
    try:
        path_obj = Path(path)
        
        # 验证路径是否存在
        if not path_obj.exists():
            return error_response(message=f"路径不存在: {path}")
        
        # 验证是否为目录
        if not path_obj.is_dir():
            return error_response(message=f"路径不是目录: {path}")
        
        files = []
        
        # 列出目录内容
        for item in path_obj.iterdir():
            try:
                # 跳过隐藏文件和系统文件
                if item.name.startswith('.'):
                    continue
                
                item_info = {
                    "name": item.name,
                    "path": str(item.absolute()),
                    "type": "dir" if item.is_dir() else "file",
                    "basename": item.name,
                    "storage": "local"
                }
                
                # 如果是文件，添加大小
                if item.is_file():
                    try:
                        item_info["size"] = item.stat().st_size
                    except (OSError, PermissionError):
                        item_info["size"] = 0
                
                files.append(item_info)
                
                # 如果递归且是目录，递归列出
                if recursive and item.is_dir():
                    sub_files = await _list_local_directory(str(item.absolute()), recursive=True)
                    if sub_files.get("success"):
                        files.extend(sub_files.get("data", []))
                        
            except (PermissionError, OSError) as e:
                logger.warning(f"无法访问文件/目录: {item}, {e}")
                continue
        
        # 排序：目录在前，然后按名称排序
        files.sort(key=lambda x: (x["type"] != "dir", x["name"].lower()))
        
        return success_response(data=files, message="获取成功")
        
    except Exception as e:
        logger.error(f"列出本地目录失败: {path}, {e}")
        return error_response(message=f"列出目录失败: {str(e)}")


@router.get("/validate", response_model=dict)
async def validate_path(
    path: str = Query(..., description="路径"),
    storage: str = Query('local', description="存储类型")
):
    """
    验证路径是否有效
    
    Args:
        path: 路径
        storage: 存储类型
    
    Returns:
        验证结果
    """
    try:
        if storage == 'local':
            path_obj = Path(path)
            exists = path_obj.exists()
            is_dir = path_obj.is_dir() if exists else False
            is_file = path_obj.is_file() if exists else False
            readable = os.access(path, os.R_OK) if exists else False
            writable = os.access(path, os.W_OK) if exists else False
            
            return success_response(data={
                "exists": exists,
                "is_dir": is_dir,
                "is_file": is_file,
                "readable": readable,
                "writable": writable,
                "path": str(path_obj.absolute())
            }, message="验证成功")
        else:
            return error_response(message="云存储路径验证需要storage_id")
            
    except Exception as e:
        logger.error(f"验证路径失败: {e}")
        return error_response(message=f"验证路径失败: {str(e)}")


@router.get("/status", response_model=BaseResponse)
async def get_storage_status(
    db: AsyncSession = Depends(get_db)
):
    """
    获取存储状态
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "total_size_gb": 1000.0,
            "used_size_gb": 500.0,
            "free_size_gb": 500.0,
            "usage_percent": 50.0,
            "directories": [...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = StorageMonitorService(db)
        # 获取所有目录的使用情况
        directories_usage = await service.get_all_directories_usage()
        
        # 计算总体统计
        total_size_gb = 0.0
        used_size_gb = 0.0
        free_size_gb = 0.0
        
        for dir_usage in directories_usage:
            total_size_gb += dir_usage.get("total_bytes", 0) / (1024 ** 3)
            used_size_gb += dir_usage.get("used_bytes", 0) / (1024 ** 3)
            free_size_gb += dir_usage.get("free_bytes", 0) / (1024 ** 3)
        
        usage_percent = (used_size_gb / total_size_gb * 100) if total_size_gb > 0 else 0.0
        
        status_data = {
            "total_size_gb": round(total_size_gb, 2),
            "used_size_gb": round(used_size_gb, 2),
            "free_size_gb": round(free_size_gb, 2),
            "usage_percent": round(usage_percent, 2),
            "directories": directories_usage
        }
        
        return success_response(data=status_data, message="获取存储状态成功")
    except Exception as e:
        logger.error(f"获取存储状态失败: {e}")
        return error_response(message=f"获取存储状态失败: {str(e)}")


@router.get("/config", response_model=BaseResponse)
async def get_storage_config(
    db: AsyncSession = Depends(get_db)
):
    """
    获取存储配置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "default_path": "/path/to/storage",
            "monitor_enabled": true,
            "alert_threshold": 80.0,
            ...
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        settings_service = SettingsService(db)
        config = {
            "default_path": await settings_service.get_setting("storage_default_path") or "",
            "monitor_enabled": await settings_service.get_setting("storage_monitor_enabled", category="storage") or True,
            "alert_threshold": float(await settings_service.get_setting("storage_alert_threshold", category="storage") or 80.0),
        }
        return success_response(data=config, message="获取存储配置成功")
    except Exception as e:
        logger.error(f"获取存储配置失败: {e}")
        return error_response(message=f"获取存储配置失败: {str(e)}")


@router.put("/config", response_model=BaseResponse)
async def update_storage_config(
    config: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    更新存储配置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "更新成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        settings_service = SettingsService(db)
        for key, value in config.items():
            await settings_service.set_setting(f"storage_{key}", value, category="storage")
        return success_response(message="更新存储配置成功")
    except Exception as e:
        logger.error(f"更新存储配置失败: {e}")
        return error_response(message=f"更新存储配置失败: {str(e)}")


@router.get("/manual-transfer-options", response_model=BaseResponse)
async def get_manual_transfer_storage_options(
    db: AsyncSession = Depends(get_db)
):
    """
    获取手动整理可用的存储选项
    
    返回系统中已启用且支持手动整理的存储选项。
    本地存储始终包含在内，其他存储基于云存储配置中的启用状态。
    
    返回格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [
            {"key": "local", "label": "本地", "kind": "local"},
            {"key": "115", "label": "115网盘", "kind": "pan115"},
            {"key": "rclone", "label": "RClone", "kind": "rclone"},
            {"key": "openlist", "label": "OpenList", "kind": "openlist"}
        ],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        # 构建存储选项列表
        storage_options = []
        
        # 1. 本地存储始终可用
        storage_options.append(ManualStorageOption(
            key="local",
            label="本地",
            kind="local"
        ))
        
        # 2. 获取已启用的云存储
        try:
            service = CloudStorageService(db)
            cloud_storages = await service.list_enabled_storages()
            
            # 存储类型映射
            provider_mapping = {
                "115": {"label": "115网盘", "kind": "pan115"},
                "rclone": {"label": "RClone", "kind": "rclone"},
                "openlist": {"label": "OpenList", "kind": "openlist"}
            }
            
            # 添加已启用的云存储
            for storage in cloud_storages:
                provider = storage.provider
                if provider in provider_mapping:
                    mapping = provider_mapping[provider]
                    storage_options.append(ManualStorageOption(
                        key=provider,
                        label=mapping["label"],
                        kind=mapping["kind"]
                    ))
                    
        except Exception as e:
            logger.warning(f"获取云存储配置失败，仅返回本地存储: {e}")
            # 即使云存储查询失败，也返回本地存储选项
        
        return success_response(
            data=[option.model_dump() for option in storage_options],
            message="获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取手动整理存储选项失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取存储选项时发生错误: {str(e)}"
            ).model_dump()
        )

