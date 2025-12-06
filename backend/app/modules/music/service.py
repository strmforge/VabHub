"""
音乐服务 - VabHub特色功能
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, text, desc, and_
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from uuid import uuid4
from loguru import logger
import json
from app.models.subscription import Subscription

from app.models.music import (
    MusicSubscription,
    MusicTrack,
    MusicPlaylist,
    MusicLibrary,
    MusicChartRecord,
)
from app.core.music_clients import SpotifyClient, NeteaseClient, QQMusicClient
from app.modules.settings.service import SettingsService
from app.modules.charts.service import ChartsService
from app.core.cache import get_cache
from app.modules.music.metadata_extractor import MusicMetadataExtractor
from app.modules.music.scraper import MusicScraper
from app.modules.music.lyrics_fetcher import LyricsFetcher
from app.modules.music.cover_downloader import CoverDownloader
from app.modules.music.schemas import MusicChartEntry
from app.modules.music import query_builder
from app.modules.music.schema_utils import ensure_music_schema


class MusicService:
    """音乐服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._spotify_client = None
        self._netease_client = None
        self._qq_music_client = None
        self._charts_service = ChartsService(db)
        self.cache = get_cache()  # 使用统一缓存系统
        self._schema_checked = False
        
        # 初始化音乐处理模块
        self.metadata_extractor = MusicMetadataExtractor()
        import os
        acoustid_api_key = os.getenv("ACOUSTID_API_KEY")
        self.music_scraper = MusicScraper(acoustid_api_key=acoustid_api_key)
        self.lyrics_fetcher = LyricsFetcher()
        self.cover_downloader = CoverDownloader()

    async def _ensure_music_schema(self) -> None:
        """确保 music_subscriptions 表具备新字段"""
        if self._schema_checked:
            return
        await ensure_music_schema()
        self._schema_checked = True
    
    def _get_spotify_client(self) -> Optional[SpotifyClient]:
        """获取Spotify客户端"""
        try:
            if self._spotify_client is None:
                settings_service = SettingsService(self.db)
                # 注意：这里需要同步调用，但SettingsService是异步的
                # 我们将在实际调用时获取设置
                pass
            return self._spotify_client
        except Exception as e:
            logger.error(f"初始化Spotify客户端失败: {e}")
            return None
    
    async def _get_client(self, platform: str):
        """获取音乐平台客户端"""
        try:
            if platform == "spotify":
                if self._spotify_client is None:
                    # 从设置中获取API密钥
                    settings_service = SettingsService(self.db)
                    try:
                        # 尝试从设置中获取
                        client_id = await settings_service.get_setting("spotify_client_id")
                        client_secret = await settings_service.get_setting("spotify_client_secret")
                        
                        # 如果设置中没有，尝试环境变量
                        if not client_id or not client_secret:
                            import os
                            client_id = os.getenv("SPOTIFY_CLIENT_ID", "")
                            client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")
                        
                        if client_id and client_secret:
                            self._spotify_client = SpotifyClient(client_id, client_secret)
                        else:
                            logger.warning("Spotify API密钥未配置，将返回模拟数据")
                            return None
                    except Exception as e:
                        logger.warning(f"获取Spotify设置失败: {e}，尝试环境变量")
                        import os
                        client_id = os.getenv("SPOTIFY_CLIENT_ID", "")
                        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")
                        if client_id and client_secret:
                            self._spotify_client = SpotifyClient(client_id, client_secret)
                        else:
                            return None
                return self._spotify_client
            
            elif platform == "netease":
                if self._netease_client is None:
                    # 网易云音乐不需要API密钥，直接初始化
                    self._netease_client = NeteaseClient()
                return self._netease_client
            
            elif platform == "qq_music":
                if self._qq_music_client is None:
                    # QQ音乐不需要API密钥，直接初始化
                    self._qq_music_client = QQMusicClient()
                return self._qq_music_client
            
            return None
        except Exception as e:
            logger.error(f"获取{platform}客户端失败: {e}")
            return None
    
    async def search_music(
        self,
        query: str,
        search_type: str = "all",
        platform: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """搜索音乐（带缓存和并发处理）"""
        import asyncio
        
        logger.info(f"搜索音乐: {query} (类型: {search_type}, 平台: {platform})")
        
        # 生成缓存键
        cache_key = self.cache.generate_key(
            "music_search",
            query=query,
            search_type=search_type,
            platform=platform or "all",
            limit=limit
        )
        
        # 尝试从缓存获取
        cached_result = await self.cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"从缓存获取音乐搜索结果: {query}")
            return cached_result
        
        results = []
        
        # 确定要搜索的平台
        platforms_to_search = [platform] if platform else ["spotify", "qq_music", "netease"]
        
        # 并发搜索所有平台
        async def search_platform(platform_name: str) -> List[Dict]:
            try:
                client = await self._get_client(platform_name)
                
                if client is None:
                    logger.warning(f"{platform_name}客户端不可用，跳过")
                    return []
                
                # 调用真实API搜索
                platform_results = await client.search(query, search_type, limit)
                
                # 统一格式化结果
                formatted_results = []
                for result in platform_results:
                    formatted_result = self._format_search_result(result, platform_name)
                    if formatted_result:
                        formatted_results.append(formatted_result)
                
                return formatted_results
            except Exception as e:
                logger.error(f"从{platform_name}搜索失败: {e}")
                return []
        
        # 并发搜索所有平台
        search_tasks = [search_platform(platform_name) for platform_name in platforms_to_search]
        platform_results_list = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # 合并结果
        for platform_results in platform_results_list:
            if isinstance(platform_results, Exception):
                logger.error(f"平台搜索异常: {platform_results}")
                continue
            if isinstance(platform_results, list):
                results.extend(platform_results)
        
        # 如果没有结果，返回模拟数据作为备选
        if not results:
            logger.warning("所有平台搜索失败，返回模拟数据")
            results = self._get_mock_search_results(query, search_type, platform, limit)
        
        # 去重（基于标题和艺术家）
        seen = set()
        deduplicated_results = []
        for result in results:
            key = (result.get("title", ""), result.get("artist", ""))
            if key not in seen and key[0] and key[1]:
                seen.add(key)
                deduplicated_results.append(result)
        
        final_results = deduplicated_results[:limit]
        
        # 缓存结果（30分钟）
        await self.cache.set(cache_key, final_results, ttl=1800)
        logger.debug(f"音乐搜索结果已缓存: {query}")
        
        return final_results
    
    def _format_search_result(self, result: Dict, platform: str) -> Dict:
        """统一格式化搜索结果"""
        try:
            # 统一字段名映射
            formatted = {
                "id": result.get("id", ""),
                "title": result.get("title", result.get("name", "")),
                "artist": result.get("artist", ""),
                "album": result.get("album", ""),
                "duration": result.get("duration", 0),
                "release_date": result.get("release_date"),
                "genre": result.get("genre", result.get("genres", [])),
                "platform": platform,
                "external_url": result.get("external_url"),
                "preview_url": result.get("preview_url"),
                "cover_url": result.get("cover_url", result.get("image_url")),
                "popularity": result.get("popularity", 0),
                "type": result.get("type", "track")
            }
            
            # 确保所有必需字段都有值
            if not formatted["id"] or not formatted["title"]:
                return None
            
            return formatted
        except Exception as e:
            logger.warning(f"格式化搜索结果失败: {e}")
            return None
    
    def _get_mock_search_results(self, query: str, search_type: str, platform: Optional[str], limit: int) -> List[Dict]:
        """获取模拟搜索结果（备选方案）"""
        results = []
        platforms = [platform] if platform else ["spotify", "qq_music", "netease"]
        
        for i, platform_name in enumerate(platforms[:3]):
            for j in range(min(5, limit // len(platforms) + 1)):
                result = {
                    "id": f"{platform_name}_{i}_{j}",
                    "title": f"{query} - {search_type} {j+1}",
                    "artist": f"Artist {j+1}",
                    "album": f"Album {j+1}",
                    "duration": 180 + j * 30,
                    "release_date": "2024-01-01",
                    "genre": ["Pop", "Rock"],
                    "platform": platform_name,
                    "external_url": f"https://{platform_name}.com/track/{j+1}",
                    "preview_url": f"https://{platform_name}.com/preview/{j+1}",
                    "cover_url": f"https://example.com/cover/{j+1}.jpg",
                    "popularity": 0.5 + j * 0.1,
                    "type": search_type if search_type != "all" else "track"
                }
                results.append(result)
        
        return results[:limit]
    
    async def get_charts(
        self,
        platform: str,
        chart_type: str = "hot",
        region: str = "CN",
        limit: int = 50,
        persist: bool = True,
    ) -> List[Dict]:
        """获取音乐榜单 - 使用统一的榜单服务"""
        logger.info(f"获取榜单: {platform} - {chart_type} ({region})")
        
        try:
            # 使用统一的榜单服务
            charts = await self._charts_service.get_charts(
                platform=platform,
                chart_type=chart_type,
                region=region,
                limit=limit
            )
            
            # 转换为统一格式
            results = []
            for chart in charts:
                result = {
                    "id": chart.get("id", ""),
                    "title": chart.get("title", ""),
                    "artist": chart.get("artist", ""),
                    "album": chart.get("album", ""),
                    "duration": chart.get("duration", 0),
                    "platform": chart.get("platform", platform),
                    "external_url": chart.get("external_url"),
                    "cover_url": chart.get("image_url"),
                    "popularity": chart.get("popularity", 0),
                    "rank": chart.get("rank", 0),
                    "type": "track"
                }
                results.append(result)
            
            if results and persist:
                await self._store_chart_entries(platform, chart_type, region, results)
            
            return results if results else []
            
        except Exception as e:
            logger.error(f"获取{platform}榜单失败: {e}")
            return []
    
    def _get_mock_charts(self, platform: str, chart_type: str, limit: int) -> List[Dict]:
        """获取模拟榜单数据（备选方案）"""
        results = []
        for i in range(min(limit, 50)):
            result = {
                "id": f"{platform}_chart_{i+1}",
                "title": f"Chart Song {i+1}",
                "artist": f"Artist {i+1}",
                "album": f"Album {i+1}",
                "duration": 180 + i * 30,
                "release_date": "2024-01-01",
                "genre": ["Pop"],
                "platform": platform,
                "cover_url": f"https://example.com/cover/{i+1}.jpg",
                "popularity": 1.0 - i * 0.02,
                "rank": i + 1,
                "change": "up" if i % 3 == 0 else "down" if i % 3 == 1 else "same",
                "type": "track"
            }
            results.append(result)
        return results
    
    async def _store_chart_entries(
        self,
        platform: str,
        chart_type: str,
        region: str,
        charts: List[Dict]
    ) -> Optional[str]:
        """持久化本次榜单结果，便于后续查询/GraphQL"""
        if not charts:
            return None
        
        batch_id = str(uuid4())
        now = datetime.utcnow()
        records = []
        
        for item in charts:
            try:
                rank_value = item.get("rank") if isinstance(item, dict) else None
                if rank_value is not None:
                    try:
                        rank_value = int(rank_value)
                    except (TypeError, ValueError):
                        rank_value = None
                
                record = MusicChartRecord(
                    batch_id=batch_id,
                    platform=item.get("platform") or platform,
                    chart_type=chart_type,
                    region=region,
                    rank=rank_value,
                    title=item.get("title", ""),
                    artist=item.get("artist", ""),
                    album=item.get("album"),
                    external_url=item.get("external_url"),
                    cover_url=item.get("cover_url"),
                    raw_data=item,
                    captured_at=now,
                )
                if record.title and record.artist:
                    records.append(record)
            except Exception as exc:
                logger.debug(f"跳过无效榜单记录: {exc}")
        
        if not records:
            return None
        
        try:
            self.db.add_all(records)
            await self.db.commit()
            return batch_id
        except Exception as exc:
            await self.db.rollback()
            logger.warning(f"持久化音乐榜单失败: {exc}")
            return None
    
    async def get_chart_history(
        self,
        platform: Optional[str] = None,
        chart_type: Optional[str] = None,
        region: Optional[str] = None,
        batches: int = 3
    ) -> List[Dict[str, Any]]:
        """返回最近若干组榜单历史记录"""
        filters = []
        if platform:
            filters.append(MusicChartRecord.platform == platform)
        if chart_type:
            filters.append(MusicChartRecord.chart_type == chart_type)
        if region:
            filters.append(MusicChartRecord.region == region)
        
        batch_stmt = select(
            MusicChartRecord.batch_id,
            func.max(MusicChartRecord.captured_at).label("captured_at"),
            func.max(MusicChartRecord.platform).label("platform"),
            func.max(MusicChartRecord.chart_type).label("chart_type"),
            func.max(MusicChartRecord.region).label("region"),
        )
        if filters:
            batch_stmt = batch_stmt.where(and_(*filters))
        batch_stmt = (
            batch_stmt.group_by(MusicChartRecord.batch_id)
            .order_by(desc("captured_at"))
            .limit(max(1, min(batches, 10)))
        )
        batch_rows = (await self.db.execute(batch_stmt)).all()
        if not batch_rows:
            return []
        
        batch_ids = [row.batch_id for row in batch_rows]
        entries_stmt = select(MusicChartRecord).where(MusicChartRecord.batch_id.in_(batch_ids))
        if filters:
            entries_stmt = entries_stmt.where(and_(*filters))
        entries_stmt = entries_stmt.order_by(
            MusicChartRecord.captured_at.desc(),
            MusicChartRecord.rank.asc().nullslast(),
            MusicChartRecord.id.asc(),
        )
        entries = (await self.db.execute(entries_stmt)).scalars().all()
        
        entry_map: Dict[str, List[Dict[str, Any]]] = {row.batch_id: [] for row in batch_rows}
        for item in entries:
            entry_map.setdefault(item.batch_id, []).append({
                "id": item.id,
                "rank": item.rank,
                "title": item.title,
                "artist": item.artist,
                "album": item.album,
                "platform": item.platform,
                "chart_type": item.chart_type,
                "region": item.region,
                "external_url": item.external_url,
                "cover_url": item.cover_url,
                "captured_at": item.captured_at,
                "raw_data": item.raw_data,
            })
        
        history = []
        for row in batch_rows:
            history.append({
                "batch_id": row.batch_id,
                "captured_at": row.captured_at,
                "platform": row.platform,
                "chart_type": row.chart_type,
                "region": row.region,
                "entries": entry_map.get(row.batch_id, []),
            })
        return history

    async def get_chart_entry_by_id(self, entry_id: int) -> Optional[MusicChartRecord]:
        """根据榜单记录ID获取单个条目"""
        result = await self.db.execute(
            select(MusicChartRecord).where(MusicChartRecord.id == entry_id)
        )
        return result.scalar_one_or_none()
    
    async def get_trending_music(
        self,
        platform: str = "all",
        region: str = "CN",
        limit: int = 20
    ) -> List[Dict]:
        """获取热门音乐（并发处理）"""
        import asyncio
        
        # 获取热门榜单
        if platform == "all":
            # 并发从多个平台获取
            platforms = ["spotify", "qq_music", "netease"]
            chart_tasks = [self.get_charts(p, "hot", region, limit // len(platforms) + 1) for p in platforms]
            charts_list = await asyncio.gather(*chart_tasks, return_exceptions=True)
            
            results = []
            for charts in charts_list:
                if isinstance(charts, Exception):
                    logger.error(f"获取榜单失败: {charts}")
                    continue
                if isinstance(charts, list):
                    results.extend(charts)
            
            return results[:limit]
        else:
            return await self.get_charts(platform, "hot", region, limit)
    
    async def _ensure_core_subscription_link(
        self,
        music_subscription: MusicSubscription,
        payload: Optional[Dict] = None
    ) -> Subscription:
        """确保音乐订阅与通用 Subscription 之间建立关联"""
        if music_subscription.subscription_id:
            result = await self.db.execute(
                select(Subscription).where(Subscription.id == music_subscription.subscription_id)
            )
            existing = result.scalar_one_or_none()
            if existing:
                return existing
        
        core_payload = self._build_core_subscription_payload(music_subscription, payload or {})
        subscription = Subscription(**core_payload)
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        
        music_subscription.subscription_id = subscription.id
        self.db.add(music_subscription)
        await self.db.commit()
        await self.db.refresh(music_subscription)
        
        await self._record_core_history(subscription.id, music_subscription)
        return subscription
    
    def _build_core_subscription_payload(
        self,
        music_subscription: MusicSubscription,
        payload: Dict
    ) -> Dict:
        """构建通用订阅所需字段"""
        music_rules = {
            "type": music_subscription.type,
            "platform": music_subscription.platform,
            "target_id": music_subscription.target_id,
            "target_name": music_subscription.target_name or music_subscription.name,
            "keywords": payload.get("search_keywords") or [],
            "chart_entry": payload.get("chart_entry"),
        }
        
        # 默认用户 ID（CI/开发环境下使用）
        # 实际生产环境应该从认证上下文中获取
        default_user_id = payload.get("user_id", 1)
        
        return {
            "user_id": default_user_id,  # 必填字段
            "title": music_subscription.target_name or music_subscription.name,
            "original_title": music_subscription.name,
            "media_type": "music",
            "status": "active",
            "quality": music_subscription.quality,
            "sites": payload.get("sites"),
            "downloader": payload.get("downloader"),
            "save_path": payload.get("save_path"),
            "min_seeders": payload.get("min_seeders", 2),
            "auto_download": payload.get("auto_download", True),
            "include": payload.get("include"),
            "exclude": payload.get("exclude"),
            "search_rules": {
                "music": music_rules
            }
        }
    
    async def _record_core_history(
        self,
        subscription_id: int,
        music_subscription: MusicSubscription
    ) -> None:
        """调用通用订阅记录历史（旁路日志）"""
        try:
            from app.modules.subscription.service import SubscriptionService
            
            service = SubscriptionService(self.db)
            await service._record_history(
                subscription_id=subscription_id,
                action="create_music_subscription",
                action_type="operation",
                description=f"绑定音乐订阅 {music_subscription.name}",
                new_value={
                    "music_subscription_id": music_subscription.id,
                    "platform": music_subscription.platform,
                    "target_id": music_subscription.target_id,
                    "target_name": music_subscription.target_name,
                }
            )
        except Exception as exc:
            logger.warning(f"记录音乐订阅历史失败: {exc}")
    
    async def auto_download_subscription(
        self,
        music_subscription_id: int,
        *,
        preview_only: bool = False,
        limit: int = 5
    ) -> Dict:
        """基于音乐订阅触发一次 PT 搜索/下载"""
        await self._ensure_music_schema()
        from app.modules.subscription.service import SubscriptionService
        
        music_subscription = await self.get_subscription(music_subscription_id)
        if not music_subscription:
            return {"success": False, "message": "音乐订阅不存在"}
        
        core_subscription = await self._ensure_core_subscription_link(music_subscription)
        subscription_service = SubscriptionService(self.db)
        
        search_result = await subscription_service.execute_search(
            core_subscription.id,
            auto_download_override=False if preview_only else None
        )
        keywords = query_builder.build_music_keywords(core_subscription)
        
        response = {
            "success": search_result.get("success", False),
            "preview_queries": keywords[:limit],
            "subscription_id": core_subscription.id,
            "music_subscription_id": music_subscription_id,
            "result": search_result,
        }
        
        if preview_only:
            response["mode"] = "preview"
            return response
        
        downloaded = search_result.get("downloaded_count", 0) or 0
        if downloaded:
            music_subscription.download_count = (music_subscription.download_count or 0) + downloaded
            music_subscription.updated_at = datetime.utcnow()
            self.db.add(music_subscription)
            await self.db.commit()
            await self.db.refresh(music_subscription)
        
        response["mode"] = "auto"
        return response
    
    async def create_subscription(self, subscription_data: Dict) -> MusicSubscription:
        """创建音乐订阅"""
        await self._ensure_music_schema()
        new_subscription = MusicSubscription(
            name=subscription_data.get("name"),
            type=subscription_data.get("type"),
            platform=subscription_data.get("platform"),
            target_id=subscription_data.get("target_id"),
            target_name=subscription_data.get("target_name") or subscription_data.get("name"),
            status="active",
            auto_download=subscription_data.get("auto_download", True),
            quality=subscription_data.get("quality"),
            download_count=0,
            created_at=datetime.utcnow()
        )
        
        self.db.add(new_subscription)
        await self.db.commit()
        await self.db.refresh(new_subscription)

        # 确保与通用订阅体系建立关联
        await self._ensure_core_subscription_link(new_subscription, subscription_data)
        
        logger.info(f"音乐订阅已创建: {new_subscription.name} (ID: {new_subscription.id})")
        return new_subscription
    
    async def list_subscriptions(
        self,
        platform: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[MusicSubscription]:
        """获取音乐订阅列表"""
        await self._ensure_music_schema()
        query = select(MusicSubscription)
        
        if platform:
            query = query.where(MusicSubscription.platform == platform)
        
        if status:
            query = query.where(MusicSubscription.status == status)
        
        query = query.order_by(MusicSubscription.created_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_subscription(self, subscription_id: int) -> Optional[MusicSubscription]:
        """获取音乐订阅详情"""
        await self._ensure_music_schema()
        result = await self.db.execute(
            select(MusicSubscription).where(MusicSubscription.id == subscription_id)
        )
        return result.scalar_one_or_none()
    
    async def update_subscription(
        self,
        subscription_id: int,
        subscription_data: Dict
    ) -> Optional[MusicSubscription]:
        """更新音乐订阅"""
        existing = await self.get_subscription(subscription_id)
        if not existing:
            return None
        
        if "name" in subscription_data:
            existing.name = subscription_data["name"]
        if "status" in subscription_data:
            existing.status = subscription_data["status"]
        if "auto_download" in subscription_data:
            existing.auto_download = subscription_data["auto_download"]
        if "quality" in subscription_data:
            existing.quality = subscription_data["quality"]
        
        existing.updated_at = datetime.utcnow()
        
        self.db.add(existing)
        await self.db.commit()
        await self.db.refresh(existing)
        
        return existing
    
    async def delete_subscription(self, subscription_id: int) -> bool:
        """删除音乐订阅"""
        result = await self.db.execute(
            delete(MusicSubscription).where(MusicSubscription.id == subscription_id)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def get_library_stats(self) -> Dict:
        """获取音乐库统计"""
        try:
            # 统计曲目数
            tracks_result = await self.db.execute(
                select(func.count(MusicTrack.id))
            )
            total_tracks = tracks_result.scalar() or 0
            
            # 统计艺术家数
            artists_result = await self.db.execute(
                select(func.count(func.distinct(MusicTrack.artist)))
            )
            total_artists = artists_result.scalar() or 0
            
            # 统计专辑数
            albums_result = await self.db.execute(
                select(func.count(func.distinct(MusicTrack.album)))
            )
            total_albums = albums_result.scalar() or 0
            
            # 统计总大小
            size_result = await self.db.execute(
                select(func.sum(MusicLibrary.file_size_mb))
            )
            total_size_mb = size_result.scalar() or 0.0
            
            return {
                "total_tracks": total_tracks,
                "total_artists": total_artists,
                "total_albums": total_albums,
                "total_size_mb": round(total_size_mb, 2),
                "total_size_gb": round(total_size_mb / 1024, 2)
            }
        except Exception as e:
            logger.error(f"获取音乐库统计失败: {e}")
            return {
                "total_tracks": 0,
                "total_artists": 0,
                "total_albums": 0,
                "total_size_mb": 0.0,
                "total_size_gb": 0.0
            }
    
    async def scan_music_library(
        self,
        path: str,
        recursive: bool = True
    ) -> Dict:
        """扫描音乐库"""
        import os
        from pathlib import Path
        
        logger.info(f"扫描音乐库: {path} (递归: {recursive})")
        
        scanned_files = 0
        added_tracks = 0
        errors = []
        
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return {
                    "success": False,
                    "scanned_files": 0,
                    "added_tracks": 0,
                    "errors": [f"路径不存在: {path}"]
                }
            
            # 支持的音频格式
            audio_extensions = {'.mp3', '.flac', '.wav', '.aac', '.ogg', '.m4a', '.wma'}
            
            # 扫描文件
            if recursive:
                files = [f for f in path_obj.rglob('*') if f.suffix.lower() in audio_extensions]
            else:
                files = [f for f in path_obj.iterdir() if f.is_file() and f.suffix.lower() in audio_extensions]
            
            scanned_files = len(files)
            
            # 处理每个文件
            for file_path in files:
                try:
                    # 提取元数据
                    metadata = self.metadata_extractor.extract_metadata(str(file_path))
                    
                    # 刮削元数据
                    scraped_metadata = await self.music_scraper.scrape_music_file(str(file_path))
                    metadata.update(scraped_metadata)
                    
                    # 检查是否已存在
                    existing = await self.db.execute(
                        select(MusicTrack).where(MusicTrack.file_path == str(file_path))
                    )
                    if existing.scalar_one_or_none():
                        continue
                    
                    # 创建或更新曲目记录
                    track = MusicTrack(
                        title=metadata.get('title', 'Unknown Title'),
                        artist=metadata.get('artist', 'Unknown Artist'),
                        album=metadata.get('album', 'Unknown Album'),
                        duration=metadata.get('duration'),
                        genre=json.dumps(metadata.get('genre', [])) if isinstance(metadata.get('genre'), list) else metadata.get('genre'),
                        platform='local',
                        platform_id=str(file_path),
                        file_path=str(file_path),
                        file_size_mb=metadata.get('file_size', 0) / (1024 * 1024),
                        quality=metadata.get('format', 'Unknown'),
                        cover_url=None  # 封面URL将在后续下载
                    )
                    
                    self.db.add(track)
                    added_tracks += 1
                    
                except Exception as e:
                    logger.error(f"处理文件失败 {file_path}: {e}")
                    errors.append(f"{file_path}: {str(e)}")
            
            await self.db.commit()
            
            return {
                "success": True,
                "scanned_files": scanned_files,
                "added_tracks": added_tracks,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"扫描音乐库失败: {e}")
            return {
                "success": False,
                "scanned_files": scanned_files,
                "added_tracks": added_tracks,
                "errors": [str(e)]
            }
    
    async def get_lyrics(
        self,
        title: str,
        artist: str,
        platform: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """获取歌词"""
        return await self.lyrics_fetcher.fetch_lyrics(title, artist, platform)
    
    async def download_cover(
        self,
        title: str,
        artist: str,
        album: Optional[str] = None,
        platform: Optional[str] = None,
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """下载专辑封面"""
        return await self.cover_downloader.download_cover(
            title, artist, album, platform, save_path
        )
    
    async def scrape_music_file(self, file_path: str) -> Dict[str, Any]:
        """刮削音乐文件"""
        return await self.music_scraper.scrape_music_file(file_path)
    
    async def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取音乐文件元数据"""
        return self.metadata_extractor.extract_metadata(file_path)
    
    async def get_recommendations(
        self,
        user_id: str,
        count: int = 20,
        algorithm: str = "hybrid"
    ) -> List[Dict]:
        """获取音乐推荐"""
        # TODO: 实现真实的推荐算法
        # 当前返回模拟数据
        
        logger.info(f"获取音乐推荐: 用户 {user_id} (算法: {algorithm}, 数量: {count})")
        
        recommendations = []
        for i in range(count):
            recommendation = {
                "id": f"recommendation_{i+1}",
                "title": f"Recommended Song {i+1}",
                "artist": f"Artist {i+1}",
                "album": f"Album {i+1}",
                "reason": f"基于{algorithm}算法推荐",
                "score": 0.9 - i * 0.05,
                "cover_url": f"https://example.com/cover/{i+1}.jpg"
            }
            recommendations.append(recommendation)
        
        return recommendations
