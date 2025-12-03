"""
插件媒体库查询客户端

PLUGIN-SDK-2 实现

提供媒体库查询能力，帮助插件判断作品是否已入库。
"""

from typing import Any, Optional, TYPE_CHECKING
from loguru import logger

from app.plugin_sdk.types import PluginCapability

if TYPE_CHECKING:
    from app.plugin_sdk.api import VabHubSDK


class MediaClient:
    """
    媒体库查询客户端
    
    封装主系统的媒体库查询能力，允许插件检查作品是否已存在。
    
    权限要求：
    - media.read: 查询媒体库
    
    Example:
        # 检查电影是否存在
        exists = await sdk.media.has_movie(tmdb_id=550)
        if not exists:
            # 触发下载
            pass
        
        # 检查电视剧是否存在
        exists = await sdk.media.has_tv(tmdb_id=1399, season=1)
    """
    
    def __init__(self, sdk: "VabHubSDK") -> None:
        """
        初始化媒体库客户端
        
        Args:
            sdk: VabHub SDK 实例
        """
        self._sdk = sdk
    
    async def has_movie(
        self,
        *,
        tmdb_id: Optional[int] = None,
        imdb_id: Optional[str] = None,
        title: Optional[str] = None,
        year: Optional[int] = None,
    ) -> bool:
        """
        检查电影是否已在媒体库中
        
        至少提供一个查询条件。
        
        Args:
            tmdb_id: TMDB ID
            imdb_id: IMDB ID
            title: 电影标题（模糊匹配）
            year: 年份
            
        Returns:
            是否存在
            
        Raises:
            PermissionError: 未声明 media.read 权限
        """
        self._sdk._require_capability(PluginCapability.MEDIA_READ)
        
        try:
            from app.core.database import get_session
            from app.models.media import Media
            from sqlalchemy import select, or_, and_
            
            async for session in get_session():
                conditions = [Media.media_type == "movie"]
                
                # 构建查询条件
                id_conditions = []
                if tmdb_id:
                    id_conditions.append(Media.tmdb_id == tmdb_id)
                if imdb_id:
                    id_conditions.append(Media.imdb_id == imdb_id)
                
                if id_conditions:
                    conditions.append(or_(*id_conditions))
                elif title:
                    # 标题模糊匹配
                    conditions.append(
                        or_(
                            Media.title.ilike(f"%{title}%"),
                            Media.original_title.ilike(f"%{title}%")
                        )
                    )
                    if year:
                        conditions.append(Media.year == year)
                else:
                    # 没有有效条件
                    return False
                
                stmt = select(Media.id).where(and_(*conditions)).limit(1)
                result = await session.execute(stmt)
                return result.scalar_one_or_none() is not None
                
        except Exception as e:
            self._sdk.log.error(f"Failed to check movie: {e}")
            return False
    
    async def has_tv(
        self,
        *,
        tmdb_id: Optional[int] = None,
        imdb_id: Optional[str] = None,
        title: Optional[str] = None,
        season: Optional[int] = None,
    ) -> bool:
        """
        检查电视剧是否已在媒体库中
        
        Args:
            tmdb_id: TMDB ID
            imdb_id: IMDB ID
            title: 剧集标题（模糊匹配）
            season: 季数（可选，暂不支持精确到季）
            
        Returns:
            是否存在
            
        Raises:
            PermissionError: 未声明 media.read 权限
        """
        self._sdk._require_capability(PluginCapability.MEDIA_READ)
        
        try:
            from app.core.database import get_session
            from app.models.media import Media
            from sqlalchemy import select, or_, and_
            
            async for session in get_session():
                # tv 和 anime 都算电视剧
                conditions = [or_(Media.media_type == "tv", Media.media_type == "anime")]
                
                id_conditions = []
                if tmdb_id:
                    id_conditions.append(Media.tmdb_id == tmdb_id)
                if imdb_id:
                    id_conditions.append(Media.imdb_id == imdb_id)
                
                if id_conditions:
                    conditions.append(or_(*id_conditions))
                elif title:
                    conditions.append(
                        or_(
                            Media.title.ilike(f"%{title}%"),
                            Media.original_title.ilike(f"%{title}%")
                        )
                    )
                else:
                    return False
                
                stmt = select(Media.id).where(and_(*conditions)).limit(1)
                result = await session.execute(stmt)
                return result.scalar_one_or_none() is not None
                
        except Exception as e:
            self._sdk.log.error(f"Failed to check TV: {e}")
            return False
    
    async def has_audiobook(
        self,
        *,
        ebook_id: Optional[int] = None,
        title: Optional[str] = None,
    ) -> bool:
        """
        检查有声书是否已存在
        
        Args:
            ebook_id: 电子书 ID
            title: 有声书标题（模糊匹配）
            
        Returns:
            是否存在
            
        Raises:
            PermissionError: 未声明 media.read 权限
        """
        self._sdk._require_capability(PluginCapability.MEDIA_READ)
        
        try:
            from app.core.database import get_session
            from app.models.audiobook import Audiobook
            from sqlalchemy import select, or_
            
            async for session in get_session():
                conditions = []
                
                if ebook_id:
                    conditions.append(Audiobook.ebook_id == ebook_id)
                elif title:
                    conditions.append(Audiobook.title.ilike(f"%{title}%"))
                else:
                    return False
                
                stmt = select(Audiobook.id).where(*conditions).limit(1)
                result = await session.execute(stmt)
                return result.scalar_one_or_none() is not None
                
        except Exception as e:
            self._sdk.log.error(f"Failed to check audiobook: {e}")
            return False
    
    async def has_manga(
        self,
        *,
        series_id: Optional[int] = None,
        title: Optional[str] = None,
    ) -> bool:
        """
        检查漫画系列是否已存在
        
        Args:
            series_id: 漫画系列 ID
            title: 漫画标题（模糊匹配）
            
        Returns:
            是否存在
            
        Raises:
            PermissionError: 未声明 media.read 权限
        """
        self._sdk._require_capability(PluginCapability.MEDIA_READ)
        
        try:
            from app.core.database import get_session
            from app.models.manga_series_local import MangaSeriesLocal
            from sqlalchemy import select, or_
            
            async for session in get_session():
                conditions = []
                
                if series_id:
                    conditions.append(MangaSeriesLocal.id == series_id)
                elif title:
                    conditions.append(MangaSeriesLocal.title.ilike(f"%{title}%"))
                else:
                    return False
                
                stmt = select(MangaSeriesLocal.id).where(*conditions).limit(1)
                result = await session.execute(stmt)
                return result.scalar_one_or_none() is not None
                
        except Exception as e:
            self._sdk.log.error(f"Failed to check manga: {e}")
            return False
    
    async def search_media(
        self,
        query: str,
        *,
        media_type: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        搜索媒体库
        
        Args:
            query: 搜索关键词
            media_type: 媒体类型过滤（movie/tv/anime）
            limit: 返回数量限制
            
        Returns:
            媒体列表
            
        Raises:
            PermissionError: 未声明 media.read 权限
        """
        self._sdk._require_capability(PluginCapability.MEDIA_READ)
        
        try:
            from app.core.database import get_session
            from app.models.media import Media
            from sqlalchemy import select, or_, desc
            
            async for session in get_session():
                conditions = [
                    or_(
                        Media.title.ilike(f"%{query}%"),
                        Media.original_title.ilike(f"%{query}%")
                    )
                ]
                
                if media_type:
                    conditions.append(Media.media_type == media_type)
                
                stmt = (
                    select(Media)
                    .where(*conditions)
                    .order_by(desc(Media.created_at))
                    .limit(limit)
                )
                result = await session.execute(stmt)
                medias = result.scalars().all()
                
                return [
                    {
                        "id": m.id,
                        "title": m.title,
                        "original_title": m.original_title,
                        "year": m.year,
                        "media_type": m.media_type,
                        "tmdb_id": m.tmdb_id,
                        "imdb_id": m.imdb_id,
                        "poster_url": m.poster_url,
                    }
                    for m in medias
                ]
                
        except Exception as e:
            self._sdk.log.error(f"Failed to search media: {e}")
            return []
