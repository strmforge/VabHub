"""
日历服务
"""
from datetime import datetime, timedelta
from typing import List, Optional

import httpx
from loguru import logger
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.media_types import is_tv_like
from app.core.config import settings
from app.models.download import DownloadTask
from app.models.subscription import Subscription

TMDB_API_BASE = "https://api.themoviedb.org/3"


class CalendarService:
    """日历服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_calendar_events(
        self,
        start_date: datetime,
        end_date: datetime,
        event_types: Optional[List[str]] = None
    ) -> List[dict]:
        """获取日历事件"""
        events = []
        
        # 默认包含所有事件类型
        if event_types is None:
            event_types = ["subscription", "download", "media_update"]
        
        try:
            # 1. 从订阅中获取媒体发布日期
            if "subscription" in event_types:
                subscription_events = await self._get_subscription_events(start_date, end_date)
                events.extend(subscription_events)
            
            # 2. 从下载任务中获取下载完成时间
            if "download" in event_types:
                download_events = await self._get_download_events(start_date, end_date)
                events.extend(download_events)
            
            # 3. 从媒体更新中获取更新事件（未来可以从TMDB获取）
            if "media_update" in event_types:
                media_events = await self._get_media_update_events(start_date, end_date)
                events.extend(media_events)
            
            # 按日期排序
            events.sort(key=lambda x: x.get("date") or datetime.min)
            
            return events
        
        except Exception as e:
            logger.error(f"获取日历事件失败: {e}")
            return []
    
    async def _get_subscription_events(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[dict]:
        """从订阅中获取日历事件"""
        events = []
        
        try:
            # 获取所有活跃的订阅
            result = await self.db.execute(
                select(Subscription).where(
                    Subscription.status == "active"
                )
            )
            subscriptions = result.scalars().all()
            
            api_key = settings.TMDB_API_KEY
            
            for subscription in subscriptions:
                if subscription.media_type == "movie":
                    # 电影：使用发布日期
                    if subscription.tmdb_id and api_key:
                        try:
                            movie_details = await self._get_tmdb_movie_details(subscription.tmdb_id, api_key)
                            release_date = movie_details.get("release_date")
                            if release_date:
                                event_date = datetime.strptime(release_date, "%Y-%m-%d")
                                event = {
                                    "id": f"subscription_{subscription.id}",
                                    "title": f"电影上映: {subscription.title}",
                                    "date": event_date,
                                    "type": "subscription",
                                    "subscription_id": subscription.id,
                                    "media_type": subscription.media_type,
                                    "color": "#1976d2",
                                    "description": f"订阅的电影: {subscription.title}"
                                }
                                if start_date <= event_date <= end_date:
                                    events.append(event)
                        except Exception as e:
                            logger.warning(f"获取电影详情失败 {subscription.tmdb_id}: {e}")
                
                elif is_tv_like(subscription.media_type):
                    # 电视剧：获取播出时间
                    if subscription.tmdb_id and api_key:
                        try:
                            tv_events = await self._get_tv_air_dates(
                                subscription.tmdb_id,
                                subscription.season,
                                subscription.id,
                                subscription.title,
                                start_date,
                                end_date,
                                api_key
                            )
                            events.extend(tv_events)
                        except Exception as e:
                            logger.warning(f"获取电视剧播出时间失败 {subscription.tmdb_id}: {e}")
        
        except Exception as e:
            logger.error(f"获取订阅事件失败: {e}")
        
        return events
    
    async def _get_tmdb_movie_details(self, tmdb_id: int, api_key: str) -> dict:
        """获取TMDB电影详情"""
        async with httpx.AsyncClient() as client:
            url = f"{TMDB_API_BASE}/movie/{tmdb_id}"
            params = {
                "api_key": api_key,
                "language": "zh-CN"
            }
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            return response.json()
    
    async def _get_tv_air_dates(
        self,
        tmdb_id: int,
        season_number: Optional[int],
        subscription_id: int,
        title: str,
        start_date: datetime,
        end_date: datetime,
        api_key: str
    ) -> List[dict]:
        """获取电视剧的播出时间"""
        events = []
        
        try:
            async with httpx.AsyncClient() as client:
                # 获取电视剧详情
                url = f"{TMDB_API_BASE}/tv/{tmdb_id}"
                params = {
                    "api_key": api_key,
                    "language": "zh-CN"
                }
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                tv_data = response.json()
                
                # 获取下一集播出时间
                next_episode = tv_data.get("next_episode_to_air")
                if next_episode and next_episode.get("air_date"):
                    air_date_str = next_episode.get("air_date")
                    air_date = datetime.strptime(air_date_str, "%Y-%m-%d")
                    
                    if start_date <= air_date <= end_date:
                        event = {
                            "id": f"subscription_{subscription_id}_next_episode",
                            "title": f"新集播出: {title} S{next_episode.get('season_number')}E{next_episode.get('episode_number')}",
                            "date": air_date,
                            "type": "subscription",
                            "subscription_id": subscription_id,
                            "media_type": "tv",
                            "season": next_episode.get("season_number"),
                            "color": "#1976d2",
                            "description": f"{title} 第 {next_episode.get('season_number')} 季第 {next_episode.get('episode_number')} 集"
                        }
                        events.append(event)
                
                # 如果指定了季数，获取该季的播出时间
                if season_number is not None:
                    season_url = f"{TMDB_API_BASE}/tv/{tmdb_id}/season/{season_number}"
                    season_response = await client.get(season_url, params=params, timeout=10.0)
                    if season_response.is_success:
                        season_data = season_response.json()
                        episodes = season_data.get("episodes", [])
                        
                        for episode in episodes:
                            air_date_str = episode.get("air_date")
                            if air_date_str:
                                try:
                                    air_date = datetime.strptime(air_date_str, "%Y-%m-%d")
                                    if start_date <= air_date <= end_date:
                                        event = {
                                            "id": f"subscription_{subscription_id}_s{season_number}_e{episode.get('episode_number')}",
                                            "title": f"{title} S{season_number}E{episode.get('episode_number')}",
                                            "date": air_date,
                                            "type": "subscription",
                                            "subscription_id": subscription_id,
                                            "media_type": "tv",
                                            "season": season_number,
                                            "color": "#1976d2",
                                            "description": f"{title} 第 {season_number} 季第 {episode.get('episode_number')} 集: {episode.get('name', '')}"
                                        }
                                        events.append(event)
                                except ValueError:
                                    continue
        
        except Exception as e:
            logger.error(f"获取电视剧播出时间失败: {e}")
        
        return events
    
    async def _get_download_events(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[dict]:
        """从下载任务中获取日历事件"""
        events = []
        
        try:
            # 获取在日期范围内完成的下载任务
            result = await self.db.execute(
                select(DownloadTask).where(
                    and_(
                        DownloadTask.status == "completed",
                        DownloadTask.completed_at.isnot(None),
                        DownloadTask.completed_at >= start_date,
                        DownloadTask.completed_at <= end_date
                    )
                )
            )
            downloads = result.scalars().all()
            
            for download in downloads:
                event = {
                    "id": f"download_{download.id}",
                    "title": f"下载完成: {download.title}",
                    "date": download.completed_at,
                    "type": "download",
                    "download_id": download.id,
                    "color": "#4caf50",  # 绿色
                    "description": f"下载完成: {download.title}"
                }
                events.append(event)
        
        except Exception as e:
            logger.error(f"获取下载事件失败: {e}")
        
        return events
    
    async def _get_media_update_events(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[dict]:
        """获取媒体更新事件"""
        events = []
        
        # TODO: 从TMDB获取即将上映/播出的媒体信息
        # 这里可以调用TMDB API获取：
        # - 即将上映的电影
        # - 即将播出的电视剧集
        # - 媒体更新通知
        
        # 示例：获取未来30天内的媒体更新
        # 实际实现应该调用TMDB API
        
        return events
    
    async def get_subscription_calendar_ics(
        self,
        subscription_id: int
    ) -> Optional[str]:
        """生成订阅的iCalendar格式日历"""
        try:
            result = await self.db.execute(
                select(Subscription).where(Subscription.id == subscription_id)
            )
            subscription = result.scalar_one_or_none()
            
            if not subscription:
                return None
            
            # 生成iCalendar格式
            # 这里简化处理，实际应该根据TMDB数据生成完整的日历
            ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//VabHub//Calendar//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:subscription_{subscription_id}@vabhub
DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{subscription.created_at.strftime('%Y%m%dT%H%M%SZ')}
SUMMARY:{subscription.title}
DESCRIPTION:订阅: {subscription.title}
END:VEVENT
END:VCALENDAR"""
            
            return ics_content
        
        except Exception as e:
            logger.error(f"生成订阅日历失败: {e}")
            return None

