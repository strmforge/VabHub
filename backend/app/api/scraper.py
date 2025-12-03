"""
刮削器管理API
用于管理媒体刮削器配置和测试
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from pydantic import BaseModel
from loguru import logger

from app.core.database import get_db
from app.modules.settings.service import SettingsService
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)

router = APIRouter(prefix="/scraper", tags=["刮削器"])


class ScraperConfig(BaseModel):
    """刮削器配置"""
    tmdb_enabled: bool = True
    douban_enabled: bool = True
    tvdb_enabled: bool = True
    fanart_enabled: bool = True
    musicbrainz_enabled: bool = True
    acoustid_enabled: bool = True
    tmdb_api_key: Optional[str] = None
    douban_api_key: Optional[str] = None
    acoustid_api_key: Optional[str] = None
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 缓存TTL（秒）


@router.get("/config", response_model=BaseResponse)
async def get_scraper_config(
    db: AsyncSession = Depends(get_db)
):
    """
    获取刮削器配置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": ScraperConfig,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        settings_service = SettingsService(db)
        
        # 从设置中获取刮削器配置
        config = {
            "tmdb_enabled": await settings_service.get_setting("scraper_tmdb_enabled", category="scraper") or True,
            "douban_enabled": await settings_service.get_setting("scraper_douban_enabled", category="scraper") or True,
            "tvdb_enabled": await settings_service.get_setting("scraper_tvdb_enabled", category="scraper") or True,
            "fanart_enabled": await settings_service.get_setting("scraper_fanart_enabled", category="scraper") or True,
            "musicbrainz_enabled": await settings_service.get_setting("scraper_musicbrainz_enabled", category="scraper") or True,
            "acoustid_enabled": await settings_service.get_setting("scraper_acoustid_enabled", category="scraper") or True,
            "tmdb_api_key": await settings_service.get_setting("TMDB_API_KEY", category="advanced_media") or "",
            "douban_api_key": await settings_service.get_setting("DOUBAN_API_KEY", category="advanced_media") or "",
            "acoustid_api_key": await settings_service.get_setting("ACOUSTID_API_KEY", category="advanced_media") or "",
            "cache_enabled": await settings_service.get_setting("scraper_cache_enabled", category="scraper") or True,
            "cache_ttl": int(await settings_service.get_setting("scraper_cache_ttl", category="scraper") or 3600)
        }
        
        return success_response(
            data=config,
            message="获取刮削器配置成功"
        )
    except Exception as e:
        logger.error(f"获取刮削器配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取刮削器配置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.put("/config", response_model=BaseResponse)
async def update_scraper_config(
    config: ScraperConfig,
    db: AsyncSession = Depends(get_db)
):
    """
    更新刮削器配置
    
    返回统一响应格式：
    {
        "success": true,
        "message": "更新成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        settings_service = SettingsService(db)
        
        # 更新刮削器配置
        await settings_service.set_setting("scraper_tmdb_enabled", config.tmdb_enabled, category="scraper")
        await settings_service.set_setting("scraper_douban_enabled", config.douban_enabled, category="scraper")
        await settings_service.set_setting("scraper_tvdb_enabled", config.tvdb_enabled, category="scraper")
        await settings_service.set_setting("scraper_fanart_enabled", config.fanart_enabled, category="scraper")
        await settings_service.set_setting("scraper_musicbrainz_enabled", config.musicbrainz_enabled, category="scraper")
        await settings_service.set_setting("scraper_acoustid_enabled", config.acoustid_enabled, category="scraper")
        await settings_service.set_setting("scraper_cache_enabled", config.cache_enabled, category="scraper")
        await settings_service.set_setting("scraper_cache_ttl", config.cache_ttl, category="scraper")
        
        # 更新API密钥（如果提供）
        if config.tmdb_api_key:
            await settings_service.set_setting("TMDB_API_KEY", config.tmdb_api_key, category="advanced_media")
        if config.douban_api_key:
            await settings_service.set_setting("DOUBAN_API_KEY", config.douban_api_key, category="advanced_media")
        if config.acoustid_api_key:
            await settings_service.set_setting("ACOUSTID_API_KEY", config.acoustid_api_key, category="advanced_media")
        
        return success_response(message="更新刮削器配置成功")
    except Exception as e:
        logger.error(f"更新刮削器配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新刮削器配置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/test", response_model=BaseResponse)
async def test_scraper(
    scraper_type: str,  # tmdb, douban, tvdb, fanart, musicbrainz, acoustid
    test_query: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    测试刮削器连接
    
    返回统一响应格式：
    {
        "success": true,
        "message": "测试成功",
        "data": {
            "scraper_type": "...",
            "connected": true,
            "response_time_ms": 100
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        import time
        settings_service = SettingsService(db)
        
        start_time = time.time()
        connected = False
        error_message = None
        
        if scraper_type == "tmdb":
            # 测试TMDB连接
            try:
                from app.api.media import search_tmdb_movie
                tmdb_api_key = await settings_service.get_setting("TMDB_API_KEY", category="advanced_media")
                if not tmdb_api_key:
                    raise ValueError("TMDB API Key未配置")
                # 测试搜索
                test_title = test_query or "The Matrix"
                result = await search_tmdb_movie(test_title, tmdb_api_key)
                connected = result is not None and len(result) > 0
            except Exception as e:
                error_message = str(e)
                connected = False
        
        elif scraper_type == "douban":
            # 测试豆瓣连接
            try:
                from app.modules.douban.client import DoubanClient
                client = DoubanClient()
                # 测试搜索
                test_title = test_query or "肖申克的救赎"
                result = await client.search_movie(test_title)
                connected = result is not None
            except Exception as e:
                error_message = str(e)
                connected = False
        
        elif scraper_type == "tvdb":
            # 测试TVDB连接
            try:
                from app.modules.thetvdb.tvdb_v4_official import TVDB
                from app.core.api_key_manager import get_api_key_manager
                api_key_manager = get_api_key_manager()
                tvdb_api_key = api_key_manager.get_tvdb_api_key()
                tvdb_pin = api_key_manager.get_tvdb_api_pin()
                if not tvdb_api_key:
                    raise ValueError("TVDB API Key未配置")
                client = TVDB(apikey=tvdb_api_key, pin=tvdb_pin or "")
                # 测试搜索
                test_title = test_query or "Game of Thrones"
                result = await client.search(test_title)
                connected = result is not None and len(result) > 0
            except Exception as e:
                error_message = str(e)
                connected = False
        
        elif scraper_type == "fanart":
            # 测试Fanart连接
            try:
                # Fanart可能没有独立的客户端，使用HTTP请求测试
                from app.utils.http_client import create_httpx_client
                test_tmdb_id = test_query or "603"  # The Matrix
                async with create_httpx_client(timeout=10.0, use_proxy=True) as client:
                    # 使用Fanart API测试（需要API Key）
                    from app.core.api_key_manager import get_api_key_manager
                    api_key_manager = get_api_key_manager()
                    fanart_api_key = api_key_manager.get_fanart_api_key()
                    if not fanart_api_key:
                        raise ValueError("Fanart API Key未配置")
                    url = f"https://webservice.fanart.tv/v3/movies/{test_tmdb_id}"
                    headers = {"api-key": fanart_api_key}
                    response = await client.get(url, headers=headers)
                    connected = response.status_code == 200
            except Exception as e:
                error_message = str(e)
                connected = False
        
        elif scraper_type == "musicbrainz":
            # 测试MusicBrainz连接
            try:
                import musicbrainzngs
                musicbrainzngs.set_useragent("VabHub/1.0.0", "1.0.0", "contact@vabhub.com")
                # 测试搜索
                test_query_str = test_query or "The Beatles"
                result = musicbrainzngs.search_artists(artist=test_query_str, limit=1)
                connected = result is not None
            except Exception as e:
                error_message = str(e)
                connected = False
        
        elif scraper_type == "acoustid":
            # 测试AcoustID连接
            try:
                from app.modules.music.scraper import MusicScraper
                acoustid_api_key = await settings_service.get_setting("ACOUSTID_API_KEY", category="advanced_media")
                scraper = MusicScraper(acoustid_api_key=acoustid_api_key)
                # AcoustID需要音频文件，这里只测试初始化
                connected = scraper is not None
            except Exception as e:
                error_message = str(e)
                connected = False
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="INVALID_SCRAPER_TYPE",
                    error_message=f"不支持的刮削器类型: {scraper_type}"
                ).model_dump()
            )
        
        response_time = int((time.time() - start_time) * 1000)
        
        if not connected:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="SCRAPER_TEST_FAILED",
                    error_message=f"刮削器测试失败: {error_message or '未知错误'}"
                ).model_dump()
            )
        
        return success_response(
            data={
                "scraper_type": scraper_type,
                "connected": connected,
                "response_time_ms": response_time
            },
            message="刮削器测试成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试刮削器失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"测试刮削器时发生错误: {str(e)}"
            ).model_dump()
        )

