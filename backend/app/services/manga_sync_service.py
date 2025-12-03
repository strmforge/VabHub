"""
漫画同步服务（追更）

对已入库的漫画，从远程源同步新增章节
"""
from datetime import datetime
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models.manga_series_local import MangaSeriesLocal
from app.models.manga_chapter_local import MangaChapterLocal, MangaChapterStatus
from app.models.manga_source import MangaSource
from app.models.enums.notification_type import NotificationType
from app.models.enums.reading_media_type import ReadingMediaType
from app.services.manga_remote_service import list_chapters
from app.services.manga_import_service import download_chapter
from app.services.notification_service import create_notifications_for_users, get_user_ids_for_manga_series, notify_manga_updated, notify_manga_sync_failed
from app.schemas.manga_remote import RemoteMangaChapter


async def sync_series_from_remote(
    session: AsyncSession,
    series_id: int,
    download_new: bool = False,
) -> int:
    """
    对单个 MangaSeriesLocal 执行追更
    
    - 找到对应的 MangaSource + remote_series_id
    - 通过 MangaRemoteService / Adapter 获取最新章节列表
    - 与本地 MangaChapterLocal.remote_chapter_id 做 diff
    - 为新增的章节创建 MangaChapterLocal（status=PENDING）
    - 若 download_new=True，则可直接触发下载逻辑
    
    返回新增章节数量
    """
    try:
        # 1. 获取本地系列
        stmt = select(MangaSeriesLocal).where(MangaSeriesLocal.id == series_id)
        result = await session.execute(stmt)
        series = result.scalar_one_or_none()
        
        if not series:
            raise ValueError(f"Series {series_id} not found")
        
        # 2. 获取源信息
        stmt = select(MangaSource).where(MangaSource.id == series.source_id)
        result = await session.execute(stmt)
        source = result.scalar_one_or_none()
        
        if not source or not source.is_enabled:
            raise ValueError(f"Source {series.source_id} not found or disabled")
        
        # 3. 获取远程章节列表
        remote_chapters = await list_chapters(
            session=session,
            source_id=series.source_id,
            remote_series_id=series.remote_series_id
        )
        
        # 4. 获取本地已有章节的 remote_chapter_id 集合
        stmt = select(MangaChapterLocal).where(
            MangaChapterLocal.series_id == series_id
        )
        result = await session.execute(stmt)
        local_chapters = result.scalars().all()
        local_remote_ids = {ch.remote_chapter_id for ch in local_chapters}
        
        # 5. 找出新增的章节
        new_chapters = [
            ch for ch in remote_chapters
            if ch.remote_id not in local_remote_ids
        ]
        
        if not new_chapters:
            return 0
        
        # 6. 为新增章节创建本地记录
        new_count = 0
        for remote_chapter in new_chapters:
            local_chapter = MangaChapterLocal(
                series_id=series_id,
                remote_chapter_id=remote_chapter.remote_id,
                title=remote_chapter.title,
                number=remote_chapter.number,
                volume=remote_chapter.volume,
                published_at=remote_chapter.published_at,
                status=MangaChapterStatus.PENDING,
            )
            session.add(local_chapter)
            new_count += 1
        
        # 7. 更新系列统计和新章节数量
        series.total_chapters = len(remote_chapters)
        series.last_sync_at = datetime.now()
        series.new_chapter_count = new_count
        
        await session.commit()
        
        # 8. 如果新增了章节，创建通知
        if new_count > 0:
            try:
                # 获取收藏该系列的用户
                user_ids = await get_user_ids_for_manga_series(session, series_id)
                
                if user_ids:
                    # 获取最新章节ID用于跳转
                    latest_chapter_id = None
                    if new_count > 0:
                        stmt = select(MangaChapterLocal).where(
                            MangaChapterLocal.series_id == series_id
                        ).order_by(MangaChapterLocal.id.desc()).limit(1)
                        result = await session.execute(stmt)
                        latest_chapter = result.scalar_one_or_none()
                        if latest_chapter:
                            latest_chapter_id = latest_chapter.id
                    
                    # 为每个用户创建漫画更新通知
                    for user_id in user_ids:
                        await notify_manga_updated(
                            session=session,
                            user_id=user_id,
                            series_id=series.id,
                            series_title=series.title,
                            new_chapters=new_count,
                            latest_chapter_id=latest_chapter_id
                        )
                    
                    logger.info(f"为 {len(user_ids)} 个用户创建漫画更新通知")
            except Exception as e:
                logger.error(f"创建漫画更新通知失败: {e}")
        
        # 9. 如果 download_new=True，触发下载
        if download_new and new_count > 0:
            # 获取刚创建的新章节
            stmt = select(MangaChapterLocal).where(
                MangaChapterLocal.series_id == series_id,
                MangaChapterLocal.status == MangaChapterStatus.PENDING
            ).order_by(MangaChapterLocal.id.desc()).limit(new_count)
            result = await session.execute(stmt)
            pending_chapters = result.scalars().all()
            
            # 异步下载（不阻塞）
            for chapter in pending_chapters:
                try:
                    await download_chapter(session, chapter)
                except Exception as e:
                    logger.error(f"自动下载章节 {chapter.id} 失败: {e}")
        
        # 返回更详细的同步结果
        return {
            "series_id": series_id,
            "series_title": series.title,
            "new_chapters": new_count,
            "total_chapters": series.total_chapters,
            "last_sync_at": series.last_sync_at.isoformat() if series.last_sync_at else None,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"同步系列 {series_id} 失败: {e}", exc_info=True)
        
        # 在同步失败时发送通知给收藏用户
        try:
            # 获取系列信息用于通知
            stmt = select(MangaSeriesLocal).where(MangaSeriesLocal.id == series_id)
            result = await session.execute(stmt)
            failed_series = result.scalar_one_or_none()
            
            if failed_series:
                # 获取收藏该系列的用户
                user_ids = await get_user_ids_for_manga_series(session, series_id)
                
                # 为每个用户发送同步失败通知
                for user_id in user_ids:
                    await notify_manga_sync_failed(
                        session=session,
                        user_id=user_id,
                        series_id=series_id,
                        series_title=failed_series.title,
                        error_message=str(e)
                    )
                
                logger.info(f"为 {len(user_ids)} 个用户发送了漫画同步失败通知")
        except Exception as notify_error:
            logger.error(f"发送同步失败通知时出错: {notify_error}")
        
        await session.rollback()
        raise


