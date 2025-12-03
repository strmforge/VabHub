"""
作品中心（Work Hub）API

提供统一的作品详情聚合接口，支持电子书、有声书、漫画等多种形态。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from loguru import logger

from app.core.database import get_db
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)
from app.models.ebook import EBook, EBookFile
from app.models.audiobook import AudiobookFile
from app.models.comic import Comic, ComicFile
from app.models.media import Media
from app.models.music import Music
from app.models.work_link import WorkLink
from app.constants.media_types import MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV, MEDIA_TYPE_ANIME, MEDIA_TYPE_SHORT_DRAMA
from app.schemas.work import (
    WorkDetailResponse,
    WorkEBook,
    WorkEBookFile,
    WorkAudiobookFile,
    WorkComic,
    WorkComicFile,
    WorkVideoItem,
    WorkMusicItem
)
from app.schemas.work_link import WorkLinkResponse

router = APIRouter()


@router.get("/{ebook_id}", response_model=BaseResponse)
async def get_work_detail(
    ebook_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取作品详情（聚合电子书、有声书、漫画）
    
    本阶段以 EBook 作为 Work 的"锚点"（work_id = ebook_id）。
    未来可以扩展为真正的 Work 表，但本次只做"聚合视图"。
    
    Args:
        ebook_id: 电子书作品 ID（作为 work_id）
    
    Returns:
        WorkDetailResponse: 包含 ebook、ebook_files、audiobooks、comics、comic_files
    """
    try:
        # 步骤 1: 查询 EBook + 其 EBookFile 列表
        ebook_stmt = select(EBook).where(EBook.id == ebook_id)
        ebook_result = await db.execute(ebook_stmt)
        ebook = ebook_result.scalar_one_or_none()
        
        if not ebook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message=f"作品 ID {ebook_id} 不存在"
                ).model_dump()
            )
        
        # 查询 EBookFile 列表
        ebook_files_stmt = select(EBookFile).where(
            EBookFile.ebook_id == ebook_id,
            EBookFile.is_deleted == False
        ).order_by(EBookFile.created_at.desc())
        ebook_files_result = await db.execute(ebook_files_stmt)
        ebook_files = ebook_files_result.scalars().all()
        
        # 步骤 1.5: 加载 WorkLink（手动关联）
        links_stmt = select(WorkLink).where(WorkLink.ebook_id == ebook_id)
        links_result = await db.execute(links_stmt)
        all_links = links_result.scalars().all()
        
        # 按 target_type 和 relation 分组
        includes_video_ids: set = set()
        includes_comic_ids: set = set()
        includes_music_ids: set = set()
        excludes_video_ids: set = set()
        excludes_comic_ids: set = set()
        excludes_music_ids: set = set()
        
        for link in all_links:
            if link.relation == "include":
                if link.target_type == "video":
                    includes_video_ids.add(link.target_id)
                elif link.target_type == "comic":
                    includes_comic_ids.add(link.target_id)
                elif link.target_type == "music":
                    includes_music_ids.add(link.target_id)
            elif link.relation == "exclude":
                if link.target_type == "video":
                    excludes_video_ids.add(link.target_id)
                elif link.target_type == "comic":
                    excludes_comic_ids.add(link.target_id)
                elif link.target_type == "music":
                    excludes_music_ids.add(link.target_id)
        
        # 步骤 2: 查询关联的 Audiobook
        audiobook_stmt = select(AudiobookFile).where(
            AudiobookFile.ebook_id == ebook_id,
            AudiobookFile.is_deleted == False
        ).order_by(AudiobookFile.created_at.desc())
        audiobook_result = await db.execute(audiobook_stmt)
        audiobook_files = audiobook_result.scalars().all()
        
        # 扁平化为 WorkAudiobookFile 列表（包含标题信息）
        audiobooks: List[WorkAudiobookFile] = []
        for ab_file in audiobook_files:
            audiobook_item = WorkAudiobookFile(
                id=ab_file.id,
                title=ebook.title,  # 使用 EBook 的标题
                format=ab_file.format,
                duration_seconds=ab_file.duration_seconds,
                bitrate_kbps=ab_file.bitrate_kbps,
                sample_rate_hz=ab_file.sample_rate_hz,
                channels=ab_file.channels,
                narrator=ab_file.narrator,
                language=ab_file.language,
                file_size_mb=ab_file.file_size_mb,
                source_site_id=ab_file.source_site_id,
                download_task_id=ab_file.download_task_id,
                is_tts_generated=ab_file.is_tts_generated,
                tts_provider=ab_file.tts_provider,
                created_at=ab_file.created_at
            )
            audiobooks.append(audiobook_item)
        
        # 步骤 3: 查询"相关漫画"（手动 include + 启发式匹配，过滤 exclude）
        comics: List[WorkComic] = []
        comic_files: List[WorkComicFile] = []
        
        # 3.1: 手动 include 的漫画
        if includes_comic_ids:
            include_comic_stmt = select(Comic).where(Comic.id.in_(list(includes_comic_ids)))
            include_comic_result = await db.execute(include_comic_stmt)
            include_comics = include_comic_result.scalars().all()
            
            if include_comics:
                include_comic_ids_list = [c.id for c in include_comics]
                
                # 查询对应的 ComicFile
                include_comic_file_stmt = select(ComicFile).where(
                    ComicFile.comic_id.in_(include_comic_ids_list),
                    ComicFile.is_deleted == False
                ).order_by(ComicFile.created_at.desc())
                include_comic_file_result = await db.execute(include_comic_file_stmt)
                include_comic_files = include_comic_file_result.scalars().all()
                
                comics.extend([WorkComic.model_validate(c) for c in include_comics])
                comic_files.extend([WorkComicFile.model_validate(cf) for cf in include_comic_files])
        
        # 3.2: 启发式匹配的漫画（过滤 exclude 和已 include 的）
        if ebook.series or ebook.title:
            # 构建匹配条件
            comic_conditions = []
            
            # 优先匹配 series
            if ebook.series:
                comic_conditions.append(Comic.series.ilike(f"%{ebook.series}%"))
            
            # 如果没有 series 或 series 匹配失败，尝试匹配 title
            if ebook.title:
                comic_conditions.append(Comic.title.ilike(f"%{ebook.title}%"))
            
            # 如果条件不为空，执行查询
            if comic_conditions:
                comic_stmt = select(Comic).where(
                    or_(*comic_conditions)
                ).limit(50)  # 限制最多 50 条
                comic_result = await db.execute(comic_stmt)
                matched_comics = comic_result.scalars().all()
                
                # 过滤：排除 exclude 和已 include 的
                filtered_comics = [
                    c for c in matched_comics
                    if c.id not in excludes_comic_ids and c.id not in includes_comic_ids
                ]
                
                if filtered_comics:
                    filtered_comic_ids = [c.id for c in filtered_comics]
                    
                    # 查询对应的 ComicFile
                    comic_file_stmt = select(ComicFile).where(
                        ComicFile.comic_id.in_(filtered_comic_ids),
                        ComicFile.is_deleted == False
                    ).order_by(ComicFile.created_at.desc())
                    comic_file_result = await db.execute(comic_file_stmt)
                    matched_comic_files = comic_file_result.scalars().all()
                    
                    # 转换为响应格式
                    comics.extend([WorkComic.model_validate(c) for c in filtered_comics])
                    comic_files.extend([WorkComicFile.model_validate(cf) for cf in matched_comic_files])
        
        # 步骤 4: 查询"相关视频改编"（手动 include + 启发式匹配，过滤 exclude）
        videos: List[WorkVideoItem] = []
        
        # 4.1: 手动 include 的视频
        if includes_video_ids:
            include_video_stmt = select(Media).where(
                Media.id.in_(list(includes_video_ids)),
                Media.media_type.in_([MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV, MEDIA_TYPE_ANIME, MEDIA_TYPE_SHORT_DRAMA])
            )
            include_video_result = await db.execute(include_video_stmt)
            include_videos = include_video_result.scalars().all()
            
            for video in include_videos:
                rating = None
                season_index = None
                if video.extra_metadata and isinstance(video.extra_metadata, dict):
                    rating = video.extra_metadata.get("rating")
                    season_index = video.extra_metadata.get("season_index")
                
                video_item = WorkVideoItem(
                    id=video.id,
                    media_type=video.media_type,
                    title=video.title,
                    original_title=video.original_title,
                    year=video.year,
                    season_index=season_index,
                    poster_url=video.poster_url,
                    rating=rating,
                    source_site_id=None,
                    created_at=video.created_at
                )
                videos.append(video_item)
        
        # 4.2: 启发式匹配的视频（过滤 exclude 和已 include 的）
        if ebook.series or ebook.title:
            video_conditions = []
            
            # 优先用 ebook.series 作为"作品 IP 名"
            if ebook.series:
                video_conditions.append(Media.title.ilike(f"%{ebook.series}%"))
                video_conditions.append(Media.original_title.ilike(f"%{ebook.series}%"))
            
            # 否则用 ebook.title
            if ebook.title:
                video_conditions.append(Media.title.ilike(f"%{ebook.title}%"))
                video_conditions.append(Media.original_title.ilike(f"%{ebook.title}%"))
            
            if video_conditions:
                video_stmt = (
                    select(Media)
                    .where(
                        or_(*video_conditions),
                        Media.media_type.in_([MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV, MEDIA_TYPE_ANIME, MEDIA_TYPE_SHORT_DRAMA])
                    )
                    .order_by(Media.created_at.desc())
                    .limit(30)  # 限制最多 30 条
                )
                video_result = await db.execute(video_stmt)
                matched_videos = video_result.scalars().all()
                
                # 过滤：排除 exclude 和已 include 的
                filtered_videos = [
                    v for v in matched_videos
                    if v.id not in excludes_video_ids and v.id not in includes_video_ids
                ]
                
                for video in filtered_videos:
                    # 从 extra_metadata 中提取 rating 和 season_index
                    rating = None
                    season_index = None
                    if video.extra_metadata and isinstance(video.extra_metadata, dict):
                        rating = video.extra_metadata.get("rating")
                        season_index = video.extra_metadata.get("season_index")
                    
                    video_item = WorkVideoItem(
                        id=video.id,
                        media_type=video.media_type,
                        title=video.title,
                        original_title=video.original_title,
                        year=video.year,
                        season_index=season_index,
                        poster_url=video.poster_url,
                        rating=rating,
                        source_site_id=None,
                        created_at=video.created_at
                    )
                    videos.append(video_item)
        
        # 步骤 5: 查询"相关音乐"（手动 include + 启发式匹配，过滤 exclude）
        music: List[WorkMusicItem] = []
        
        # 5.1: 手动 include 的音乐
        if includes_music_ids:
            include_music_stmt = select(Music).where(Music.id.in_(list(includes_music_ids)))
            include_music_result = await db.execute(include_music_stmt)
            include_music = include_music_result.scalars().all()
            
            for m in include_music:
                cover_url = None
                if m.extra_metadata and isinstance(m.extra_metadata, dict):
                    cover_url = m.extra_metadata.get("cover_url")
                
                music_item = WorkMusicItem(
                    id=m.id,
                    title=m.title,
                    artist=m.artist,
                    album=m.album,
                    year=m.year,
                    genre=m.genre,
                    cover_url=cover_url,
                    created_at=m.created_at
                )
                music.append(music_item)
        
        # 5.2: 启发式匹配的音乐（过滤 exclude 和已 include 的）
        if ebook.title or ebook.series or ebook.author:
            # 构造候选关键字
            keywords = []
            if ebook.title:
                keywords.append(ebook.title)
            if ebook.series:
                keywords.append(ebook.series)
            if ebook.author:
                keywords.append(ebook.author)
            
            if keywords:
                music_conditions = []
                
                # 在 Music.title / Music.album / Music.tags 里做 ilike 匹配
                for keyword in keywords:
                    music_conditions.append(Music.title.ilike(f"%{keyword}%"))
                    music_conditions.append(Music.album.ilike(f"%{keyword}%"))
                    # tags 可能是 JSON 字符串或逗号分隔，也做 ilike 匹配
                    music_conditions.append(Music.tags.ilike(f"%{keyword}%"))
                
                if music_conditions:
                    music_stmt = (
                        select(Music)
                        .where(or_(*music_conditions))
                        .order_by(Music.created_at.desc())
                        .limit(50)  # 限制最多 50 条
                    )
                    music_result = await db.execute(music_stmt)
                    matched_music = music_result.scalars().all()
                    
                    # 过滤：排除 exclude 和已 include 的
                    filtered_music = [
                        m for m in matched_music
                        if m.id not in excludes_music_ids and m.id not in includes_music_ids
                    ]
                    
                    for m in filtered_music:
                        # cover_url 可以从 extra_metadata 获取，当前先留 None
                        cover_url = None
                        if m.extra_metadata and isinstance(m.extra_metadata, dict):
                            cover_url = m.extra_metadata.get("cover_url")
                        
                        music_item = WorkMusicItem(
                            id=m.id,
                            title=m.title,
                            artist=m.artist,
                            album=m.album,
                            year=m.year,
                            genre=m.genre,
                            cover_url=cover_url,
                            created_at=m.created_at
                        )
                        music.append(music_item)
        
        # 步骤 6: 构造响应（包含 WorkLink 列表）
        response = WorkDetailResponse(
            ebook=WorkEBook.model_validate(ebook),
            ebook_files=[WorkEBookFile.model_validate(ef) for ef in ebook_files],
            audiobooks=audiobooks,
            comics=comics,
            comic_files=comic_files,
            videos=videos,
            music=music,
            links=[WorkLinkResponse.model_validate(link) for link in all_links]  # 包含所有 WorkLink
        )
        
        return success_response(
            data=response.model_dump(),
            message="获取作品详情成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取作品详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取作品详情时发生错误: {str(e)}"
            ).model_dump()
        )

