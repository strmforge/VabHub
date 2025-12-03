"""
备份系统API
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from loguru import logger

from app.core.database import get_db
from app.core.schemas import BaseResponse, success_response, error_response
from app.modules.backup.service import BackupService, BackupConfig
from app.models.backup import BackupRecord
from app.core.config import settings

router = APIRouter(prefix="/backup", tags=["备份"])


# 请求/响应模型
class BackupCreateRequest(BaseModel):
    """创建备份请求"""
    backup_name: Optional[str] = None
    compression_enabled: bool = True
    verify_backup: bool = True


class BackupRecordResponse(BaseModel):
    """备份记录响应"""
    id: int
    backup_id: str
    backup_path: str
    created_at: str
    database_version: str
    file_size: int
    checksum: str
    compressed: bool
    encrypted: bool
    tables_count: dict
    status: str
    error_message: Optional[str] = None
    metadata: Optional[dict] = None
    
    class Config:
        from_attributes = True


class BackupListResponse(BaseModel):
    """备份列表响应"""
    backups: List[BackupRecordResponse]
    total: int


class BackupStatusResponse(BaseModel):
    """备份状态响应"""
    auto_backup_enabled: bool
    backup_running: bool
    total_backups: int
    successful_backups: int
    failed_backups: int
    total_size_bytes: int
    total_size_mb: float
    latest_backup: Optional[dict] = None
    backup_directory: str
    max_backups: int


class BackupRestoreRequest(BaseModel):
    """恢复备份请求"""
    backup_id: str
    confirm: bool = False


@router.post("/create", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_backup(
    request: BackupCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """创建备份"""
    try:
        config = BackupConfig(
            backup_dir=settings.BACKUP_DIR,
            compression_enabled=request.compression_enabled,
            verify_backup=request.verify_backup
        )
        
        backup_service = BackupService(db, config)
        
        # 在后台任务中创建备份
        backup_record = await backup_service.create_backup(request.backup_name)
        
        if not backup_record:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_response(
                    error_code="BACKUP_FAILED",
                    error_message="备份创建失败"
                ).model_dump()
            )
        
        return success_response(
            data=BackupRecordResponse.model_validate(backup_record).model_dump(),
            message="备份创建成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建备份失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"创建备份时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/list", response_model=BaseResponse)
async def list_backups(
    limit: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """列出所有备份"""
    try:
        config = BackupConfig(
            backup_dir=settings.BACKUP_DIR
        )
        backup_service = BackupService(db, config)
        
        backups = await backup_service.list_backups(limit)
        
        backup_responses = [
            BackupRecordResponse.model_validate(backup).model_dump()
            for backup in backups
        ]
        
        return success_response(
            data={
                "backups": backup_responses,
                "total": len(backup_responses)
            },
            message="获取备份列表成功"
        )
        
    except Exception as e:
        logger.error(f"获取备份列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取备份列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/{backup_id}", response_model=BaseResponse)
async def get_backup(
    backup_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取指定备份"""
    try:
        config = BackupConfig(
            backup_dir=settings.BACKUP_DIR
        )
        backup_service = BackupService(db, config)
        
        backup = await backup_service.get_backup(backup_id)
        
        if not backup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="BACKUP_NOT_FOUND",
                    error_message=f"备份不存在: {backup_id}"
                ).model_dump()
            )
        
        return success_response(
            data=BackupRecordResponse.model_validate(backup).model_dump(),
            message="获取备份详情成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取备份详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取备份详情时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/{backup_id}", response_model=BaseResponse)
