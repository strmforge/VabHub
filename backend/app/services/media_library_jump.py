"""
媒体库跳转服务模块

用于根据媒体信息和配置构造 Emby/Jellyfin 的 Web 详情/搜索页 URL
支持电影和剧集的不同搜索策略
"""

from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote_plus
from loguru import logger

from app.core.config import Settings


@dataclass
class MediaLibraryJump:
    """媒体库跳转信息"""
    enabled: bool
    url: Optional[str] = None
    reason: Optional[str] = None
    
    def __post_init__(self):
        """确保 enabled 为 False 时，url 和 reason 保持一致"""
        if not self.enabled and self.url:
            self.url = None


def build_media_library_jump(
    media_title: str,
    media_year: Optional[int] = None,
    media_season: Optional[int] = None,
    media_type: str = "movie",
    config: Optional[Settings] = None
) -> MediaLibraryJump:
    """
    根据媒体信息和配置构造媒体库跳转 URL
    
    Args:
        media_title: 媒体标题
        media_year: 媒体年份（可选）
        media_season: 季数（剧集类使用，可选）
        media_type: 媒体类型，movie/tv/short_drama/other
        config: 应用配置对象
        
    Returns:
        MediaLibraryJump: 跳转信息，包含是否启用、URL 和原因
        
    v1 规则：
    - 若 MEDIA_LIBRARY_TYPE == "none" 或 MEDIA_LIBRARY_BASE_URL 为空 → disabled
    - 电影：使用 "{title} {year}" 作为搜索词
    - 剧集：使用 "{title} s{season:02d}" 或仅标题作为搜索词
    - 通过模板构造搜索页 URL
    """
    
    if not config:
        return MediaLibraryJump(
            enabled=False,
            reason="config not provided"
        )
    
    # 检查媒体库配置
    library_type = getattr(config, 'MEDIA_LIBRARY_TYPE', 'none')
    base_url = getattr(config, 'MEDIA_LIBRARY_BASE_URL', None)
    
    if library_type == "none" or not base_url:
        logger.debug("Media library not configured or base URL missing")
        return MediaLibraryJump(
            enabled=False,
            reason="media library not configured"
        )
    
    # 构造搜索查询
    query = _build_search_query(media_title, media_year, media_season, media_type)
    if not query:
        return MediaLibraryJump(
            enabled=False,
            reason="failed to build search query"
        )
    
    # 构造完整 URL
    try:
        search_template = getattr(config, 'MEDIA_LIBRARY_SEARCH_PATH_TEMPLATE', 
                                 '/web/index.html#!/search.html?query={query}')
        search_path = search_template.format(query=quote_plus(query))
        full_url = base_url.rstrip('/') + search_path
        
        logger.debug(f"Built media library URL: {full_url} for query: {query}")
        
        return MediaLibraryJump(
            enabled=True,
            url=full_url,
            reason=None
        )
        
    except Exception as e:
        logger.error(f"Failed to build media library URL: {e}")
        return MediaLibraryJump(
            enabled=False,
            reason=f"URL construction failed: {str(e)}"
        )


def _build_search_query(
    title: str,
    year: Optional[int] = None,
    season: Optional[int] = None,
    media_type: str = "movie"
) -> Optional[str]:
    """
    根据媒体信息构造搜索查询字符串
    
    Args:
        title: 媒体标题
        year: 年份
        season: 季数
        media_type: 媒体类型
        
    Returns:
        str | None: 搜索查询字符串，失败返回 None
    """
    
    if not title or not title.strip():
        logger.warning("Media title is empty, cannot build search query")
        return None
    
    title = title.strip()
    
    # 媒体类型分支处理
    if media_type in ["movie", "短片电影", "单集纪录片"]:
        # 电影类：标题 + 年份
        if year and year > 0:
            return f"{title} {year}"
        return title
    
    elif media_type in ["tv", "series", "短剧", "综艺", "short_drama"]:
        # 剧集类：标题 + 季数（如果有）
        if season and season > 0:
            return f"{title} s{season:02d}"
        return title
    
    else:
        # 其他类型：仅使用标题
        logger.debug(f"Unknown media type '{media_type}', using title only")
        return title


def is_media_library_enabled(config: Settings) -> bool:
    """
    检查媒体库跳转功能是否已启用
    
    Args:
        config: 应用配置对象
        
    Returns:
        bool: True 表示已启用
    """
    library_type = getattr(config, 'MEDIA_LIBRARY_TYPE', 'none')
    base_url = getattr(config, 'MEDIA_LIBRARY_BASE_URL', None)
    
    return library_type != "none" and bool(base_url)


def get_media_library_type(config: Settings) -> str:
    """
    获取配置的媒体库类型
    
    Args:
        config: 应用配置对象
        
    Returns:
        str: 媒体库类型 (emby/jellyfin/none)
    """
    return getattr(config, 'MEDIA_LIBRARY_TYPE', 'none')


def build_media_library_jump_from_media_item(
    media_item: dict,
    config: Settings
) -> MediaLibraryJump:
    """
    从媒体项字典构造跳转信息（便捷函数）
    
    Args:
        media_item: 媒体项字典，应包含 title, year, season, type 等字段
        config: 应用配置对象
        
    Returns:
        MediaLibraryJump: 跳转信息
    """
    
    title = media_item.get('title') or media_item.get('name')
    year = media_item.get('year') or media_item.get('release_year')
    season = media_item.get('season') or media_item.get('season_number')
    media_type = media_item.get('type') or media_item.get('media_type', 'movie')
    
    return build_media_library_jump(
        media_title=title or "",
        media_year=year,
        media_season=season,
        media_type=media_type,
        config=config
    )