async def sync_all_favorite_series(
    session: AsyncSession,
    limit: int = 20,
    download_new: bool = False,
) -> dict:
    """
    对所有被用户收藏的漫画系列执行 sync_series_from_remote
    
    基于 UserFavoriteMedia 表识别追更目标
    返回同步结果统计
    """
    try:
        # 获取所有被收藏的漫画系列（去重）
        from app.models.user_favorite_media import UserFavoriteMedia
        from app.models.enums.reading_media_type import ReadingMediaType
        
        stmt = select(UserFavoriteMedia.target_id).where(
            UserFavoriteMedia.media_type == ReadingMediaType.MANGA
        ).distinct().limit(limit)
        
        result = await session.execute(stmt)
        favorite_series_ids = [row[0] for row in result.all()]
        
        if not favorite_series_ids:
            logger.info("没有找到收藏的漫画系列")
            return {
                "success": True,
                "processed_series": 0,
                "total_new_chapters": 0,
                "message": "没有找到收藏的漫画系列"
            }
        
        # 获取系列详情
        stmt = select(MangaSeriesLocal).where(
            MangaSeriesLocal.id.in_(favorite_series_ids)
        )
        result = await session.execute(stmt)
        favorite_series = result.scalars().all()
        
        total_new_chapters = 0
        series_count = 0
        
        for series in favorite_series:
            try:
                logger.info(f"开始同步收藏漫画系列: {series.title} (ID: {series.id})")
                
                new_count = await sync_series_from_remote(
                    session=session,
                    series_id=series.id,
                    download_new=download_new
                )
                
                total_new_chapters += new_count
                series_count += 1
                
                if new_count > 0:
                    logger.info(f"漫画系列 {series.title} 新增 {new_count} 个章节")
                else:
                    logger.info(f"漫画系列 {series.title} 暂无更新")
                    
            except Exception as e:
                logger.error(f"同步收藏系列 {series.id} 失败: {e}")
                
                # 为收藏用户发送失败通知
                try:
                    user_ids = await get_user_ids_for_manga_series(session, series.id)
                    for user_id in user_ids:
                        await notify_manga_sync_failed(
                            session=session,
                            user_id=user_id,
                            series_id=series.id,
                            series_title=series.title,
                            error_message=str(e)
                        )
                    logger.info(f"为 {len(user_ids)} 个用户发送了系列 {series.title} 的同步失败通知")
                except Exception as notify_error:
                    logger.error(f"发送同步失败通知时出错: {notify_error}")
                
                continue
        
        logger.info(f"漫画追更同步完成: 共处理 {series_count} 个系列，新增 {total_new_chapters} 个章节")
        return {
            "success": True,
            "processed_series": series_count,
            "total_new_chapters": total_new_chapters,
            "details": favorite_series,  # 包含所有处理的系列详情
            "message": f"同步完成，处理了 {series_count} 个系列，新增 {total_new_chapters} 个章节"
        }
        
    except Exception as e:
        logger.error(f"批量同步收藏系列失败: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "processed_series": 0,
            "total_new_chapters": 0
        }

