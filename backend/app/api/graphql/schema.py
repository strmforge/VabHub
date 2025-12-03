"""
GraphQL Schema定义
使用strawberry-graphql构建现代化API
"""

import strawberry
from typing import List, Optional, AsyncIterator
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession


# ==================== 类型定义 ====================

@strawberry.type
class SubscriptionType:
    """订阅类型"""
    id: int
    title: str
    original_title: Optional[str]
    year: Optional[int]
    media_type: str
    tmdb_id: Optional[int]
    tvdb_id: Optional[int]
    imdb_id: Optional[str]
    poster: Optional[str]
    backdrop: Optional[str]
    status: str
    season: Optional[int]
    total_episode: Optional[int]
    quality: Optional[str]
    resolution: Optional[str]
    effect: Optional[str]
    auto_download: bool
    best_version: bool
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_model(cls, sub):
        """从数据库模型转换为GraphQL类型"""
        return cls(
            id=sub.id,
            title=sub.title,
            original_title=sub.original_title,
            year=sub.year,
            media_type=sub.media_type,
            tmdb_id=sub.tmdb_id,
            tvdb_id=sub.tvdb_id,
            imdb_id=sub.imdb_id,
            poster=sub.poster,
            backdrop=sub.backdrop,
            status=sub.status,
            season=sub.season,
            total_episode=sub.total_episode,
            quality=sub.quality,
            resolution=sub.resolution,
            effect=sub.effect,
            auto_download=sub.auto_download,
            best_version=sub.best_version,
            created_at=sub.created_at,
            updated_at=sub.updated_at
        )


@strawberry.type
class MediaType:
    """媒体类型"""
    id: int
    title: str
    original_title: Optional[str]
    year: Optional[int]
    media_type: str
    tmdb_id: Optional[int]
    tvdb_id: Optional[int]
    imdb_id: Optional[str]
    poster_url: Optional[str]
    backdrop_url: Optional[str]
    overview: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_model(cls, media):
        """从数据库模型转换为GraphQL类型"""
        return cls(
            id=media.id,
            title=media.title,
            original_title=media.original_title,
            year=media.year,
            media_type=media.media_type,
            tmdb_id=media.tmdb_id,
            tvdb_id=media.tvdb_id,
            imdb_id=media.imdb_id,
            poster_url=media.poster_url,
            backdrop_url=media.backdrop_url,
            overview=media.overview,
            created_at=media.created_at,
            updated_at=media.updated_at
        )


@strawberry.type
class DownloadTaskType:
    """下载任务类型"""
    id: int
    task_id: str
    title: str
    status: str
    progress: float
    size_gb: float
    downloaded_gb: float
    speed_mbps: Optional[float]
    eta: Optional[int]
    downloader: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    
    @classmethod
    def from_model(cls, task):
        """从数据库模型转换为GraphQL类型"""
        return cls(
            id=task.id,
            task_id=task.task_id,
            title=task.title,
            status=task.status,
            progress=task.progress,
            size_gb=task.size_gb,
            downloaded_gb=task.downloaded_gb,
            speed_mbps=task.speed_mbps,
            eta=task.eta,
            downloader=task.downloader,
            created_at=task.created_at,
            updated_at=task.updated_at,
            completed_at=task.completed_at
        )


@strawberry.type
class LogEntryType:
    """日志条目类型"""
    level: str
    message: str
    source: str
    component: str
    timestamp: datetime


@strawberry.type
class DashboardStatsType:
    """仪表盘统计类型"""
    total_media: int
    total_subscriptions: int
    active_downloads: int
    completed_downloads: int
    total_storage_gb: float
    used_storage_gb: float


# ==================== 输入类型 ====================

@strawberry.input
class SubscriptionInput:
    """订阅输入类型"""
    title: str
    original_title: Optional[str] = None
    year: Optional[int] = None
    media_type: str
    tmdb_id: Optional[int] = None
    quality: Optional[str] = None
    auto_download: bool = True


@strawberry.input
class SubscriptionFilter:
    """订阅过滤类型"""
    status: Optional[str] = None
    media_type: Optional[str] = None
    year: Optional[int] = None


@strawberry.input
class DownloadTaskFilter:
    """下载任务过滤类型"""
    status: Optional[str] = None
    downloader: Optional[str] = None


# ==================== Query ====================

