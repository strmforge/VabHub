"""
目录配置API端点
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from loguru import logger

from app.core.database import get_db
from app.core.schemas import BaseResponse, success_response, error_response
from app.models.directory import Directory
from app.models.enums.media_type import MediaType
from app.schemas.directory import DirectoryConfig

router = APIRouter(tags=["目录配置"])


def normalize_strm_capability(directory: Directory) -> None:
    """
    规范化 STRM 能力：如果媒体类型不支持 STRM，强制禁用
    
    Args:
        directory: 目录配置对象
    """
    if directory.media_type:
        try:
            media_type = MediaType(directory.media_type)
            if not media_type.supports_strm:
                directory.enable_strm = False
        except ValueError:
            # 如果 media_type 不是有效的枚举值，保持原样
            pass


@router.get("", response_model=BaseResponse)
async def get_directories(
    monitor_type: Optional[str] = None,
    enabled: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有目录配置
    
    Args:
        monitor_type: 监控类型过滤（downloader/directory/null）
        enabled: 是否启用过滤
        db: 数据库会话
    
    Returns:
        目录配置列表
    """
    try:
        query = select(Directory)
        
        if monitor_type is not None:
            query = query.where(Directory.monitor_type == monitor_type)
        
        if enabled is not None:
            query = query.where(Directory.enabled == enabled)
        
        query = query.order_by(Directory.priority)
        
        result = await db.execute(query)
        directories = result.scalars().all()
        
        return success_response(
            data=[
                {
                    "id": dir.id,
                    "download_path": dir.download_path,
                    "library_path": dir.library_path,
                    "storage": dir.storage,
                    "library_storage": dir.library_storage,
                    "monitor_type": dir.monitor_type,
                    "transfer_type": dir.transfer_type,
                    "media_type": dir.media_type,
                    "media_category": dir.media_category,
                    "priority": dir.priority,
                    "enabled": dir.enabled,
                    "enable_strm": dir.enable_strm if dir.enable_strm is not None else False,
                    "created_at": dir.created_at,
                    "updated_at": dir.updated_at
                }
                for dir in directories
            ],
            message="获取目录配置成功"
        )
    except Exception as e:
        logger.error(f"获取目录配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取目录配置失败: {str(e)}"
            ).model_dump()
        )


