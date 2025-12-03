"""
站点与订阅概览工具

FUTURE-AI-ORCHESTRATOR-1 P2 实现
提供当前环境中站点、订阅、RSSHub 源的速览
"""

from typing import Optional
from pydantic import BaseModel, Field
from loguru import logger

from .base import AITool, OrchestratorContext, MediaTypeInput


class SiteSummary(BaseModel):
    """站点摘要"""
    id: int
    name: str
    category: Optional[str] = None
    is_active: bool = True
    hr_policy: Optional[str] = None
    error_count: int = 0


class SubscriptionSummary(BaseModel):
    """订阅摘要"""
    total_count: int = 0
    by_media_type: dict[str, int] = Field(default_factory=dict)
    active_count: int = 0


class RSSHubSummary(BaseModel):
    """RSSHub 源摘要"""
    total_sources: int = 0
    by_type: dict[str, int] = Field(default_factory=dict)
    user_subscriptions: int = 0


class SiteAndSubOverviewOutput(BaseModel):
    """站点与订阅概览输出"""
    sites: list[SiteSummary] = Field(default_factory=list)
    subscriptions: SubscriptionSummary = Field(default_factory=SubscriptionSummary)
    rsshub: RSSHubSummary = Field(default_factory=RSSHubSummary)
    summary_text: str = ""


class GetSiteAndSubOverviewTool(AITool):
    """
    获取站点与订阅概览
    
    提供当前环境中站点配置、订阅规则、RSSHub 源的快速概览
    """
    
    name = "get_site_and_sub_overview"
    description = (
        "获取当前 VabHub 环境中的站点配置、订阅规则和 RSSHub 源的概览信息。"
        "可以按媒体类型过滤。返回站点列表（含 HR 策略）、订阅统计、RSSHub 源统计。"
    )
    input_model = MediaTypeInput
    output_model = SiteAndSubOverviewOutput
    
    async def run(
        self,
        params: MediaTypeInput,
        context: OrchestratorContext,
    ) -> SiteAndSubOverviewOutput:
        """执行工具"""
        try:
            sites = await self._get_sites(context)
            subscriptions = await self._get_subscriptions(context, params.media_type)
            rsshub = await self._get_rsshub(context, params.media_type)
            
            # 生成摘要文本
            summary_parts = [
                f"共配置 {len(sites)} 个站点",
                f"其中活跃 {sum(1 for s in sites if s.is_active)} 个",
                f"共 {subscriptions.total_count} 条订阅规则",
                f"RSSHub 源 {rsshub.total_sources} 个",
            ]
            summary_text = "，".join(summary_parts)
            
            return SiteAndSubOverviewOutput(
                sites=sites,
                subscriptions=subscriptions,
                rsshub=rsshub,
                summary_text=summary_text,
            )
            
        except Exception as e:
            logger.error(f"[site_overview] 获取概览失败: {e}")
            return SiteAndSubOverviewOutput(
                summary_text=f"获取概览时发生错误: {str(e)[:100]}"
            )
    
    async def _get_sites(self, context: OrchestratorContext) -> list[SiteSummary]:
        """获取站点列表"""
        try:
            from sqlalchemy import select
            from app.models.site import Site
            
            result = await context.db.execute(select(Site))
            sites = result.scalars().all()
            
            return [
                SiteSummary(
                    id=s.id,
                    name=s.name,
                    category=getattr(s, "category", None),
                    is_active=getattr(s, "is_active", True),
                    hr_policy=getattr(s, "hr_policy", None),
                    error_count=getattr(s, "error_count", 0),
                )
                for s in sites
            ]
        except Exception as e:
            logger.warning(f"[site_overview] 获取站点失败: {e}")
            return []
    
    async def _get_subscriptions(
        self,
        context: OrchestratorContext,
        media_type: Optional[str],
    ) -> SubscriptionSummary:
        """获取订阅统计"""
        try:
            from sqlalchemy import select, func
            from app.models.subscription import Subscription
            
            # 总数查询
            query = select(func.count()).select_from(Subscription)
            result = await context.db.execute(query)
            total_count = result.scalar() or 0
            
            # 按媒体类型统计
            by_media_type: dict[str, int] = {}
            if hasattr(Subscription, "media_type"):
                type_query = select(
                    Subscription.media_type,
                    func.count()
                ).group_by(Subscription.media_type)
                result = await context.db.execute(type_query)
                for row in result:
                    if row[0]:
                        by_media_type[row[0]] = row[1]
            
            # 活跃订阅数
            active_count = total_count
            if hasattr(Subscription, "is_active"):
                active_query = select(func.count()).select_from(Subscription).where(
                    Subscription.is_active == True
                )
                result = await context.db.execute(active_query)
                active_count = result.scalar() or 0
            
            return SubscriptionSummary(
                total_count=total_count,
                by_media_type=by_media_type,
                active_count=active_count,
            )
            
        except Exception as e:
            logger.warning(f"[site_overview] 获取订阅统计失败: {e}")
            return SubscriptionSummary()
    
    async def _get_rsshub(
        self,
        context: OrchestratorContext,
        media_type: Optional[str],
    ) -> RSSHubSummary:
        """获取 RSSHub 源统计"""
        try:
            from sqlalchemy import select, func
            
            # 尝试导入 RSSHub 模型
            try:
                from app.models.rsshub_simple import RSSHubSource, UserRSSHubSubscription
            except ImportError:
                try:
                    from app.models.rsshub import RSSHubSource, UserRSSHubSubscription
                except ImportError:
                    return RSSHubSummary()
            
            # 源总数
            result = await context.db.execute(
                select(func.count()).select_from(RSSHubSource)
            )
            total_sources = result.scalar() or 0
            
            # 按类型统计
            by_type: dict[str, int] = {}
            if hasattr(RSSHubSource, "type"):
                type_query = select(
                    RSSHubSource.type,
                    func.count()
                ).group_by(RSSHubSource.type)
                result = await context.db.execute(type_query)
                for row in result:
                    if row[0]:
                        by_type[row[0]] = row[1]
            
            # 用户订阅数
            user_subs_query = select(func.count()).select_from(UserRSSHubSubscription)
            if context.user_id:
                user_subs_query = user_subs_query.where(
                    UserRSSHubSubscription.user_id == context.user_id
                )
            result = await context.db.execute(user_subs_query)
            user_subscriptions = result.scalar() or 0
            
            return RSSHubSummary(
                total_sources=total_sources,
                by_type=by_type,
                user_subscriptions=user_subscriptions,
            )
            
        except Exception as e:
            logger.warning(f"[site_overview] 获取 RSSHub 统计失败: {e}")
            return RSSHubSummary()