async def delete_backup(
    backup_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除备份"""
    try:
        config = BackupConfig(
            backup_dir=settings.BACKUP_DIR
        )
        backup_service = BackupService(db, config)
        
        success = await backup_service.delete_backup(backup_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="BACKUP_NOT_FOUND",
                    error_message=f"备份不存在: {backup_id}"
                ).model_dump()
            )
        
        return success_response(
            data=None,
            message="备份删除成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除备份失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除备份时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/restore", response_model=BaseResponse)
async def restore_backup(
    request: BackupRestoreRequest,
    db: AsyncSession = Depends(get_db)
):
    """恢复备份"""
    try:
        if not request.confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="CONFIRMATION_REQUIRED",
                    error_message="恢复操作需要明确确认（confirm=true）"
                ).model_dump()
            )
        
        config = BackupConfig(
            backup_dir=settings.BACKUP_DIR
        )
        backup_service = BackupService(db, config)
        
        success = await backup_service.restore_backup(request.backup_id, confirm=True)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_response(
                    error_code="RESTORE_FAILED",
                    error_message="备份恢复失败"
                ).model_dump()
            )
        
        return success_response(
            data=None,
            message="备份恢复成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复备份失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"恢复备份时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/status", response_model=BaseResponse)
async def get_backup_status(
    db: AsyncSession = Depends(get_db)
):
    """获取备份系统状态"""
    try:
        config = BackupConfig(
            backup_dir=settings.BACKUP_DIR,
            auto_backup_enabled=settings.AUTO_BACKUP_ENABLED,
            max_backups=settings.MAX_BACKUPS
        )
        backup_service = BackupService(db, config)
        
        status_data = await backup_service.get_backup_status()
        
        return success_response(
            data=status_data,
            message="获取备份状态成功"
        )
        
    except Exception as e:
        logger.error(f"获取备份状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取备份状态时发生错误: {str(e)}"
            ).model_dump()
        )


# ============== LAUNCH-1 L4 新增 API ==============

@router.get("/export/config", response_model=BaseResponse)
async def export_config(
    db: AsyncSession = Depends(get_db)
):
    """
    导出配置 (L4-1)
    
    返回全局配置（敏感字段用 *** 替代）、外部源配置等
    """
    try:
        from app.core.config_schema import get_effective_config
        from sqlalchemy import select
        from app.models.manga_source import MangaSource
        from app.models.music_chart_source import MusicChartSource
        
        # 获取全局配置
        global_config = get_effective_config(mask_sensitive=True)
        
        # 获取漫画源配置
        manga_sources = []
        try:
            result = await db.execute(select(MangaSource))
            for src in result.scalars().all():
                manga_sources.append({
                    "id": src.id,
                    "name": src.name,
                    "source_type": src.source_type if hasattr(src, 'source_type') else None,
                    "base_url": src.base_url if hasattr(src, 'base_url') else None,
                    "is_enabled": src.is_enabled,
                })
        except Exception as e:
            logger.warning(f"导出漫画源配置失败: {e}")
        
        # 获取音乐榜单源配置
        music_chart_sources = []
        try:
            result = await db.execute(select(MusicChartSource))
            for src in result.scalars().all():
                music_chart_sources.append({
                    "id": src.id,
                    "name": src.name,
                    "platform": src.platform if hasattr(src, 'platform') else None,
                    "is_enabled": src.is_enabled,
                })
        except Exception as e:
            logger.warning(f"导出音乐榜单源配置失败: {e}")
        
        export_data = {
            "export_time": datetime.utcnow().isoformat(),
            "global_config": global_config,
            "manga_sources": manga_sources,
            "music_chart_sources": music_chart_sources,
        }
        
        return success_response(
            data=export_data,
            message="配置导出成功"
        )
        
    except Exception as e:
        logger.error(f"导出配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="EXPORT_FAILED",
                error_message=f"导出配置失败: {str(e)}"
            ).model_dump()
        )


@router.get("/export/user_data", response_model=BaseResponse)
async def export_user_data(
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    导出用户数据 (L4-2)
    
    导出阅读进度、收藏、追更设置等
    可选 user_id 参数，不传则导出全部用户
    """
    try:
        from sqlalchemy import select
        from app.models.user import User
        
        user_data_list = []
        
        # 获取用户列表
        if user_id:
            result = await db.execute(select(User).where(User.id == user_id))
            users = [result.scalar_one_or_none()]
            users = [u for u in users if u]
        else:
            result = await db.execute(select(User))
            users = result.scalars().all()
        
        for user in users:
            user_export = {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role if hasattr(user, 'role') else "user",
                "reading_progress": [],
                "favorites": [],
                "follows": [],
            }
            
            # 获取阅读进度（尝试多个表）
            try:
                from app.models.ebook_reading_progress import EBookReadingProgress
                result = await db.execute(
                    select(EBookReadingProgress).where(EBookReadingProgress.user_id == user.id)
                )
                for p in result.scalars().all():
                    user_export["reading_progress"].append({
                        "type": "ebook",
                        "item_id": p.ebook_id,
                        "chapter_index": p.chapter_index if hasattr(p, 'chapter_index') else None,
                        "progress_percent": p.progress_percent if hasattr(p, 'progress_percent') else None,
                        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
                    })
            except Exception as e:
                logger.debug(f"获取电子书阅读进度失败: {e}")
            
            try:
                from app.models.manga_reading_progress import MangaReadingProgress
                result = await db.execute(
                    select(MangaReadingProgress).where(MangaReadingProgress.user_id == user.id)
                )
                for p in result.scalars().all():
                    user_export["reading_progress"].append({
                        "type": "manga",
                        "series_id": p.series_id if hasattr(p, 'series_id') else None,
                        "chapter_id": p.chapter_id if hasattr(p, 'chapter_id') else None,
                        "page_number": p.page_number if hasattr(p, 'page_number') else None,
                        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
                    })
            except Exception as e:
                logger.debug(f"获取漫画阅读进度失败: {e}")
            
            # 获取追更设置
            try:
                from app.models.user_manga_follow import UserMangaFollow
                result = await db.execute(
                    select(UserMangaFollow).where(UserMangaFollow.user_id == user.id)
                )
                for f in result.scalars().all():
                    user_export["follows"].append({
                        "type": "manga",
                        "series_id": f.series_id if hasattr(f, 'series_id') else None,
                        "source_id": f.source_id if hasattr(f, 'source_id') else None,
                        "created_at": f.created_at.isoformat() if f.created_at else None,
                    })
            except Exception as e:
                logger.debug(f"获取漫画追更失败: {e}")
            
            user_data_list.append(user_export)
        
        export_data = {
            "export_time": datetime.utcnow().isoformat(),
            "users": user_data_list,
        }
        
        return success_response(
            data=export_data,
            message="用户数据导出成功"
        )
        
    except Exception as e:
        logger.error(f"导出用户数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="EXPORT_FAILED",
                error_message=f"导出用户数据失败: {str(e)}"
            ).model_dump()
        )
