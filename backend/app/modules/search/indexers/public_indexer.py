"""
公开站点索引器
支持1337x、Nyaa、YTS等公开站点
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from app.constants.media_types import MEDIA_TYPE_MOVIE, is_tv_like
from .base import IndexerBase, IndexerConfig


class PublicIndexer(IndexerBase):
    """公开站点索引器（不需要账号）"""
    
    def __init__(self, config: IndexerConfig):
        super().__init__(config)
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={
                'User-Agent': config.user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
    
    async def search(
        self,
        query: str,
        media_type: Optional[str] = None,
        year: Optional[int] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """搜索公开站点"""
        try:
            self.last_search = datetime.utcnow()
            
            # 构建搜索关键词
            search_terms = self._build_search_terms(query, media_type, year)
            
            results = []
            for term in search_terms:
                site_results = await self._search_site(term, media_type)
                results.extend(site_results)
            
            # 解析和清理结果
            parsed_results = []
            for result in results:
                parsed_result = self._parse_result(result)
                if parsed_result:
                    parsed_results.append(parsed_result)
            
            logger.info(f"索引器 {self.name} 搜索完成: {len(parsed_results)} 个结果")
            self.reset_errors()
            return parsed_results
            
        except Exception as e:
            logger.error(f"索引器 {self.name} 搜索失败: {e}")
            self.record_error()
            return []
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            self.last_check = datetime.utcnow()
            
            # 简单的连接测试
            response = await self.client.get(
                self.base_url,
                timeout=5.0
            )
            
            is_healthy = response.status_code == 200
            if is_healthy:
                self.reset_errors()
            else:
                self.record_error()
            
            return is_healthy
        except Exception as e:
            logger.error(f"索引器 {self.name} 健康检查失败: {e}")
            self.record_error()
            return False
    
    def _build_search_terms(
        self,
        query: str,
        media_type: Optional[str] = None,
        year: Optional[int] = None
    ) -> List[str]:
        """构建搜索关键词"""
        terms = [query]
        
        if year:
            terms.append(f"{query} {year}")
        
        if media_type:
            normalized = media_type.lower()
            if is_tv_like(normalized):
                terms.append(f"{query} season")
            elif normalized == MEDIA_TYPE_MOVIE:
                terms.append(f"{query} movie")
        
        return terms[:3]  # 限制搜索词数量
    
    async def _search_site(
        self,
        query: str,
        media_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """搜索站点（具体实现由子类或根据站点类型决定）"""
        # 这里先返回模拟数据
        # 实际实现需要根据具体站点进行网页爬虫或API调用
        
        # 1337x: 通过网页爬虫
        # Nyaa: 通过RSS或网页爬虫
        # YTS: 通过API
        
        # 模拟搜索结果
        return [
            {
                'title': f"{query} 2023 1080p x265 BluRay",
                'magnet_link': f"magnet:?xt=urn:btih:{'a' * 40}",
                'size_gb': 8.5,
                'seeders': 50,
                'leechers': 10,
                'upload_date': datetime.utcnow().isoformat()
            }
        ]
    
    def _parse_result(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析搜索结果"""
        try:
            title = result.get('title', '')
            if not title:
                return None
            
            # 解析标题中的质量信息
            quality_info = self._parse_title_quality(title)
            
            return {
                'title': title,
                'site': self.name,
                'magnet_link': result.get('magnet_link'),
                'torrent_url': result.get('torrent_url'),
                'info_hash': self._extract_info_hash(result.get('magnet_link', '')),
                'size_gb': result.get('size_gb', 0.0),
                'seeders': result.get('seeders', 0),
                'leechers': result.get('leechers', 0),
                'resolution': quality_info.get('resolution'),
                'quality': quality_info.get('quality'),
                'encoding': quality_info.get('codec'),
                'source': quality_info.get('source'),
                'category': quality_info.get('category'),
                'language': quality_info.get('language'),
                'upload_date': result.get('upload_date'),
                'indexer': self.name
            }
        except Exception as e:
            logger.error(f"解析搜索结果失败: {e}")
            return None
    
    def _parse_title_quality(self, title: str) -> Dict[str, Optional[str]]:
        """从标题解析质量信息"""
        quality_info = {
            'resolution': None,
            'quality': None,
            'codec': None,
            'source': None,
            'category': None,
            'language': None
        }
        
        title_upper = title.upper()
        
        # 解析分辨率
        resolution_patterns = [
            r'(\d{3,4}P)', r'(4K)', r'(UHD)', r'(FHD)', r'(HD)'
        ]
        for pattern in resolution_patterns:
            match = re.search(pattern, title_upper)
            if match:
                quality_info['resolution'] = match.group(1)
                quality_info['quality'] = match.group(1)
                break
        
        # 解析编码
        codec_patterns = [
            r'(X265)', r'(X264)', r'(H\.?265)', r'(H\.?264)', r'(HEVC)', r'(AVC)'
        ]
        for pattern in codec_patterns:
            match = re.search(pattern, title_upper)
            if match:
                quality_info['codec'] = match.group(1).replace('.', '')
                break
        
        # 解析来源
        source_patterns = [
            r'(BLURAY)', r'(BLU-RAY)', r'(BDMV)', r'(WEB-DL)', r'(WEBRIP)', 
            r'(HDTV)', r'(PDTV)', r'(DVDRIP)', r'(CAM)', r'(TS)', r'(TC)'
        ]
        for pattern in source_patterns:
            match = re.search(pattern, title_upper)
            if match:
                quality_info['source'] = match.group(1).replace('-', '')
                break
        
        # 解析语言
        if any(lang in title_upper for lang in ['中文', 'CHINESE', 'CHN', 'CHS', 'CHT']):
            quality_info['language'] = 'zh'
        elif any(lang in title_upper for lang in ['ENGLISH', 'ENG']):
            quality_info['language'] = 'en'
        
        return quality_info
    
    def _extract_info_hash(self, magnet_link: str) -> Optional[str]:
        """从磁力链接提取info_hash"""
        if not magnet_link:
            return None
        
        match = re.search(r'btih:([a-fA-F0-9]{40})', magnet_link)
        if match:
            return match.group(1).lower()
        
        return None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

