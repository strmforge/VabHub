"""
上传进度记录清理模块
定期清理旧的进度记录
"""

from datetime import datetime, timedelta
from typing import Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_

from app.core.database import get_db
from app.models.upload import UploadProgress, UploadTask


async def cleanup_old_progress_records(
    days: int = 30,
    keep_completed: bool = True,
    keep_failed: bool = False
):
    """
    清理旧的进度记录
    
    Args:
        days: 保留天数（默认30天）
        keep_completed: 是否保留已完成任务的进度记录（默认True）
        keep_failed: 是否保留失败任务的进度记录（默认False）
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    async for db in get_db():
        try:
            # 构建查询条件
            conditions = [UploadProgress.recorded_at < cutoff_date]
            
            # 如果需要保留已完成或失败任务的进度记录，需要排除这些任务
            if keep_completed or keep_failed:
                # 获取需要保留的任务ID
                task_query = select(UploadTask.id)
                task_conditions = []
                
                if keep_completed:
                    task_conditions.append(UploadTask.status == "completed")
                if keep_failed:
                    task_conditions.append(UploadTask.status == "failed")
                
                if task_conditions:
                    from sqlalchemy import or_
                    task_query = task_query.where(or_(*task_conditions))
                    
                    result = await db.execute(task_query)
                    keep_task_ids = [row[0] for row in result.all()]
                    
                    if keep_task_ids:
                        # 排除需要保留的任务
                        conditions.append(~UploadProgress.task_id.in_(keep_task_ids))
            
            # 删除旧的进度记录
            delete_query = delete(UploadProgress).where(and_(*conditions))
            result = await db.execute(delete_query)
            deleted_count = result.rowcount
            
            await db.commit()
            
            logger.info(f"清理旧的进度记录: 删除了 {deleted_count} 条记录（保留 {days} 天内的记录）")
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "cutoff_date": cutoff_date.isoformat()
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"清理进度记录异常: {e}")
            return {
                "success": False,
                "error": str(e)
            }


async def cleanup_orphaned_progress_records():
    """
    清理孤立的进度记录（任务已不存在的进度记录）
    """
    async for db in get_db():
        try:
            # 查找所有任务ID
            task_query = select(UploadTask.id)
            result = await db.execute(task_query)
            existing_task_ids = {row[0] for row in result.all()}
            
            # 查找所有进度记录的任务ID
            progress_query = select(UploadProgress.task_id).distinct()
            result = await db.execute(progress_query)
            progress_task_ids = {row[0] for row in result.all()}
            
            # 找出孤立的任务ID
            orphaned_task_ids = progress_task_ids - existing_task_ids
            
            if orphaned_task_ids:
                # 删除孤立的进度记录
                delete_query = delete(UploadProgress).where(
                    UploadProgress.task_id.in_(orphaned_task_ids)
                )
                result = await db.execute(delete_query)
                deleted_count = result.rowcount
                
                await db.commit()
                
                logger.info(f"清理孤立的进度记录: 删除了 {deleted_count} 条记录（{len(orphaned_task_ids)} 个孤立任务）")
                
                return {
                    "success": True,
                    "deleted_count": deleted_count,
                    "orphaned_task_count": len(orphaned_task_ids)
                }
            else:
                logger.info("没有孤立的进度记录需要清理")
                return {
                    "success": True,
                    "deleted_count": 0,
                    "orphaned_task_count": 0
                }
                
        except Exception as e:
            await db.rollback()
            logger.error(f"清理孤立进度记录异常: {e}")
            return {
                "success": False,
                "error": str(e)
            }


async def cleanup_task_progress_records(
    task_id: str,
    keep_latest: int = 10
):
    """
    清理特定任务的进度记录（只保留最新的N条）
    
    Args:
        task_id: 任务ID
        keep_latest: 保留最新的记录数（默认10条）
    """
    async for db in get_db():
        try:
            # 查找该任务的所有进度记录，按时间倒序
            progress_query = select(UploadProgress.id).where(
                UploadProgress.task_id == task_id
            ).order_by(UploadProgress.recorded_at.desc())
            
            result = await db.execute(progress_query)
            all_progress_ids = [row[0] for row in result.all()]
            
            # 如果需要删除的记录
            if len(all_progress_ids) > keep_latest:
                # 获取需要删除的记录ID（保留最新的keep_latest条）
                delete_ids = all_progress_ids[keep_latest:]
                
                # 删除旧记录
                delete_query = delete(UploadProgress).where(
                    UploadProgress.id.in_(delete_ids)
                )
                result = await db.execute(delete_query)
                deleted_count = result.rowcount
                
                await db.commit()
                
                logger.info(f"清理任务进度记录: 任务 {task_id}, 删除了 {deleted_count} 条记录（保留最新的 {keep_latest} 条）")
                
                return {
                    "success": True,
                    "deleted_count": deleted_count,
                    "kept_count": keep_latest
                }
            else:
                logger.info(f"任务 {task_id} 的进度记录数量不超过 {keep_latest} 条，无需清理")
                return {
                    "success": True,
                    "deleted_count": 0,
                    "kept_count": len(all_progress_ids)
                }
                
        except Exception as e:
            await db.rollback()
            logger.error(f"清理任务进度记录异常: {e}")
            return {
                "success": False,
                "error": str(e)
            }

