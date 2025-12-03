"""
媒体信息识别器
从文件路径和文件名识别媒体信息，并查询TMDB/豆瓣获取完整信息
"""

from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
import httpx
import asyncio
from app.core.cache import get_cache
from .parser import MediaInfo, FilenameParser


class MediaIdentifier:
    """媒体信息识别器"""
    
    def __init__(self, tmdb_api_key: Optional[str] = None, max_concurrent: int = 5):
        """
        初始化识别器
        
        Args:
            tmdb_api_key: TMDB API密钥（可选）
            max_concurrent: 最大并发请求数
        """
        self.parser = FilenameParser()
        self.tmdb_api_key = tmdb_api_key
        self.tmdb_base_url = "https://api.themoviedb.org/3"
        self.max_concurrent = max_concurrent
        self.cache = get_cache()
        self.timeout = 10.0
        self.max_retries = 3
    
    async def identify(self, file_path: str) -> MediaInfo:
        """
        识别媒体文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            MediaInfo对象（包含完整信息）
        """
        file_path_obj = Path(file_path)
        filename = file_path_obj.stem  # 文件名（不含扩展名）
        
        # 先解析文件名
        media_info = self.parser.parse(filename)
        
        # 优先使用MediaIdentificationService进行完整识别（包含TVDB、Fanart等）
        try:
            from app.modules.media_identification.service import MediaIdentificationService
            from app.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as session:
                identification_service = MediaIdentificationService(session)
                identification_result = await identification_service.identify_media(
                    file_path=str(file_path),
                    file_name=file_path_obj.name
                )
                
                if identification_result and identification_result.get("success"):
                    # 更新媒体信息（包含TMDB ID、TVDB ID、IMDB ID等）
                    media_info.title = identification_result.get("title", media_info.title)
                    media_info.year = identification_result.get("year", media_info.year)
                    media_info.season = identification_result.get("season", media_info.season)
                    media_info.episode = identification_result.get("episode", media_info.episode)
                    media_info.tmdb_id = identification_result.get("tmdb_id")
                    media_info.tvdb_id = identification_result.get("tvdb_id")
                    media_info.imdb_id = identification_result.get("imdb_id")
                    media_info.overview = identification_result.get("overview")
                    media_info.poster_url = identification_result.get("poster_url")
                    media_info.backdrop_url = identification_result.get("backdrop_url")
                    
                    # 如果识别结果包含Fanart图片，优先使用Fanart图片
                    fanart_images = identification_result.get("fanart_images")
                    if fanart_images:
                        if fanart_images.get("poster") and not media_info.poster_url:
                            media_info.poster_url = fanart_images["poster"]
                        if fanart_images.get("backdrop") and not media_info.backdrop_url:
                            media_info.backdrop_url = fanart_images["backdrop"]
                    
                    logger.debug(f"使用MediaIdentificationService识别成功: {media_info.title}")
                    return media_info
        except Exception as e:
            logger.debug(f"MediaIdentificationService识别失败，回退到TMDB查询: {e}")
        
        # 如果MediaIdentificationService失败，回退到TMDB查询
        if media_info.title and media_info.year:
            try:
                tmdb_info = await self._query_tmdb(media_info)
                if tmdb_info:
                    # 更新媒体信息
                    media_info = self._merge_tmdb_info(media_info, tmdb_info)
            except Exception as e:
                logger.warning(f"查询TMDB失败: {e}")
        
        return media_info
    
    async def _query_tmdb(self, media_info: MediaInfo) -> Optional[Dict[str, Any]]:
        """
        查询TMDB获取媒体信息（带缓存和重试机制）
        
        Args:
            media_info: 基础媒体信息
            
        Returns:
            TMDB媒体信息字典
        """
        if not self.tmdb_api_key:
            logger.debug("TMDB API密钥未配置，跳过TMDB查询")
            return None
        
        # 生成缓存键
        cache_key = self.cache.generate_key(
            "tmdb_search",
            media_type=media_info.media_type,
            title=media_info.title,
            year=media_info.year
        )
        
        # 尝试从缓存获取
        cached_result = await self.cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"从缓存获取TMDB信息: {media_info.title}")
            return cached_result
        
        # 重试机制
        last_error = None
        for attempt in range(self.max_retries):
            try:
                if media_info.media_type == "movie":
                    # 查询电影
                    url = f"{self.tmdb_base_url}/search/movie"
                    params = {
                        "api_key": self.tmdb_api_key,
                        "query": media_info.title,
                        "year": media_info.year,
                        "language": "zh-CN"
                    }
                else:
                    # 查询电视剧
                    url = f"{self.tmdb_base_url}/search/tv"
                    params = {
                        "api_key": self.tmdb_api_key,
                        "query": media_info.title,
                        "first_air_date_year": media_info.year,
                        "language": "zh-CN"
                    }
                
                # 使用代理（如果配置了）
                from app.utils.http_client import create_httpx_client
                async with create_httpx_client(timeout=self.timeout, use_proxy=True) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                
                # 获取第一个结果（最匹配的）
                results = data.get("results", [])
                if results:
                    result = results[0]
                    # 缓存结果（24小时）
                    await self.cache.set(cache_key, result, ttl=86400)
                    return result
                
                return None
                
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    logger.warning(f"TMDB API请求超时，重试 {attempt + 1}/{self.max_retries}: {media_info.title}")
                    await asyncio.sleep(1 * (attempt + 1))
                else:
                    logger.error(f"TMDB API请求超时，已达最大重试次数: {media_info.title}")
                    return None
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code >= 500 and attempt < self.max_retries - 1:
                    logger.warning(f"TMDB API服务器错误，重试 {attempt + 1}/{self.max_retries}: {media_info.title}, 状态码: {e.response.status_code}")
                    await asyncio.sleep(1 * (attempt + 1))
                else:
                    logger.error(f"TMDB API请求失败: {media_info.title}, 状态码: {e.response.status_code}")
                    return None
            except Exception as e:
                last_error = e
                logger.error(f"查询TMDB失败: {media_info.title}, 错误: {e}")
                return None
        
        return None
    
    def _merge_tmdb_info(self, media_info: MediaInfo, tmdb_info: Dict[str, Any]) -> MediaInfo:
        """
        合并TMDB信息到媒体信息中
        
        Args:
            media_info: 基础媒体信息
            tmdb_info: TMDB返回的信息
            
        Returns:
            更新后的MediaInfo对象
        """
        # 更新标题（使用TMDB的标题）
        if tmdb_info.get("title") or tmdb_info.get("name"):
            media_info.title = tmdb_info.get("title") or tmdb_info.get("name")
        
        # 更新年份
        if media_info.media_type == "movie":
            release_date = tmdb_info.get("release_date", "")
        else:
            release_date = tmdb_info.get("first_air_date", "")
        
        if release_date:
            try:
                year = int(release_date.split("-")[0])
                media_info.year = year
            except (ValueError, IndexError):
                pass
        
        # 更新TMDB ID
        tmdb_id = tmdb_info.get("id")
        if tmdb_id:
            media_info.tmdb_id = tmdb_id
        
        # 更新概述
        overview = tmdb_info.get("overview")
        if overview:
            media_info.overview = overview
        
        # 更新图片URL
        poster_path = tmdb_info.get("poster_path")
        if poster_path:
            media_info.poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
        
        backdrop_path = tmdb_info.get("backdrop_path")
        if backdrop_path:
            media_info.backdrop_url = f"https://image.tmdb.org/t/p/w1280{backdrop_path}"
        
        # 对于电视剧，如果TMDB有季数和集数信息，可以更新
        # 但通常文件名中的季数和集数更准确
        
        return media_info
    
    async def identify_batch(self, file_paths: list[str]) -> list[MediaInfo]:
        """
        批量识别媒体文件（并发处理）
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            MediaInfo对象列表
        """
        # 使用信号量限制并发数
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def identify_with_semaphore(file_path: str) -> MediaInfo:
            async with semaphore:
                try:
                    return await self.identify(file_path)
                except Exception as e:
                    logger.error(f"识别文件失败: {file_path}, 错误: {e}")
                    # 即使失败也创建一个基础信息
                    filename = Path(file_path).stem
                    return self.parser.parse(filename)
        
        # 并发处理所有文件
        tasks = [identify_with_semaphore(file_path) for file_path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"识别文件失败: {file_paths[i]}, 错误: {result}")
                filename = Path(file_paths[i]).stem
                basic_info = self.parser.parse(filename)
                processed_results.append(basic_info)
            else:
                processed_results.append(result)
        
        return processed_results

    async def search_tmdb_multi(
        self,
        query: str,
        media_type: Optional[str] = None,
        year: Optional[int] = None,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        搜索TMDB多类型内容
        
        Args:
            query: 搜索关键词
            media_type: 媒体类型过滤 (movie/tv)
            year: 年份过滤
            page: 页码
            
        Returns:
            TMDB搜索结果字典
        """
        if not self.tmdb_api_key:
            logger.debug("TMDB API密钥未配置，跳过TMDB搜索")
            return {"results": [], "total_results": 0, "total_pages": 0, "page": 1}
        
        # 重试机制
        last_error = None
        for attempt in range(self.max_retries):
            try:
                if media_type:
                    # 搜索特定类型
                    if media_type == "movie":
                        url = f"{self.tmdb_base_url}/search/movie"
                        params = {
                            "api_key": self.tmdb_api_key,
                            "query": query,
                            "year": year,
                            "page": page,
                            "language": "zh-CN"
                        }
                    else:  # tv
                        url = f"{self.tmdb_base_url}/search/tv"
                        params = {
                            "api_key": self.tmdb_api_key,
                            "query": query,
                            "first_air_date_year": year,
                            "page": page,
                            "language": "zh-CN"
                        }
                else:
                    # 搜索多类型
                    url = f"{self.tmdb_base_url}/search/multi"
                    params = {
                        "api_key": self.tmdb_api_key,
                        "query": query,
                        "year": year,
                        "page": page,
                        "language": "zh-CN"
                    }
                
                # 使用代理（如果配置了）
                from app.utils.http_client import create_httpx_client
                async with create_httpx_client(timeout=self.timeout, use_proxy=True) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                
                # 为每个结果添加 media_type 字段（multi search 时需要）
                if "results" in data:
                    for result in data["results"]:
                        if "media_type" not in result:
                            # 根据 media_type 参数或结果字段推断
                            if media_type:
                                result["media_type"] = media_type
                            else:
                                # multi search 结果中 TMDB 会返回 media_type
                                pass
                
                return data
                
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    logger.warning(f"TMDB搜索请求超时，重试 {attempt + 1}/{self.max_retries}: {query}")
                    await asyncio.sleep(1 * (attempt + 1))
                else:
                    logger.error(f"TMDB搜索请求超时，已达最大重试次数: {query}")
                    raise
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code >= 500 and attempt < self.max_retries - 1:
                    logger.warning(f"TMDB搜索服务器错误，重试 {attempt + 1}/{self.max_retries}: {query}, 状态码: {e.response.status_code}")
                    await asyncio.sleep(1 * (attempt + 1))
                else:
                    logger.error(f"TMDB搜索请求失败: {query}, 状态码: {e.response.status_code}")
                    raise
            except Exception as e:
                last_error = e
                logger.error(f"TMDB搜索失败: {query}, 错误: {e}")
                raise
        
        if last_error:
            raise last_error
        
        return {"results": [], "total_results": 0, "total_pages": 0, "page": 1}

    async def get_tmdb_details(self, tmdb_id: int, media_type: str) -> Optional[Dict[str, Any]]:
        """
        获取TMDB详细信息
        
        Args:
            tmdb_id: TMDB ID
            media_type: 媒体类型 (movie/tv)
            
        Returns:
            TMDB详细信息字典
        """
        if not self.tmdb_api_key:
            logger.debug("TMDB API密钥未配置，跳过TMDB详情查询")
            return None
        
        # 生成缓存键
        cache_key = self.cache.generate_key(
            "tmdb_details",
            media_type=media_type,
            tmdb_id=tmdb_id
        )
        
        # 尝试从缓存获取
        cached_result = await self.cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"从缓存获取TMDB详情: {media_type} {tmdb_id}")
            return cached_result
        
        # 重试机制
        last_error = None
        for attempt in range(self.max_retries):
            try:
                if media_type == "movie":
                    url = f"{self.tmdb_base_url}/movie/{tmdb_id}"
                else:  # tv
                    url = f"{self.tmdb_base_url}/tv/{tmdb_id}"
                
                params = {
                    "api_key": self.tmdb_api_key,
                    "language": "zh-CN"
                }
                
                # 使用代理（如果配置了）
                from app.utils.http_client import create_httpx_client
                async with create_httpx_client(timeout=self.timeout, use_proxy=True) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                
                # 缓存结果（24小时）
                await self.cache.set(cache_key, data, ttl=86400)
                return data
                
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    logger.warning(f"TMDB详情请求超时，重试 {attempt + 1}/{self.max_retries}: {media_type} {tmdb_id}")
                    await asyncio.sleep(1 * (attempt + 1))
                else:
                    logger.error(f"TMDB详情请求超时，已达最大重试次数: {media_type} {tmdb_id}")
                    return None
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code == 404:
                    logger.debug(f"TMDB项目不存在: {media_type} {tmdb_id}")
                    return None
                elif e.response.status_code >= 500 and attempt < self.max_retries - 1:
                    logger.warning(f"TMDB详情服务器错误，重试 {attempt + 1}/{self.max_retries}: {media_type} {tmdb_id}, 状态码: {e.response.status_code}")
                    await asyncio.sleep(1 * (attempt + 1))
                else:
                    logger.error(f"TMDB详情请求失败: {media_type} {tmdb_id}, 状态码: {e.response.status_code}")
                    return None
            except Exception as e:
                last_error = e
                logger.error(f"获取TMDB详情失败: {media_type} {tmdb_id}, 错误: {e}")
                return None
        
        return None

