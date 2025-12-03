"""
RSSHub定时任务：抓取、合并、去重
"""

import hashlib
import re
from typing import List, Dict, Set, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from loguru import logger

from app.models.rsshub import RSSHubSource, RSSHubComposite, UserRSSHubSubscription
from app.core.config import settings
from app.core.rsshub.client import get_rsshub_client
from app.modules.rss.parser import RSSParser, RSSItem
from app.modules.rsshub.media_extractor import RSSHubMediaExtractor
from app.modules.rsshub.constants import (
    RSSHUB_ERROR_FETCH_FAILED,
    RSSHUB_ERROR_MISSING_TARGET,
    RSSHUB_ERROR_PROCESSING,
)
from app.modules.rsshub.schema_utils import ensure_subscription_health_columns


class RSSHubScheduler:
    """RSSHub定时任务调度器"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.enabled = settings.RSSHUB_ENABLED
        self.client = get_rsshub_client() if self.enabled else None
        self.parser = RSSParser()
        self.media_extractor = RSSHubMediaExtractor()
    
    async def process_user_subscriptions(self, user_id: int) -> Dict[str, int]:
        """
        处理用户的所有RSSHub订阅
        
        Args:
            user_id: 用户ID
            
        Returns:
            处理统计: {"processed": count, "new_items": count, "errors": count}
        """
        if not self.enabled:
            logger.info("RSSHub 功能已禁用，跳过用户订阅处理")
            return {"processed": 0, "new_items": 0, "errors": 0}

        # 确保结构最新
        await ensure_subscription_health_columns(self.db)

        # 获取用户的所有启用订阅
        service = RSSHubService(self.db)
        subscriptions = await service.get_user_subscriptions(user_id, enabled_only=True)
        
        stats = {
            "processed": 0,
            "new_items": 0,
            "errors": 0
        }
        
        for subscription in subscriptions:
            try:
                if subscription.target_type == 'source':
                    # 处理单源
                    new_count = await self._process_source_subscription(subscription)
                    stats["new_items"] += new_count
                elif subscription.target_type == 'composite':
                    # 处理组合订阅
                    new_count = await self._process_composite_subscription(subscription)
                    stats["new_items"] += new_count
                
                stats["processed"] += 1
            except Exception as e:
                logger.error(f"处理用户 {user_id} 的订阅 {subscription.target_id} 失败: {e}")
                stats["errors"] += 1
        
        return stats
    
    async def _process_source_subscription(
        self,
        subscription: UserRSSHubSubscription
    ) -> int:
        """
        处理单源订阅
        
        Args:
            subscription: 用户订阅对象
            
        Returns:
            新项数量
        """
        # 获取源信息
        result = await self.db.execute(
            select(RSSHubSource).where(RSSHubSource.id == subscription.target_id)
        )
        source = result.scalar_one_or_none()
        
        if not source:
            await self._handle_missing_target(subscription, target_kind="source")
            return 0
        
        try:
            rss_xml = await self.client.fetch_rss(source.url_path)
        except Exception as exc:
            await self._mark_subscription_error(subscription, RSSHUB_ERROR_FETCH_FAILED, str(exc))
            raise

        try:
            import feedparser

            feed = feedparser.parse(rss_xml)
            items = []
            for entry in feed.entries:
                pub_date = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    from datetime import datetime as dt

                    pub_date = dt(*entry.published_parsed[:6])
                items.append(
                    RSSItem(
                        title=entry.get("title", ""),
                        link=entry.get("link", ""),
                        description=entry.get("description", ""),
                        pub_date=pub_date,
                    )
                )

            if not items:
                await self._clear_subscription_error(subscription)
                return 0

            if subscription.last_item_hash:
                new_items = []
                for item in items:
                    if item.hash != subscription.last_item_hash:
                        new_items.append(item)
                    else:
                        break
            else:
                new_items = items[:1] if items else []

            if new_items:
                await self._enqueue_items_to_workflow(new_items, source.type, subscription.user_id)
                subscription.last_item_hash = new_items[0].hash
                subscription.last_checked_at = datetime.utcnow()
                await self._clear_subscription_error(subscription, commit=False)
                await self.db.commit()
            else:
                await self._clear_subscription_error(subscription)

            return len(new_items)
        except Exception as exc:
            await self._mark_subscription_error(subscription, RSSHUB_ERROR_PROCESSING, str(exc))
            raise
    
    async def _process_composite_subscription(
        self,
        subscription: UserRSSHubSubscription
    ) -> int:
        """
        处理组合订阅（合并、去重）
        
        Args:
            subscription: 用户订阅对象
            
        Returns:
            新项数量
        """
        # 获取组合信息
        result = await self.db.execute(
            select(RSSHubComposite).where(RSSHubComposite.id == subscription.target_id)
        )
        composite = result.scalar_one_or_none()
        
        if not composite:
            await self._handle_missing_target(subscription, target_kind="composite")
            return 0
        
        try:
            await self.db.refresh(composite, ["sources"])
            
            all_items = []
            for source in composite.sources:
                try:
                    rss_xml = await self.client.fetch_rss(source.url_path)
                    import feedparser

                    feed = feedparser.parse(rss_xml)
                    items = []
                    for entry in feed.entries:
                        pub_date = None
                        if hasattr(entry, "published_parsed") and entry.published_parsed:
                            from datetime import datetime as dt

                            pub_date = dt(*entry.published_parsed[:6])
                        items.append(
                            {
                                "title": entry.get("title", ""),
                                "link": entry.get("link", ""),
                                "description": entry.get("description", ""),
                                "pub_date": pub_date.isoformat() if pub_date else None,
                                "hash": hashlib.md5(
                                    f"{entry.get('title', '')}{entry.get('link', '')}".encode("utf-8")
                                ).hexdigest(),
                            }
                        )

                    for item in items:
                        item["source_id"] = source.id
                        item["source_name"] = source.name
                        all_items.append(item)
                except Exception as e:  # pragma: no cover - 网络异常路径
                    logger.error(f"抓取源 {source.id} 失败: {e}")
                    continue
            
            if not all_items:
                await self._clear_subscription_error(subscription)
                return 0
            
            deduplicated_items = await self._deduplicate_items(all_items)
            
            if subscription.last_item_hash:
                new_items = []
                for item in deduplicated_items:
                    if item.get("hash") != subscription.last_item_hash:
                        new_items.append(item)
                    else:
                        break
            else:
                new_items = deduplicated_items[:1] if deduplicated_items else []
            
            if new_items:
                await self._enqueue_items_to_workflow(new_items, composite.type, subscription.user_id)
                subscription.last_item_hash = new_items[0].get("hash")
                subscription.last_checked_at = datetime.utcnow()
                await self._clear_subscription_error(subscription, commit=False)
                await self.db.commit()
            else:
                await self._clear_subscription_error(subscription)
            
            return len(new_items)
        except Exception as exc:
            await self._mark_subscription_error(subscription, RSSHUB_ERROR_PROCESSING, str(exc))
            raise

    async def _handle_missing_target(
        self,
        subscription: UserRSSHubSubscription,
        target_kind: str,
    ) -> None:
        """当订阅指向的 Source/Composite 不存在时的统一处理"""
        logger.warning(
            f"RSSHub订阅目标缺失: user={subscription.user_id} "
            f"type={target_kind} target_id={subscription.target_id}，已禁用该订阅"
        )
        await self._mark_subscription_error(
            subscription,
            RSSHUB_ERROR_MISSING_TARGET,
            f"{target_kind}:{subscription.target_id}",
            disable=True,
        )
    
    async def _deduplicate_items(self, items: List[Dict]) -> List[Dict]:
        """
        对RSS项进行去重（基于标题规范化）
        
        Args:
            items: RSS项列表
            
        Returns:
            去重后的项列表（按发布时间倒序）
        """
        # 提取媒体信息并生成去重key
        seen_keys: Set[str] = set()
        deduplicated = []
        
        for item in items:
            # 提取媒体信息
            media_info = self.media_extractor.extract_media_info(item.get('title', ''))
            
            # 生成去重key
            dedup_key = self._generate_dedup_key(media_info, item)
            
            if dedup_key not in seen_keys:
                seen_keys.add(dedup_key)
                deduplicated.append(item)
        
        # 按发布时间排序（最新的在前）
        deduplicated.sort(
            key=lambda x: x.get('pub_date') or datetime.min,
            reverse=True
        )
        
        return deduplicated
    
    def _generate_dedup_key(self, media_info: Dict, item: Dict) -> str:
        """
        生成去重key
        
        Args:
            media_info: 提取的媒体信息
            item: RSS项
            
        Returns:
            去重key字符串
        """
        # 如果有媒体信息，使用媒体信息生成key
        if media_info.get('title') and media_info.get('year'):
            key_parts = [
                media_info.get('title', '').lower().strip(),
                str(media_info.get('year', ''))
            ]
            if media_info.get('season') and media_info.get('episode'):
                key_parts.append(f"s{media_info['season']:02d}e{media_info['episode']:02d}")
            return '|'.join(key_parts)
        
        # 否则使用标题和链接的哈希
        content = f"{item.get('title', '')}{item.get('link', '')}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    async def _mark_subscription_error(
        self,
        subscription: UserRSSHubSubscription,
        code: str,
        message: str,
        *,
        disable: bool = False,
    ) -> None:
        """记录订阅的最后一次错误信息"""
        subscription.last_error_code = code
        subscription.last_error_message = (message or "")[:500]
        subscription.last_error_at = datetime.utcnow()
        if disable:
            subscription.enabled = False
        subscription.updated_at = datetime.utcnow()
        await self.db.commit()

    async def _clear_subscription_error(
        self,
        subscription: UserRSSHubSubscription,
        *,
        commit: bool = True,
    ) -> None:
        """清理订阅的错误状态"""
        if not (
            subscription.last_error_code
            or subscription.last_error_message
            or subscription.last_error_at
        ):
            return

        subscription.last_error_code = None
        subscription.last_error_message = None
        subscription.last_error_at = None
        if commit:
            subscription.updated_at = datetime.utcnow()
            await self.db.commit()
    
    async def _enqueue_items_to_workflow(
        self,
        items: List[Dict],
        media_type: str,
        user_id: int
    ):
        """
        将RSS项入队到工作流
        
        Args:
            items: RSS项列表
            media_type: 媒体类型（video/tv/variety/anime/music/mixed）
            user_id: 用户ID
        """
        from app.modules.workflow.engine import WorkflowEngine
        
        workflow_engine = WorkflowEngine(db=self.db)
        
        for item in items:
            try:
                # 提取媒体信息
                media_info = self.media_extractor.extract_media_info(item.get('title', ''))
                
                # 如果提取的媒体类型与传入的不同，使用提取的类型
                detected_type = media_info.get('type', media_type)
                
                # 根据类型选择工作流模板
                workflow_template = self._get_workflow_template(detected_type, media_info)
                
                if workflow_template:
                    # 构建工作流上下文
                    context = {
                        'rss_item': item,
                        'media_info': media_info,
                        'user_id': user_id,
                        'media_type': detected_type,
                        'title': media_info.get('title') or item.get('title', ''),
                        'year': media_info.get('year'),
                        'season': media_info.get('season'),
                        'episode': media_info.get('episode')
                    }
                    
                    # 创建虚拟工作流对象（用于执行模板）
                    class VirtualWorkflow:
                        def __init__(self, name, actions):
                            self.name = name
                            self.actions = actions
                    
                    virtual_workflow = VirtualWorkflow(
                        name=workflow_template['name'],
                        actions=workflow_template['actions']
                    )
                    
                    # 执行工作流
                    result = await workflow_engine.execute(virtual_workflow, context)
                    
                    if result.get('success'):
                        logger.info(
                            f"RSSHub工作流执行成功: {workflow_template['name']} - "
                            f"媒体: {context.get('title')} (用户: {user_id})"
                        )
                    else:
                        logger.warning(
                            f"RSSHub工作流执行失败: {workflow_template['name']} - "
                            f"媒体: {context.get('title')} - {result.get('error')}"
                        )
                else:
                    logger.warning(f"未找到 {detected_type} 类型的工作流模板，跳过处理")
            except Exception as e:
                logger.error(f"处理RSS项失败: {item.get('title', 'Unknown')} - {e}")
    
    def _get_workflow_template(self, media_type: str, media_info: Dict) -> Optional[Dict]:
        """
        根据媒体类型获取工作流模板
        
        Args:
            media_type: 媒体类型
            media_info: 媒体信息
            
        Returns:
            工作流模板配置
        """
        from app.modules.rsshub.workflow_templates import get_workflow_template_manager
        
        template_manager = get_workflow_template_manager()
        return template_manager.get_template_dict(media_type)


# 导入RSSHubService（避免循环导入）
from app.modules.rsshub.service import RSSHubService

