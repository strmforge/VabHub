"""
豆瓣API客户端
"""

import base64
import hashlib
import hmac
import time
import random
from typing import Optional, Dict, List, Tuple
from urllib import parse
import httpx
from loguru import logger
from datetime import datetime

from app.core.cache import get_cache
from app.core.config import settings

# 豆瓣API配置
DOUBAN_API_BASE = "https://frodo.douban.com/api/v2"
DOUBAN_API_KEY = "0dad551ec0f84ed02907ff5c42e8ec70"
DOUBAN_API_SECRET = "bf7dddc7c9cfe6f7"

# User-Agent列表
USER_AGENTS = [
    "api-client/1 com.douban.frodo/7.22.0.beta9(231) Android/23 product/Mate 40 vendor/HUAWEI model/Mate 40 brand/HUAWEI  rom/android  network/wifi  platform/AndroidPad",
    "api-client/1 com.douban.frodo/7.18.0(230) Android/22 product/MI 9 vendor/Xiaomi model/MI 9 brand/Android  rom/miui6  network/wifi  platform/mobile nd/1",
    "api-client/1 com.douban.frodo/7.1.0(205) Android/29 product/perseus vendor/Xiaomi model/Mi MIX 3  rom/miui6  network/wifi  platform/mobile nd/1"
]


class DoubanClient:
    """豆瓣API客户端"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key or DOUBAN_API_KEY
        self.api_secret = api_secret or DOUBAN_API_SECRET
        self.cache = get_cache()
        self.timeout = 30
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 1  # 重试延迟（秒）
    
    def _generate_signature(self, url: str, ts: str, method: str = "GET") -> str:
        """生成签名"""
        url_path = parse.urlparse(url).path
        raw_sign = '&'.join([method.upper(), parse.quote(url_path, safe=''), ts])
        return base64.b64encode(
            hmac.new(
                self.api_secret.encode('utf-8'),
                raw_sign.encode('utf-8'),
                hashlib.sha1
            ).digest()
        ).decode('utf-8')
    
    def _prepare_request_params(self, endpoint: str, params: Optional[Dict] = None) -> Tuple[str, Dict]:
        """准备请求URL和参数"""
        url = f"{DOUBAN_API_BASE}{endpoint}"
        
        # 准备参数
        request_params: Dict = {'apiKey': self.api_key}
        if params:
            request_params.update(params)
        
        # 生成时间戳（使用日期格式）
        from datetime import datetime
        ts = request_params.pop('_ts', datetime.now().strftime('%Y%m%d'))
        request_params.update({
            'os_rom': 'android',
            'apiKey': self.api_key,
            '_ts': ts,
            '_sig': self._generate_signature(url, ts)
        })
        
        return url, request_params
    
    async def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """发送API请求（带重试机制）"""
        import asyncio
        
        url, request_params = self._prepare_request_params(endpoint, params)
        
        # 生成缓存键
        cache_key = self.cache.generate_key("douban_api", endpoint=endpoint, params=request_params)
        
        # 尝试从缓存获取
        cached_result = await self.cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"从缓存获取豆瓣API结果: {endpoint}")
            return cached_result
        
        # 重试机制
        last_error = None
        for attempt in range(self.max_retries):
            try:
                headers = {
                    "User-Agent": random.choice(USER_AGENTS)
                }
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, headers=headers, params=request_params, follow_redirects=True)
                    response.raise_for_status()
                    result = response.json()
                    
                    # 缓存结果（2小时，增加缓存时间）
                    await self.cache.set(cache_key, result, ttl=7200)
                    return result
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    logger.warning(f"豆瓣API请求超时，重试 {attempt + 1}/{self.max_retries}: {endpoint}")
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"豆瓣API请求超时，已达最大重试次数: {endpoint}")
                    raise
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code >= 500 and attempt < self.max_retries - 1:
                    logger.warning(f"豆瓣API服务器错误，重试 {attempt + 1}/{self.max_retries}: {endpoint}, 状态码: {e.response.status_code}")
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"豆瓣API请求失败: {endpoint}, 状态码: {e.response.status_code}")
                    raise
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    logger.warning(f"豆瓣API请求失败，重试 {attempt + 1}/{self.max_retries}: {endpoint}, 错误: {e}")
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"豆瓣API请求失败，已达最大重试次数: {endpoint}, 错误: {e}")
                    raise
        
        if last_error:
            raise last_error
        else:
            raise Exception(f"豆瓣API请求失败: {endpoint}")
    
    async def search_subject(self, query: str, media_type: str = "movie") -> List[Dict]:
        """搜索主题（电影或电视剧）"""
        try:
            if media_type == "movie":
                result = await self.search_movie(query)
            else:
                result = await self.search_tv(query)
            
            return result.get("items", []) if "items" in result else result.get("subjects", [])
        except Exception as e:
            logger.error(f"搜索主题失败: {query}, 类型: {media_type}, 错误: {e}")
            return []
    
    async def get_subject_rating(self, subject_id: str, media_type: str = "movie") -> Optional[Dict]:
        """获取主题评分"""
        try:
            if media_type == "movie":
                return await self.get_movie_rating(subject_id)
            else:
                return await self.get_tv_rating(subject_id)
        except Exception as e:
            logger.error(f"获取评分失败: {subject_id}, 类型: {media_type}, 错误: {e}")
            return None
    
    async def search_movie(self, query: str, start: int = 0, count: int = 20) -> Dict:
        """搜索电影"""
        endpoint = "/search/movie"
        params = {
            "q": query,
            "start": start,
            "count": count
        }
        return await self._request(endpoint, params)
    
    async def search_tv(self, query: str, start: int = 0, count: int = 20) -> Dict:
        """搜索电视剧"""
        endpoint = "/search/tv"
        params = {
            "q": query,
            "start": start,
            "count": count
        }
        return await self._request(endpoint, params)
    
    async def get_movie_detail(self, movie_id: str) -> Dict:
        """获取电影详情"""
        endpoint = f"/movie/{movie_id}"
        return await self._request(endpoint)
    
    async def get_tv_detail(self, tv_id: str) -> Dict:
        """获取电视剧详情"""
        endpoint = f"/tv/{tv_id}"
        return await self._request(endpoint)
    
    async def get_movie_rating(self, movie_id: str) -> Dict:
        """获取电影评分"""
        endpoint = f"/movie/{movie_id}/rating"
        return await self._request(endpoint)
    
    async def get_tv_rating(self, tv_id: str) -> Dict:
        """获取电视剧评分"""
        endpoint = f"/tv/{tv_id}/rating"
        return await self._request(endpoint)
    
    async def get_movie_top250(self, start: int = 0, count: int = 20) -> Dict:
        """获取电影TOP250"""
        endpoint = "/subject_collection/movie_top250/items"
        params = {
            "start": start,
            "count": count
        }
        return await self._request(endpoint, params)
    
    async def get_movie_hot(self, start: int = 0, count: int = 20) -> Dict:
        """获取热门电影"""
        endpoint = "/subject_collection/movie_hot_gaia/items"
        params = {
            "start": start,
            "count": count
        }
        return await self._request(endpoint, params)
    
    async def get_tv_hot(self, start: int = 0, count: int = 20) -> Dict:
        """获取热门电视剧"""
        endpoint = "/subject_collection/tv_hot/items"
        params = {
            "start": start,
            "count": count
        }
        return await self._request(endpoint, params)

