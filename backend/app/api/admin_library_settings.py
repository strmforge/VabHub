"""
媒体库设置管理 API（只读）

提供媒体库根目录和 Inbox 配置的只读总览。
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.library import LibrarySettingsResponse, InboxSettings, LibraryRootsSettings
from app.api.smart_health import get_inbox_health

router = APIRouter()


@router.get("/", response_model=LibrarySettingsResponse, summary="获取媒体库设置总览（只读）")
async def get_library_settings(
    db: AsyncSession = Depends(get_db)
) -> LibrarySettingsResponse:
    """
    获取媒体库和 Inbox 设置的只读总览
    
    返回当前配置的媒体库根目录和 Inbox 设置，包括健康状态。
    此接口为只读，不提供修改功能。
    
    Returns:
        LibrarySettingsResponse: 包含 inbox 和 library_roots 设置
    """
    try:
        # 获取 Inbox 健康状态（复用 smart_health 的逻辑）
        inbox_health = await get_inbox_health(settings, db)
        
        # 构建 InboxSettings
        inbox_settings = InboxSettings(
            inbox_root=inbox_health["inbox_root"],
            enabled=inbox_health["enabled"],
            enabled_media_types=inbox_health["enabled_media_types"],
            detection_min_score=settings.INBOX_DETECTION_MIN_SCORE,
            scan_max_items=settings.INBOX_SCAN_MAX_ITEMS,
            last_run_at=inbox_health["last_run_at"],
            last_run_status=inbox_health["last_run_status"],
            last_run_summary=inbox_health["last_run_summary"],
            pending_warning=inbox_health["pending_warning"]
        )
        
        # 构建 LibraryRootsSettings
        library_roots_settings = LibraryRootsSettings(
            movie=settings.MOVIE_LIBRARY_ROOT,
            tv=settings.TV_LIBRARY_ROOT,
            anime=settings.ANIME_LIBRARY_ROOT,
            short_drama=settings.SHORT_DRAMA_LIBRARY_ROOT,
            ebook=settings.EBOOK_LIBRARY_ROOT,
            comic=settings.COMIC_LIBRARY_ROOT,
            music=settings.MUSIC_LIBRARY_ROOT
        )
        
        return LibrarySettingsResponse(
            inbox=inbox_settings,
            library_roots=library_roots_settings
        )
        
    except Exception as e:
        logger.error(f"获取媒体库设置失败: {e}", exc_info=True)
        # 即使出错，也返回基本结构（使用默认值）
        inbox_settings = InboxSettings(
            inbox_root=settings.INBOX_ROOT,
            enabled=False,
            enabled_media_types=[],
            detection_min_score=settings.INBOX_DETECTION_MIN_SCORE,
            scan_max_items=settings.INBOX_SCAN_MAX_ITEMS,
            last_run_at=None,
            last_run_status="never",
            last_run_summary=None,
            pending_warning=None
        )
        library_roots_settings = LibraryRootsSettings(
            movie=settings.MOVIE_LIBRARY_ROOT,
            tv=settings.TV_LIBRARY_ROOT,
            anime=settings.ANIME_LIBRARY_ROOT,
            short_drama=settings.SHORT_DRAMA_LIBRARY_ROOT,
            ebook=settings.EBOOK_LIBRARY_ROOT,
            comic=settings.COMIC_LIBRARY_ROOT,
            music=settings.MUSIC_LIBRARY_ROOT
        )
        return LibrarySettingsResponse(
            inbox=inbox_settings,
            library_roots=library_roots_settings
        )

