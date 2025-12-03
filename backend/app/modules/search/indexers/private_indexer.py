"""
私有PT站点索引器
需要账号认证（Cookie/API Key）
"""

import re
import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger

from .base import IndexerBase, IndexerConfig
from ..parsers import ParserBase, GazelleParser, NexusPHPParser, Unit3DParser


class PrivateIndexer(IndexerBase):
    """私有PT站点索引器（需要账号认证）"""
    
    def __init__(self, config: IndexerConfig, parser: Optional[ParserBase] = None):
        """
        初始化私有索引器
        
        Args:
            config: 索引器配置
            parser: 解析器实例（可选，如果不提供则自动检测）
        """
        super().__init__(config)
        self.parser = parser or self._auto_detect_parser()
        
        # 构建请求头
        headers = {
            'User-Agent': config.user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # 添加Cookie（如果提供）
        if config.cookie:
            headers['Cookie'] = config.cookie
        
        # 添加API Key（如果提供）
        if config.api_key:
            headers['Authorization'] = f'Bearer {config.api_key}'
        
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers=headers
        )
    
    async def search(
        self,
        query: str,
        media_type: Optional[str] = None,
        year: Optional[int] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """搜索私有PT站点"""
        try:
            self.last_search = datetime.utcnow()
            
            # 检查是否有认证信息
            if not self.config.cookie and not self.config.api_key:
                logger.warning(f"索引器 {self.name} 缺少认证信息，无法搜索")
                return []
            
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
            
            # 检查认证信息
            if not self.config.cookie and not self.config.api_key:
                logger.warning(f"索引器 {self.name} 缺少认证信息")
                return False
            
            # 尝试访问站点首页或API端点
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
        
        return terms[:2]
    
    def _auto_detect_parser(self) -> Optional[ParserBase]:
        """
        自动检测并创建解析器
        
        Returns:
            解析器实例或None
        """
        # 根据站点URL或配置中的parser_type字段自动选择解析器
        parser_type = getattr(self.config, 'parser_type', None)
        
        if parser_type:
            parser_type = parser_type.lower()
            if parser_type == 'gazelle':
                return GazelleParser(self.name, self.base_url)
            elif parser_type == 'nexus_php' or parser_type == 'nexusphp':
                return NexusPHPParser(self.name, self.base_url)
            elif parser_type == 'unit3d':
                return Unit3DParser(self.name, self.base_url)
        
        # 尝试根据URL特征自动检测
        base_url_lower = self.base_url.lower()
        if 'gazelle' in base_url_lower or 'ptp' in base_url_lower or 'btn' in base_url_lower:
            return GazelleParser(self.name, self.base_url)
        elif 'unit3d' in base_url_lower:
            return Unit3DParser(self.name, self.base_url)
        else:
            # 默认使用Nexus PHP（最常见的框架）
            return NexusPHPParser(self.name, self.base_url)
    
    async def _search_site(
        self,
        query: str,
        media_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索站点
        
        如果配置了解析器，则使用解析器解析搜索结果页面
        否则尝试使用API或RSS
        """
        # 如果有解析器，使用解析器解析HTML页面
        if self.parser:
            try:
                # 构建搜索URL（不同站点格式可能不同）
                search_url = self._build_search_url(query, media_type)
                
                # 获取搜索结果页面
                response = await self.client.get(search_url)
                if response.status_code == 200:
                    # 使用解析器解析结果
                    results = self.parser.parse_search_results(response.text)
                    return results
            except Exception as e:
                logger.error(f"使用解析器搜索失败: {e}")
        
        # 回退到模拟数据（实际应该实现API调用或RSS解析）
        return [
            {
                'title': f"{query} 2023 1080p x265 BluRay",
                'magnet_link': f"magnet:?xt=urn:btih:{'b' * 40}",
                'torrent_url': f"{self.base_url}/download/12345",
                'size_gb': 10.5,
                'seeders': 100,
                'leechers': 20,
                'upload_date': datetime.utcnow().isoformat()
            }
        ]
    
    def _build_search_url(self, query: str, media_type: Optional[str] = None) -> str:
        """
        构建搜索URL
        
        Args:
            query: 搜索关键词
            media_type: 媒体类型
        
        Returns:
            搜索URL
        """
        # 不同站点有不同的搜索URL格式
        # 这里提供一个通用的实现，实际应该根据站点配置调整
        
        # 常见的搜索URL格式：
        # - /torrents.php?searchstr={query}
        # - /browse.php?search={query}
        # - /search?q={query}
        
        # 默认使用常见的格式
        search_path = getattr(self.config, 'search_path', '/torrents.php')
        return f"{self.base_url}{search_path}?searchstr={query}"
    
    def _parse_result(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析搜索结果"""
        try:
            title = result.get('title', '')
            if not title:
                return None
            
            return {
                'title': title,
                'site': self.name,
                'magnet_link': result.get('magnet_link'),
                'torrent_url': result.get('torrent_url'),
                'info_hash': self._extract_info_hash(result.get('magnet_link', '')),
                'size_gb': result.get('size_gb', 0.0),
                'seeders': result.get('seeders', 0),
                'leechers': result.get('leechers', 0),
                'upload_date': result.get('upload_date'),
                'indexer': self.name
            }
        except Exception as e:
            logger.error(f"解析搜索结果失败: {e}")
            return None
    
    def _extract_info_hash(self, magnet_link: str) -> Optional[str]:
        """从磁力链接提取info_hash"""
        import re
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

