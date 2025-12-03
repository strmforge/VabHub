"""
Torrent 索引洞察工具

FUTURE-AI-ORCHESTRATOR-1 P2 实现
从 Local Intel / TorrentIndex 提供 HR 风险提示素材
"""

from typing import Optional
from pydantic import BaseModel, Field
from loguru import logger

from .base import AITool, OrchestratorContext


class TorrentInsightInput(BaseModel):
    """Torrent 洞察输入参数"""
    site_name: Optional[str] = Field(None, description="站点名称过滤")
    media_type: Optional[str] = Field(None, description="媒体类型过滤")


class HRRiskStat(BaseModel):
    """HR 风险统计"""
    site_name: str
    total_indexed: int = 0
    hr_count: int = 0
    at_risk_count: int = 0
    risk_ratio: float = 0.0


class CommonHRScenario(BaseModel):
    """常见 HR 场景"""
    scenario: str
    description: str
    frequency: str  # "高" / "中" / "低"


class TorrentIndexInsightOutput(BaseModel):
    """Torrent 索引洞察输出"""
    hr_risk_stats: list[HRRiskStat] = Field(default_factory=list)
    common_scenarios: list[CommonHRScenario] = Field(default_factory=list)
    total_indexed: int = 0
    last_sync_time: Optional[str] = None
    summary_text: str = ""


class GetTorrentIndexInsightTool(AITool):
    """
    Torrent 索引洞察工具
    
    从 Local Intel / TorrentIndex 提供 HR 风险统计和常见场景
    """
    
    name = "get_torrent_index_insight"
    description = (
        "从本地 Torrent 索引获取 HR/HNR 风险洞察信息。"
        "包括各站点的 HR 风险统计、危险种子数量、常见 HR 场景等。"
        "用于帮助用户了解当前做种风险状况。"
    )
    input_model = TorrentInsightInput
    output_model = TorrentIndexInsightOutput
    
    async def run(
        self,
        params: TorrentInsightInput,
        context: OrchestratorContext,
    ) -> TorrentIndexInsightOutput:
        """执行洞察分析"""
        try:
            hr_stats = await self._get_hr_stats(context, params.site_name)
            scenarios = self._get_common_scenarios(params.media_type)
            total_indexed = await self._get_total_indexed(context)
            
            # 生成摘要
            at_risk_total = sum(s.at_risk_count for s in hr_stats)
            if hr_stats:
                high_risk_sites = [s.site_name for s in hr_stats if s.risk_ratio > 0.3]
                if high_risk_sites:
                    summary_text = (
                        f"共索引 {total_indexed} 条种子，"
                        f"当前有 {at_risk_total} 条处于 HR 风险区。"
                        f"高风险站点：{', '.join(high_risk_sites[:3])}"
                    )
                else:
                    summary_text = (
                        f"共索引 {total_indexed} 条种子，"
                        f"当前有 {at_risk_total} 条处于 HR 风险区，整体风险可控。"
                    )
            else:
                summary_text = "暂无本地索引数据，建议先执行站点索引任务。"
            
            return TorrentIndexInsightOutput(
                hr_risk_stats=hr_stats,
                common_scenarios=scenarios,
                total_indexed=total_indexed,
                summary_text=summary_text,
            )
            
        except Exception as e:
            logger.error(f"[torrent_insight] 获取洞察失败: {e}")
            return TorrentIndexInsightOutput(
                summary_text=f"获取洞察时发生错误: {str(e)[:100]}"
            )
    
    async def _get_hr_stats(
        self,
        context: OrchestratorContext,
        site_name: Optional[str],
    ) -> list[HRRiskStat]:
        """获取 HR 风险统计"""
        try:
            from sqlalchemy import select, func
            
            # 尝试导入 TorrentIndex 模型
            try:
                from app.models.intel_local import TorrentIndex
            except ImportError:
                logger.warning("[torrent_insight] TorrentIndex 模型不可用")
                return []
            
            # 按站点统计
            stats: list[HRRiskStat] = []
            
            # 获取站点列表
            from app.models.site import Site
            site_query = select(Site)
            if site_name:
                site_query = site_query.where(Site.name.ilike(f"%{site_name}%"))
            
            result = await context.db.execute(site_query)
            sites = result.scalars().all()
            
            for site in sites:
                # 统计该站点的索引数
                count_query = select(func.count()).select_from(TorrentIndex).where(
                    TorrentIndex.site_id == site.id
                )
                result = await context.db.execute(count_query)
                total = result.scalar() or 0
                
                if total == 0:
                    continue
                
                # 统计 HR 种子数
                hr_count = 0
                if hasattr(TorrentIndex, "is_hr"):
                    hr_query = count_query.where(TorrentIndex.is_hr == True)
                    result = await context.db.execute(hr_query)
                    hr_count = result.scalar() or 0
                
                # 计算风险比例
                risk_ratio = hr_count / total if total > 0 else 0.0
                
                stats.append(HRRiskStat(
                    site_name=site.name,
                    total_indexed=total,
                    hr_count=hr_count,
                    at_risk_count=hr_count,  # 简化：假设所有 HR 都是风险
                    risk_ratio=round(risk_ratio, 3),
                ))
            
            return sorted(stats, key=lambda x: -x.risk_ratio)
            
        except Exception as e:
            logger.warning(f"[torrent_insight] 获取 HR 统计失败: {e}")
            return []
    
    async def _get_total_indexed(self, context: OrchestratorContext) -> int:
        """获取总索引数"""
        try:
            from sqlalchemy import select, func
            from app.models.intel_local import TorrentIndex
            
            result = await context.db.execute(
                select(func.count()).select_from(TorrentIndex)
            )
            return result.scalar() or 0
        except Exception:
            return 0
    
    def _get_common_scenarios(self, media_type: Optional[str]) -> list[CommonHRScenario]:
        """获取常见 HR 场景（静态知识）"""
        scenarios = [
            CommonHRScenario(
                scenario="新种 HR",
                description="种子发布后 72 小时内需要保持做种，否则会被标记为 HNR",
                frequency="高",
            ),
            CommonHRScenario(
                scenario="大文件 HR",
                description="大于 10GB 的种子通常有更严格的做种要求",
                frequency="中",
            ),
            CommonHRScenario(
                scenario="热门资源 HR",
                description="热门新番/新剧的种子往往有较高的做种人数要求",
                frequency="高",
            ),
        ]
        
        # 根据媒体类型添加特定场景
        if media_type == "tv":
            scenarios.append(CommonHRScenario(
                scenario="剧集连载 HR",
                description="连载剧集每集都需要单独保种，容易累积 HNR 风险",
                frequency="高",
            ))
        elif media_type == "music":
            scenarios.append(CommonHRScenario(
                scenario="无损音乐 HR",
                description="FLAC/DSD 等无损格式文件较大，需要长期保种",
                frequency="中",
            ))
        
        return scenarios