@router.get("/{directory_id}", response_model=BaseResponse)
async def get_directory(
    directory_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取单个目录配置
    
    Args:
        directory_id: 目录ID
        db: 数据库会话
    
    Returns:
        目录配置
    """
    try:
        result = await db.execute(
            select(Directory).where(Directory.id == directory_id)
        )
        directory = result.scalar_one_or_none()
        
        if not directory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message="目录配置不存在"
                ).model_dump()
            )
        
        return success_response(
            data={
                "id": directory.id,
                "download_path": directory.download_path,
                "library_path": directory.library_path,
                "storage": directory.storage,
                "library_storage": directory.library_storage,
                "monitor_type": directory.monitor_type,
                "transfer_type": directory.transfer_type,
                "media_type": directory.media_type,
                "media_category": directory.media_category,
                "priority": directory.priority,
                "enabled": directory.enabled,
                "created_at": directory.created_at,
                "updated_at": directory.updated_at
            },
            message="获取目录配置成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取目录配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取目录配置失败: {str(e)}"
            ).model_dump()
        )


@router.post("", response_model=BaseResponse)
async def create_directory(
    directory_config: DirectoryConfig,
    db: AsyncSession = Depends(get_db)
):
    """
    创建目录配置
    
    Args:
        directory_config: 目录配置
        db: 数据库会话
    
    Returns:
        创建的目录配置
    """
    try:
        new_directory = Directory(
            download_path=directory_config.download_path,
            library_path=directory_config.library_path,
            storage=directory_config.storage,
            library_storage=directory_config.library_storage,
            monitor_type=directory_config.monitor_type,
            transfer_type=directory_config.transfer_type,
            media_type=directory_config.media_type,
            media_category=directory_config.media_category,
            priority=directory_config.priority,
            enabled=directory_config.enabled,
            enable_strm=directory_config.enable_strm,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # 规范化 STRM 能力
        normalize_strm_capability(new_directory)
        
        db.add(new_directory)
        await db.commit()
        await db.refresh(new_directory)
        
        logger.info(f"创建目录配置成功: {new_directory.id}")
        
        return success_response(
            data={
                "id": new_directory.id,
                "download_path": new_directory.download_path,
                "library_path": new_directory.library_path,
                "storage": new_directory.storage,
                "library_storage": new_directory.library_storage,
                "monitor_type": new_directory.monitor_type,
                "transfer_type": new_directory.transfer_type,
                "media_type": new_directory.media_type,
                "media_category": new_directory.media_category,
                "priority": new_directory.priority,
                "enabled": new_directory.enabled,
                "created_at": new_directory.created_at,
                "updated_at": new_directory.updated_at
            },
            message="创建目录配置成功"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"创建目录配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"创建目录配置失败: {str(e)}"
            ).model_dump()
        )


@router.put("/{directory_id}", response_model=BaseResponse)
async def update_directory(
    directory_id: int,
    directory_config: DirectoryConfig,
    db: AsyncSession = Depends(get_db)
):
    """
    更新目录配置
    
    Args:
        directory_id: 目录ID
        directory_config: 目录配置
        db: 数据库会话
    
    Returns:
        更新的目录配置
    """
    try:
        result = await db.execute(
            select(Directory).where(Directory.id == directory_id)
        )
        directory = result.scalar_one_or_none()
        
        if not directory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message="目录配置不存在"
                ).model_dump()
            )
        
        # 更新字段
        directory.download_path = directory_config.download_path
        directory.library_path = directory_config.library_path
        directory.storage = directory_config.storage
        directory.library_storage = directory_config.library_storage
        directory.monitor_type = directory_config.monitor_type
        directory.transfer_type = directory_config.transfer_type
        directory.media_type = directory_config.media_type
        directory.media_category = directory_config.media_category
        directory.priority = directory_config.priority
        directory.enabled = directory_config.enabled
        directory.enable_strm = directory_config.enable_strm
        directory.updated_at = datetime.now().isoformat()
        
        # 规范化 STRM 能力
        normalize_strm_capability(directory)
        
        await db.commit()
        await db.refresh(directory)
        
        logger.info(f"更新目录配置成功: {directory_id}")
        
        return success_response(
            data={
                "id": directory.id,
                "download_path": directory.download_path,
                "library_path": directory.library_path,
                "storage": directory.storage,
                "library_storage": directory.library_storage,
                "monitor_type": directory.monitor_type,
                "transfer_type": directory.transfer_type,
                "media_type": directory.media_type,
                "media_category": directory.media_category,
                "priority": directory.priority,
                "enabled": directory.enabled,
                "created_at": directory.created_at,
                "updated_at": directory.updated_at
            },
            message="更新目录配置成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"更新目录配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新目录配置失败: {str(e)}"
            ).model_dump()
        )


@router.delete("/{directory_id}", response_model=BaseResponse)
async def delete_directory(
    directory_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    删除目录配置
    
    Args:
        directory_id: 目录ID
        db: 数据库会话
    
    Returns:
        删除结果
    """
    try:
        result = await db.execute(
            select(Directory).where(Directory.id == directory_id)
        )
        directory = result.scalar_one_or_none()
        
        if not directory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message="目录配置不存在"
                ).model_dump()
            )
        
        await db.delete(directory)
        await db.commit()
        
        logger.info(f"删除目录配置成功: {directory_id}")
        
        return success_response(
            data={"id": directory_id},
            message="删除目录配置成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"删除目录配置失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除目录配置失败: {str(e)}"
            ).model_dump()
        )

