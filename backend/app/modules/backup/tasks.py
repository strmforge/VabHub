"""
备份系统定时任务
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import AsyncSessionLocal
from app.modules.backup.service import BackupService, BackupConfig
from app.core.config import settings


async def auto_backup_task():
    """自动备份任务"""
    try:
        logger.info("开始执行自动备份任务")
        
        config = BackupConfig(
            backup_dir=settings.BACKUP_DIR,
            max_backups=settings.MAX_BACKUPS,
            compression_enabled=settings.BACKUP_COMPRESSION_ENABLED,
            verify_backup=settings.BACKUP_VERIFY_ENABLED,
            auto_backup_enabled=settings.AUTO_BACKUP_ENABLED
        )
        
        async with AsyncSessionLocal() as db:
            backup_service = BackupService(db, config)
            backup_record = await backup_service.create_backup()
            
            if backup_record:
                logger.info(f"自动备份成功: {backup_record.backup_id}")
            else:
                logger.error("自动备份失败")
                
    except Exception as e:
        logger.error(f"自动备份任务执行失败: {e}")


def register_backup_tasks(scheduler):
    """注册备份任务到调度器"""
    if settings.AUTO_BACKUP_ENABLED:
        # 每天执行一次备份（可配置间隔）
        interval_hours = settings.AUTO_BACKUP_INTERVAL_HOURS
        
        scheduler.add_job(
            auto_backup_task,
            'interval',
            hours=interval_hours,
            id='auto_backup',
            name='自动备份',
            replace_existing=True
        )
        
        logger.info(f"已注册自动备份任务，间隔: {interval_hours} 小时")
    else:
        logger.info("自动备份已禁用")

