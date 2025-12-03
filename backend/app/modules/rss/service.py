"""
RSS订阅服务
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
from loguru import logger

from app.models.rss_subscription import RSSSubscription, RSSItem
from app.modules.filter_rule_group.service import FilterRuleGroupService
from app.modules.rss.parser import RSSParser, RSSItem as ParserRSSItem
from app.modules.rss.media_extractor import RSSMediaExtractor, ExtractedMediaInfo
from app.modules.rss.rule_engine import RSSRuleEngine
from app.modules.search.service import SearchService
from app.modules.download.service import DownloadService
from app.modules.subscription.service import SubscriptionService
from app.models.subscription import Subscription
from sqlalchemy import or_, and_
import re
from copy import deepcopy
from app.constants.media_types import is_tv_like


class RSSSubscriptionService:
    """RSS订阅服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.parser = RSSParser()
        self.media_extractor = RSSMediaExtractor()
        self.rule_engine = RSSRuleEngine()  # 初始化规则引擎
        self.filter_rule_group_service = FilterRuleGroupService(db)  # 过滤规则组服务
        # 延迟初始化服务，避免循环导入
        self._download_service = None
        self._subscription_service = None
    
    def _get_subscription_service(self) -> SubscriptionService:
        if not self._subscription_service:
            self._subscription_service = SubscriptionService(self.db)
        return self._subscription_service
    
    async def create_rss_subscription(self, data: dict) -> RSSSubscription:
        """创建RSS订阅"""
        # 创建RSS订阅对象
        rss_subscription = RSSSubscription(
            user_id=data.get("user_id", 1),  # 添加用户ID，默认为admin用户
            name=data.get("name"),
            url=data.get("url"),
            site_id=data.get("site_id"),
            enabled=data.get("enabled", True),
            interval=data.get("interval", 30),
            filter_rules=data.get("filter_rules"),
            download_rules=data.get("download_rules"),
            filter_group_ids=data.get("filter_group_ids", []),  # 添加规则组ID数组
            description=data.get("description")
        )
        
        # 设置下次检查时间（立即检查）
        rss_subscription.next_check = datetime.utcnow()
        
        self.db.add(rss_subscription)
        await self.db.commit()
        await self.db.refresh(rss_subscription)
        
        logger.info(f"创建RSS订阅成功: {rss_subscription.name} (ID: {rss_subscription.id})")
        return rss_subscription
    
    async def list_rss_subscriptions(
        self,
        enabled: Optional[bool] = None
    ) -> List[RSSSubscription]:
        """获取RSS订阅列表"""
        query = select(RSSSubscription)
        
        if enabled is not None:
            query = query.where(RSSSubscription.enabled == enabled)
        
        query = query.order_by(RSSSubscription.created_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_rss_subscription(self, subscription_id: int) -> Optional[RSSSubscription]:
        """获取RSS订阅详情"""
        result = await self.db.execute(
            select(RSSSubscription).where(RSSSubscription.id == subscription_id)
        )
        return result.scalar_one_or_none()
    
    async def update_rss_subscription(
        self,
        subscription_id: int,
        data: dict
    ) -> Optional[RSSSubscription]:
        """更新RSS订阅"""
        subscription = await self.get_rss_subscription(subscription_id)
        if not subscription:
            return None
        
        # 更新字段
        for key, value in data.items():
            if hasattr(subscription, key):
                setattr(subscription, key, value)
        
        subscription.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(subscription)
        
        logger.info(f"更新RSS订阅成功: {subscription.name} (ID: {subscription_id})")
        return subscription
    
    async def delete_rss_subscription(self, subscription_id: int) -> bool:
        """删除RSS订阅"""
        subscription = await self.get_rss_subscription(subscription_id)
        if not subscription:
            return False
        
        # 删除关联的RSS项
        await self.db.execute(
            delete(RSSItem).where(RSSItem.subscription_id == subscription_id)
        )
        
        # 删除订阅
        await self.db.delete(subscription)
        await self.db.commit()
        
        logger.info(f"删除RSS订阅成功: {subscription.name} (ID: {subscription_id})")
        return True
    
    async def check_rss_updates(self, subscription_id: int) -> Dict:
        """
        检查RSS订阅更新
        
        Returns:
            {
                "success": bool,
                "new_items": int,
                "processed_items": int,
                "downloaded_items": int,
                "skipped_items": int,
                "errors": List[str]
            }
        """
        subscription = await self.get_rss_subscription(subscription_id)
        if not subscription:
            return {
                "success": False,
                "error": "RSS订阅不存在"
            }
        
        if not subscription.enabled:
            return {
                "success": False,
                "error": "RSS订阅未启用"
            }
        
        try:
            # 检查RSS Feed更新
            new_items = await self.parser.check_updates(
                subscription.url,
                subscription.last_item_hash
            )
            
            if not new_items:
                # 更新检查时间
                subscription.last_check = datetime.utcnow()
                subscription.next_check = datetime.utcnow() + timedelta(minutes=subscription.interval)
                await self.db.commit()
                
                return {
                    "success": True,
                    "new_items": 0,
                    "processed_items": 0,
                    "downloaded_items": 0,
                    "skipped_items": 0,
                    "errors": []
                }
            
            # 批量处理新的RSS项（性能优化）
            processed_items = 0
            downloaded_items = 0
            skipped_items = 0
            errors = []
            last_item_hash = None
            rss_items_to_add = []  # 批量添加RSS项
            
            # 第一步：批量检查已存在的RSS项（优化：使用IN查询）
            existing_hashes = set()
            if new_items:
                item_hashes = [item.hash for item in new_items]
                existing_items = await self.db.execute(
                    select(RSSItem.item_hash).where(
                        RSSItem.subscription_id == subscription_id,
                        RSSItem.item_hash.in_(item_hashes)
                    )
                )
                existing_hashes = set(existing_items.scalars().all())
            
            # 第二步：批量准备新的RSS项
            for item in new_items:
                try:
                    # 检查是否已存在（防止重复）
                    if item.hash in existing_hashes:
                        logger.debug(f"RSS项已存在，跳过: {item.title}")
                        continue
                    
                    rss_item = RSSItem(
                        subscription_id=subscription_id,
                        item_hash=item.hash,
                        title=item.title,
                        link=item.link,
                        description=item.description or "",
                        pub_date=item.pub_date
                    )
                    rss_items_to_add.append((rss_item, item))
                except Exception as e:
                    logger.error(f"准备RSS项失败: {item.title}, 错误: {e}")
                    errors.append(f"{item.title}: {str(e)}")
                    continue
            
            # 第三步：批量添加RSS项
            if rss_items_to_add:
                for rss_item, item in rss_items_to_add:
                    self.db.add(rss_item)
                await self.db.flush()  # 批量flush，不commit
            
            # 第四步：批量处理RSS项（应用规则和下载）
            for rss_item, item in rss_items_to_add:
                try:
                    # 解析规则组并合并过滤规则
                    merged_filter_rules = subscription.filter_rules or {}
                    
                    # 获取规则组并合并规则
                    if subscription.filter_group_ids:
                        try:
                            rule_groups = await self.filter_rule_group_service.resolve_groups_for_subscription(
                                subscription.user_id, 
                                subscription.filter_group_ids, 
                                'movie'  # RSS默认使用movie媒体类型
                            )
                            
                            # 合并规则组的过滤规则
                            for group in rule_groups:
                                if group.get('rules'):
                                    rules = group['rules']
                                    # 合并include_keywords
                                    if rules.get('include'):
                                        if not merged_filter_rules.get('include_keywords'):
                                            merged_filter_rules['include_keywords'] = []
                                        include_list = rules['include'] if isinstance(rules['include'], list) else [str(rules['include'])]
                                        merged_filter_rules['include_keywords'].extend(include_list)
                                    
                                    # 合并exclude_keywords
                                    if rules.get('exclude'):
                                        if not merged_filter_rules.get('exclude_keywords'):
                                            merged_filter_rules['exclude_keywords'] = []
                                        exclude_list = rules['exclude'] if isinstance(rules['exclude'], list) else [str(rules['exclude'])]
                                        merged_filter_rules['exclude_keywords'].extend(exclude_list)
                        except Exception as e:
                            logger.warning(f"解析RSS规则组失败，使用默认规则: {e}")
                    
                    # 检查过滤规则
                    if not self._match_filter_rules(item, merged_filter_rules):
                        rss_item.processed = True
                        skipped_items += 1
                        subscription.skipped_items += 1
                        continue
                    
                    # 尝试匹配订阅并下载
                    download_result = await self._process_rss_item(item, subscription)
                    
                    if download_result.get("downloaded"):
                        rss_item.processed = True
                        rss_item.downloaded = True
                        rss_item.download_task_id = download_result.get("task_id")
                        rss_item.processed_at = datetime.utcnow()
                        downloaded_items += 1
                        subscription.downloaded_items += 1
                    else:
                        rss_item.processed = True
                        rss_item.processed_at = datetime.utcnow()
                        skipped_items += 1
                        subscription.skipped_items += 1
                    
                    processed_items += 1
                    subscription.total_items += 1
                    last_item_hash = item.hash
                    
                except Exception as e:
                    logger.error(f"处理RSS项失败: {item.title}, 错误: {e}")
                    errors.append(f"{item.title}: {str(e)}")
                    subscription.error_count += 1
                    # 标记为已处理但失败
                    rss_item.processed = True
                    rss_item.processed_at = datetime.utcnow()
                    continue
            
            # 第五步：批量提交所有更改（减少commit次数）
            try:
                await self.db.commit()
            except Exception as e:
                logger.error(f"提交RSS项批量处理失败: {e}")
                await self.db.rollback()
                raise
            
            # 更新订阅状态
            subscription.last_check = datetime.utcnow()
            subscription.next_check = datetime.utcnow() + timedelta(minutes=subscription.interval)
            if last_item_hash:
                subscription.last_item_hash = last_item_hash
            await self.db.commit()
            
            logger.info(
                f"RSS订阅更新检查完成: {subscription.name} (ID: {subscription_id}), "
                f"新项: {len(new_items)}, 处理: {processed_items}, 下载: {downloaded_items}, 跳过: {skipped_items}"
            )
            
            return {
                "success": True,
                "new_items": len(new_items),
                "processed_items": processed_items,
                "downloaded_items": downloaded_items,
                "skipped_items": skipped_items,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"检查RSS订阅更新失败: {subscription.name} (ID: {subscription_id}), 错误: {e}")
            subscription.error_count += 1
            subscription.last_check = datetime.utcnow()
            subscription.next_check = datetime.utcnow() + timedelta(minutes=subscription.interval)
            await self.db.commit()
            
            return {
                "success": False,
                "error": str(e),
                "new_items": 0,
                "processed_items": 0,
                "downloaded_items": 0,
                "skipped_items": 0,
                "errors": [str(e)]
            }
    
    def _match_filter_rules(self, item: ParserRSSItem, filter_rules: Optional[Dict]) -> bool:
        """
        检查RSS项是否匹配过滤规则
        
        Args:
            item: RSS项
            filter_rules: 过滤规则
            
        Returns:
            True: 匹配（通过过滤），False: 不匹配（被过滤）
        """
        if not filter_rules:
            return True
        
        # 检查包含规则
        include_keywords = filter_rules.get("include_keywords", [])
        if include_keywords:
            title_lower = item.title.lower()
            description_lower = item.description.lower()
            matched = False
            for keyword in include_keywords:
                if keyword.lower() in title_lower or keyword.lower() in description_lower:
                    matched = True
                    break
            if not matched:
                return False
        
        # 检查排除规则
        exclude_keywords = filter_rules.get("exclude_keywords", [])
        if exclude_keywords:
            title_lower = item.title.lower()
            description_lower = item.description.lower()
            for keyword in exclude_keywords:
                if keyword.lower() in title_lower or keyword.lower() in description_lower:
                    return False
        
        # 检查正则规则
        include_regex = filter_rules.get("include_regex")
        if include_regex:
            import re
            if not re.search(include_regex, item.title, re.IGNORECASE):
                return False
        
        exclude_regex = filter_rules.get("exclude_regex")
        if exclude_regex:
            import re
            if re.search(exclude_regex, item.title, re.IGNORECASE):
                return False
        
        return True
    
    async def _process_rss_item(
        self,
        item: ParserRSSItem,
        subscription: RSSSubscription
    ) -> Dict:
        """
        处理RSS项（匹配订阅并下载）
        
        Args:
            item: RSS项
            subscription: RSS订阅
            
        Returns:
            {
                "downloaded": bool,
                "task_id": Optional[str],
                "error": Optional[str]
            }
        """
        try:
            # 1. 提取媒体信息
            extracted_info = self.media_extractor.extract(item.title, item.description)
            
            if not extracted_info or not extracted_info.title:
                logger.info(f"无法从RSS项 '{item.title}' 提取媒体信息，跳过下载")
                return {"downloaded": False, "task_id": None, "error": "无法提取媒体信息"}
            
            # 2. 检查是否开启自动下载
            download_rules = subscription.download_rules or {}
            auto_download = download_rules.get("auto_download", False)
            
            if not auto_download:
                logger.info(f"RSS订阅 '{subscription.name}' 未开启自动下载，跳过下载")
                return {"downloaded": False, "task_id": None, "error": "未开启自动下载"}
            
            # 3. 匹配现有媒体订阅
            matched_subscription = await self._find_matching_subscription(extracted_info)
            
            if not matched_subscription:
                logger.info(f"RSS项 '{item.title}' 未匹配到任何媒体订阅，跳过下载")
                return {"downloaded": False, "task_id": None, "error": "未匹配到媒体订阅"}
            
            # 4. 使用高级规则引擎检查订阅规则
            rule_result = self.rule_engine.evaluate_rss_item(
                item,
                extracted_info,
                matched_subscription
            )
            
            if not rule_result.get("matched"):
                logger.info(
                    f"RSS项 '{item.title}' 不满足订阅规则（订阅: {matched_subscription.title}），"
                    f"原因: {rule_result.get('reason', '未知')}"
                )
                return {
                    "downloaded": False,
                    "task_id": None,
                    "error": f"不满足订阅规则: {rule_result.get('reason', '未知')}",
                    "rule_result": rule_result
                }
            
            logger.info(
                f"RSS项 '{item.title}' 匹配订阅规则（订阅: {matched_subscription.title}），"
                f"匹配分数: {rule_result.get('score', 0):.2f}，原因: {rule_result.get('reason', '未知')}"
            )
            
            # 5. 下载决策评估
            decision_result = None
            try:
                subscription_service = self._get_subscription_service()
                decision_candidate = self._build_decision_candidate_from_rss(
                    item=item,
                    extracted_info=extracted_info,
                    matched_subscription=matched_subscription,
                    download_rules=download_rules,
                    rss_subscription=subscription,
                )
                decision_result = await subscription_service.evaluate_candidate_with_decision(
                    matched_subscription,
                    decision_candidate,
                )
                if decision_result:
                    logger.debug(
                        "[decision] RSS项 %s -> %s (%s)",
                        item.title,
                        decision_result.reason.value,
                        decision_result.message,
                    )
                    if not decision_result.should_download:
                        return {
                            "downloaded": False,
                            "task_id": None,
                            "error": f"决策拒绝: {decision_result.reason.value}",
                            "decision_result": decision_result.model_dump(),
                        }
            except Exception as dec_err:  # pragma: no cover - 决策层异常回退
                logger.warning(
                    "[decision] RSS项 %s 决策评估失败，回退旧逻辑: %s",
                    item.title,
                    dec_err,
                )

            # 6. 触发下载
            try:
                # 初始化下载服务（延迟初始化）
                if not self._download_service:
                    self._download_service = DownloadService(self.db)
                
                # 确定下载路径
                download_path = download_rules.get("download_target_path") or matched_subscription.save_path
                downloader = download_rules.get("downloader") or matched_subscription.downloader or "qBittorrent"
                extra_metadata = (
                    deepcopy(matched_subscription.extra_metadata) if matched_subscription.extra_metadata else {}
                )
                if decision_result:
                    extra_metadata.setdefault("decision", {})
                    extra_metadata["decision"] = {
                        "reason": decision_result.reason.value,
                        "score": decision_result.score,
                    }

                # 创建下载任务
                download_data = {
                    "title": item.title,
                    "magnet_link": item.link if item.link.startswith("magnet:") else None,
                    "torrent_url": item.link if not item.link.startswith("magnet:") else None,
                    "downloader": downloader,
                    "save_path": download_path,
                    "media_type": matched_subscription.media_type,
                    "extra_metadata": extra_metadata or None,
                }
                
                download_task = await self._download_service.create_download(download_data)
                
                if download_task:
                    download_task_id = str(download_task.get("id", ""))
                    logger.info(f"RSS项 '{item.title}' 已成功触发下载，任务ID: {download_task_id}")
                    return {"downloaded": True, "task_id": download_task_id, "error": None}
                else:
                    logger.error(f"RSS项 '{item.title}' 触发下载失败")
                    return {"downloaded": False, "task_id": None, "error": "下载失败"}
                    
            except Exception as e:
                logger.error(f"触发下载失败: {item.title}, 错误: {e}")
                return {"downloaded": False, "task_id": None, "error": f"下载失败: {str(e)}"}
            
        except Exception as e:
            logger.error(f"处理RSS项失败: {item.title}, 错误: {e}")
            return {"downloaded": False, "task_id": None, "error": str(e)}
    
    def _build_decision_candidate_from_rss(
        self,
        *,
        item: ParserRSSItem,
        extracted_info: ExtractedMediaInfo,
        matched_subscription: Subscription,
        download_rules: Dict,
        rss_subscription: RSSSubscription,
    ) -> Dict:
        """构建传入决策层的候选字典。"""
        media_type = extracted_info.media_type or matched_subscription.media_type
        site_hint = None
        if matched_subscription.sites:
            try:
                if isinstance(matched_subscription.sites, list) and matched_subscription.sites:
                    site_hint = matched_subscription.sites[0]
                elif isinstance(matched_subscription.sites, dict):
                    site_hint = next(iter(matched_subscription.sites.keys()), None)
            except Exception:  # pragma: no cover
                site_hint = None

        return {
            "title": item.title,
            "subtitle": item.description,
            "media_type": media_type,
            "quality": extracted_info.quality or download_rules.get("quality"),
            "resolution": extracted_info.resolution or download_rules.get("resolution"),
            "effect": extracted_info.codec or download_rules.get("effect"),
            "seeders": download_rules.get("min_seeders", 0),
            "size_gb": download_rules.get("expected_size_gb"),
            "site": site_hint or rss_subscription.site_id,
            "release_group": extracted_info.group,
            "raw": {
                "rss_subscription_id": rss_subscription.id,
                "rss_item_hash": item.hash,
                "rss_title": item.title,
            },
        }
    
    async def _find_matching_subscription(self, extracted_info: ExtractedMediaInfo) -> Optional[Subscription]:
        """
        查找匹配的媒体订阅
        
        Args:
            extracted_info: 提取的媒体信息
            
        Returns:
            匹配的订阅对象，如果未找到则返回None
        """
        try:
            # 构建查询条件
            query = select(Subscription).where(
                Subscription.status == "active",
                Subscription.auto_download == True
            )
            
            # 匹配标题（支持中文标题和英文标题）
            title_conditions = [
                Subscription.title.ilike(f"%{extracted_info.title}%"),
                Subscription.original_title.ilike(f"%{extracted_info.title}%")
            ]
            query = query.where(or_(*title_conditions))
            
            # 匹配媒体类型
            if extracted_info.media_type != "unknown":
                query = query.where(Subscription.media_type == extracted_info.media_type)
            
            # 匹配年份（允许±1年的误差）
            if extracted_info.year:
                query = query.where(
                    or_(
                        Subscription.year == extracted_info.year,
                        Subscription.year == extracted_info.year - 1,
                        Subscription.year == extracted_info.year + 1,
                        Subscription.year.is_(None)  # 如果没有指定年份，也匹配
                    )
                )
            
            # 对于电视剧，匹配季数和集数
            if is_tv_like(extracted_info.media_type):
                if extracted_info.season:
                    query = query.where(
                        or_(
                            Subscription.season == extracted_info.season,
                            Subscription.season.is_(None)  # 如果没有指定季数，也匹配
                        )
                    )
            
            # 执行查询
            result = await self.db.execute(query)
            subscriptions = result.scalars().all()
            
            if not subscriptions:
                return None
            
            # 如果有多个匹配，选择最匹配的（优先级：精确匹配 > 年份匹配 > 标题匹配）
            best_match = None
            best_score = 0
            
            for sub in subscriptions:
                score = 0
                
                # 标题精确匹配（+10分）
                if sub.title and extracted_info.title.lower() in sub.title.lower():
                    score += 10
                if sub.original_title and extracted_info.title.lower() in sub.original_title.lower():
                    score += 10
                
                # 年份精确匹配（+5分）
                if sub.year and extracted_info.year and sub.year == extracted_info.year:
                    score += 5
                
                # 季数匹配（+3分）
                if is_tv_like(extracted_info.media_type) and sub.season and extracted_info.season:
                    if sub.season == extracted_info.season:
                        score += 3
                
                if score > best_score:
                    best_score = score
                    best_match = sub
            
            return best_match if best_match else subscriptions[0]  # 如果没有最佳匹配，返回第一个
            
        except Exception as e:
            logger.error(f"查找匹配订阅失败: {e}")
            return None
    
    def _check_subscription_rules(
        self,
        extracted_info: ExtractedMediaInfo,
        subscription: Subscription
    ) -> bool:
        """
        检查RSS项是否满足订阅规则（已废弃）
        
        注意：此方法已被 RSSRuleEngine.evaluate_rss_item 替代
        请使用 rule_engine.evaluate_rss_item 方法进行高级规则匹配
        此方法保留仅用于向后兼容
        
        Args:
            extracted_info: 提取的媒体信息
            subscription: 订阅对象
            
        Returns:
            是否满足规则
        """
        # 注意：此方法已被废弃，实际应该使用 rule_engine.evaluate_rss_item
        # 这里只做基础的简单检查，不支持高级规则（include、exclude、filter_groups等）
        
        # 检查质量要求
        if subscription.quality and extracted_info.quality:
            quality_priority = {"4K": 4, "1080p": 3, "720p": 2, "480p": 1}
            sub_quality_priority = quality_priority.get(subscription.quality, 0)
            ext_quality_priority = quality_priority.get(extracted_info.quality, 0)
            
            if ext_quality_priority < sub_quality_priority:
                return False
        
        return True
    
    async def list_rss_items(
        self,
        subscription_id: Optional[int] = None,
        processed: Optional[bool] = None,
        downloaded: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[RSSItem], int]:
        """
        获取RSS项列表（支持分页和过滤）
        
        Args:
            subscription_id: RSS订阅ID（可选）
            processed: 是否已处理（可选）
            downloaded: 是否已下载（可选）
            page: 页码
            page_size: 每页数量
            
        Returns:
            (RSS项列表, 总数量)
        """
        # 构建查询
        query = select(RSSItem)
        count_query = select(func.count(RSSItem.id))
        
        # 添加过滤条件
        conditions = []
        if subscription_id is not None:
            conditions.append(RSSItem.subscription_id == subscription_id)
        if processed is not None:
            conditions.append(RSSItem.processed == processed)
        if downloaded is not None:
            conditions.append(RSSItem.downloaded == downloaded)
        
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # 排序
        query = query.order_by(RSSItem.created_at.desc())
        
        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # 执行查询
        result = await self.db.execute(query)
        items = list(result.scalars().all())
        
        # 获取总数
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        return items, total
    
    async def get_rss_item(self, item_id: int) -> Optional[RSSItem]:
        """获取RSS项详情"""
        result = await self.db.execute(
            select(RSSItem).where(RSSItem.id == item_id)
        )
        return result.scalar_one_or_none()
    
    async def count_rss_items(
        self,
        subscription_id: Optional[int] = None,
        processed: Optional[bool] = None,
        downloaded: Optional[bool] = None
    ) -> Dict[str, int]:
        """
        统计RSS项数量
        
        Args:
            subscription_id: RSS订阅ID（可选）
            processed: 是否已处理（可选）
            downloaded: 是否已下载（可选）
            
        Returns:
            统计信息字典
        """
        conditions = []
        if subscription_id is not None:
            conditions.append(RSSItem.subscription_id == subscription_id)
        
        # 总数量
        total_query = select(func.count(RSSItem.id))
        if conditions:
            total_query = total_query.where(and_(*conditions))
        total_result = await self.db.execute(total_query)
        total = total_result.scalar() or 0
        
        # 已处理数量
        processed_conditions = conditions + [RSSItem.processed == True]
        processed_query = select(func.count(RSSItem.id)).where(and_(*processed_conditions))
        processed_result = await self.db.execute(processed_query)
        processed_count = processed_result.scalar() or 0
        
        # 已下载数量
        downloaded_conditions = conditions + [RSSItem.downloaded == True]
        downloaded_query = select(func.count(RSSItem.id)).where(and_(*downloaded_conditions))
        downloaded_result = await self.db.execute(downloaded_query)
        downloaded_count = downloaded_result.scalar() or 0
        
        # 未处理数量
        unprocessed_count = total - processed_count
        
        return {
            "total": total,
            "processed": processed_count,
            "unprocessed": unprocessed_count,
            "downloaded": downloaded_count,
            "skipped": processed_count - downloaded_count
        }

