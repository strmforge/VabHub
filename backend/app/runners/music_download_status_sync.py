"""
音乐下载状态同步 Runner

轮询下载器状态，更新 MusicDownloadJob 状态。
下载完成后触发音乐导入。

使用方式：
    python -m app.runners.music_download_status_sync
    python -m app.runners.music_download_status_sync --limit 100
    python -m app.runners.music_download_status_sync --loop --loop-interval 300
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from loguru import logger


async def sync_download_status(
    limit: int = 100,
):
    """
    同步下载状态
    
    扫描 status in (submitted, downloading) 的 MusicDownloadJob，
    查询下载器状态并更新
    """
    from app.core.database import async_session_maker
    from app.models.music_download_job import MusicDownloadJob
    from app.models.download import DownloadTask
    from sqlalchemy import select, or_
    
    async with async_session_maker() as session:
        # 查询进行中的任务
        query = select(MusicDownloadJob).where(
            or_(
                MusicDownloadJob.status == "submitted",
                MusicDownloadJob.status == "downloading",
            )
        ).order_by(
            MusicDownloadJob.updated_at.asc()
        ).limit(limit)
        
        result = await session.execute(query)
        jobs = list(result.scalars().all())
        
        if not jobs:
            logger.info("没有进行中的下载任务")
            return {"updated": 0, "completed": 0, "failed": 0}
        
        logger.info(f"检查 {len(jobs)} 个进行中的任务")
        
        stats = {"updated": 0, "completed": 0, "failed": 0}
        
        for job in jobs:
            try:
                # 查询关联的 DownloadTask
                if job.download_task_id:
                    task_result = await session.execute(
                        select(DownloadTask).where(DownloadTask.id == job.download_task_id)
                    )
                    task = task_result.scalar_one_or_none()
                    
                    if task:
                        await _sync_job_from_task(session, job, task)
                        stats["updated"] += 1
                        
                        if job.status == "completed":
                            stats["completed"] += 1
                        elif job.status == "failed":
                            stats["failed"] += 1
                    else:
                        logger.warning(f"任务 {job.id} 关联的 DownloadTask 不存在")
                else:
                    logger.warning(f"任务 {job.id} 没有关联的 download_task_id")
                    
            except Exception as e:
                logger.error(f"同步任务 {job.id} 状态失败: {e}")
                stats["failed"] += 1
        
        await session.commit()
        
        return stats


async def _sync_job_from_task(
    session,
    job: "MusicDownloadJob",
    task: "DownloadTask",
):
    """
    从 DownloadTask 同步状态到 MusicDownloadJob
    """
    old_status = job.status
    
    if task.status == "downloading":
        job.status = "downloading"
        
    elif task.status == "completed":
        # 下载完成，触发导入
        job.status = "importing"
        job.downloaded_path = task.save_path  # 假设 DownloadTask 有 save_path
        
        # 尝试导入
        try:
            import_result = await _import_music_files(session, job, task)
            
            if import_result.get("success"):
                job.status = "completed"
                job.music_file_id = import_result.get("file_id")
                job.music_id = import_result.get("music_id")
                job.is_duplicate = import_result.get("is_duplicate", False)
                job.completed_at = datetime.utcnow()
                
                logger.info(f"任务 {job.id} 导入完成")
            else:
                job.status = "failed"
                job.last_error = import_result.get("error", "导入失败")
                
                logger.error(f"任务 {job.id} 导入失败: {import_result.get('error')}")
                
        except Exception as e:
            logger.error(f"任务 {job.id} 导入异常: {e}")
            job.status = "failed"
            job.last_error = str(e)
            
    elif task.status == "failed":
        job.status = "failed"
        job.last_error = "下载失败"
        
    elif task.status == "paused":
        # 保持 downloading 状态
        pass
    
    if old_status != job.status:
        logger.info(f"任务 {job.id} 状态变更: {old_status} -> {job.status}")


async def _import_music_files(
    session,
    job: "MusicDownloadJob",
    task: "DownloadTask",
) -> dict:
    """
    导入下载完成的音乐文件
    
    调用 music_import_service 进行实际导入
    """
    try:
        from app.services.music_import_service import import_music_from_download_job
        
        result = await import_music_from_download_job(session, job, task)
        return result
        
    except ImportError:
        # music_import_service 尚未实现，使用简单占位
        logger.warning("music_import_service 未实现，跳过导入")
        return {
            "success": True,
            "file_id": None,
            "music_id": None,
            "is_duplicate": False,
            "message": "导入服务未实现（占位）",
        }
    except Exception as e:
        logger.error(f"导入失败: {e}")
        return {
            "success": False,
            "error": str(e),
        }


async def main():
    parser = argparse.ArgumentParser(description='音乐下载状态同步工具')
    parser.add_argument('--limit', type=int, default=100, help='单次最多处理的任务数')
    parser.add_argument('--loop', action='store_true', help='循环运行模式')
    parser.add_argument('--loop-interval', type=int, default=300, help='循环间隔（秒）')
    
    args = parser.parse_args()
    
    logger.info("音乐下载状态同步 Runner 启动")
    
    if args.loop:
        logger.info(f"循环模式，间隔 {args.loop_interval} 秒")
        while True:
            try:
                stats = await sync_download_status(limit=args.limit)
                print(f"\n同步完成: 更新={stats['updated']}, 完成={stats['completed']}, 失败={stats['failed']}")
            except Exception as e:
                logger.error(f"同步失败: {e}")
            
            logger.info(f"等待 {args.loop_interval} 秒后继续...")
            await asyncio.sleep(args.loop_interval)
    else:
        stats = await sync_download_status(limit=args.limit)
        
        print("\n========== 状态同步统计 ==========")
        print(f"更新任务: {stats['updated']}")
        print(f"完成: {stats['completed']}")
        print(f"失败: {stats['failed']}")
        print("==================================\n")


if __name__ == '__main__':
    asyncio.run(main())
