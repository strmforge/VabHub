"""
漫画导入服务

从远程源拉取 Series/Chapter 信息，并在本地创建或更新记录
下载章节图片并保存为本地文件
"""
import os
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from loguru import logger

from app.core.config import settings
from app.models.manga_source import MangaSource
from app.models.manga_series_local import MangaSeriesLocal
from app.models.manga_chapter_local import MangaChapterLocal, MangaChapterStatus
from app.schemas.manga_import import MangaImportOptions
from app.schemas.manga_remote import RemoteMangaSeries, RemoteMangaChapter
from app.services.manga_remote_service import get_series_detail, list_chapters
from app.modules.manga_sources.factory import get_manga_source_adapter


# 漫画存储根路径
MANGA_ROOT = getattr(settings, 'COMIC_LIBRARY_ROOT', './data/library/comics')


def slugify(title: str) -> str:
    """将标题转换为安全的文件名（支持unicode/CJK字符）"""
    if not title:
        return "unknown"
    # 移除特殊字符，保留字母、数字、空格、连字符和unicode字符
    cleaned = re.sub(r'[^\w\s-]', '', title, flags=re.UNICODE)
    # 替换空格为连字符，转换为小写
    return cleaned.strip().replace(' ', '-').lower()


def get_series_path(series: MangaSeriesLocal) -> str:
    """获取系列目录路径"""
    return slugify(series.title)


def get_chapter_path(series: MangaSeriesLocal, chapter: MangaChapterLocal) -> str:
    """获取章节目录路径"""
    chapter_num = f"{chapter.number:g}" if chapter.number is not None else "000"
    chapter_title = slugify(chapter.title) if chapter.title else "unknown"
    return f"{get_series_path(series)}/{chapter_num} - {chapter_title}"


async def import_series_from_remote(
    session: AsyncSession,
    source_id: int,
    remote_series_id: str,
    options: MangaImportOptions,
) -> MangaSeriesLocal:
    """
    从远程源导入漫画系列
    
    - 若本地不存在该 series，则创建
    - 同步远程基本信息
    - 根据 options 决定导入哪些章节
    """
    # 1. 获取源
    stmt = select(MangaSource).where(
        MangaSource.id == source_id,
        MangaSource.is_enabled == True  # noqa: E712
    )
    result = await session.execute(stmt)
    source = result.scalar_one_or_none()
    
    if not source:
        raise ValueError(f"Source {source_id} not found or disabled")
    
    # 2. 检查本地是否已存在
    stmt = select(MangaSeriesLocal).where(
        MangaSeriesLocal.source_id == source_id,
        MangaSeriesLocal.remote_series_id == remote_series_id
    )
    result = await session.execute(stmt)
    local_series = result.scalar_one_or_none()
    
    # 3. 获取远程详情
    remote_series = await get_series_detail(session, source_id, remote_series_id)
    if not remote_series:
        raise ValueError(f"Remote series {remote_series_id} not found")
    
    # 4. 创建或更新本地系列
    if local_series:
        # 更新基本信息
        local_series.title = remote_series.title
        local_series.alt_titles = remote_series.alt_titles
        local_series.summary = remote_series.summary
        local_series.authors = remote_series.authors
        local_series.tags = remote_series.tags
        local_series.status = remote_series.status
        local_series.last_sync_at = datetime.now()
        local_series.remote_meta = _build_remote_meta(remote_series)
    else:
        # 创建新系列
        local_series = MangaSeriesLocal(
            source_id=source_id,
            remote_series_id=remote_series_id,
            title=remote_series.title,
            alt_titles=remote_series.alt_titles,
            summary=remote_series.summary,
            authors=remote_series.authors,
            tags=remote_series.tags,
            status=remote_series.status,
            remote_meta=_build_remote_meta(remote_series),
            last_sync_at=datetime.now(),
        )
        session.add(local_series)
        await session.flush()
    
    # 5. 下载封面（如果有）
    if remote_series.cover_url:
        try:
            cover_path = await _download_cover(local_series, remote_series.cover_url, source)
            if cover_path:
                local_series.cover_path = cover_path
        except Exception as e:
            logger.warning(f"Failed to download cover: {e}")
    
    await session.flush()
    
    # 6. 获取远程章节列表
    remote_chapters = await list_chapters(session, source_id, remote_series_id)
    
    # 7. 根据 options 筛选要导入的章节
    target_chapters = _filter_chapters(remote_chapters, options)
    
    # 8. 创建或更新本地章节记录
    for remote_chapter in target_chapters:
        stmt = select(MangaChapterLocal).where(
            MangaChapterLocal.series_id == local_series.id,
            MangaChapterLocal.remote_chapter_id == remote_chapter.remote_id
        )
        result = await session.execute(stmt)
        local_chapter = result.scalar_one_or_none()
        
        if not local_chapter:
            local_chapter = MangaChapterLocal(
                series_id=local_series.id,
                remote_chapter_id=remote_chapter.remote_id,
                title=remote_chapter.title,
                number=remote_chapter.number,
                volume=remote_chapter.volume,
                published_at=remote_chapter.published_at,
                status=MangaChapterStatus.PENDING,
            )
            session.add(local_chapter)
    
    # 9. 更新统计信息
    total_chapters = len(remote_chapters)
    downloaded_count = await session.execute(
        select(MangaChapterLocal).where(
            MangaChapterLocal.series_id == local_series.id,
            MangaChapterLocal.status == MangaChapterStatus.READY
        )
    )
    local_series.total_chapters = total_chapters
    local_series.downloaded_chapters = len(downloaded_count.scalars().all())
    
    await session.commit()
    await session.refresh(local_series)
    
    return local_series


