"""
阅读进度快照工具

FUTURE-AI-READING-ASSISTANT-1 P1 实现
获取用户阅读进度和活动，用于阅读规划
"""

from typing import Optional
from pydantic import BaseModel, Field
from loguru import logger

from .base import AITool, OrchestratorContext, EmptyInput


class OngoingItem(BaseModel):
    """进行中的阅读项"""
    media_type: str  # novel / audiobook / manga
    item_id: int
    title: str
    author: Optional[str] = None
    progress_label: str
    progress_percent: Optional[float] = None
    last_read_at: str


class RecentActivity(BaseModel):
    """最近活动"""
    media_type: str
    title: str
    activity_label: str
    occurred_at: str


class ReadingStats(BaseModel):
    """阅读统计"""
    ongoing_count: int = 0
    finished_count: int = 0
    finished_recent_30d: int = 0
    by_type: dict = Field(default_factory=dict)


class ReadingSnapshotOutput(BaseModel):
    """阅读进度快照输出"""
    ongoing_items: list[OngoingItem] = Field(default_factory=list)
    recent_activities: list[RecentActivity] = Field(default_factory=list)
    stats: Optional[ReadingStats] = None
    summary_text: str = ""


class GetReadingSnapshotTool(AITool):
    """
    阅读进度快照工具
    
    获取用户阅读进度、最近活动和统计
    """
    
    name = "get_reading_snapshot"
    description = (
        "获取用户的阅读进度快照。"
        "包括正在阅读的项目、最近阅读活动和统计信息（小说/有声书/漫画）。"
        "用于分析阅读习惯和制定阅读计划。"
    )
    input_model = EmptyInput
    output_model = ReadingSnapshotOutput
    
    async def run(
        self,
        params: EmptyInput,
        context: OrchestratorContext,
    ) -> ReadingSnapshotOutput:
        """获取阅读快照"""
        try:
            ongoing = await self._get_ongoing_reading(context)
            activities = await self._get_recent_activities(context)
            stats = await self._get_reading_stats(context)
            
            # 生成摘要
            if not ongoing and not activities:
                summary_text = "暂无阅读记录，开始阅读第一本书吧！"
            else:
                parts = []
                if stats:
                    parts.append(f"正在阅读 {stats.ongoing_count} 本")
                    parts.append(f"已完成 {stats.finished_count} 本")
                    if stats.finished_recent_30d > 0:
                        parts.append(f"最近 30 天完成 {stats.finished_recent_30d} 本")
                
                if ongoing:
                    most_recent = ongoing[0]
                    parts.append(f"最近在读《{most_recent.title}》({most_recent.progress_label})")
                
                summary_text = "；".join(parts) + "。"
            
            return ReadingSnapshotOutput(
                ongoing_items=ongoing[:15],  # 限制返回数量
                recent_activities=activities[:10],
                stats=stats,
                summary_text=summary_text,
            )
            
        except Exception as e:
            logger.error(f"[reading_snapshot] 获取阅读快照失败: {e}")
            return ReadingSnapshotOutput(
                summary_text=f"获取阅读快照时发生错误: {str(e)[:100]}"
            )
    
    async def _get_ongoing_reading(self, context: OrchestratorContext) -> list[OngoingItem]:
        """获取进行中的阅读"""
        items: list[OngoingItem] = []
        
        try:
            from app.services.reading_hub_service import list_ongoing_reading
            
            ongoing_list = await list_ongoing_reading(
                session=context.db,
                user_id=context.user_id,
                limit_per_type=10,
            )
            
            for item in ongoing_list:
                items.append(OngoingItem(
                    media_type=item.media_type.value if hasattr(item.media_type, 'value') else str(item.media_type),
                    item_id=item.item_id,
                    title=item.title,
                    author=item.sub_title,
                    progress_label=item.progress_label or "阅读中",
                    progress_percent=item.progress_percent,
                    last_read_at=item.last_read_at.isoformat() if item.last_read_at else "",
                ))
            
        except ImportError:
            logger.warning("[reading_snapshot] reading_hub_service 不可用")
        except Exception as e:
            logger.warning(f"[reading_snapshot] 获取进行中阅读失败: {e}")
        
        return items
    
    async def _get_recent_activities(self, context: OrchestratorContext) -> list[RecentActivity]:
        """获取最近活动"""
        activities: list[RecentActivity] = []
        
        try:
            from app.services.reading_hub_service import get_recent_activity
            
            activity_list = await get_recent_activity(
                session=context.db,
                user_id=context.user_id,
                limit=20,
            )
            
            for item in activity_list:
                activities.append(RecentActivity(
                    media_type=item.media_type.value if hasattr(item.media_type, 'value') else str(item.media_type),
                    title=item.title,
                    activity_label=item.activity_label or "",
                    occurred_at=item.occurred_at.isoformat() if item.occurred_at else "",
                ))
            
        except Exception as e:
            logger.warning(f"[reading_snapshot] 获取最近活动失败: {e}")
        
        return activities
    
    async def _get_reading_stats(self, context: OrchestratorContext) -> Optional[ReadingStats]:
        """获取阅读统计"""
        try:
            from app.services.reading_hub_service import get_reading_stats
            
            stats_dict = await get_reading_stats(
                session=context.db,
                user_id=context.user_id,
            )
            
            return ReadingStats(
                ongoing_count=stats_dict.get("ongoing_count", 0),
                finished_count=stats_dict.get("finished_count", 0),
                finished_recent_30d=stats_dict.get("finished_count_recent_30d", 0),
                by_type=stats_dict.get("by_type", {}),
            )
            
        except Exception as e:
            logger.warning(f"[reading_snapshot] 获取阅读统计失败: {e}")
            return None
