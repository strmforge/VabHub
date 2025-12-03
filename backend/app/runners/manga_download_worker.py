"""
漫画下载任务 Worker

处理待处理的下载任务，支持串行处理（v1简化版本）
"""
from __future__ import annotations

import asyncio
from typing import List, Optional
from datetime import datetime

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.manga_download_job import (
    MangaDownloadJob,
    DownloadJobMode,
    DownloadJobStatus,
)
from app.models.manga_series_local import MangaSeriesLocal
from app.models.manga_chapter_local import MangaChapterLocal
from app.models.manga_source import MangaSource
from app.services.manga_download_job_service import MangaDownloadJobService
from app.services.manga_import_service import (
    download_chapter,
    import_series_from_remote,
    bulk_download_pending_chapters,
)
from app.services.runner_heartbeat import runner_context
from app.schemas.manga_import import MangaImportOptions


class MangaDownloadWorker:
    """漫画下载任务处理器"""

    def __init__(self, batch_size: int = 10):
        self.batch_size = batch_size
        self.running = True

    async def process_pending_jobs(self, db: AsyncSession) -> int:
        """处理一批待处理的下载任务
        
        Returns:
            处理的任务数量
        """
        processed_count = 0
        
        try:
            # 1. 获取待处理任务（加锁）
            jobs = await MangaDownloadJobService.get_pending_jobs(
                db, limit=self.batch_size
            )
            
            if not jobs:
                logger.debug("没有待处理的下载任务")
                return 0
            
            logger.info(f"开始处理 {len(jobs)} 个下载任务")
            
            # 2. 逐个处理任务（串行处理，v1简化版本）
            for job in jobs:
                try:
                    await self._process_single_job(db, job)
                    processed_count += 1
                    
                    # 任务间隔，避免过于频繁的请求
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"处理任务失败: job_id={job.id}, error={e}", exc_info=True)
                    # 标记任务失败，继续处理下一个
                    await MangaDownloadJobService.update_job_status(
                        db, job.id, DownloadJobStatus.FAILED, str(e)
                    )
            
            logger.info(f"下载任务处理完成，共处理 {processed_count} 个任务")
            return processed_count
            
        except Exception as e:
            logger.error(f"处理下载任务批次失败: {e}", exc_info=True)
            return processed_count

    async def _process_single_job(self, db: AsyncSession, job: MangaDownloadJob):
        """处理单个下载任务"""
        logger.info(f"开始处理下载任务: job_id={job.id}, mode={job.mode}")
        
        # 1. 标记任务为运行中
        await MangaDownloadJobService.update_job_status(
            db, job.id, DownloadJobStatus.RUNNING
        )
        
        try:
            if job.mode == DownloadJobMode.CHAPTER:
                await self._process_chapter_job(db, job)
            elif job.mode == DownloadJobMode.SERIES:
                await self._process_series_job(db, job)
            else:
                raise ValueError(f"不支持的任务模式: {job.mode}")
            
            # 2. 标记任务成功
            await MangaDownloadJobService.update_job_status(
                db, job.id, DownloadJobStatus.SUCCESS
            )
            
            logger.info(f"下载任务完成: job_id={job.id}")
            
        except Exception as e:
            # 3. 标记任务失败
            await MangaDownloadJobService.update_job_status(
                db, job.id, DownloadJobStatus.FAILED, str(e)
            )
            raise

    async def _process_chapter_job(self, db: AsyncSession, job: MangaDownloadJob):
        """处理单章节下载任务"""
        if not job.source_chapter_id:
            raise ValueError("单章节任务缺少 source_chapter_id")
        
        # 1. 查找或创建本地系列记录
        local_series = await self._ensure_local_series_exists(db, job)
        if not local_series:
            raise ValueError("无法创建或查找本地系列记录")
        
        # 2. 查找对应的本地章节
        stmt = select(MangaChapterLocal).where(
            MangaChapterLocal.series_id == local_series.id,
            MangaChapterLocal.remote_chapter_id == job.source_chapter_id,
        )
        result = await db.execute(stmt)
        chapter = result.scalar_one_or_none()
        
        if not chapter:
            raise ValueError(f"找不到对应的本地章节: {job.source_chapter_id}")
        
        # 3. 下载章节
        logger.info(f"开始下载章节: chapter_id={chapter.id}")
        updated_chapter = await download_chapter(db, chapter)
        
        # 4. 更新任务进度
        await MangaDownloadJobService.update_job_status(
            db, job.id, DownloadJobStatus.RUNNING,
            downloaded_chapters=1, total_chapters=1
        )
        
        logger.info(f"章节下载完成: chapter_id={updated_chapter.id}")

    async def _process_series_job(self, db: AsyncSession, job: MangaDownloadJob):
        """处理整部系列下载任务"""
        # 1. 查找或创建本地系列记录
        local_series = await self._ensure_local_series_exists(db, job)
        if not local_series:
            raise ValueError("无法创建或查找本地系列记录")
        
        # 2. 获取待下载章节列表
        stmt = select(MangaChapterLocal).where(
            MangaChapterLocal.series_id == local_series.id,
            MangaChapterLocal.status.in_(["PENDING", "FAILED"]),
        ).order_by(MangaChapterLocal.number.asc().nulls_last())
        
        result = await db.execute(stmt)
        chapters = result.scalars().all()
        
        if not chapters:
            logger.info(f"系列 {local_series.id} 没有待下载的章节")
            return
        
        total_chapters = len(chapters)
        logger.info(f"开始下载系列: {local_series.id}, 共 {total_chapters} 个章节")
        
        # 3. 更新任务总数
        await MangaDownloadJobService.update_job_status(
            db, job.id, DownloadJobStatus.RUNNING,
            total_chapters=total_chapters
        )
        
        # 4. 逐个下载章节
        success_count = 0
        for i, chapter in enumerate(chapters):
            try:
                logger.info(f"下载章节进度: {i+1}/{total_chapters}, chapter_id={chapter.id}")
                await download_chapter(db, chapter)
                success_count += 1
                
                # 更新进度
                await MangaDownloadJobService.update_job_status(
                    db, job.id, DownloadJobStatus.RUNNING,
                    downloaded_chapters=success_count
                )
                
            except Exception as e:
                logger.error(f"下载章节失败: chapter_id={chapter.id}, error={e}")
                # 继续下载其他章节
        
        logger.info(f"系列下载完成: {local_series.id}, 成功 {success_count}/{total_chapters}")

    async def _ensure_local_series_exists(
        self, db: AsyncSession, job: MangaDownloadJob
    ) -> Optional[MangaSeriesLocal]:
        """确保本地系列记录存在"""
        # 1. 如果任务已有关联的本地系列ID，直接返回
        if job.target_local_series_id:
            stmt = select(MangaSeriesLocal).where(
                MangaSeriesLocal.id == job.target_local_series_id
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        
        # 2. 根据 source_series_id 查找现有本地系列
        stmt = select(MangaSeriesLocal).where(
            MangaSeriesLocal.source_id == job.source_id,
            MangaSeriesLocal.remote_series_id == job.source_series_id,
        )
        result = await db.execute(stmt)
        local_series = result.scalar_one_or_none()
        
        if local_series:
            # 3. 更新任务的本地系列ID
            await MangaDownloadJobService.update_job_status(
                db, job.id, DownloadJobStatus.RUNNING
            )
            # 直接更新job的target_local_series_id
            job.target_local_series_id = local_series.id
            await db.commit()
            return local_series
        
        # 4. 创建新的本地系列记录
        logger.info(f"创建新的本地系列记录: source_series_id={job.source_series_id}")
        try:
            new_series = await import_series_from_remote(
                session=db,
                source_id=job.source_id,
                remote_series_id=job.source_series_id,
                options=MangaImportOptions(mode="ALL"),  # 导入所有章节
            )
            
            # 5. 更新任务的本地系列ID
            job.target_local_series_id = new_series.id
            await db.commit()
            
            return new_series
            
        except Exception as e:
            logger.error(f"创建本地系列失败: {e}", exc_info=True)
            return None


async def main():
    """主函数：处理所有待处理的下载任务"""
    worker = MangaDownloadWorker(batch_size=10)
    
    async with AsyncSessionLocal() as db:
        processed_count = await worker.process_pending_jobs(db)
        logger.info(f"Worker 运行完成，处理了 {processed_count} 个任务")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="漫画下载任务 Worker")
    parser.add_argument("--once", action="store_true", help="只运行一次")
    parser.add_argument("--batch-size", type=int, default=10, help="批次大小")
    
    args = parser.parse_args()
    
    if args.once:
        # 单次运行模式
        asyncio.run(main())
    else:
        # 持续运行模式（需要配合 systemd/timer）
        @runner_context("manga_download_worker", interval=30)
        async def continuous_worker():
            worker = MangaDownloadWorker(batch_size=args.batch_size)
            async with AsyncSessionLocal() as db:
                return await worker.process_pending_jobs(db)
        
        asyncio.run(continuous_worker())
