"""
RSSHub服务层
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional, Dict
from datetime import datetime
from loguru import logger

from app.models.rsshub import RSSHubSource, RSSHubComposite, UserRSSHubSubscription
from app.models.user import User
from app.core.config import settings
from app.core.rsshub.client import get_rsshub_client
from app.modules.rss.parser import RSSParser
from app.modules.rsshub.constants import (
    LEGACY_PLACEHOLDER_IDS,
    RSSHUB_ERROR_MISSING_TARGET,
)
from app.modules.rsshub.schema_utils import ensure_subscription_health_columns


class RSSHubDisabledError(RuntimeError):
    """在 RSSHub 功能被禁用时抛出的异常。"""
    pass


class RSSHubService:
    """RSSHub服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.enabled = settings.RSSHUB_ENABLED
        self.client = get_rsshub_client() if self.enabled else None
        self.parser = RSSParser()

    def _ensure_enabled(self) -> None:
        if not self.enabled:
            raise RSSHubDisabledError("RSSHub 功能已禁用，请在环境变量 RSSHUB_ENABLED 中启用后再使用相关功能")
    
    async def list_sources(
        self,
        user_id: Optional[int] = None,
        group: Optional[str] = None,
        type: Optional[str] = None
    ) -> List[Dict]:
        """
        获取源列表，附带用户订阅状态
        
        Args:
            user_id: 用户ID（用于获取订阅状态）
            group: 分组过滤（rank/update）
            type: 类型过滤（video/tv/variety/anime/music/mixed）
            
        Returns:
            源列表，每个源包含enabled状态
        """
        self._ensure_enabled()
        await ensure_subscription_health_columns(self.db)

        query = select(RSSHubSource)
        
        if group:
            query = query.where(RSSHubSource.group == group)
        if type:
            query = query.where(RSSHubSource.type == type)
        
        query = query.order_by(RSSHubSource.group, RSSHubSource.name)
        
        result = await self.db.execute(query)
        sources = result.scalars().all()
        
        # 获取用户订阅状态
        user_subscriptions = {}
        if user_id:
            sub_result = await self.db.execute(
                select(UserRSSHubSubscription).where(
                    and_(
                        UserRSSHubSubscription.user_id == user_id,
                        UserRSSHubSubscription.target_type == 'source'
                    )
                )
            )
            for sub in sub_result.scalars().all():
                user_subscriptions[sub.target_id] = sub.enabled
        
        # 构建响应
        source_list = []
        for source in sources:
            source_dict = {
                "id": source.id,
                "name": source.name,
                "url_path": source.url_path,
                "type": source.type,
                "group": source.group,
                "description": source.description,
                "default_enabled": source.default_enabled,
                "enabled": user_subscriptions.get(source.id, source.default_enabled)
            }
            source_list.append(source_dict)
        
        return source_list
    
    async def list_composites(
        self,
        user_id: Optional[int] = None,
        type: Optional[str] = None
    ) -> List[Dict]:
        """
        获取组合订阅列表，附带用户订阅状态
        
        Args:
            user_id: 用户ID（用于获取订阅状态）
            type: 类型过滤（video/tv/variety/anime/music/mixed）
            
        Returns:
            组合订阅列表，每个组合包含enabled状态和源列表
        """
        self._ensure_enabled()
        await ensure_subscription_health_columns(self.db)

        query = select(RSSHubComposite)
        
        if type:
            query = query.where(RSSHubComposite.type == type)
        
        query = query.order_by(RSSHubComposite.name)
        
        result = await self.db.execute(query)
        composites = result.scalars().all()
        
        # 获取用户订阅状态
        user_subscriptions = {}
        if user_id:
            sub_result = await self.db.execute(
                select(UserRSSHubSubscription).where(
                    and_(
                        UserRSSHubSubscription.user_id == user_id,
                        UserRSSHubSubscription.target_type == 'composite'
                    )
                )
            )
            for sub in sub_result.scalars().all():
                user_subscriptions[sub.target_id] = sub.enabled
        
        # 构建响应
        composite_list = []
        for composite in composites:
            # 获取关联的源
            await self.db.refresh(composite, ['sources'])
            source_ids = [s.id for s in composite.sources]
            
            composite_dict = {
                "id": composite.id,
                "name": composite.name,
                "type": composite.type,
                "description": composite.description,
                "default_enabled": composite.default_enabled,
                "enabled": user_subscriptions.get(composite.id, composite.default_enabled),
                "sources": source_ids
            }
            composite_list.append(composite_dict)
        
        return composite_list
    
    async def toggle_subscription(
        self,
        user_id: int,
        target_type: str,
        target_id: str,
        enabled: bool
    ) -> bool:
        """
        切换订阅状态
        
        Args:
            user_id: 用户ID
            target_type: 目标类型（source/composite）
            target_id: 目标ID
            enabled: 是否启用
            
        Returns:
            是否成功
        """
        self._ensure_enabled()
        await ensure_subscription_health_columns(self.db)

        if target_type not in ['source', 'composite']:
            raise ValueError(f"无效的目标类型: {target_type}")

        # 校验目标是否存在
        target = await self.db.get(RSSHubSource if target_type == 'source' else RSSHubComposite, target_id)
        if not target:
            logger.warning(f"用户 {user_id} 尝试订阅不存在的 {target_type}: {target_id}")
            raise ValueError(f"{target_type} 不存在: {target_id}")
        
        # 查找现有订阅
        result = await self.db.execute(
            select(UserRSSHubSubscription).where(
                and_(
                    UserRSSHubSubscription.user_id == user_id,
                    UserRSSHubSubscription.target_id == target_id,
                    UserRSSHubSubscription.target_type == target_type
                )
            )
        )
        subscription = result.scalar_one_or_none()
        
        if subscription:
            # 更新现有订阅
            subscription.enabled = enabled
            subscription.updated_at = datetime.utcnow()
            if enabled:
                subscription.last_error_code = None
                subscription.last_error_message = None
                subscription.last_error_at = None
        else:
            # 创建新订阅
            subscription = UserRSSHubSubscription(
                user_id=user_id,
                target_id=target_id,
                target_type=target_type,
                enabled=enabled
            )
            self.db.add(subscription)
        
        await self.db.commit()
        logger.info(f"用户 {user_id} {'启用' if enabled else '禁用'}了 {target_type} {target_id}")
        return True
    
    async def preview_source(self, source_id: str, limit: int = 5) -> List[Dict]:
        """
        预览源内容
        
        Args:
            source_id: 源ID
            limit: 返回的项数量
            
        Returns:
            RSS项列表
        """
        self._ensure_enabled()
        # 获取源信息
        result = await self.db.execute(
            select(RSSHubSource).where(RSSHubSource.id == source_id)
        )
        source = result.scalar_one_or_none()
        
        if not source:
            raise ValueError(f"源不存在: {source_id}")
        
        # 获取RSS内容
        items = await self.client.fetch_rss_items(source.url_path, limit=limit)
        return items
    
    async def get_user_subscriptions(
        self,
        user_id: int,
        enabled_only: bool = True
    ) -> List[UserRSSHubSubscription]:
        """
        获取用户的RSSHub订阅列表
        
        Args:
            user_id: 用户ID
            enabled_only: 是否只返回启用的订阅
            
        Returns:
            订阅列表
        """
        self._ensure_enabled()
        await ensure_subscription_health_columns(self.db)

        query = select(UserRSSHubSubscription).where(
            UserRSSHubSubscription.user_id == user_id
        )
        
        if enabled_only:
            query = query.where(UserRSSHubSubscription.enabled == True)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_subscription_health(
        self,
        *,
        user_id: Optional[int] = None,
        target_type: Optional[str] = None,
        only_legacy: bool = False,
        limit: int = 100,
    ) -> List[Dict]:
        """返回 RSSHub 订阅健康数据"""
        self._ensure_enabled()
        await ensure_subscription_health_columns(self.db)

        query = (
            select(UserRSSHubSubscription, User)
            .join(User, User.id == UserRSSHubSubscription.user_id)
            .where(UserRSSHubSubscription.enabled == False)
            .order_by(UserRSSHubSubscription.updated_at.desc())
        )

        if user_id:
            query = query.where(UserRSSHubSubscription.user_id == user_id)

        if target_type in ("source", "composite"):
            query = query.where(UserRSSHubSubscription.target_type == target_type)

        if limit:
            query = query.limit(limit)

        result = await self.db.execute(query)
        rows = result.all()

        source_ids = {sub.target_id for sub, _ in rows if sub.target_type == "source"}
        composite_ids = {sub.target_id for sub, _ in rows if sub.target_type == "composite"}

        source_map: Dict[str, str] = {}
        if source_ids:
            src_result = await self.db.execute(
                select(RSSHubSource).where(RSSHubSource.id.in_(list(source_ids)))
            )
            for src in src_result.scalars().all():
                source_map[src.id] = src.name

        composite_map: Dict[str, str] = {}
        if composite_ids:
            comp_result = await self.db.execute(
                select(RSSHubComposite).where(RSSHubComposite.id.in_(list(composite_ids)))
            )
            for comp in comp_result.scalars().all():
                composite_map[comp.id] = comp.name

        items: List[Dict] = []
        for sub, user in rows:
            is_legacy = sub.target_id in LEGACY_PLACEHOLDER_IDS
            has_error = bool(sub.last_error_code)
            if only_legacy and not is_legacy:
                continue

            target_name = (
                source_map.get(sub.target_id)
                if sub.target_type == "source"
                else composite_map.get(sub.target_id)
            )

            items.append(
                {
                    "user_id": sub.user_id,
                    "username": getattr(user, "username", None),
                    "target_id": sub.target_id,
                    "target_type": sub.target_type,
                    "target_name": target_name,
                    "enabled": sub.enabled,
                    "is_legacy_placeholder": is_legacy,
                    "last_error_code": sub.last_error_code,
                    "last_error_message": sub.last_error_message,
                    "last_error_at": self._to_iso(sub.last_error_at),
                    "last_checked_at": self._to_iso(sub.last_checked_at),
                    "updated_at": self._to_iso(sub.updated_at),
                    "health_status": "needs_fix" if (is_legacy or has_error) else "ok",
                }
            )

        return items

    @staticmethod
    def _to_iso(value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None

