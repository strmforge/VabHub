"""
漫画下载任务服务
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_
from loguru import logger

from app.models.manga_download_job import (
    MangaDownloadJob,
    DownloadJobMode,
    DownloadJobStatus,
)
from app.models.manga_series_local import MangaSeriesLocal
from app.models.manga_chapter_local import MangaChapterLocal
from app.models.manga_source import MangaSource


class MangaDownloadJobService:
    """漫画下载任务管理服务"""

    @staticmethod
    async def create_job(
        db: AsyncSession,
        user_id: int,
        source_id: int,
        source_type: str,
        source_series_id: str,
        mode: DownloadJobMode,
        source_chapter_id: Optional[str] = None,
        target_local_series_id: Optional[int] = None,
        priority: int = 0,
    ) -> MangaDownloadJob:
        """创建下载任务"""
        try:
            job = MangaDownloadJob(
                user_id=user_id,
                source_id=source_id,
                source_type=source_type,
                source_series_id=source_series_id,
                source_chapter_id=source_chapter_id,
                target_local_series_id=target_local_series_id,
                mode=mode,
                status=DownloadJobStatus.PENDING,
                priority=priority,
            )
            
            db.add(job)
            await db.commit()
            await db.refresh(job)
            
            logger.info(
                f"创建下载任务成功: job_id={job.id}, user_id={user_id}, "
                f"source={source_type}:{source_series_id}, mode={mode}"
            )
            
            return job
            
        except Exception as e:
            await db.rollback()
            logger.error(f"创建下载任务失败: {e}", exc_info=True)
            raise

    @staticmethod
    async def get_pending_jobs(
        db: AsyncSession,
        limit: int = 10,
        user_id: Optional[int] = None,
    ) -> List[MangaDownloadJob]:
        """获取待处理的下载任务（加锁）"""
        try:
            conditions = [
                MangaDownloadJob.status == DownloadJobStatus.PENDING
            ]
            
            if user_id:
                conditions.append(MangaDownloadJob.user_id == user_id)
            
            stmt = (
                select(MangaDownloadJob)
                .where(and_(*conditions))
                .order_by(MangaDownloadJob.priority.desc(), MangaDownloadJob.created_at.asc())
                .with_for_update()  # 加锁防止并发处理
                .limit(limit)
            )
            
            result = await db.execute(stmt)
            jobs = result.scalars().all()
            
            logger.info(f"获取到 {len(jobs)} 个待处理下载任务")
            return list(jobs)
            
        except Exception as e:
            logger.error(f"获取待处理任务失败: {e}", exc_info=True)
            return []

    @staticmethod
    async def update_job_status(
        db: AsyncSession,
        job_id: int,
        status: DownloadJobStatus,
        error_msg: Optional[str] = None,
        downloaded_chapters: Optional[int] = None,
        total_chapters: Optional[int] = None,
    ) -> Optional[MangaDownloadJob]:
        """更新任务状态"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow(),
            }
            
            if error_msg:
                update_data["error_msg"] = error_msg
            
            if downloaded_chapters is not None:
                update_data["downloaded_chapters"] = downloaded_chapters
            
            if total_chapters is not None:
                update_data["total_chapters"] = total_chapters
            
            # 根据状态设置时间戳
            if status == DownloadJobStatus.RUNNING:
                update_data["started_at"] = datetime.utcnow()
            elif status in (DownloadJobStatus.SUCCESS, DownloadJobStatus.FAILED):
                update_data["completed_at"] = datetime.utcnow()
            
            stmt = (
                update(MangaDownloadJob)
                .where(MangaDownloadJob.id == job_id)
                .values(**update_data)
                .returning(MangaDownloadJob)
            )
            
            result = await db.execute(stmt)
            await db.commit()
            
            job = result.scalar_one_or_none()
            if job:
                logger.info(f"更新任务状态成功: job_id={job_id}, status={status}")
            
            return job
            
        except Exception as e:
            await db.rollback()
            logger.error(f"更新任务状态失败: job_id={job_id}, error={e}", exc_info=True)
            return None

    @staticmethod
    async def get_job_by_id(
        db: AsyncSession,
        job_id: int,
        user_id: Optional[int] = None,
    ) -> Optional[MangaDownloadJob]:
        """根据ID获取任务"""
        try:
            conditions = [MangaDownloadJob.id == job_id]
            
            if user_id:
                conditions.append(MangaDownloadJob.user_id == user_id)
            
            stmt = select(MangaDownloadJob).where(and_(*conditions))
            result = await db.execute(stmt)
            
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"获取任务失败: job_id={job_id}, error={e}", exc_info=True)
            return None

    @staticmethod
    async def list_jobs(
        db: AsyncSession,
        user_id: int,
        status_filter: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[MangaDownloadJob]:
        """获取用户的任务列表"""
        try:
            conditions = [MangaDownloadJob.user_id == user_id]
            
            if status_filter:
                if status_filter == "active":
                    conditions.append(
                        MangaDownloadJob.status.in_([
                            DownloadJobStatus.PENDING,
                            DownloadJobStatus.RUNNING
                        ])
                    )
                elif status_filter == "completed":
                    conditions.append(
                        MangaDownloadJob.status.in_([
                            DownloadJobStatus.SUCCESS,
                            DownloadJobStatus.FAILED
                        ])
                    )
                else:
                    conditions.append(MangaDownloadJob.status == status_filter)
            
            stmt = (
                select(MangaDownloadJob)
                .where(and_(*conditions))
                .order_by(MangaDownloadJob.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            
            result = await db.execute(stmt)
            jobs = result.scalars().all()
            
            return list(jobs)
            
        except Exception as e:
            logger.error(f"获取任务列表失败: user_id={user_id}, error={e}", exc_info=True)
            return []

    @staticmethod
    async def count_jobs(
        db: AsyncSession,
        user_id: int,
        status_filter: Optional[str] = None,
    ) -> int:
        """统计用户任务数量"""
        try:
            conditions = [MangaDownloadJob.user_id == user_id]
            
            if status_filter:
                if status_filter == "active":
                    conditions.append(
                        MangaDownloadJob.status.in_([
                            DownloadJobStatus.PENDING,
                            DownloadJobStatus.RUNNING
                        ])
                    )
                elif status_filter == "completed":
                    conditions.append(
                        MangaDownloadJob.status.in_([
                            DownloadJobStatus.SUCCESS,
                            DownloadJobStatus.FAILED
                        ])
                    )
                else:
                    conditions.append(MangaDownloadJob.status == status_filter)
            
            stmt = select(func.count()).select_from(MangaDownloadJob).where(and_(*conditions))
            result = await db.execute(stmt)
            
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"统计任务数量失败: user_id={user_id}, error={e}", exc_info=True)
            return 0

    @staticmethod
    async def get_job_details_with_relations(
        db: AsyncSession,
        job_id: int,
        user_id: Optional[int] = None,
    ) -> Optional[dict]:
        """获取任务详情（包含关联信息）"""
        try:
            conditions = [MangaDownloadJob.id == job_id]
            
            if user_id:
                conditions.append(MangaDownloadJob.user_id == user_id)
            
            stmt = (
                select(
                    MangaDownloadJob,
                    MangaSource,
                    MangaSeriesLocal,
                )
                .join(MangaSource, MangaDownloadJob.source_id == MangaSource.id)
                .outerjoin(
                    MangaSeriesLocal,
                    MangaDownloadJob.target_local_series_id == MangaSeriesLocal.id
                )
                .where(and_(*conditions))
            )
            
            result = await db.execute(stmt)
            row = result.first()
            
            if not row:
                return None
            
            job, source, target_series = row
            
            return {
                "job": job,
                "source": source,
                "target_series": target_series,
            }
            
        except Exception as e:
            logger.error(f"获取任务详情失败: job_id={job_id}, error={e}", exc_info=True)
            return None
