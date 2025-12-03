"""
统一媒体库 API

提供跨媒体类型的统一视图接口。
"""

from fastapi import APIRouter, Query, Depends
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from datetime import datetime
from loguru import logger

from app.core.database import get_db
from app.schemas.library import LibraryPreviewItem, LibraryPreviewResponse, WorkFormats
from app.models.media import Media
from app.models.ebook import EBook
from app.models.audiobook import AudiobookFile
from app.models.comic import Comic
from app.models.music import Music
from app.constants.media_types import MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV, MEDIA_TYPE_ANIME, MEDIA_TYPE_EBOOK, MEDIA_TYPE_AUDIOBOOK, MEDIA_TYPE_COMIC, MEDIA_TYPE_MUSIC

router = APIRouter()


@router.get("/preview", response_model=LibraryPreviewResponse, summary="统一媒体库预览")
async def get_library_preview(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    media_types: Optional[str] = Query(None, description="媒体类型过滤，逗号分隔，例如: movie,ebook"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取统一媒体库预览列表
    
    返回 Movie、TV、Anime 和 EBook 的混合预览列表，按创建时间降序排序。
    
    Args:
        page: 页码（从 1 开始）
        page_size: 每页数量
        media_types: 媒体类型过滤（可选），例如 "movie,ebook"
        db: 数据库会话
    
    Returns:
        LibraryPreviewResponse: 包含预览项列表和分页信息
    """
    # 解析 media_types 参数
    requested_types: Optional[List[str]] = None
    if media_types:
        requested_types = [t.strip() for t in media_types.split(",") if t.strip()]
    
    # 默认包含的媒体类型
    default_types = [MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV, MEDIA_TYPE_ANIME, MEDIA_TYPE_EBOOK, MEDIA_TYPE_AUDIOBOOK, MEDIA_TYPE_COMIC, MEDIA_TYPE_MUSIC]
    if requested_types:
        # 只查询请求的类型
        allowed_types = [t for t in requested_types if t in default_types]
        if not allowed_types:
            # 如果请求的类型都不在允许列表中，返回空结果
            return LibraryPreviewResponse(
                items=[],
                total=0,
                page=page,
                page_size=page_size
            )
    else:
        allowed_types = default_types
    
    # 确定要查询的视频媒体类型
    video_types = [t for t in allowed_types if t in [MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV, MEDIA_TYPE_ANIME]]
    include_ebook = MEDIA_TYPE_EBOOK in allowed_types
    include_audiobook = MEDIA_TYPE_AUDIOBOOK in allowed_types
    include_comic = MEDIA_TYPE_COMIC in allowed_types
    include_music = MEDIA_TYPE_MUSIC in allowed_types
    
    # 为了分页，我们需要先获取足够的数据，然后合并排序
    # 策略：从每个表取前 (page * page_size) 条，合并后排序，再分页
    fetch_limit = page * page_size
    
    all_items: List[LibraryPreviewItem] = []
    
    # 查询视频媒体（Movie/TV/Anime）
    if video_types:
        try:
            stmt = (
                select(Media)
                .where(Media.media_type.in_(video_types))
                .order_by(desc(Media.created_at))
                .limit(fetch_limit)
            )
            result = await db.execute(stmt)
            media_list = result.scalars().all()
            
            for media in media_list:
                # 构建 extra 信息
                extra: Dict[str, Any] = {}
                if media.tmdb_id:
                    extra["tmdb_id"] = media.tmdb_id
                if media.imdb_id:
                    extra["imdb_id"] = media.imdb_id
                if media.extra_metadata:
                    # 如果有 rating 等信息，可以添加到 extra
                    if isinstance(media.extra_metadata, dict):
                        if "rating" in media.extra_metadata:
                            extra["rating"] = media.extra_metadata.get("rating")
                
                item = LibraryPreviewItem(
                    id=media.id,
                    media_type=media.media_type,
                    title=media.title,
                    year=media.year,
                    cover_url=media.poster_url,  # 使用 poster_url 作为封面
                    created_at=media.created_at,
                    extra=extra if extra else None
                )
                all_items.append(item)
        except Exception as e:
            logger.warning(f"查询视频媒体失败: {e}")
    
    # 查询电子书
    ebook_list: List[EBook] = []
    if include_ebook:
        try:
            stmt = (
                select(EBook)
                .order_by(desc(EBook.created_at))
                .limit(fetch_limit)
            )
            result = await db.execute(stmt)
            ebook_list = result.scalars().all()
            
            # 批量查询 work_formats 信息（避免 N+1 查询）
            ebook_ids = [ebook.id for ebook in ebook_list]
            ebook_work_formats_map: Dict[int, WorkFormats] = {}
            
            if ebook_ids:
                # 1. 批量查询 AudiobookFile（通过 ebook_id IN）
                audiobook_ebook_ids: set = set()
                try:
                    audiobook_stmt = (
                        select(AudiobookFile.ebook_id)
                        .where(
                            AudiobookFile.ebook_id.in_(ebook_ids),
                            AudiobookFile.is_deleted == False
                        )
                        .distinct()
                    )
                    audiobook_result = await db.execute(audiobook_stmt)
                    audiobook_ebook_ids = set(audiobook_result.scalars().all())
                except Exception as e:
                    logger.warning(f"批量查询有声书关联失败: {e}")
                
                # 2. 批量查询 Comic（通过 series/title 匹配）
                # 收集所有 ebook 的 series 和 title，建立映射
                ebook_series_map: Dict[str, List[int]] = {}  # series -> [ebook_ids]
                ebook_title_map: Dict[str, List[int]] = {}  # title -> [ebook_ids]
                
                for ebook in ebook_list:
                    # 优先使用 series 匹配
                    if ebook.series:
                        if ebook.series not in ebook_series_map:
                            ebook_series_map[ebook.series] = []
                        ebook_series_map[ebook.series].append(ebook.id)
                    # 如果没有 series，使用 title
                    elif ebook.title:
                        if ebook.title not in ebook_title_map:
                            ebook_title_map[ebook.title] = []
                        ebook_title_map[ebook.title].append(ebook.id)
                
                comic_ebook_ids: set = set()
                if ebook_series_map or ebook_title_map:
                    try:
                        comic_conditions = []
                        
                        # 构建匹配条件：优先 series，其次 title
                        if ebook_series_map:
                            for series in ebook_series_map.keys():
                                comic_conditions.append(Comic.series.ilike(f"%{series}%"))
                        
                        if ebook_title_map:
                            for title in ebook_title_map.keys():
                                comic_conditions.append(Comic.title.ilike(f"%{title}%"))
                        
                        if comic_conditions:
                            # 查询匹配的 Comic（只取 series 和 title 用于匹配）
                            comic_stmt = (
                                select(Comic.series, Comic.title)
                                .where(or_(*comic_conditions))
                                .distinct()
                            )
                            comic_result = await db.execute(comic_stmt)
                            comic_rows = comic_result.all()
                            
                            # 在 Python 中匹配 comic 到 ebook
                            # 由于 SQL 已经用 ilike 做了模糊匹配，这里只需要反向查找
                            for comic_series, comic_title in comic_rows:
                                matched_ebook_ids: set = set()
                                
                                # 优先匹配 series（检查 comic_series 是否包含或等于 ebook 的 series）
                                if comic_series:
                                    for series, ebook_id_list in ebook_series_map.items():
                                        # 检查是否匹配：comic_series 包含 series，或 series 包含 comic_series
                                        # 使用 lower() 进行不区分大小写的匹配
                                        comic_series_lower = comic_series.lower()
                                        series_lower = series.lower()
                                        if series_lower in comic_series_lower or comic_series_lower in series_lower:
                                            matched_ebook_ids.update(ebook_id_list)
                                
                                # 如果没有匹配到 series，尝试匹配 title
                                if not matched_ebook_ids and comic_title:
                                    for title, ebook_id_list in ebook_title_map.items():
                                        comic_title_lower = comic_title.lower()
                                        title_lower = title.lower()
                                        if title_lower in comic_title_lower or comic_title_lower in title_lower:
                                            matched_ebook_ids.update(ebook_id_list)
                                
                                comic_ebook_ids.update(matched_ebook_ids)
                    except Exception as e:
                        logger.warning(f"批量查询漫画关联失败: {e}")
                
                # 3. 为每个 ebook 构造 WorkFormats
                for ebook in ebook_list:
                    work_formats = WorkFormats(
                        has_ebook=True,  # ebook 项当然有电子书
                        has_audiobook=ebook.id in audiobook_ebook_ids,
                        has_comic=ebook.id in comic_ebook_ids,
                        has_music=False  # 预留，当前暂不实现
                    )
                    ebook_work_formats_map[ebook.id] = work_formats
            
            # 构建 LibraryPreviewItem
            for ebook in ebook_list:
                # 构建 extra 信息
                extra: Dict[str, Any] = {}
                if ebook.author:
                    extra["author"] = ebook.author
                if ebook.series:
                    extra["series"] = ebook.series
                if ebook.isbn:
                    extra["isbn"] = ebook.isbn
                
                item = LibraryPreviewItem(
                    id=ebook.id,
                    media_type=MEDIA_TYPE_EBOOK,
                    title=ebook.title,
                    year=ebook.publish_year,  # 使用 publish_year 作为 year
                    cover_url=ebook.cover_url,
                    created_at=ebook.created_at,
                    extra=extra if extra else None,
                    work_formats=ebook_work_formats_map.get(ebook.id)  # 添加 work_formats
                )
                all_items.append(item)
        except Exception as e:
            logger.warning(f"查询电子书失败: {e}")
    
    # 查询有声书
    if include_audiobook:
        try:
            stmt = (
                select(AudiobookFile, EBook)
                .join(EBook, AudiobookFile.ebook_id == EBook.id)
                .where(AudiobookFile.is_deleted == False)
                .order_by(desc(AudiobookFile.created_at))
                .limit(fetch_limit)
            )
            result = await db.execute(stmt)
            audiobook_list = result.all()
            
            for audiobook_file, ebook in audiobook_list:
                # 构建 extra 信息
                extra: Dict[str, Any] = {}
                extra["ebook_id"] = ebook.id  # 添加 ebook_id 用于跳转到作品详情页
                if ebook.author:
                    extra["author"] = ebook.author
                if ebook.series:
                    extra["series"] = ebook.series
                if audiobook_file.narrator:
                    extra["narrator"] = audiobook_file.narrator
                if audiobook_file.duration_seconds:
                    extra["duration_seconds"] = audiobook_file.duration_seconds
                
                item = LibraryPreviewItem(
                    id=audiobook_file.id,
                    media_type=MEDIA_TYPE_AUDIOBOOK,
                    title=ebook.title,  # 使用作品标题
                    year=ebook.publish_year,  # 使用作品的出版年份
                    cover_url=ebook.cover_url,  # 优先复用电子书封面
                    created_at=audiobook_file.created_at,
                    extra=extra if extra else None
                )
                all_items.append(item)
        except Exception as e:
            logger.warning(f"查询有声书失败: {e}")
    
    # 查询漫画
    if include_comic:
        try:
            stmt = (
                select(Comic)
                .order_by(desc(Comic.created_at))
                .limit(fetch_limit)
            )
            result = await db.execute(stmt)
            comic_list = result.scalars().all()
            
            for comic in comic_list:
                # 构建 extra 信息
                extra: Dict[str, Any] = {}
                if comic.author:
                    extra["author"] = comic.author
                if comic.series:
                    extra["series"] = comic.series
                if comic.region:
                    extra["region"] = comic.region
                if comic.illustrator:
                    extra["illustrator"] = comic.illustrator
                
                item = LibraryPreviewItem(
                    id=comic.id,
                    media_type=MEDIA_TYPE_COMIC,
                    title=comic.title or comic.series or "未知标题",
                    year=comic.publish_year,  # 使用 publish_year 作为 year
                    cover_url=comic.cover_url,
                    created_at=comic.created_at,
                    extra=extra if extra else None
                )
                all_items.append(item)
        except Exception as e:
            logger.warning(f"查询漫画失败: {e}")
    
    # 查询音乐
    if include_music:
        try:
            stmt = (
                select(Music)
                .order_by(desc(Music.created_at))
                .limit(fetch_limit)
            )
            result = await db.execute(stmt)
            music_list = result.scalars().all()
            
            for music in music_list:
                # 构建 extra 信息
                extra: Dict[str, Any] = {}
                if music.artist:
                    extra["artist"] = music.artist
                if music.album:
                    extra["album"] = music.album
                if music.genre:
                    extra["genre"] = music.genre
                if music.album_artist:
                    extra["album_artist"] = music.album_artist
                
                item = LibraryPreviewItem(
                    id=music.id,
                    media_type=MEDIA_TYPE_MUSIC,
                    title=music.title or music.album or "未知曲目",  # 优先使用 title，其次 album
                    year=music.year,
                    cover_url=None,  # 音乐封面可以从 extra_metadata 中获取，暂时返回 None
                    created_at=music.created_at,
                    extra=extra if extra else None
                )
                all_items.append(item)
        except Exception as e:
            logger.warning(f"查询音乐失败: {e}")
    
    # 按 created_at 降序排序
    all_items.sort(key=lambda x: x.created_at, reverse=True)
    
    # 计算总数（需要分别查询每个表的总数）
    total = 0
    if video_types:
        try:
            stmt = select(func.count(Media.id)).where(Media.media_type.in_(video_types))
            result = await db.execute(stmt)
            total += result.scalar() or 0
        except Exception as e:
            logger.warning(f"统计视频媒体总数失败: {e}")
    
    if include_ebook:
        try:
            stmt = select(func.count(EBook.id))
            result = await db.execute(stmt)
            total += result.scalar() or 0
        except Exception as e:
            logger.warning(f"统计电子书总数失败: {e}")
    
    if include_audiobook:
        try:
            stmt = select(func.count(AudiobookFile.id)).where(AudiobookFile.is_deleted == False)
            result = await db.execute(stmt)
            total += result.scalar() or 0
        except Exception as e:
            logger.warning(f"统计有声书总数失败: {e}")
    
    if include_comic:
        try:
            stmt = select(func.count(Comic.id))
            result = await db.execute(stmt)
            total += result.scalar() or 0
        except Exception as e:
            logger.warning(f"统计漫画总数失败: {e}")
    
    if include_music:
        try:
            stmt = select(func.count(Music.id))
            result = await db.execute(stmt)
            total += result.scalar() or 0
        except Exception as e:
            logger.warning(f"统计音乐总数失败: {e}")
    
    # 分页
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_items = all_items[start_idx:end_idx]
    
    return LibraryPreviewResponse(
        items=paginated_items,
        total=total,
        page=page,
        page_size=page_size
    )
