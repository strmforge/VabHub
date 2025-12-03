"""
存储监控定时任务
"""

from app.core.database import AsyncSessionLocal
from app.modules.storage_monitor.service import StorageMonitorService
from loguru import logger


async def record_storage_usage_task():
    """记录存储使用历史任务"""
    async with AsyncSessionLocal() as db:
        try:
            service = StorageMonitorService(db)
            directories = await service.list_directories(enabled=True)
            
            for directory in directories:
                try:
                    # 记录使用历史
                    await service.record_usage_history(directory.id, directory.path)
                    
                    # 检查并创建预警
                    alerts = await service.check_and_create_alerts(directory.id, directory.path)
                    if alerts:
                        logger.info(f"为目录 {directory.name} ({directory.path}) 创建了 {len(alerts)} 个预警")
                    
                    await db.commit()
                except Exception as e:
                    logger.error(f"记录目录 {directory.name} ({directory.path}) 使用历史失败: {e}")
                    await db.rollback()
            
            logger.info(f"存储使用历史记录完成，共处理 {len(directories)} 个目录")
        except Exception as e:
            logger.error(f"存储使用历史记录任务失败: {e}")


async def cleanup_old_usage_history_task(days: int = 30):
    """清理旧的存储使用历史记录"""
    from datetime import datetime, timedelta
    from sqlalchemy import delete
    from app.models.storage_monitor import StorageUsageHistory
    
    async with AsyncSessionLocal() as db:
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            result = await db.execute(
                delete(StorageUsageHistory).where(
                    StorageUsageHistory.recorded_at < cutoff_date
                )
            )
            await db.commit()
            
            deleted_count = result.rowcount
            logger.info(f"清理了 {deleted_count} 条旧的存储使用历史记录（保留最近 {days} 天）")
        except Exception as e:
            logger.error(f"清理旧的存储使用历史记录失败: {e}")
            await db.rollback()

