"""
音乐榜单聚合服务

提供音乐首页榜单/推荐数据，支持 RSSHub 和本地榜单源

Created: 0.0.3 DISCOVER-MUSIC-HOME P4
"""

import asyncio
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from loguru import logger

from app.core.cache import get_cache
from app.core.config import settings


class MusicChartItem(BaseModel):
    """音乐榜单项"""
    id: str
    title: str
    artist: Optional[str] = None
    album: Optional[str] = None
    cover_url: Optional[str] = None
    rank: Optional[int] = None
    external_url: Optional[str] = None
    source: str  # netease / qq / spotify / billboard 等


class MusicChartSection(BaseModel):
    """音乐榜单区块"""
    id: str
    title: str
    source: str  # rsshub/netease, rsshub/qq, local 等
    items: List[MusicChartItem] = Field(default_factory=list)
    error: Optional[str] = None
    description: Optional[str] = None


class MusicHomeResponse(BaseModel):
    """音乐首页响应"""
    sections: List[MusicChartSection] = Field(default_factory=list)
    has_rsshub: bool = False
    has_local_charts: bool = False
    message: Optional[str] = None


class MusicDiscoverService:
    """音乐榜单聚合服务"""
    
    def __init__(self):
        self.cache = get_cache()
        self.timeout = 15.0
    
    async def get_home(self) -> MusicHomeResponse:
        """
        获取音乐首页内容
        
        聚合 RSSHub 榜单和本地配置的榜单源
        """
        sections: List[MusicChartSection] = []
        has_rsshub = False
        has_local_charts = False
        
        # 检查 RSSHub 是否可用
        rsshub_enabled = getattr(settings, 'RSSHUB_ENABLED', False)
        rsshub_base = getattr(settings, 'RSSHUB_BASE_URL', 'https://rsshub.app')
        
        if rsshub_enabled and rsshub_base:
            has_rsshub = True
            # 并行获取各榜单
            tasks = [
                self._fetch_netease_hot(rsshub_base),
                self._fetch_qq_hot(rsshub_base),
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"音乐榜单获取失败: {result}")
                    continue
                if result:
                    sections.append(result)
        
        # 检查本地榜单配置
        try:
            local_sections = await self._fetch_local_charts()
            if local_sections:
                has_local_charts = True
                sections.extend(local_sections)
        except Exception as e:
            logger.warning(f"本地榜单获取失败: {e}")
        
        # 构建消息
        message = None
        if not sections:
            if not rsshub_enabled:
                message = "RSSHub 未启用，请在设置中配置 RSSHub 源以获取音乐榜单"
            else:
                message = "暂无可用的音乐榜单数据"
        
        return MusicHomeResponse(
            sections=sections,
            has_rsshub=has_rsshub,
            has_local_charts=has_local_charts,
            message=message,
        )
    
    async def _fetch_netease_hot(self, rsshub_base: str) -> Optional[MusicChartSection]:
        """获取网易云音乐热歌榜"""
        cache_key = self.cache.generate_key("music_netease_hot")
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return MusicChartSection(**cached)
        
        try:
            from app.utils.http_client import create_httpx_client
            # 网易云热歌榜 RSSHub 路由
            url = f"{rsshub_base}/netease/playlist/3778678"
            
            async with create_httpx_client(timeout=self.timeout, use_proxy=False) as client:
                response = await client.get(url, headers={"Accept": "application/json"})
                response.raise_for_status()
                
                # RSSHub 返回 RSS XML，需要解析
                # 这里简化处理，返回示例数据
                # 实际应解析 RSS XML
                
            # 由于 RSSHub 返回 XML，这里返回一个示例结构
            # 实际实现需要解析 RSS XML
            section = MusicChartSection(
                id="netease_hot",
                title="网易云热歌榜",
                source="rsshub/netease",
                description="来自 RSSHub 的网易云音乐热歌榜",
                items=[],  # 实际需要解析 RSS
            )
            
            # 缓存 1 小时
            await self.cache.set(cache_key, section.model_dump(), ttl=3600)
            return section
            
        except Exception as e:
            logger.warning(f"网易云热歌榜获取失败: {e}")
            return MusicChartSection(
                id="netease_hot",
                title="网易云热歌榜",
                source="rsshub/netease",
                items=[],
                error="网易云榜单暂时不可用",
            )
    
    async def _fetch_qq_hot(self, rsshub_base: str) -> Optional[MusicChartSection]:
        """获取 QQ 音乐热歌榜"""
        cache_key = self.cache.generate_key("music_qq_hot")
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return MusicChartSection(**cached)
        
        try:
            # QQ 音乐榜单 RSSHub 路由
            # 实际实现需要根据 RSSHub 文档配置正确的路由
            
            section = MusicChartSection(
                id="qq_hot",
                title="QQ 音乐热歌榜",
                source="rsshub/qq",
                description="来自 RSSHub 的 QQ 音乐热歌榜",
                items=[],  # 实际需要解析 RSS
            )
            
            await self.cache.set(cache_key, section.model_dump(), ttl=3600)
            return section
            
        except Exception as e:
            logger.warning(f"QQ 音乐热歌榜获取失败: {e}")
            return MusicChartSection(
                id="qq_hot",
                title="QQ 音乐热歌榜",
                source="rsshub/qq",
                items=[],
                error="QQ 音乐榜单暂时不可用",
            )
    
    async def _fetch_local_charts(self) -> List[MusicChartSection]:
        """获取本地配置的榜单"""
        sections = []
        
        try:
            # 查询数据库中的榜单配置
            from app.core.database import async_session_maker
            from sqlalchemy import select, text
            
            # 检查是否有榜单表
            # 这里简化处理，实际需要查询 music_charts 表
            
            # 返回空列表，让前端显示引导信息
            return sections
            
        except Exception as e:
            logger.debug(f"本地榜单查询跳过: {e}")
            return sections


# 全局服务实例
_music_discover_service: Optional[MusicDiscoverService] = None


def get_music_discover_service() -> MusicDiscoverService:
    """获取音乐榜单聚合服务实例"""
    global _music_discover_service
    if _music_discover_service is None:
        _music_discover_service = MusicDiscoverService()
    return _music_discover_service
