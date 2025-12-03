"""
音乐 PT 搜索服务

提供音乐专用的 PT 站点搜索功能，整合 External Indexer。
支持从 MusicChartItem 或自定义查询搜索种子，并进行质量评分。

使用方式：
    from app.services.music_indexer_service import MusicIndexerService
    
    service = MusicIndexerService()
    candidates = await service.search_for_chart_item(session, chart_item)
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from loguru import logger
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.music_chart_item import MusicChartItem


class MusicTorrentCandidate(BaseModel):
    """
    音乐种子候选结果
    
    从 PT 站点搜索返回的候选种子信息
    """
    source: str  # PT 站点 ID
    source_name: Optional[str] = None  # PT 站点名称
    torrent_id: str  # 种子 ID
    title: str  # 种子标题
    size_bytes: Optional[int] = None
    seeders: Optional[int] = None
    leechers: Optional[int] = None
    snatched: Optional[int] = None
    free_percent: Optional[int] = None  # 0/50/100
    is_hr: bool = False  # 是否 HR
    
    # 从标题解析的质量信息
    format_hint: Optional[str] = None  # flac/mp3/ape 等
    bitrate_hint: Optional[int] = None  # 320/256 等
    
    # 综合评分（越高越好）
    quality_score: float = 0.0
    
    # 原始数据
    raw: Dict[str, Any] = {}
    
    class Config:
        extra = "allow"


# 格式优先级（越高越好）
FORMAT_PRIORITY = {
    "flac": 100,
    "ape": 95,
    "wav": 90,
    "alac": 85,
    "aac": 70,
    "m4a": 65,
    "ogg": 60,
    "mp3": 50,
}


def _parse_format_from_title(title: str) -> Optional[str]:
    """从标题解析格式"""
    title_lower = title.lower()
    for fmt in FORMAT_PRIORITY.keys():
        if fmt in title_lower:
            return fmt
    return None


def _parse_bitrate_from_title(title: str) -> Optional[int]:
    """从标题解析比特率"""
    import re
    # 匹配 320kbps, 320k, 320 kbps 等
    match = re.search(r'(\d{2,4})\s*k(?:bps)?', title.lower())
    if match:
        return int(match.group(1))
    return None


def _calculate_quality_score(candidate: MusicTorrentCandidate) -> float:
    """
    计算种子质量评分
    
    评分因素：
    - 格式优先级（flac > mp3）
    - 比特率（越高越好）
    - 做种数（越多越好）
    - 文件大小（合理范围内越大越好，但不能太大）
    - 免费状态（免费加分）
    - HR 状态（HR 减分）
    """
    score = 0.0
    
    # 格式分数（0-100）
    if candidate.format_hint:
        score += FORMAT_PRIORITY.get(candidate.format_hint.lower(), 30)
    else:
        score += 30  # 未知格式给基础分
    
    # 比特率分数（0-50）
    if candidate.bitrate_hint:
        if candidate.bitrate_hint >= 320:
            score += 50
        elif candidate.bitrate_hint >= 256:
            score += 40
        elif candidate.bitrate_hint >= 192:
            score += 30
        else:
            score += 20
    
    # 做种数分数（0-30）
    if candidate.seeders:
        if candidate.seeders >= 50:
            score += 30
        elif candidate.seeders >= 20:
            score += 25
        elif candidate.seeders >= 10:
            score += 20
        elif candidate.seeders >= 5:
            score += 15
        elif candidate.seeders >= 1:
            score += 10
    
    # 文件大小分数（0-20）
    # 音乐文件合理范围：5MB - 500MB（单曲）或 50MB - 2GB（专辑）
    if candidate.size_bytes:
        size_mb = candidate.size_bytes / (1024 * 1024)
        if 5 <= size_mb <= 2000:
            score += 20
        elif 2 <= size_mb <= 5000:
            score += 10
    
    # 免费加分（0-20）
    if candidate.free_percent:
        score += candidate.free_percent * 0.2  # 100% 免费 = +20
    
    # HR 减分
    if candidate.is_hr:
        score -= 30
    
    return round(score, 2)


class MusicIndexerService:
    """
    音乐 PT 搜索服务
    
    整合 External Indexer，提供音乐专用的搜索和评分功能
    """
    
    def __init__(self):
        self._search_provider = None
    
    async def _get_search_provider(self):
        """获取搜索提供者（懒加载）"""
        if self._search_provider is None:
            try:
                from app.core.ext_indexer.registry import get_runtime
                from app.core.ext_indexer.search_provider import ExternalIndexerSearchProvider
                
                runtime = get_runtime()
                if runtime:
                    self._search_provider = ExternalIndexerSearchProvider(runtime)
                    logger.debug("音乐搜索服务已连接 External Indexer")
                else:
                    logger.warning("External Indexer 运行时未初始化")
            except Exception as e:
                logger.error(f"初始化搜索提供者失败: {e}")
        
        return self._search_provider
    
    def build_search_keywords(
        self,
        title: str,
        artist: Optional[str] = None,
        album: Optional[str] = None,
    ) -> List[str]:
        """
        构建搜索关键词列表
        
        返回多个候选关键词，按优先级排序
        """
        keywords = []
        
        # 清理函数
        def clean(s: str) -> str:
            if not s:
                return ""
            # 移除括号内容、特殊字符
            import re
            s = re.sub(r'\([^)]*\)', '', s)
            s = re.sub(r'\[[^\]]*\]', '', s)
            s = re.sub(r'[^\w\s\u4e00-\u9fff-]', ' ', s)
            return ' '.join(s.split()).strip()
        
        clean_title = clean(title)
        clean_artist = clean(artist) if artist else ""
        clean_album = clean(album) if album else ""
        
        # 优先级 1：艺术家 + 标题
        if clean_artist and clean_title:
            keywords.append(f"{clean_artist} {clean_title}")
        
        # 优先级 2：艺术家 + 专辑（如果有）
        if clean_artist and clean_album:
            keywords.append(f"{clean_artist} {clean_album}")
        
        # 优先级 3：仅标题
        if clean_title:
            keywords.append(clean_title)
        
        # 优先级 4：仅艺术家
        if clean_artist:
            keywords.append(clean_artist)
        
        return keywords
    
    async def search(
        self,
        query: str,
        *,
        sites: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[MusicTorrentCandidate]:
        """
        搜索音乐种子
        
        Args:
            query: 搜索关键词
            sites: 指定站点列表（None 表示搜索所有）
            limit: 返回结果数量限制
            
        Returns:
            候选种子列表，按质量评分排序
        """
        provider = await self._get_search_provider()
        
        if not provider:
            logger.warning("搜索提供者不可用，返回空结果")
            return []
        
        try:
            # 调用 External Indexer 搜索
            results = await provider.search(
                query=query,
                media_type="music",
                sites=sites,
            )
            
            candidates = []
            for result in results:
                # 转换为 MusicTorrentCandidate
                candidate = MusicTorrentCandidate(
                    source=result.site_id,
                    source_name=result.site_name,
                    torrent_id=result.torrent_id,
                    title=result.title,
                    size_bytes=result.size_bytes,
                    seeders=result.seeders,
                    leechers=result.leechers,
                    free_percent=result.free_percent,
                    is_hr=result.is_hr,
                    format_hint=_parse_format_from_title(result.title),
                    bitrate_hint=_parse_bitrate_from_title(result.title),
                    raw=result.raw,
                )
                
                # 计算质量评分
                candidate.quality_score = _calculate_quality_score(candidate)
                candidates.append(candidate)
            
            # 按评分排序
            candidates.sort(key=lambda x: x.quality_score, reverse=True)
            
            logger.info(f"音乐搜索 '{query}' 返回 {len(candidates)} 个候选")
            return candidates[:limit]
            
        except Exception as e:
            logger.error(f"音乐搜索失败: {e}")
            return []
    
    async def search_for_chart_item(
        self,
        session: AsyncSession,
        chart_item: MusicChartItem,
        *,
        sites: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[MusicTorrentCandidate]:
        """
        为榜单条目搜索种子
        
        会尝试多个关键词组合，合并去重后返回
        """
        keywords = self.build_search_keywords(
            title=chart_item.title,
            artist=chart_item.artist_name,
            album=chart_item.album_name,
        )
        
        if not keywords:
            logger.warning(f"无法为榜单条目 {chart_item.id} 构建搜索关键词")
            return []
        
        all_candidates: Dict[str, MusicTorrentCandidate] = {}
        
        # 尝试每个关键词
        for keyword in keywords[:3]:  # 最多尝试 3 个关键词
            candidates = await self.search(keyword, sites=sites, limit=limit)
            
            for candidate in candidates:
                # 用 site + torrent_id 去重
                key = f"{candidate.source}:{candidate.torrent_id}"
                if key not in all_candidates:
                    all_candidates[key] = candidate
                elif candidate.quality_score > all_candidates[key].quality_score:
                    all_candidates[key] = candidate
        
        # 按评分排序
        result = sorted(all_candidates.values(), key=lambda x: x.quality_score, reverse=True)
        
        logger.info(
            f"榜单条目 '{chart_item.title}' by '{chart_item.artist_name}' "
            f"搜索到 {len(result)} 个候选"
        )
        
        return result[:limit]
    
    async def get_download_link(
        self,
        site_id: str,
        torrent_id: str,
    ) -> Optional[str]:
        """
        获取种子下载链接
        
        Returns:
            下载链接（磁力链接或 .torrent URL），失败返回 None
        """
        provider = await self._get_search_provider()
        
        if not provider or not provider.runtime:
            logger.warning("搜索提供者不可用")
            return None
        
        try:
            link = await provider.runtime.get_download_link(site_id, torrent_id)
            return link
        except Exception as e:
            logger.error(f"获取下载链接失败: {e}")
            return None


# 单例
_music_indexer_service: Optional[MusicIndexerService] = None


def get_music_indexer_service() -> MusicIndexerService:
    """获取音乐搜索服务单例"""
    global _music_indexer_service
    if _music_indexer_service is None:
        _music_indexer_service = MusicIndexerService()
    return _music_indexer_service
