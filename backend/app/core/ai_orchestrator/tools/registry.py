"""
AI 工具注册中心

FUTURE-AI-ORCHESTRATOR-1 P2 实现
管理所有可用的 AI 工具
"""

from typing import Optional
from loguru import logger

from .base import AITool
from ..llm_client import LLMToolSpec


class ToolRegistry:
    """
    工具注册中心
    
    管理所有可用的 AI 工具，提供注册、查询和列表功能
    """
    
    def __init__(self):
        self._tools: dict[str, AITool] = {}
    
    def register(self, tool: AITool) -> None:
        """
        注册工具
        
        Args:
            tool: 要注册的工具实例
        """
        if tool.name in self._tools:
            logger.warning(f"[tool_registry] 工具 {tool.name} 已存在，将被覆盖")
        
        self._tools[tool.name] = tool
        logger.debug(f"[tool_registry] 已注册工具: {tool.name}")
    
    def get(self, name: str) -> Optional[AITool]:
        """
        获取工具
        
        Args:
            name: 工具名称
            
        Returns:
            工具实例，如果不存在则返回 None
        """
        return self._tools.get(name)
    
    def list_tools(self) -> list[AITool]:
        """
        列出所有已注册的工具
        
        Returns:
            工具列表
        """
        return list(self._tools.values())
    
    def list_tool_names(self) -> list[str]:
        """
        列出所有已注册的工具名称
        
        Returns:
            工具名称列表
        """
        return list(self._tools.keys())
    
    def get_llm_tool_specs(
        self,
        allowed_names: Optional[list[str]] = None,
    ) -> list[LLMToolSpec]:
        """
        获取 LLM 工具规范列表
        
        Args:
            allowed_names: 可选，仅返回指定名称的工具
            
        Returns:
            LLM 工具规范列表
        """
        tools = self._tools.values()
        
        if allowed_names is not None:
            tools = [t for t in tools if t.name in allowed_names]
        
        return [t.to_llm_spec() for t in tools]
    
    def __len__(self) -> int:
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        return name in self._tools


# 全局工具注册中心实例
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """
    获取全局工具注册中心实例
    
    首次调用时会自动注册所有内置工具
    """
    global _registry
    
    if _registry is None:
        _registry = ToolRegistry()
        _register_builtin_tools(_registry)
    
    return _registry


def _register_builtin_tools(registry: ToolRegistry) -> None:
    """
    注册所有内置工具
    """
    # 延迟导入避免循环依赖
    from .site_overview import GetSiteAndSubOverviewTool
    from .search_preview import GetSearchPreviewTool
    from .torrent_insight import GetTorrentIndexInsightTool
    from .health_status import GetHealthStatusTool
    from .log_snapshot import GetLogSnapshotTool
    from .recommendation_preview import GetRecommendationPreviewTool
    from .runner_status import GetRunnerStatusTool
    from .storage_snapshot import GetStorageSnapshotTool
    from .library_snapshot import GetLibrarySnapshotTool
    from .reading_snapshot import GetReadingSnapshotTool
    from .library_books import GetLibraryBooksTool
    
    # 注册所有工具
    builtin_tools = [
        GetSiteAndSubOverviewTool(),
        GetSearchPreviewTool(),
        GetTorrentIndexInsightTool(),
        GetHealthStatusTool(),
        GetLogSnapshotTool(),
        GetRecommendationPreviewTool(),
        GetRunnerStatusTool(),  # FUTURE-AI-LOG-DOCTOR-1
        GetStorageSnapshotTool(),  # FUTURE-AI-CLEANUP-ADVISOR-1
        GetLibrarySnapshotTool(),  # FUTURE-AI-CLEANUP-ADVISOR-1
        GetReadingSnapshotTool(),  # FUTURE-AI-READING-ASSISTANT-1
        GetLibraryBooksTool(),  # FUTURE-AI-READING-ASSISTANT-1
    ]
    
    for tool in builtin_tools:
        registry.register(tool)
    
    logger.info(f"[tool_registry] 已注册 {len(builtin_tools)} 个内置工具")
