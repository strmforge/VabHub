"""
Bangumi API客户端
用于获取动漫推荐和探索数据
"""

import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger
from app.core.cache import get_cache
from app.utils.http_client import create_httpx_client


class BangumiClient:
    """Bangumi API客户端"""
    
    BASE_URL = "https://api.bgm.tv"
    
    def __init__(self):
        self.cache = get_cache()
        self.timeout = 30.0
    
    async def search_subject(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        搜索动漫主题
        
        Args:
            query: 搜索关键词
            limit: 返回数量限制
        
        Returns:
            搜索结果列表
        """
        try:
            # 生成缓存键
            cache_key = self.cache.generate_key("bangumi_search", query=query, limit=limit)
            
            # 尝试从缓存获取
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"从缓存获取Bangumi搜索结果: {query}")
                return cached_result
            
            # 构建请求URL
            url = f"{self.BASE_URL}/search/subject/{query}"
            params = {
                "limit": limit,
                "type": 2  # 2 = 动画
            }
            
            # 发送请求
            async with create_httpx_client(timeout=self.timeout, use_proxy=False) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            # 解析结果
            results = []
            items = data.get("list", [])
            for item in items[:limit]:
                result = {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "name_cn": item.get("name_cn") or item.get("name"),
                    "type": item.get("type"),
                    "summary": item.get("summary", ""),
                    "date": item.get("date"),
                    "images": item.get("images", {}),
                    "rating": item.get("rating", {}),
                    "tags": item.get("tags", []),
                    "url": f"https://bgm.tv/subject/{item.get('id')}"
                }
                results.append(result)
            
            # 缓存结果（1小时）
            await self.cache.set(cache_key, results, ttl=3600)
            
            return results
            
        except Exception as e:
            logger.error(f"Bangumi搜索失败: {e}")
            return []
    
    async def get_subject_detail(self, subject_id: int) -> Optional[Dict[str, Any]]:
        """
        获取动漫主题详情
        
        Args:
            subject_id: 主题ID
        
        Returns:
            主题详情
        """
        try:
            # 生成缓存键
            cache_key = self.cache.generate_key("bangumi_subject", subject_id=subject_id)
            
            # 尝试从缓存获取
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"从缓存获取Bangumi主题详情: {subject_id}")
                return cached_result
            
            # 构建请求URL
            url = f"{self.BASE_URL}/v0/subjects/{subject_id}"
            
            # 发送请求
            async with create_httpx_client(timeout=self.timeout, use_proxy=False) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            # 格式化结果
            result = {
                "id": data.get("id"),
                "name": data.get("name"),
                "name_cn": data.get("name_cn") or data.get("name"),
                "type": data.get("type"),
                "summary": data.get("summary", ""),
                "date": data.get("date"),
                "images": data.get("images", {}),
                "rating": data.get("rating", {}),
                "tags": data.get("tags", []),
                "platform": data.get("platform", []),
                "infobox": data.get("infobox", []),
                "eps": data.get("eps", 0),  # 集数
                "characters": data.get("characters", []),  # 角色信息（如果有）
                "url": f"https://bgm.tv/subject/{data.get('id')}"
            }
            
            # 缓存结果（24小时）
            await self.cache.set(cache_key, result, ttl=86400)
            
            return result
            
        except Exception as e:
            logger.error(f"获取Bangumi主题详情失败: {e}")
            return None
    
    async def get_calendar(self) -> List[Dict[str, Any]]:
        """
        获取每日放送日历
        
        Returns:
            每日放送列表
        """
        try:
            # 生成缓存键（按日期）
            today = datetime.now().strftime("%Y-%m-%d")
            cache_key = self.cache.generate_key("bangumi_calendar", date=today)
            
            # 尝试从缓存获取
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                logger.debug("从缓存获取Bangumi日历")
                return cached_result
            
            # 构建请求URL
            url = f"{self.BASE_URL}/calendar"
            
            # 发送请求
            async with create_httpx_client(timeout=self.timeout, use_proxy=False) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            # 解析结果
            results = []
            for weekday_data in data:
                weekday_info = weekday_data.get("weekday", {})
                weekday_id = weekday_info.get("id", 0)
                weekday_cn = weekday_info.get("cn", "")
                items = weekday_data.get("items", [])
                for item in items:
                    result = {
                        "id": item.get("id"),
                        "name": item.get("name"),
                        "name_cn": item.get("name_cn") or item.get("name"),
                        "summary": item.get("summary", ""),
                        "images": item.get("images", {}),
                        "rating": item.get("rating", {}),
                        "weekday": weekday_id,  # 返回星期ID，前端可以根据ID分组
                        "url": f"https://bgm.tv/subject/{item.get('id')}"
                    }
                    results.append(result)
            
            # 缓存结果（1小时）
            await self.cache.set(cache_key, results, ttl=3600)
            
            return results
            
        except Exception as e:
            logger.error(f"获取Bangumi日历失败: {e}")
            return []
    
    async def get_popular_anime(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取热门动漫
        
        Args:
            limit: 返回数量限制
        
        Returns:
            热门动漫列表
        """
        try:
            # 生成缓存键
            cache_key = self.cache.generate_key("bangumi_popular", limit=limit)
            
            # 尝试从缓存获取
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                logger.debug("从缓存获取Bangumi热门动漫")
                return cached_result
            
            # 构建请求URL（使用搜索API，按评分排序）
            url = f"{self.BASE_URL}/search/subject/动画"
            params = {
                "limit": limit,
                "type": 2,  # 2 = 动画
                "sort": "rank"  # 按排名排序
            }
            
            # 发送请求
            async with create_httpx_client(timeout=self.timeout, use_proxy=False) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            # 解析结果
            results = []
            items = data.get("list", [])
            for item in items[:limit]:
                result = {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "name_cn": item.get("name_cn") or item.get("name"),
                    "summary": item.get("summary", ""),
                    "images": item.get("images", {}),
                    "rating": item.get("rating", {}),
                    "tags": item.get("tags", []),
                    "url": f"https://bgm.tv/subject/{item.get('id')}"
                }
                results.append(result)
            
            # 缓存结果（6小时）
            await self.cache.set(cache_key, results, ttl=21600)
            
            return results
            
        except Exception as e:
            logger.error(f"获取Bangumi热门动漫失败: {e}")
            return []

