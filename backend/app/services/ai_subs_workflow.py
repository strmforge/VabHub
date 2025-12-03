"""
AI 订阅工作流服务

FUTURE-AI-SUBS-WORKFLOW-1 P3 实现
提供订阅工作流草案的预览与应用功能
"""

from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_orchestrator.service import (
    AIOrchestratorService,
    OrchestratorMode,
    OrchestratorResult,
)
from app.core.ai_orchestrator.tools.base import OrchestratorContext
from app.core.ai_orchestrator.factory import get_llm_client
from app.models.rsshub import RSSHubSource, UserRSSHubSubscription
from app.models.site import Site
from app.modules.subscription.service import SubscriptionService
from app.modules.rsshub.service import RSSHubService
from app.schemas.ai_subs_workflow import (
    SubsWorkflowDraft,
    SubsWorkflowSource,
    SubsSourceType,
    SubsTargetMediaType,
    SubsFilterRule,
    SubsActionConfig,
    draft_to_subscription_dict,
)


class AISubsWorkflowService:
    """
    AI 订阅工作流服务
    
    职责：
    - 调用 Orchestrator 生成订阅草案
    - 验证和补全草案数据
    - 将草案应用到真实订阅模型
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.subscription_service = SubscriptionService(db)
        self.rsshub_service = RSSHubService(db)
    
    async def preview(
        self,
        user_id: int,
        prompt: str,
        force_dummy: bool = False,
    ) -> Tuple[List[SubsWorkflowDraft], str, Optional[str], List[Dict[str, Any]]]:
        """
        预览订阅工作流草案
        
        Args:
            user_id: 用户 ID
            prompt: 自然语言请求
            force_dummy: 是否强制使用 Dummy LLM
            
        Returns:
            (drafts, summary, notes, orchestrator_plan) 四元组
        """
        # 1. 获取 LLM 客户端
        llm_client = get_llm_client(force_dummy=force_dummy)
        orchestrator = AIOrchestratorService(llm_client)
        
        # 2. 构造上下文
        context = OrchestratorContext(
            user_id=user_id,
            db=self.db,
            debug_mode=False,
        )
        
        # 3. 调用 Orchestrator
        result = await orchestrator.run(
            context=context,
            mode=OrchestratorMode.SUBS_ADVISOR,
            prompt=prompt,
        )
        
        # 4. 解析草案
        raw_drafts, summary, notes = orchestrator.parse_subs_advisor_drafts(
            result.llm_suggested_changes
        )
        
        # 如果没有从 suggested_changes 解析出草案，尝试从 summary 中提取
        if not raw_drafts and result.llm_summary:
            # 尝试从 summary 中提取 JSON
            import re
            import json
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', result.llm_summary)
            if json_match:
                try:
                    parsed = json.loads(json_match.group(1))
                    raw_drafts, summary, notes = orchestrator.parse_subs_advisor_drafts(parsed)
                except json.JSONDecodeError:
                    pass
        
        # 5. 验证和补全草案
        drafts = await self._validate_and_enrich_drafts(raw_drafts, user_id)
        
        # 6. 构造 plan 信息
        plan = [p.model_dump() for p in result.plan]
        
        # 如果没有总结，使用 LLM summary
        if not summary and result.llm_summary:
            summary = result.llm_summary
        
        return drafts, summary, notes, plan
    
    async def apply(
        self,
        user_id: int,
        draft: SubsWorkflowDraft,
    ) -> Tuple[Optional[int], str, List[str], int]:
        """
        应用订阅工作流草案
        
        Args:
            user_id: 用户 ID
            draft: 订阅草案
            
        Returns:
            (subscription_id, subscription_name, warnings, rsshub_count) 四元组
        """
        warnings: List[str] = []
        rsshub_count = 0
        
        # 1. 验证草案
        if draft.validation_errors:
            raise ValueError(f"草案验证失败: {'; '.join(draft.validation_errors)}")
        
        # 2. 处理 RSSHub 订阅
        for source in draft.sources:
            if source.type == SubsSourceType.RSSHUB and source.id:
                try:
                    # 验证源存在
                    rsshub_source = await self.db.get(RSSHubSource, source.id)
                    if not rsshub_source:
                        warnings.append(f"RSSHub 源 {source.id} 不存在，跳过")
                        continue
                    
                    # 创建/更新用户订阅
                    await self.rsshub_service.toggle_subscription(
                        user_id=user_id,
                        target_type="source",
                        target_id=source.id,
                        enabled=True,
                    )
                    rsshub_count += 1
                    logger.info(f"[ai_subs_workflow] 用户 {user_id} 启用 RSSHub 源: {source.id}")
                    
                except Exception as e:
                    warnings.append(f"启用 RSSHub 源 {source.id} 失败: {str(e)[:50]}")
        
        # 3. 创建媒体订阅
        subscription_id = None
        subscription_name = draft.name
        
        # 只有当有 PT 站点来源时才创建订阅
        has_pt_source = any(s.type == SubsSourceType.PT_SEARCH for s in draft.sources)
        
        if has_pt_source or not draft.sources:
            try:
                # 转换草案为订阅字典
                sub_dict = draft_to_subscription_dict(draft, user_id)
                
                # v1 安全策略：默认不启用自动下载
                sub_dict["auto_download"] = False
                sub_dict["status"] = "paused"
                
                # 创建订阅
                subscription = await self.subscription_service.create_subscription(sub_dict)
                subscription_id = subscription.id
                subscription_name = subscription.title
                
                logger.info(f"[ai_subs_workflow] 用户 {user_id} 创建订阅: {subscription_id} - {subscription_name}")
                
            except Exception as e:
                logger.error(f"[ai_subs_workflow] 创建订阅失败: {e}")
                raise ValueError(f"创建订阅失败: {str(e)[:100]}")
        
        # 4. 添加安全提示
        if not warnings:
            warnings.append("订阅已创建但处于暂停状态，请在订阅中心手动启用")
        
        return subscription_id, subscription_name, warnings, rsshub_count
    
    async def _validate_and_enrich_drafts(
        self,
        raw_drafts: List[Dict[str, Any]],
        user_id: int,
    ) -> List[SubsWorkflowDraft]:
        """
        验证和补全草案数据
        
        Args:
            raw_drafts: 原始草案列表
            user_id: 用户 ID
            
        Returns:
            验证后的草案列表
        """
        drafts: List[SubsWorkflowDraft] = []
        
        for raw in raw_drafts:
            try:
                # 解析基础字段
                name = raw.get("name", "未命名订阅")
                description = raw.get("description")
                media_type_str = raw.get("media_type", "movie").lower()
                
                # 映射 media_type
                media_type_map = {
                    "movie": SubsTargetMediaType.MOVIE,
                    "tv": SubsTargetMediaType.TV,
                    "anime": SubsTargetMediaType.ANIME,
                    "short_drama": SubsTargetMediaType.SHORT_DRAMA,
                    "music": SubsTargetMediaType.MUSIC,
                    "book": SubsTargetMediaType.BOOK,
                    "comic": SubsTargetMediaType.COMIC,
                }
                media_type = media_type_map.get(media_type_str, SubsTargetMediaType.MOVIE)
                
                # 解析来源
                sources: List[SubsWorkflowSource] = []
                raw_sources = raw.get("sources", [])
                for src in raw_sources:
                    if not isinstance(src, dict):
                        continue
                    
                    src_type_str = src.get("type", "").lower()
                    src_type = SubsSourceType.RSSHUB if src_type_str == "rsshub" else SubsSourceType.PT_SEARCH
                    
                    source = SubsWorkflowSource(
                        type=src_type,
                        id=src.get("id"),
                        name=src.get("name"),
                        extra_params=src.get("extra_params", {}),
                    )
                    
                    # 验证来源
                    await self._validate_source(source)
                    sources.append(source)
                
                # 解析过滤规则
                raw_filter = raw.get("filter_rule", {})
                filter_rule = SubsFilterRule(
                    include_keywords=raw_filter.get("include_keywords", []),
                    exclude_keywords=raw_filter.get("exclude_keywords", []),
                    min_resolution=raw_filter.get("min_resolution"),
                    preferred_resolution=raw_filter.get("preferred_resolution"),
                    effect=raw_filter.get("effect"),
                    hr_safe=raw_filter.get("hr_safe", True),  # 默认安全
                    free_only=raw_filter.get("free_only", False),
                    languages=raw_filter.get("languages", []),
                    min_seeders=raw_filter.get("min_seeders"),
                )
                
                # 解析动作配置
                raw_action = raw.get("action", {})
                action = SubsActionConfig(
                    download_enabled=raw_action.get("download_enabled", False),  # 默认不启用
                    dry_run=raw_action.get("dry_run", True),
                    target_library=raw_action.get("target_library"),
                    notify_on_match=raw_action.get("notify_on_match", True),
                    downloader=raw_action.get("downloader"),
                    best_version=raw_action.get("best_version", False),
                )
                
                # 构造草案
                draft = SubsWorkflowDraft(
                    name=name,
                    description=description,
                    media_type=media_type,
                    sources=sources,
                    filter_rule=filter_rule,
                    action=action,
                    ai_explanation=raw.get("ai_explanation"),
                )
                
                # 整体验证
                await self._validate_draft(draft)
                
                drafts.append(draft)
                
            except Exception as e:
                logger.warning(f"[ai_subs_workflow] 解析草案失败: {e}")
                continue
        
        return drafts
    
    async def _validate_source(self, source: SubsWorkflowSource) -> None:
        """验证单个来源"""
        if source.type == SubsSourceType.RSSHUB and source.id:
            # 验证 RSSHub 源存在
            rsshub_source = await self.db.get(RSSHubSource, source.id)
            if rsshub_source:
                source.valid = True
                source.validation_message = f"RSSHub 源有效: {rsshub_source.name}"
            else:
                source.valid = False
                source.validation_message = f"RSSHub 源不存在: {source.id}"
        
        elif source.type == SubsSourceType.PT_SEARCH and source.id:
            # 验证站点存在
            try:
                site_id = int(source.id)
                result = await self.db.execute(
                    select(Site).where(Site.id == site_id)
                )
                site = result.scalar_one_or_none()
                if site:
                    source.valid = True
                    source.validation_message = f"站点有效: {site.name}"
                else:
                    source.valid = False
                    source.validation_message = f"站点不存在: {source.id}"
            except ValueError:
                source.valid = False
                source.validation_message = f"无效的站点 ID: {source.id}"
        
        else:
            source.valid = True
            source.validation_message = "无需验证"
    
    async def _validate_draft(self, draft: SubsWorkflowDraft) -> None:
        """验证整个草案"""
        errors: List[str] = []
        warnings: List[str] = []
        
        # 检查名称
        if not draft.name or len(draft.name.strip()) < 2:
            errors.append("订阅名称太短")
        
        # 检查来源
        if not draft.sources:
            warnings.append("未指定任何来源，将使用默认搜索")
        else:
            invalid_sources = [s for s in draft.sources if s.valid is False]
            if invalid_sources:
                for s in invalid_sources:
                    warnings.append(s.validation_message or f"来源 {s.id} 无效")
        
        # 检查媒体类型
        if draft.media_type not in (SubsTargetMediaType.MOVIE, SubsTargetMediaType.TV, SubsTargetMediaType.ANIME):
            warnings.append(f"媒体类型 {draft.media_type.value} 在 v1 中支持有限")
        
        # 安全检查
        if draft.action.download_enabled:
            warnings.append("自动下载已启用，请确认这是您期望的行为")
        
        if not draft.filter_rule.hr_safe:
            warnings.append("HR 安全策略未启用，可能下载到 HR 种子")
        
        draft.validation_errors = errors
        draft.validation_warnings = warnings
        draft.valid = len(errors) == 0
