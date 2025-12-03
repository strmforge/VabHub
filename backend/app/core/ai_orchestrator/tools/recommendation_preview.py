"""
推荐预览工具

FUTURE-AI-ORCHESTRATOR-1 P2 实现
调用推荐系统，提供个性化内容推荐预览
"""

from typing import Optional
from pydantic import BaseModel, Field
from loguru import logger

from .base import AITool, OrchestratorContext, MediaTypeInput


class RecommendationItem(BaseModel):
    """推荐项"""
    title: str
    media_type: Optional[str] = None
    reason: Optional[str] = None
    score: Optional[float] = None
    year: Optional[int] = None
    genres: list[str] = Field(default_factory=list)


class RecommendationPreviewOutput(BaseModel):
    """推荐预览输出"""
    items: list[RecommendationItem] = Field(default_factory=list)
    algorithm_used: Optional[str] = None
    total_candidates: int = 0
    summary_text: str = ""


class GetRecommendationPreviewTool(AITool):
    """
    推荐预览工具
    
    调用推荐系统获取个性化内容推荐
    """
    
    name = "get_recommendation_preview"
    description = (
        "获取个性化内容推荐预览。"
        "基于用户历史行为和内容特征，推荐可能感兴趣的影视/音乐/书籍等。"
        "返回推荐列表及推荐理由。"
    )
    input_model = MediaTypeInput
    output_model = RecommendationPreviewOutput
    
    async def run(
        self,
        params: MediaTypeInput,
        context: OrchestratorContext,
    ) -> RecommendationPreviewOutput:
        """获取推荐预览"""
        try:
            items, algorithm, total = await self._get_recommendations(
                context=context,
                media_type=params.media_type,
            )
            
            # 生成摘要
            if items:
                type_text = params.media_type or "全部类型"
                summary_text = (
                    f"基于您的偏好，为您推荐 {len(items)} 个{type_text}内容。"
                    f"使用算法：{algorithm or '混合推荐'}"
                )
            else:
                summary_text = "暂无推荐内容，可能需要更多历史数据来分析您的偏好。"
            
            return RecommendationPreviewOutput(
                items=items,
                algorithm_used=algorithm,
                total_candidates=total,
                summary_text=summary_text,
            )
            
        except Exception as e:
            logger.error(f"[recommendation_preview] 获取推荐失败: {e}")
            return RecommendationPreviewOutput(
                summary_text=f"获取推荐时发生错误: {str(e)[:100]}"
            )
    
    async def _get_recommendations(
        self,
        context: OrchestratorContext,
        media_type: Optional[str],
    ) -> tuple[list[RecommendationItem], Optional[str], int]:
        """
        获取推荐
        
        尝试调用推荐服务，如果不可用则返回空结果
        """
        items: list[RecommendationItem] = []
        algorithm: Optional[str] = None
        total: int = 0
        
        try:
            # 尝试使用推荐服务
            from app.modules.recommendation.service import RecommendationService
            
            rec_service = RecommendationService(context.db)
            
            # 获取推荐
            recommendations = await rec_service.get_recommendations(
                user_id=context.user_id,
                media_type=media_type,
                limit=10,
            )
            
            # 转换结果
            if isinstance(recommendations, dict):
                raw_items = recommendations.get("items", [])
                algorithm = recommendations.get("algorithm")
                total = recommendations.get("total", len(raw_items))
            elif isinstance(recommendations, list):
                raw_items = recommendations
                total = len(raw_items)
            else:
                raw_items = []
            
            for item in raw_items:
                if isinstance(item, dict):
                    items.append(RecommendationItem(
                        title=item.get("title", "未知"),
                        media_type=item.get("media_type"),
                        reason=item.get("reason"),
                        score=item.get("score"),
                        year=item.get("year"),
                        genres=item.get("genres", []),
                    ))
                else:
                    items.append(RecommendationItem(
                        title=getattr(item, "title", str(item)),
                        media_type=getattr(item, "media_type", None),
                        reason=getattr(item, "reason", None),
                        score=getattr(item, "score", None),
                        year=getattr(item, "year", None),
                        genres=getattr(item, "genres", []),
                    ))
            
        except ImportError:
            logger.warning("[recommendation_preview] RecommendationService 不可用")
            # 返回一些默认推荐作为演示
            items = self._get_fallback_recommendations(media_type)
            algorithm = "fallback"
            total = len(items)
        except AttributeError as e:
            logger.warning(f"[recommendation_preview] 推荐服务接口不兼容: {e}")
            items = self._get_fallback_recommendations(media_type)
            algorithm = "fallback"
            total = len(items)
        except Exception as e:
            logger.warning(f"[recommendation_preview] 获取推荐失败: {e}")
        
        return items, algorithm, total
    
    def _get_fallback_recommendations(
        self,
        media_type: Optional[str],
    ) -> list[RecommendationItem]:
        """
        获取降级推荐
        
        当推荐服务不可用时，返回一些通用推荐
        """
        fallback_items = {
            "movie": [
                RecommendationItem(
                    title="沙丘2",
                    media_type="movie",
                    reason="2024年热门科幻大片",
                    score=8.5,
                    year=2024,
                    genres=["科幻", "冒险"],
                ),
                RecommendationItem(
                    title="奥本海默",
                    media_type="movie",
                    reason="2023年奥斯卡最佳影片",
                    score=8.7,
                    year=2023,
                    genres=["传记", "历史"],
                ),
            ],
            "tv": [
                RecommendationItem(
                    title="庆余年2",
                    media_type="tv",
                    reason="2024年热门国产剧",
                    score=8.0,
                    year=2024,
                    genres=["古装", "剧情"],
                ),
                RecommendationItem(
                    title="繁花",
                    media_type="tv",
                    reason="王家卫执导年度大剧",
                    score=8.5,
                    year=2024,
                    genres=["剧情", "年代"],
                ),
            ],
        }
        
        if media_type and media_type in fallback_items:
            return fallback_items[media_type]
        
        # 返回混合推荐
        result = []
        for items in fallback_items.values():
            result.extend(items[:1])
        return result
