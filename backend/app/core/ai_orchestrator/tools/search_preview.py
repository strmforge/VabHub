"""
搜索预览工具

FUTURE-AI-ORCHESTRATOR-1 P2 实现
在不触发真实下载的情况下，提供搜索预览
"""

from typing import Optional
from pydantic import BaseModel, Field
from loguru import logger

from .base import AITool, OrchestratorContext, KeywordSearchInput


class SearchResultItem(BaseModel):
    """搜索结果项"""
    title: str
    site_name: Optional[str] = None
    size: Optional[str] = None
    seeders: Optional[int] = None
    leechers: Optional[int] = None
    is_hr: bool = False
    is_free: bool = False
    category: Optional[str] = None


class SiteDistribution(BaseModel):
    """站点分布"""
    site_name: str
    count: int


class SearchPreviewOutput(BaseModel):
    """搜索预览输出"""
    keyword: str
    total_hits: int = 0
    site_distribution: list[SiteDistribution] = Field(default_factory=list)
    top_results: list[SearchResultItem] = Field(default_factory=list)
    summary_text: str = ""


class GetSearchPreviewTool(AITool):
    """
    搜索预览工具
    
    使用 External Indexer 执行搜索预览，不触发下载
    """
    
    name = "get_search_preview"
    description = (
        "执行搜索预览，返回匹配结果的概览信息。"
        "包括命中数、站点分布、前 N 条候选的标题/站点/大小/做种人数/HR 标记等。"
        "此操作不会触发任何下载。"
    )
    input_model = KeywordSearchInput
    output_model = SearchPreviewOutput
    
    async def run(
        self,
        params: KeywordSearchInput,
        context: OrchestratorContext,
    ) -> SearchPreviewOutput:
        """执行搜索预览"""
        try:
            # 尝试调用搜索服务
            results = await self._search(
                keyword=params.keyword,
                media_type=params.media_type,
                site_ids=params.site_ids,
                context=context,
            )
            
            # 统计站点分布
            site_counts: dict[str, int] = {}
            for r in results:
                site = r.get("site_name", "未知")
                site_counts[site] = site_counts.get(site, 0) + 1
            
            site_distribution = [
                SiteDistribution(site_name=k, count=v)
                for k, v in sorted(site_counts.items(), key=lambda x: -x[1])
            ]
            
            # 转换结果
            top_results = [
                SearchResultItem(
                    title=r.get("title", "")[:100],  # 截断标题
                    site_name=r.get("site_name"),
                    size=r.get("size"),
                    seeders=r.get("seeders"),
                    leechers=r.get("leechers"),
                    is_hr=r.get("is_hr", False),
                    is_free=r.get("is_free", False),
                    category=r.get("category"),
                )
                for r in results[:10]  # 最多返回 10 条
            ]
            
            # 生成摘要
            total_hits = len(results)
            if total_hits > 0:
                hr_count = sum(1 for r in results if r.get("is_hr"))
                free_count = sum(1 for r in results if r.get("is_free"))
                summary_text = (
                    f"搜索「{params.keyword}」命中 {total_hits} 条结果，"
                    f"来自 {len(site_distribution)} 个站点，"
                    f"其中 HR {hr_count} 条，免费 {free_count} 条"
                )
            else:
                summary_text = f"搜索「{params.keyword}」未找到结果"
            
            return SearchPreviewOutput(
                keyword=params.keyword,
                total_hits=total_hits,
                site_distribution=site_distribution,
                top_results=top_results,
                summary_text=summary_text,
            )
            
        except Exception as e:
            logger.error(f"[search_preview] 搜索预览失败: {e}")
            return SearchPreviewOutput(
                keyword=params.keyword,
                summary_text=f"搜索时发生错误: {str(e)[:100]}"
            )
    
    async def _search(
        self,
        keyword: str,
        media_type: Optional[str],
        site_ids: Optional[list[int]],
        context: OrchestratorContext,
    ) -> list[dict]:
        """
        执行搜索
        
        尝试调用现有的搜索服务，如果失败则返回空列表
        """
        try:
            # 尝试使用搜索服务
            from app.modules.search.service import SearchService
            
            search_service = SearchService(context.db)
            
            # 调用搜索
            results = await search_service.search(
                keyword=keyword,
                media_type=media_type,
                limit=50,  # 限制结果数
            )
            
            # 转换为字典列表
            if isinstance(results, list):
                return [
                    {
                        "title": getattr(r, "title", str(r)),
                        "site_name": getattr(r, "site_name", None),
                        "size": getattr(r, "size", None),
                        "seeders": getattr(r, "seeders", None),
                        "leechers": getattr(r, "leechers", None),
                        "is_hr": getattr(r, "is_hr", False),
                        "is_free": getattr(r, "is_free", False),
                        "category": getattr(r, "category", None),
                    }
                    for r in results
                ]
            
            return []
            
        except ImportError:
            logger.warning("[search_preview] SearchService 不可用")
            return []
        except Exception as e:
            logger.warning(f"[search_preview] 搜索服务调用失败: {e}")
            return []