@strawberry.type
class Query:
    """GraphQL查询根类型"""
    
    @strawberry.field
    async def subscriptions(
        self,
        filter: Optional[SubscriptionFilter] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SubscriptionType]:
        """获取订阅列表"""
        from app.core.database import AsyncSessionLocal
        from app.models.subscription import Subscription
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            query = select(Subscription)
            
            if filter:
                if filter.status:
                    query = query.where(Subscription.status == filter.status)
                if filter.media_type:
                    query = query.where(Subscription.media_type == filter.media_type)
                if filter.year:
                    query = query.where(Subscription.year == filter.year)
            
            query = query.limit(limit).offset(offset)
            result = await db.execute(query)
            subscriptions = result.scalars().all()
            
            return [SubscriptionType.from_model(sub) for sub in subscriptions]
    
    @strawberry.field
    async def subscription(self, id: int) -> Optional[SubscriptionType]:
        """根据ID获取订阅"""
        from app.core.database import AsyncSessionLocal
        from app.models.subscription import Subscription
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Subscription).where(Subscription.id == id))
            sub = result.scalar_one_or_none()
            
            if sub:
                return SubscriptionType.from_model(sub)
            return None
    
    @strawberry.field
    async def media_list(
        self,
        search: Optional[str] = None,
        media_type: Optional[str] = None,
        year: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[MediaType]:
        """获取媒体列表"""
        from app.core.database import AsyncSessionLocal
        from app.models.media import Media
        from sqlalchemy import select, or_
        
        async with AsyncSessionLocal() as db:
            query = select(Media)
            
            if search:
                query = query.where(
                    or_(
                        Media.title.contains(search),
                        Media.original_title.contains(search)
                    )
                )
            if media_type:
                query = query.where(Media.media_type == media_type)
            if year:
                query = query.where(Media.year == year)
            
            query = query.limit(limit).offset(offset)
            result = await db.execute(query)
            media_list = result.scalars().all()
            
            return [MediaType.from_model(media) for media in media_list]
    
    @strawberry.field
    async def media(self, id: int) -> Optional[MediaType]:
        """根据ID获取媒体"""
        from app.core.database import AsyncSessionLocal
        from app.models.media import Media
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Media).where(Media.id == id))
            media = result.scalar_one_or_none()
            
            if media:
                return MediaType.from_model(media)
            return None
    
    @strawberry.field
    async def download_tasks(
        self,
        filter: Optional[DownloadTaskFilter] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DownloadTaskType]:
        """获取下载任务列表"""
        from app.core.database import AsyncSessionLocal
        from app.models.download import DownloadTask
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            query = select(DownloadTask)
            
            if filter:
                if filter.status:
                    query = query.where(DownloadTask.status == filter.status)
                if filter.downloader:
                    query = query.where(DownloadTask.downloader == filter.downloader)
            
            query = query.limit(limit).offset(offset)
            result = await db.execute(query)
            tasks = result.scalars().all()
            
            return [DownloadTaskType.from_model(task) for task in tasks]
    
    @strawberry.field
    async def download_task(self, id: int) -> Optional[DownloadTaskType]:
        """根据ID获取下载任务"""
        from app.core.database import AsyncSessionLocal
        from app.models.download import DownloadTask
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(DownloadTask).where(DownloadTask.id == id))
            task = result.scalar_one_or_none()
            
            if task:
                return DownloadTaskType.from_model(task)
            return None
    
    @strawberry.field
    async def dashboard_stats(self) -> DashboardStatsType:
        """获取仪表盘统计信息"""
        from app.core.database import AsyncSessionLocal
        from app.models.media import Media
        from app.models.subscription import Subscription
        from app.models.download import DownloadTask
        from sqlalchemy import select, func
        
        async with AsyncSessionLocal() as db:
            # 统计媒体数量
            result = await db.execute(select(func.count(Media.id)))
            total_media = result.scalar() or 0
            
            # 统计订阅数量
            result = await db.execute(select(func.count(Subscription.id)))
            total_subscriptions = result.scalar() or 0
            
            # 统计下载任务
            result = await db.execute(
                select(func.count(DownloadTask.id)).where(DownloadTask.status == "downloading")
            )
            active_downloads = result.scalar() or 0
            
            result = await db.execute(
                select(func.count(DownloadTask.id)).where(DownloadTask.status == "completed")
            )
            completed_downloads = result.scalar() or 0
            
            # TODO: 实现存储统计
            total_storage_gb = 0.0
            used_storage_gb = 0.0
            
            return DashboardStatsType(
                total_media=total_media,
                total_subscriptions=total_subscriptions,
                active_downloads=active_downloads,
                completed_downloads=completed_downloads,
                total_storage_gb=total_storage_gb,
                used_storage_gb=used_storage_gb
            )


