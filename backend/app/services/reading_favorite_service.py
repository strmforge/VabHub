"""
阅读收藏服务
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.user_favorite_media import UserFavoriteMedia
from app.models.enums.reading_media_type import ReadingMediaType
from app.models.ebook import EBook
from app.models.audiobook import AudiobookFile
from app.models.manga_series_local import MangaSeriesLocal
from app.schemas.user_favorite_media import UserFavoriteMediaCreate, UserFavoriteMediaRead
from app.schemas.reading_hub import ReadingShelfItem


async def add_favorite(
    session: AsyncSession,
    user_id: int,
    data: UserFavoriteMediaCreate,
) -> UserFavoriteMediaRead:
    """
    收藏：
    - 如果已经存在同 user_id + media_type + target_id，则直接返回现有记录
    - 否则新建
    """
    # 检查是否已存在
    existing = await session.execute(
        select(UserFavoriteMedia).where(
            and_(
                UserFavoriteMedia.user_id == user_id,
                UserFavoriteMedia.media_type == data.media_type,
                UserFavoriteMedia.target_id == data.target_id,
            )
        )
    )
    existing = existing.scalar_one_or_none()
    
    if existing:
        return UserFavoriteMediaRead.from_orm(existing)
    
    # 创建新收藏
    favorite = UserFavoriteMedia(
        user_id=user_id,
        media_type=data.media_type,
        target_id=data.target_id,
    )
    session.add(favorite)
    await session.commit()
    await session.refresh(favorite)
    
    return UserFavoriteMediaRead.from_orm(favorite)


async def remove_favorite(
    session: AsyncSession,
    user_id: int,
    media_type: ReadingMediaType,
    target_id: int,
) -> None:
    """
    取消收藏：
    - 删除对应的 user_favorite_media 记录（如果存在）
    """
    result = await session.execute(
        select(UserFavoriteMedia).where(
            and_(
                UserFavoriteMedia.user_id == user_id,
                UserFavoriteMedia.media_type == media_type,
                UserFavoriteMedia.target_id == target_id,
            )
        )
    )
    favorite = result.scalar_one_or_none()
    
    if favorite:
        await session.delete(favorite)
        await session.commit()


async def is_favorite(
    session: AsyncSession,
    user_id: int,
    media_type: ReadingMediaType,
    target_id: int,
) -> bool:
    """
    查询是否收藏
    """
    result = await session.execute(
        select(UserFavoriteMedia).where(
            and_(
                UserFavoriteMedia.user_id == user_id,
                UserFavoriteMedia.media_type == media_type,
                UserFavoriteMedia.target_id == target_id,
            )
        )
    )
    return result.scalar_one_or_none() is not None


async def list_favorites(
    session: AsyncSession,
    user_id: int,
    media_type: Optional[ReadingMediaType] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[ReadingShelfItem]:
    """
    列出当前用户的收藏列表
    """
    # 构建基础查询
    query = select(UserFavoriteMedia).where(
        UserFavoriteMedia.user_id == user_id
    ).order_by(UserFavoriteMedia.created_at.desc())
    
    if media_type:
        query = query.where(UserFavoriteMedia.media_type == media_type)
    
    if limit > 0:
        query = query.limit(limit).offset(offset)
    
    result = await session.execute(query)
    favorites = result.scalars().all()
    
    shelf_items = []
    
    for fav in favorites:
        shelf_item = await _build_reading_shelf_item(session, fav)
        if shelf_item:
            shelf_items.append(shelf_item)
    
    return shelf_items


async def _build_reading_shelf_item(
    session: AsyncSession,
    favorite: UserFavoriteMedia,
) -> Optional[ReadingShelfItem]:
    """
    根据收藏记录构建书架项
    """
    try:
        if favorite.media_type == ReadingMediaType.NOVEL:
            return await _build_novel_shelf_item(session, favorite)
        elif favorite.media_type == ReadingMediaType.AUDIOBOOK:
            return await _build_audiobook_shelf_item(session, favorite)
        elif favorite.media_type == ReadingMediaType.MANGA:
            return await _build_manga_shelf_item(session, favorite)
    except Exception:
        # 如果资源不存在，跳过此项
        return None
    
    return None


async def _build_novel_shelf_item(
    session: AsyncSession,
    favorite: UserFavoriteMedia,
) -> Optional[ReadingShelfItem]:
    """构建小说书架项"""
    result = await session.execute(
        select(EBook).where(EBook.id == favorite.target_id)
    )
    ebook = result.scalar_one_or_none()
    
    if not ebook:
        return None
    
    return ReadingShelfItem(
        media_type=ReadingMediaType.NOVEL,
        item_id=ebook.id,
        title=ebook.title,
        cover_url=ebook.cover_url,
        source_label="小说中心",
        route_name="NovelReader",
        route_params={"ebookId": ebook.id},
    )


async def _build_audiobook_shelf_item(
    session: AsyncSession,
    favorite: UserFavoriteMedia,
) -> Optional[ReadingShelfItem]:
    """构建有声书书架项"""
    # 注意：有声书也关联到 EBook
    result = await session.execute(
        select(EBook).where(EBook.id == favorite.target_id)
    )
    ebook = result.scalar_one_or_none()
    
    if not ebook:
        return None
    
    return ReadingShelfItem(
        media_type=ReadingMediaType.AUDIOBOOK,
        item_id=ebook.id,
        title=ebook.title,
        cover_url=ebook.cover_url,
        source_label="有声书",
        route_name="WorkDetail",
        route_params={"workId": ebook.id, "workType": "audiobook"},
    )


async def _build_manga_shelf_item(
    session: AsyncSession,
    favorite: UserFavoriteMedia,
) -> Optional[ReadingShelfItem]:
    """构建漫画书架项"""
    result = await session.execute(
        select(MangaSeriesLocal).where(MangaSeriesLocal.id == favorite.target_id)
    )
    manga_series = result.scalar_one_or_none()
    
    if not manga_series:
        return None
    
    return ReadingShelfItem(
        media_type=ReadingMediaType.MANGA,
        item_id=manga_series.id,
        title=manga_series.title,
        cover_url=manga_series.cover_path,
        source_label="漫画",
        route_name="MangaReaderPage",
        route_params={"series_id": manga_series.id},
    )