def _build_remote_meta(remote_series: RemoteMangaSeries) -> Dict[str, Any]:
    """构造一份用于调试的裁剪远端元数据。

    仅保留对排错有用且尺寸较小的字段，避免把完整远端响应塞入数据库。
    """
    try:
        meta: Dict[str, Any] = {
            "source_id": remote_series.source_id,
            "source_type": str(remote_series.source_type),
            "remote_id": remote_series.remote_id,
            "title": remote_series.title,
        }

        if remote_series.alt_titles:
            meta["alt_titles"] = remote_series.alt_titles
        if remote_series.authors:
            meta["authors"] = remote_series.authors
        if remote_series.tags:
            meta["tags"] = remote_series.tags
        if remote_series.status is not None:
            meta["status"] = remote_series.status
        if remote_series.summary:
            # 避免过长摘要
            summary = remote_series.summary
            meta["summary"] = summary[:2000] if len(summary) > 2000 else summary
        if remote_series.cover_url:
            meta["cover_url"] = str(remote_series.cover_url)
        if remote_series.chapters_count is not None:
            meta["chapters_count"] = remote_series.chapters_count

        return meta
    except Exception as e:  # 极端情况下不阻塞导入
        logger.warning(f"Failed to build remote_meta for series {remote_series.remote_id}: {e}")
        return {}


def _filter_chapters(
    chapters: List[RemoteMangaChapter],
    options: MangaImportOptions,
) -> List[RemoteMangaChapter]:
    """根据选项筛选章节"""
    if options.mode == "ALL":
        return chapters
    elif options.mode == "LATEST_N":
        if options.latest_n:
            # 按 number 排序，取最新的 N 个
            sorted_chapters = sorted(
                chapters,
                key=lambda c: c.number if c.number is not None else 0,
                reverse=True
            )
            return sorted_chapters[:options.latest_n]
        return chapters
    elif options.mode == "SELECTED":
        if options.chapter_ids:
            return [c for c in chapters if c.remote_id in options.chapter_ids]
        return []
    return chapters


async def _download_cover(
    series: MangaSeriesLocal,
    cover_url: str,
    source: MangaSource,
) -> Optional[str]:
    """下载封面图片"""
    try:
        import httpx
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {}
            if source.api_key:
                headers['Authorization'] = f'Bearer {source.api_key}'
            
            response = await client.get(cover_url, headers=headers)
            response.raise_for_status()
            
            # 保存封面（使用可读性路径结构）
            cover_dir = Path(MANGA_ROOT) / get_series_path(series)
            cover_dir.mkdir(parents=True, exist_ok=True)
            
            # 根据 URL 判断扩展名
            ext = '.jpg'
            if '.png' in cover_url.lower():
                ext = '.png'
            elif '.webp' in cover_url.lower():
                ext = '.webp'
            
            cover_path = cover_dir / f"cover{ext}"
            cover_path.write_bytes(response.content)
            
            # 返回相对路径（相对于 media_root，即 data 目录）
            media_root = Path(MANGA_ROOT).parent.parent
            relative_path = cover_path.relative_to(media_root)
            return relative_path.as_posix()
    except Exception as e:
        logger.error(f"Failed to download cover: {e}")
        return None


