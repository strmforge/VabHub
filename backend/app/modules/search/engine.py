"""
搜索引擎
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.constants.media_types import MEDIA_TYPE_ANIME, MEDIA_TYPE_MOVIE, MEDIA_TYPE_EBOOK, is_tv_like


class SearchEngine:
    """搜索引擎"""
    
    def __init__(self):
        # 模拟的站点列表
        self.sites = ["站点A", "站点B", "站点C", "站点D"]
        # 质量选项
        self.qualities = ["4K", "1080p", "720p", "480p"]
        # 分辨率选项
        self.resolutions = ["2160p", "1080p", "720p", "480p"]
    
    async def search(
        self,
        query: str,
        media_type: Optional[str] = None,
        year: Optional[int] = None,
        quality: Optional[str] = None,
        resolution: Optional[str] = None,
        min_size: Optional[float] = None,
        max_size: Optional[float] = None,
        min_seeders: Optional[int] = None,
        max_seeders: Optional[int] = None,
        include: Optional[str] = None,
        exclude: Optional[str] = None,
        sites: Optional[List[str]] = None,
        language: Optional[str] = None,
        category: Optional[str] = None,
        encoding: Optional[str] = None,
        source: Optional[str] = None
    ) -> List[Dict]:
        """
        执行搜索
        
        当前实现：返回模拟数据，用于测试和演示
        后续可以接入真实的PT站点API
        """
        # 模拟搜索延迟
        await asyncio.sleep(0.5)
        
        # 生成模拟搜索结果
        results = []
        num_results = random.randint(5, 20)
        
        # 如果指定了站点，使用指定站点；否则使用所有站点
        search_sites = sites if sites else self.sites
        
        for i in range(num_results):
            # 随机选择一个站点
            site = random.choice(search_sites)
            
            # 生成标题（基于查询关键词）
            title = f"{query} - {self._generate_title_suffix(media_type)}"
            
            # 生成质量信息
            result_quality = quality if quality else random.choice(self.qualities)
            result_resolution = resolution if resolution else random.choice(self.resolutions)
            
            # 生成大小（GB）- 电子书通常较小
            if media_type == MEDIA_TYPE_EBOOK:
                size_gb = round(random.uniform(0.01, 0.5), 3)  # 电子书通常 10MB - 500MB
            else:
                size_gb = round(random.uniform(1.0, 50.0), 2)
            
            # 应用大小过滤
            if min_size and size_gb < min_size:
                continue
            if max_size and size_gb > max_size:
                continue
            
            # 生成做种信息
            seeders = random.randint(0, 1000)
            leechers = random.randint(0, 500)
            
            # 应用做种过滤
            if min_seeders and seeders < min_seeders:
                continue
            if max_seeders and seeders > max_seeders:
                continue
            
            # 应用包含/排除关键词过滤
            if include and include.lower() not in title.lower():
                continue
            if exclude and exclude.lower() in title.lower():
                continue
            
            # 应用多维度筛选
            if language and language.lower() not in title.lower():
                continue
            if category and category.lower() not in title.lower():
                continue
            if encoding and encoding.lower() not in title.lower():
                continue
            if source and source.lower() not in title.lower():
                continue
            
            # 生成上传日期（最近30天内）
            upload_date = datetime.now() - timedelta(days=random.randint(0, 30))
            
            # 生成磁力链接（模拟）
            magnet_link = f"magnet:?xt=urn:btih:{self._generate_hash()}"
            
            # 生成语言和分类（模拟）
            if media_type == MEDIA_TYPE_EBOOK:
                result_language = language if language else random.choice(["中文", "英文", "日文", "韩文"])
                result_category = category if category else random.choice(["电子书", "小说", "技术", "文学"])
                result_encoding = None  # 电子书不需要编码格式
                result_source = None  # 电子书不需要来源格式
            else:
                result_language = language if language else random.choice(["中文", "英文", "日文", "韩文"])
                result_category = category if category else random.choice(["电影", "剧集", "动漫", "纪录片"])
                result_encoding = encoding if encoding else random.choice(["H.264", "H.265", "AV1"])
                result_source = source if source else random.choice(["BluRay", "WEB-DL", "HDTV", "DVD"])
            
            result = {
                "title": title,
                "site": site,
                "magnet_link": magnet_link,
                "torrent_url": f"https://{site.lower()}.com/torrent/{i+1}",
                "size_gb": size_gb,
                "seeders": seeders,
                "leechers": leechers,
                "resolution": result_resolution,
                "quality": result_quality,
                "upload_date": upload_date.isoformat(),
                "category": result_category,
                "language": result_language,
                "encoding": result_encoding,
                "source": result_source
            }
            
            results.append(result)
        
        # 注意：排序现在由服务层处理，这里不再排序
        
        return results
    
    def _generate_title_suffix(self, media_type: Optional[str]) -> str:
        """生成标题后缀"""
        if media_type == MEDIA_TYPE_MOVIE:
            suffixes = ["BluRay", "WEB-DL", "DVDRip", "BDRip"]
        elif is_tv_like(media_type):
            suffixes = ["S01E01", "Complete", "Season 1", "WEB-DL"]
        elif media_type == MEDIA_TYPE_ANIME:
            suffixes = ["Episode 01", "Complete", "BD", "WEB"]
        elif media_type == MEDIA_TYPE_EBOOK:
            suffixes = ["EPUB", "PDF", "MOBI", "AZW3", "Complete Collection"]
        else:
            suffixes = ["BluRay", "WEB-DL", "DVDRip", "BDRip", "Complete"]
        
        return random.choice(suffixes)
    
    def _generate_hash(self) -> str:
        """生成随机哈希（用于磁力链接）"""
        import string
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(40))

