"""
Fanart模块
用于获取Fanart.tv图片资源
使用内置API Key，无需用户配置
使用内置API Key，无需用户配置
"""
import re
from typing import Optional, Dict, Any, Union, List
from loguru import logger

from app.core.config import settings
from app.core.cache import get_cache
from app.utils.http_client import create_httpx_client


class FanartModule:
    """
    Fanart图片获取模块
    使用内置API Key，无需用户配置
    """
    
    # Fanart API URL模板
    _movie_url: str = 'https://webservice.fanart.tv/v3/movies/%s?api_key={api_key}'
    _tv_url: str = 'https://webservice.fanart.tv/v3/tv/%s?api_key={api_key}'
    
    def __init__(self):
        """初始化Fanart模块"""
        self.cache = get_cache()
        # 使用加密存储的API Key（优先从加密存储读取）
        self.api_key = settings.FANART_API_KEY
    
    async def obtain_images(
        self, 
        media_type: str, 
        tmdb_id: Optional[int] = None, 
        tvdb_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取Fanart图片（异步）
        
        Args:
            media_type: 媒体类型（movie/tv）
            tmdb_id: TMDB ID（电影必需，电视剧可选）
            tvdb_id: TVDB ID（电视剧必需）
            
        Returns:
            Fanart图片数据字典，失败返回None
        """
        if not settings.FANART_ENABLE:
            logger.debug("Fanart功能未启用")
            return None
        
        if not tmdb_id and not tvdb_id:
            logger.debug("缺少TMDB ID和TVDB ID，无法获取Fanart图片")
            return None
        
        # 电影：使用TMDB ID
        if media_type == "movie":
            if not tmdb_id:
                logger.debug("电影类型需要TMDB ID")
                return None
            result = await self._request_fanart(media_type, tmdb_id)
        # 电视剧：优先使用TVDB ID
        else:
            if tvdb_id:
                result = await self._request_fanart(media_type, tvdb_id)
            else:
                logger.info(f"电视剧类型缺少TVDB ID，无法获取Fanart图片")
                return None
        
        if not result or result.get('status') == 'error':
            logger.warning(f"没有获取到Fanart图片数据")
            return None
        
        return result
    
    async def _request_fanart(
        self, 
        media_type: str, 
        query_id: Union[str, int]
    ) -> Optional[Dict[str, Any]]:
        """
        请求Fanart API（异步，带缓存）
        
        Args:
            media_type: 媒体类型（movie/tv）
            query_id: 查询ID（TMDB ID或TVDB ID）
            
        Returns:
            Fanart API响应数据，失败返回None
        """
        # 生成缓存键
        cache_key = self.cache.generate_key("fanart", media_type=media_type, query_id=query_id)
        
        # 尝试从缓存获取
        cached_result = await self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # 构建URL
        if media_type == "movie":
            image_url = self._movie_url % str(query_id)
        else:
            image_url = self._tv_url % str(query_id)
        
        image_url = image_url.format(api_key=self.api_key)
        
        try:
            # 使用httpx异步请求（支持代理）
            async with create_httpx_client(timeout=10.0, use_proxy=True) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                result = response.json()
                
                # 缓存结果（24小时）
                await self.cache.set(cache_key, result, ttl=86400)
                return result
        except Exception as err:
            logger.error(f"获取{query_id}的Fanart图片失败：{str(err)}")
            # 不缓存错误结果，允许重试
            return None
    
    @staticmethod
    def _name(fanart_name: str) -> str:
        """
        转换Fanart图片的名字（移除tv/movie/hd等前缀）
        
        Args:
            fanart_name: Fanart图片名称
            
        Returns:
            转换后的名称
        """
        words_to_remove = r'tv|movie|hdmovie|hdtv|show|hd'
        pattern = re.compile(words_to_remove, re.IGNORECASE)
        result = re.sub(pattern, '', fanart_name)
        return result
    
    async def test(self) -> tuple[bool, str]:
        """
        测试模块连接性（异步）
        
        Returns:
            (是否成功, 错误信息)
        """
        try:
            async with create_httpx_client(timeout=10.0, use_proxy=True) as client:
                response = await client.get("https://webservice.fanart.tv")
                if response.status_code == 200:
                    return True, ""
                else:
                    return False, f"无法连接fanart，错误码：{response.status_code}"
        except Exception as e:
            return False, f"fanart网络连接失败: {str(e)}"