async def download_chapter(
    session: AsyncSession,
    chapter: MangaChapterLocal,
) -> MangaChapterLocal:
    """
    下载章节所有图片
    
    - 为该 series/chapter 创建目录
    - 逐页下载图片
    - 保存为标准命名（001.jpg, 002.jpg, ...)
    - 填写 chapter.file_path, page_count
    - 更新状态为 READY / FAILED
    """
    try:
        # 1. 获取系列和源信息
        stmt = select(MangaSeriesLocal).where(MangaSeriesLocal.id == chapter.series_id)
        result = await session.execute(stmt)
        series = result.scalar_one_or_none()
        if not series:
            raise ValueError(f"Series {chapter.series_id} not found")
        
        stmt = select(MangaSource).where(MangaSource.id == series.source_id)
        result = await session.execute(stmt)
        source = result.scalar_one_or_none()
        if not source:
            raise ValueError(f"Source {series.source_id} not found")
        
        # 2. 更新状态为 DOWNLOADING
        chapter.status = MangaChapterStatus.DOWNLOADING
        chapter.last_error = None
        await session.commit()
        
        # 3. 获取适配器
        adapter = get_manga_source_adapter(source)
        
        # 4. 获取页面列表
        pages = await adapter.list_pages(
            series.remote_series_id,
            chapter.remote_chapter_id
        )
        
        if not pages:
            raise ValueError("No pages found for chapter")
        
        # 5. 创建章节目录（使用可读性路径结构）
        chapter_dir = Path(MANGA_ROOT) / get_chapter_path(series, chapter)
        chapter_dir.mkdir(parents=True, exist_ok=True)
        
        # 6. 下载所有页面
        page_count = 0
        for page in pages:
            try:
                content = await adapter.fetch_page_content(page)
                
                # 判断图片格式
                ext = '.jpg'
                if content.startswith(b'\x89PNG'):
                    ext = '.png'
                elif content.startswith(b'WEBP'):
                    ext = '.webp'
                
                # 保存文件
                page_filename = f"{page.index:03d}{ext}"
                page_path = chapter_dir / page_filename
                page_path.write_bytes(content)
                page_count += 1
            except Exception as e:
                logger.error(f"Failed to download page {page.index}: {e}")
                # 继续下载其他页面
        
        if page_count == 0:
            raise ValueError("No pages downloaded")
        
        # 7. 更新章节信息
        # 存储相对于MANGA_ROOT的路径（简化路径处理）
        relative_path = chapter_dir.relative_to(Path(MANGA_ROOT))
        chapter.file_path = relative_path.as_posix()
        chapter.page_count = page_count
        chapter.status = MangaChapterStatus.READY
        chapter.last_error = None
        
        # 8. 更新系列统计
        downloaded_count = await session.execute(
            select(MangaChapterLocal).where(
                MangaChapterLocal.series_id == series.id,
                MangaChapterLocal.status == MangaChapterStatus.READY
            )
        )
        series.downloaded_chapters = len(downloaded_count.scalars().all())
        
        await session.commit()
        await session.refresh(chapter)
        
        return chapter
        
    except Exception as e:
        logger.error(f"Failed to download chapter {chapter.id}: {e}")
        chapter.status = MangaChapterStatus.FAILED
        chapter.last_error = str(e)
        await session.commit()
        raise


async def bulk_download_pending_chapters(
    session: AsyncSession,
    limit: int = 10,
    series_id: Optional[int] = None,
) -> int:
    """
    批量下载待处理的章节
    
    扫描 status=PENDING/FAILED 的章节，批量触发 download_chapter
    返回成功下载的章节数
    
    Args:
        session: 数据库会话
        limit: 最多下载章节数
        series_id: 可选，仅下载指定系列的章节
    """
    # 构建查询条件
    conditions = [
        MangaChapterLocal.status.in_([
            MangaChapterStatus.PENDING,
            MangaChapterStatus.FAILED
        ])
    ]
    
    # 如果指定了series_id，添加过滤条件
    if series_id is not None:
        conditions.append(MangaChapterLocal.series_id == series_id)
    
    stmt = select(MangaChapterLocal).where(
        and_(*conditions)
    ).limit(limit)
    
    result = await session.execute(stmt)
    chapters = result.scalars().all()
    
    success_count = 0
    for chapter in chapters:
        try:
            await download_chapter(session, chapter)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to download chapter {chapter.id}: {e}")
    
    return success_count

