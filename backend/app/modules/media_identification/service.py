"""
媒体识别服务 - 整合过往版本的媒体识别功能
可以直接调用VabHub-1等版本的媒体识别功能
"""

from typing import Dict, Optional, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, or_
from datetime import datetime, timedelta
from loguru import logger
import json

from app.core.legacy_adapter import get_legacy_adapter
from app.core.legacy_wrapper import MediaParserWrapper
from app.models.identification_history import IdentificationHistory
from app.modules.thetvdb import TheTvDbModule
from app.modules.fanart import FanartModule
from app.core.config import settings


class MediaIdentificationService:
    """媒体识别服务 - 整合过往版本的媒体识别功能"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._parser_wrapper = None
        self._adapter = get_legacy_adapter()
        self._tvdb_module = None
        self._fanart_module = None
    
    def _get_parser(self) -> MediaParserWrapper:
        """获取媒体解析器包装器"""
        if self._parser_wrapper is None:
            # 优先使用vabhub_1版本的解析器
            self._parser_wrapper = MediaParserWrapper(version="vabhub_1")
        return self._parser_wrapper
    
    def _get_tvdb_module(self) -> Optional[TheTvDbModule]:
        """获取TVDB模块实例"""
        if self._tvdb_module is None:
            try:
                self._tvdb_module = TheTvDbModule()
            except Exception as e:
                logger.warning(f"TVDB模块初始化失败: {e}")
                return None
        return self._tvdb_module
    
    def _get_fanart_module(self) -> Optional[FanartModule]:
        """获取Fanart模块实例"""
        if self._fanart_module is None:
            try:
                self._fanart_module = FanartModule()
            except Exception as e:
                logger.warning(f"Fanart模块初始化失败: {e}")
                return None
        return self._fanart_module
    
    async def identify_media(self, file_path: str, file_name: Optional[str] = None, file_size: Optional[int] = None) -> Dict[str, Any]:
        """
        识别媒体文件
        
        识别链：
        1. 文件名解析
        2. TMDB搜索（如果文件名解析成功）
        3. TVDB搜索（电视剧备选，如果TMDB失败或未找到）
        4. 增强识别服务（如果以上都失败）
        
        Args:
            file_path: 文件路径
            file_name: 原始文件名（可选）
            file_size: 文件大小（可选）
        """
        try:
            # 第一步：文件名解析
            parser = self._get_parser()
            parse_result = parser.parse_filename(file_path)
            
            identification_result = None
            
            if parse_result:
                title = parse_result.get("title", "")
                year = parse_result.get("year")
                season = parse_result.get("season")
                episode = parse_result.get("episode")
                media_type = parse_result.get("type", "unknown")
                
                # 第二步：尝试TMDB搜索（如果TMDB API Key已配置）
                tmdb_result = None
                if title and settings.TMDB_API_KEY:
                    tmdb_result = await self._search_tmdb(title, year, media_type)
                
                # 如果TMDB搜索成功，使用TMDB结果
                if tmdb_result and tmdb_result.get("success"):
                    identification_result = {
                        "success": True,
                        "title": tmdb_result.get("title", title),
                        "year": tmdb_result.get("year", year),
                        "season": season,
                        "episode": episode,
                        "type": media_type,
                        "tmdb_id": tmdb_result.get("tmdb_id"),
                        "tvdb_id": tmdb_result.get("tvdb_id"),
                        "imdb_id": tmdb_result.get("imdb_id"),
                        "poster_url": tmdb_result.get("poster_url"),
                        "backdrop_url": tmdb_result.get("backdrop_url"),
                        "overview": tmdb_result.get("overview"),
                        "confidence": 0.9,  # TMDB结果置信度较高
                        "source": "tmdb"
                    }
                    # 获取Fanart图片（如果启用且是电视剧）
                    if media_type in ["tv", "series"] and settings.FANART_ENABLE:
                        fanart_images = await self._get_fanart_images(
                            media_type=media_type,
                            tmdb_id=tmdb_result.get("tmdb_id"),
                            tvdb_id=tmdb_result.get("tvdb_id")
                        )
                        if fanart_images:
                            identification_result["fanart_images"] = fanart_images
                # 如果TMDB失败，尝试豆瓣回退（对中文内容特别有效）
                if not tmdb_result or not tmdb_result.get("success"):
                    douban_result = await self._search_douban(title, year, media_type)
                    if douban_result and douban_result.get("success"):
                        identification_result = {
                            "success": True,
                            "title": douban_result.get("title", title),
                            "year": douban_result.get("year", year),
                            "season": season,
                            "episode": episode,
                            "type": media_type,
                            "douban_id": douban_result.get("douban_id"),
                            "tmdb_id": douban_result.get("tmdb_id"),  # 豆瓣可能包含TMDB ID
                            "imdb_id": douban_result.get("imdb_id"),
                            "poster_url": douban_result.get("poster_url"),
                            "backdrop_url": douban_result.get("backdrop_url"),
                            "overview": douban_result.get("overview"),
                            "rating": douban_result.get("rating"),  # 豆瓣评分
                            "confidence": 0.75,  # 豆瓣结果置信度中等
                            "source": "douban"
                        }
                        logger.info(f"使用豆瓣回退识别成功: {title} ({year})")
                    # 如果是电视剧且豆瓣也失败，尝试TVDB搜索
                    elif media_type in ["tv", "series"]:
                        tvdb_result = await self._search_tvdb(title, year)
                        if tvdb_result and tvdb_result.get("success"):
                            identification_result = {
                                "success": True,
                                "title": tvdb_result.get("title", title),
                                "year": tvdb_result.get("year", year),
                                "season": season,
                                "episode": episode,
                                "type": media_type,
                                "tvdb_id": tvdb_result.get("tvdb_id"),
                                "tmdb_id": tvdb_result.get("tmdb_id"),
                                "imdb_id": tvdb_result.get("imdb_id"),
                                "poster_url": tvdb_result.get("poster_url"),
                                "backdrop_url": tvdb_result.get("backdrop_url"),
                                "overview": tvdb_result.get("overview"),
                                "confidence": 0.8,  # TVDB结果置信度中等
                                "source": "tvdb"
                            }
                            # 获取Fanart图片（如果启用，优先使用TVDB ID）
                            if settings.FANART_ENABLE:
                                fanart_images = await self._get_fanart_images(
                                    media_type=media_type,
                                    tmdb_id=tvdb_result.get("tmdb_id"),
                                    tvdb_id=tvdb_result.get("tvdb_id")
                                )
                                if fanart_images:
                                    identification_result["fanart_images"] = fanart_images
                        else:
                            # 如果TVDB也失败，使用文件名解析结果
                            identification_result = {
                                "success": True,
                                "title": title,
                                "year": year,
                                "season": season,
                                "episode": episode,
                                "type": media_type,
                                "confidence": parse_result.get("confidence", 0.6),
                                "source": "filename_parser"
                            }
                else:
                    # 如果TMDB失败但不是电视剧，使用文件名解析结果
                    identification_result = {
                        "success": True,
                        "title": title,
                        "year": year,
                        "season": season,
                        "episode": episode,
                        "type": media_type,
                        "confidence": parse_result.get("confidence", 0.6),
                        "source": "filename_parser"
                    }
            else:
                # 如果文件名解析失败，尝试使用增强识别服务
                identification_result = await self._enhanced_identification(file_path)
            
            # 保存识别历史
            await self._save_history(
                file_path=file_path,
                file_name=file_name,
                file_size=file_size,
                result=identification_result
            )
            
            return identification_result
            
        except Exception as e:
            logger.error(f"识别媒体文件失败: {e}")
            error_result = {
                "success": False,
                "error": str(e)
            }
            
            # 保存失败的历史记录
            await self._save_history(
                file_path=file_path,
                file_name=file_name,
                file_size=file_size,
                result=error_result
            )
            
            return error_result
    
    async def _search_tmdb(self, title: str, year: Optional[int] = None, media_type: str = "movie") -> Optional[Dict[str, Any]]:
        """
        搜索TMDB（异步）
        
        Args:
            title: 标题
            year: 年份（可选）
            media_type: 媒体类型（movie/tv）
            
        Returns:
            TMDB搜索结果，失败返回None
        """
        try:
            from app.api.media import search_tmdb_movie, search_tmdb_tv, get_tmdb_movie_details, get_tmdb_tv_details
            
            if not settings.TMDB_API_KEY:
                return None
            
            # 搜索TMDB
            if media_type == "movie":
                results = await search_tmdb_movie(title, settings.TMDB_API_KEY)
            else:
                results = await search_tmdb_tv(title, settings.TMDB_API_KEY)
            
            if not results:
                return None
            
            # 选择最佳匹配（优先匹配年份）
            best_match = results[0]
            if year:
                for result in results:
                    result_year = result.get("release_date", "")[:4] if result.get("release_date") else None
                    if result_year and str(year) == result_year:
                        best_match = result
                        break
            
            tmdb_id = best_match.get("id")
            if not tmdb_id:
                return None
            
            # 获取详细信息
            if media_type == "movie":
                details = await get_tmdb_movie_details(tmdb_id, settings.TMDB_API_KEY)
            else:
                details = await get_tmdb_tv_details(tmdb_id, settings.TMDB_API_KEY)
            
            if not details:
                return None
            
            # 对于电视剧，获取external_ids（包含TVDB ID）
            external_ids = {}
            if media_type in ["tv", "series"]:
                try:
                    from app.utils.http_client import create_httpx_client
                    async with create_httpx_client(timeout=10.0, use_proxy=True) as client:
                        url = f"https://api.themoviedb.org/3/tv/{tmdb_id}/external_ids"
                        params = {"api_key": settings.TMDB_API_KEY}
                        response = await client.get(url, params=params)
                        if response.status_code == 200:
                            external_ids = response.json()
                except Exception as e:
                    logger.debug(f"获取TMDB external_ids失败: {e}")
            
            # 构建结果
            result = {
                "success": True,
                "title": details.get("title") or details.get("name", title),
                "year": int(details.get("release_date", "")[:4]) if details.get("release_date") else year,
                "tmdb_id": tmdb_id,
                "imdb_id": details.get("imdb_id") or external_ids.get("imdb_id"),
                "overview": details.get("overview"),
            }
            
            # 获取图片URL
            if details.get("poster_path"):
                result["poster_url"] = f"https://image.tmdb.org/t/p/w500{details['poster_path']}"
            if details.get("backdrop_path"):
                result["backdrop_url"] = f"https://image.tmdb.org/t/p/w1280{details['backdrop_path']}"
            
            # 对于电视剧，从external_ids获取TVDB ID
            if media_type in ["tv", "series"] and external_ids.get("tvdb_id"):
                result["tvdb_id"] = external_ids["tvdb_id"]
            
            return result
            
        except Exception as e:
            logger.warning(f"TMDB搜索失败 ({title}): {e}")
            return None
    
    async def _get_fanart_images(
        self,
        media_type: str,
        tmdb_id: Optional[int] = None,
        tvdb_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取Fanart图片（异步）
        
        Args:
            media_type: 媒体类型（movie/tv）
            tmdb_id: TMDB ID（可选）
            tvdb_id: TVDB ID（可选，电视剧优先使用）
            
        Returns:
            Fanart图片数据字典，失败返回None
        """
        try:
            fanart_module = self._get_fanart_module()
            if not fanart_module:
                return None
            
            # 获取Fanart图片
            fanart_images = await fanart_module.obtain_images(
                media_type=media_type,
                tmdb_id=tmdb_id,
                tvdb_id=tvdb_id
            )
            
            if not fanart_images:
                return None
            
            # 处理Fanart图片数据，提取最佳图片URL
            processed_images = {}
            
            # 电视剧：优先使用TVDB ID获取的图片
            if media_type in ["tv", "series"]:
                # 海报
                if fanart_images.get("tvposter"):
                    # 选择语言匹配或likes最高的
                    posters = fanart_images["tvposter"]
                    if isinstance(posters, list) and len(posters) > 0:
                        # 优先选择中文或英文，然后按likes排序
                        preferred_langs = ["zh", "en", "00"]  # 00表示无语言
                        best_poster = None
                        for lang in preferred_langs:
                            lang_posters = [p for p in posters if p.get("lang") == lang]
                            if lang_posters:
                                best_poster = max(lang_posters, key=lambda x: int(x.get("likes", "0")))
                                break
                        if not best_poster:
                            best_poster = max(posters, key=lambda x: int(x.get("likes", "0")))
                        processed_images["poster"] = best_poster.get("url")
                
                # 背景图
                if fanart_images.get("showbackground"):
                    backgrounds = fanart_images["showbackground"]
                    if isinstance(backgrounds, list) and len(backgrounds) > 0:
                        best_background = max(backgrounds, key=lambda x: int(x.get("likes", "0")))
                        processed_images["backdrop"] = best_background.get("url")
                
                # Logo
                if fanart_images.get("hdtvlogo"):
                    logos = fanart_images["hdtvlogo"]
                    if isinstance(logos, list) and len(logos) > 0:
                        best_logo = max(logos, key=lambda x: int(x.get("likes", "0")))
                        processed_images["logo"] = best_logo.get("url")
            
            # 电影：使用TMDB ID获取的图片
            elif media_type == "movie":
                # 海报
                if fanart_images.get("movieposter"):
                    posters = fanart_images["movieposter"]
                    if isinstance(posters, list) and len(posters) > 0:
                        best_poster = max(posters, key=lambda x: int(x.get("likes", "0")))
                        processed_images["poster"] = best_poster.get("url")
                
                # 背景图
                if fanart_images.get("moviebackground"):
                    backgrounds = fanart_images["moviebackground"]
                    if isinstance(backgrounds, list) and len(backgrounds) > 0:
                        best_background = max(backgrounds, key=lambda x: int(x.get("likes", "0")))
                        processed_images["backdrop"] = best_background.get("url")
            
            return processed_images if processed_images else None
            
        except Exception as e:
            logger.warning(f"获取Fanart图片失败: {e}")
            return None
    
    async def _search_tvdb(self, title: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        搜索TVDB（异步，仅用于电视剧）
        
        Args:
            title: 标题
            year: 年份（可选）
            
        Returns:
            TVDB搜索结果，失败返回None
        """
        try:
            tvdb_module = self._get_tvdb_module()
            if not tvdb_module:
                return None
            
            # 搜索TVDB
            results = await tvdb_module.search_tvdb(title)
            if not results:
                return None
            
            # 选择最佳匹配（优先匹配年份）
            best_match = results[0]
            if year:
                for result in results:
                    result_year = result.get("year")
                    if result_year and result_year == year:
                        best_match = result
                        break
            
            tvdb_id = best_match.get("id")
            if not tvdb_id:
                return None
            
            # 获取详细信息
            tvdb_info = await tvdb_module.tvdb_info(tvdb_id)
            if not tvdb_info:
                return None
            
            # 构建结果
            result = {
                "success": True,
                "title": tvdb_info.get("name", title),
                "year": tvdb_info.get("year", year),
                "tvdb_id": tvdb_id,
                "overview": tvdb_info.get("overview"),
            }
            
            # 获取图片URL
            if tvdb_info.get("image"):
                result["poster_url"] = tvdb_info["image"]
            if tvdb_info.get("banner"):
                result["backdrop_url"] = tvdb_info["banner"]
            
            # 尝试获取IMDB ID
            if tvdb_info.get("remoteIds"):
                for remote_id in tvdb_info["remoteIds"]:
                    if remote_id.get("type") == "imdb":
                        result["imdb_id"] = remote_id.get("id")
                        break
            
            # 尝试获取TMDB ID（通过remoteIds）
            if tvdb_info.get("remoteIds"):
                for remote_id in tvdb_info["remoteIds"]:
                    if remote_id.get("type") == "themoviedb":
                        result["tmdb_id"] = remote_id.get("id")
                        break
            
            return result
            
        except Exception as e:
            logger.warning(f"TVDB搜索失败 ({title}): {e}")
            return None
    
    async def _search_douban(self, title: str, year: Optional[int] = None, media_type: str = "movie") -> Optional[Dict[str, Any]]:
        """
        搜索豆瓣（异步，作为TMDB的回退）
        
        Args:
            title: 标题
            year: 年份（可选）
            media_type: 媒体类型（movie/tv）
            
        Returns:
            豆瓣搜索结果，失败返回None
        """
        try:
            from app.modules.douban.client import DoubanClient
            
            douban_client = DoubanClient()
            
            # 搜索豆瓣
            if media_type == "movie":
                search_results = await douban_client.search_movie(title, count=5)
            else:
                search_results = await douban_client.search_tv(title, count=5)
            
            # 提取items（豆瓣API返回格式可能不同）
            items = search_results.get("items", []) or search_results.get("subjects", [])
            if not items:
                return None
            
            # 选择最佳匹配（优先匹配年份）
            best_match = items[0]
            if year:
                for item in items:
                    item_year = item.get("year")
                    if item_year and item_year == year:
                        best_match = item
                        break
            
            douban_id = best_match.get("id") or best_match.get("subject_id")
            if not douban_id:
                return None
            
            # 获取详细信息
            if media_type == "movie":
                detail_result = await douban_client.get_movie_detail(douban_id)
            else:
                detail_result = await douban_client.get_tv_detail(douban_id)
            if not detail_result:
                return None
            
            # 构建结果
            result = {
                "success": True,
                "title": detail_result.get("title", title),
                "year": detail_result.get("year", year),
                "douban_id": douban_id,
                "tmdb_id": detail_result.get("tmdb_id"),  # 豆瓣可能包含TMDB ID
                "imdb_id": detail_result.get("imdb_id"),
                "overview": detail_result.get("summary") or detail_result.get("intro"),
                "rating": detail_result.get("rating", {}).get("average") if detail_result.get("rating") else None,
            }
            
            # 获取图片URL
            if detail_result.get("pic"):
                result["poster_url"] = detail_result["pic"]
            if detail_result.get("cover"):
                result["backdrop_url"] = detail_result["cover"]
            
            return result
            
        except Exception as e:
            logger.warning(f"豆瓣搜索失败 ({title}): {e}")
            return None
    
    async def _enhanced_identification(self, file_path: str) -> Dict[str, Any]:
        """使用增强识别服务"""
        try:
            # 尝试使用增强媒体识别服务
            service = self._adapter.get_instance("enhanced_media_identification", version="vabhub_1")
            if service and hasattr(service, "identify_media"):
                result = await service.identify_media(file_path)
                
                if result:
                    return {
                        "success": True,
                        "title": result.title if hasattr(result, 'title') else result.get("title", ""),
                        "year": result.year if hasattr(result, 'year') else result.get("year"),
                        "season": result.season if hasattr(result, 'season') else result.get("season"),
                        "episode": result.episode if hasattr(result, 'episode') else result.get("episode"),
                        "type": result.media_type if hasattr(result, 'media_type') else result.get("media_type", "unknown"),
                        "confidence": result.confidence if hasattr(result, 'confidence') else result.get("confidence", 0.0),
                        "source": "enhanced_identification"
                    }
        except Exception as e:
            logger.warning(f"增强识别服务不可用: {e}")
        
        return {
            "success": False,
            "error": "无法识别媒体文件"
        }
    
    async def batch_identify(self, file_paths: list[str]) -> List[Dict[str, Any]]:
        """批量识别媒体文件"""
        results = []
        for file_path in file_paths:
            result = await self.identify_media(file_path)
            results.append({
                "file_path": file_path,
                **result
            })
        return results
    
    async def _save_history(self, file_path: str, file_name: Optional[str], file_size: Optional[int], result: Dict[str, Any]):
        """保存识别历史记录"""
        try:
            # 处理raw_result（JSON字段）
            raw_result_json = result.copy() if result else {}
            
            history = IdentificationHistory(
                file_path=file_path,
                file_name=file_name,
                file_size=file_size,
                title=result.get("title"),
                year=result.get("year"),
                season=result.get("season"),
                episode=result.get("episode"),
                media_type=result.get("type"),
                confidence=result.get("confidence", 0.0),
                source=result.get("source"),
                success="true" if result.get("success") else "false",
                error=result.get("error"),
                raw_result=raw_result_json,
                identified_at=datetime.utcnow()
            )
            
            self.db.add(history)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"保存识别历史失败: {e}")
            # 不抛出异常，避免影响识别流程
    
    async def get_history(
        self,
        limit: int = 50,
        offset: int = 0,
        file_path: Optional[str] = None,
        title: Optional[str] = None,
        media_type: Optional[str] = None,
        success: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        获取识别历史记录
        
        Args:
            limit: 返回记录数
            offset: 偏移量
            file_path: 文件路径过滤（模糊匹配）
            title: 标题过滤（模糊匹配）
            media_type: 媒体类型过滤
            success: 成功状态过滤（true, false）
            start_date: 开始日期
            end_date: 结束日期
        """
        try:
            query = select(IdentificationHistory)
            
            # 构建过滤条件
            conditions = []
            if file_path:
                conditions.append(IdentificationHistory.file_path.contains(file_path))
            if title:
                conditions.append(IdentificationHistory.title.contains(title))
            if media_type:
                conditions.append(IdentificationHistory.media_type == media_type)
            if success:
                conditions.append(IdentificationHistory.success == success)
            if start_date:
                conditions.append(IdentificationHistory.identified_at >= start_date)
            if end_date:
                conditions.append(IdentificationHistory.identified_at <= end_date)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # 排序和分页
            query = query.order_by(desc(IdentificationHistory.identified_at))
            query = query.offset(offset).limit(limit)
            
            result = await self.db.execute(query)
            histories = result.scalars().all()
            
            return [
                {
                    "id": h.id,
                    "file_path": h.file_path,
                    "file_name": h.file_name,
                    "file_size": h.file_size,
                    "title": h.title,
                    "year": h.year,
                    "season": h.season,
                    "episode": h.episode,
                    "media_type": h.media_type,
                    "confidence": h.confidence,
                    "source": h.source,
                    "success": h.success == "true",
                    "error": h.error,
                    "raw_result": h.raw_result,
                    "identified_at": h.identified_at.isoformat() if h.identified_at else None,
                    "created_at": h.created_at.isoformat() if h.created_at else None
                }
                for h in histories
            ]
        
        except Exception as e:
            logger.error(f"获取识别历史失败: {e}")
            return []
    
    async def get_history_count(
        self,
        file_path: Optional[str] = None,
        title: Optional[str] = None,
        media_type: Optional[str] = None,
        success: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """获取识别历史记录总数"""
        try:
            from sqlalchemy import func
            
            query = select(func.count(IdentificationHistory.id))
            
            # 构建过滤条件
            conditions = []
            if file_path:
                conditions.append(IdentificationHistory.file_path.contains(file_path))
            if title:
                conditions.append(IdentificationHistory.title.contains(title))
            if media_type:
                conditions.append(IdentificationHistory.media_type == media_type)
            if success:
                conditions.append(IdentificationHistory.success == success)
            if start_date:
                conditions.append(IdentificationHistory.identified_at >= start_date)
            if end_date:
                conditions.append(IdentificationHistory.identified_at <= end_date)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            result = await self.db.execute(query)
            return result.scalar() or 0
        
        except Exception as e:
            logger.error(f"获取识别历史总数失败: {e}")
            return 0
    
    async def get_history_by_id(self, history_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取识别历史记录"""
        try:
            result = await self.db.execute(
                select(IdentificationHistory).where(IdentificationHistory.id == history_id)
            )
            history = result.scalar_one_or_none()
            
            if not history:
                return None
            
            return {
                "id": history.id,
                "file_path": history.file_path,
                "file_name": history.file_name,
                "file_size": history.file_size,
                "title": history.title,
                "year": history.year,
                "season": history.season,
                "episode": history.episode,
                "media_type": history.media_type,
                "confidence": history.confidence,
                "source": history.source,
                "success": history.success == "true",
                "error": history.error,
                "raw_result": history.raw_result,
                "identified_at": history.identified_at.isoformat() if history.identified_at else None,
                "created_at": history.created_at.isoformat() if history.created_at else None
            }
        
        except Exception as e:
            logger.error(f"获取识别历史失败: {e}")
            return None
    
    async def delete_history(self, history_id: int) -> bool:
        """删除识别历史记录"""
        try:
            from sqlalchemy import delete
            
            result = await self.db.execute(
                delete(IdentificationHistory).where(IdentificationHistory.id == history_id)
            )
            await self.db.commit()
            
            return result.rowcount > 0
        
        except Exception as e:
            logger.error(f"删除识别历史失败: {e}")
            return False
    
    async def clear_history(self, days: Optional[int] = None) -> int:
        """
        清理识别历史记录
        
        Args:
            days: 保留最近N天的记录，如果为None则清理所有记录
        """
        try:
            from sqlalchemy import delete
            
            if days:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                result = await self.db.execute(
                    delete(IdentificationHistory).where(IdentificationHistory.identified_at < cutoff_date)
                )
            else:
                result = await self.db.execute(delete(IdentificationHistory))
            
            await self.db.commit()
            
            deleted_count = result.rowcount
            logger.info(f"清理识别历史完成，删除了 {deleted_count} 条记录")
            
            return deleted_count
        
        except Exception as e:
            logger.error(f"清理识别历史失败: {e}")
            return 0
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取识别历史统计信息"""
        try:
            from sqlalchemy import func
            
            # 总记录数
            total_result = await self.db.execute(select(func.count(IdentificationHistory.id)))
            total = total_result.scalar() or 0
            
            # 成功记录数
            success_result = await self.db.execute(
                select(func.count(IdentificationHistory.id)).where(IdentificationHistory.success == "true")
            )
            success_count = success_result.scalar() or 0
            
            # 失败记录数
            failed_count = total - success_count
            
            # 按媒体类型统计
            type_result = await self.db.execute(
                select(
                    IdentificationHistory.media_type,
                    func.count(IdentificationHistory.id).label("count")
                ).group_by(IdentificationHistory.media_type)
            )
            type_stats = {row.media_type or "unknown": row.count for row in type_result.all()}
            
            # 按识别来源统计
            source_result = await self.db.execute(
                select(
                    IdentificationHistory.source,
                    func.count(IdentificationHistory.id).label("count")
                ).group_by(IdentificationHistory.source)
            )
            source_stats = {row.source or "unknown": row.count for row in source_result.all()}
            
            # 平均置信度
            avg_confidence_result = await self.db.execute(
                select(func.avg(IdentificationHistory.confidence))
            )
            avg_confidence = avg_confidence_result.scalar() or 0.0
            
            return {
                "total": total,
                "success_count": success_count,
                "failed_count": failed_count,
                "success_rate": (success_count / total * 100) if total > 0 else 0.0,
                "type_stats": type_stats,
                "source_stats": source_stats,
                "avg_confidence": float(avg_confidence)
            }
        
        except Exception as e:
            logger.error(f"获取识别历史统计失败: {e}")
            return {
                "total": 0,
                "success_count": 0,
                "failed_count": 0,
                "success_rate": 0.0,
                "type_stats": {},
                "source_stats": {},
                "avg_confidence": 0.0
            }