# ==================== Mutation ====================

@strawberry.type
class Mutation:
    """GraphQL变更根类型"""
    
    @strawberry.mutation
    async def create_subscription(self, input: SubscriptionInput) -> SubscriptionType:
        """创建订阅"""
        from app.core.database import AsyncSessionLocal
        from app.models.subscription import Subscription
        
        async with AsyncSessionLocal() as db:
            subscription = Subscription(
                title=input.title,
                original_title=input.original_title,
                year=input.year,
                media_type=input.media_type,
                tmdb_id=input.tmdb_id,
                quality=input.quality,
                auto_download=input.auto_download,
                status="active"
            )
            db.add(subscription)
            await db.commit()
            await db.refresh(subscription)
            
            return SubscriptionType.from_model(subscription)
    
    @strawberry.mutation
    async def update_subscription(
        self,
        id: int,
        input: SubscriptionInput
    ) -> Optional[SubscriptionType]:
        """更新订阅"""
        from app.core.database import AsyncSessionLocal
        from app.models.subscription import Subscription
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Subscription).where(Subscription.id == id))
            subscription = result.scalar_one_or_none()
            
            if not subscription:
                return None
            
            subscription.title = input.title
            subscription.original_title = input.original_title
            subscription.year = input.year
            subscription.media_type = input.media_type
            subscription.tmdb_id = input.tmdb_id
            subscription.quality = input.quality
            subscription.auto_download = input.auto_download
            
            await db.commit()
            await db.refresh(subscription)
            
            return SubscriptionType.from_model(subscription)
    
    @strawberry.mutation
    async def delete_subscription(self, id: int) -> bool:
        """删除订阅"""
        from app.core.database import AsyncSessionLocal
        from app.models.subscription import Subscription
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Subscription).where(Subscription.id == id))
            subscription = result.scalar_one_or_none()
            
            if not subscription:
                return False
            
            await db.delete(subscription)
            await db.commit()
            
            return True
    
    @strawberry.mutation
    async def pause_subscription(self, id: int) -> Optional[SubscriptionType]:
        """暂停订阅"""
        from app.core.database import AsyncSessionLocal
        from app.models.subscription import Subscription
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Subscription).where(Subscription.id == id))
            subscription = result.scalar_one_or_none()
            
            if not subscription:
                return None
            
            subscription.status = "paused"
            await db.commit()
            await db.refresh(subscription)
            
            return SubscriptionType.from_model(subscription)
    
    @strawberry.mutation
    async def resume_subscription(self, id: int) -> Optional[SubscriptionType]:
        """恢复订阅"""
        from app.core.database import AsyncSessionLocal
        from app.models.subscription import Subscription
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Subscription).where(Subscription.id == id))
            subscription = result.scalar_one_or_none()
            
            if not subscription:
                return None
            
            subscription.status = "active"
            await db.commit()
            await db.refresh(subscription)
            
            return SubscriptionType.from_model(subscription)


# ==================== Subscription ====================

@strawberry.type
class SubscriptionRoot:
    """GraphQL订阅根类型（实时数据推送）"""
    
    @strawberry.subscription
    async def log_stream(
        self,
        level: Optional[str] = None,
        source: Optional[str] = None
    ) -> AsyncIterator[LogEntryType]:
        """实时日志流订阅"""
        from app.modules.log_center.service import get_log_center
        import asyncio
        
        log_center = get_log_center()
        
        # 使用轮询方式模拟实时推送
        last_timestamp = datetime.now()
        
        while True:
            # 获取最近的日志
            filters = {}
            if level:
                filters["level"] = level
            if source:
                filters["source"] = source
            
            logs = await log_center.get_logs(limit=100, **filters)
            
            # 只返回新日志
            for log in logs:
                log_timestamp = datetime.fromisoformat(log["timestamp"])
                if log_timestamp > last_timestamp:
                    yield LogEntryType(
                        level=log["level"],
                        message=log["message"],
                        source=log["source"],
                        component=log["component"],
                        timestamp=log_timestamp
                    )
            
            last_timestamp = datetime.now()
            await asyncio.sleep(1)  # 每秒检查一次


# ==================== Schema ====================

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=SubscriptionRoot
)

