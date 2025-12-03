"""
健康检查状态工具

FUTURE-AI-ORCHESTRATOR-1 P2 实现
调用健康检查服务，提供系统健康状态概览
"""

from typing import Optional
from pydantic import BaseModel, Field
from loguru import logger

from .base import AITool, OrchestratorContext, HealthFilterInput


class ComponentHealth(BaseModel):
    """组件健康状态"""
    name: str
    status: str  # "ok" / "warning" / "error"
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    meta: Optional[dict] = None


class HealthStatusOutput(BaseModel):
    """健康状态输出"""
    overall_status: str = "unknown"  # "healthy" / "degraded" / "unhealthy"
    components: list[ComponentHealth] = Field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    summary_text: str = ""


class GetHealthStatusTool(AITool):
    """
    健康检查状态工具
    
    调用 health_checks.py 提供系统各组件的健康状态
    """
    
    name = "get_health_status"
    description = (
        "获取系统各组件的健康检查状态。"
        "包括数据库、Redis、下载器、索引器、磁盘空间等组件的状态和错误信息。"
        "用于诊断系统问题和确认服务可用性。"
    )
    input_model = HealthFilterInput
    output_model = HealthStatusOutput
    
    async def run(
        self,
        params: HealthFilterInput,
        context: OrchestratorContext,
    ) -> HealthStatusOutput:
        """执行健康检查"""
        try:
            components = await self._run_health_checks(context, params.module)
            
            # 统计状态
            error_count = sum(1 for c in components if c.status == "error")
            warning_count = sum(1 for c in components if c.status == "warning")
            
            # 判断整体状态
            if error_count > 0:
                overall_status = "unhealthy"
            elif warning_count > 0:
                overall_status = "degraded"
            else:
                overall_status = "healthy"
            
            # 生成摘要
            if overall_status == "healthy":
                summary_text = f"系统健康，共检查 {len(components)} 个组件，全部正常。"
            elif overall_status == "degraded":
                warning_names = [c.name for c in components if c.status == "warning"]
                summary_text = (
                    f"系统部分降级，{warning_count} 个组件有警告：{', '.join(warning_names[:3])}"
                )
            else:
                error_names = [c.name for c in components if c.status == "error"]
                summary_text = (
                    f"系统不健康，{error_count} 个组件异常：{', '.join(error_names[:3])}"
                )
            
            return HealthStatusOutput(
                overall_status=overall_status,
                components=components,
                error_count=error_count,
                warning_count=warning_count,
                summary_text=summary_text,
            )
            
        except Exception as e:
            logger.error(f"[health_status] 健康检查失败: {e}")
            return HealthStatusOutput(
                overall_status="unknown",
                summary_text=f"健康检查时发生错误: {str(e)[:100]}"
            )
    
    async def _run_health_checks(
        self,
        context: OrchestratorContext,
        module_filter: Optional[str],
    ) -> list[ComponentHealth]:
        """运行健康检查"""
        components: list[ComponentHealth] = []
        
        # 定义要检查的模块
        checks = [
            ("database", self._check_database),
            ("redis", self._check_redis),
            ("downloader", self._check_downloader),
            ("disk", self._check_disk),
        ]
        
        # 过滤模块
        if module_filter:
            checks = [(name, func) for name, func in checks if module_filter in name]
        
        # 执行检查
        for name, check_func in checks:
            try:
                result = await check_func(context)
                components.append(result)
            except Exception as e:
                components.append(ComponentHealth(
                    name=name,
                    status="error",
                    error_message=str(e)[:200],
                ))
        
        return components
    
    async def _check_database(self, context: OrchestratorContext) -> ComponentHealth:
        """检查数据库"""
        try:
            from app.services.health_checks import check_database
            result = await check_database(context.db)
            return ComponentHealth(
                name="database",
                status=result.status,
                duration_ms=result.duration_ms,
                error_message=result.error,
                meta=result.meta,
            )
        except Exception as e:
            return ComponentHealth(
                name="database",
                status="error",
                error_message=str(e)[:200],
            )
    
    async def _check_redis(self, context: OrchestratorContext) -> ComponentHealth:
        """检查 Redis"""
        try:
            from app.services.health_checks import check_redis
            result = await check_redis()
            return ComponentHealth(
                name="redis",
                status=result.status,
                duration_ms=result.duration_ms,
                error_message=result.error,
                meta=result.meta,
            )
        except Exception as e:
            return ComponentHealth(
                name="redis",
                status="error",
                error_message=str(e)[:200],
            )
    
    async def _check_downloader(self, context: OrchestratorContext) -> ComponentHealth:
        """检查下载器"""
        try:
            from app.services.health_checks import check_download_client
            result = await check_download_client()
            return ComponentHealth(
                name="downloader",
                status=result.status,
                duration_ms=result.duration_ms,
                error_message=result.error,
                meta=result.meta,
            )
        except Exception as e:
            return ComponentHealth(
                name="downloader",
                status="error",
                error_message=str(e)[:200],
            )
    
    async def _check_disk(self, context: OrchestratorContext) -> ComponentHealth:
        """检查磁盘空间"""
        try:
            import shutil
            from app.core.config import settings
            
            # 检查存储路径
            storage_path = getattr(settings, "STORAGE_PATH", "./data")
            usage = shutil.disk_usage(storage_path)
            
            free_gb = usage.free / (1024 ** 3)
            total_gb = usage.total / (1024 ** 3)
            used_percent = (usage.used / usage.total) * 100
            
            # 判断状态
            if free_gb < 1:
                status = "error"
                error_message = f"磁盘空间严重不足：仅剩 {free_gb:.1f} GB"
            elif free_gb < 10 or used_percent > 90:
                status = "warning"
                error_message = f"磁盘空间紧张：剩余 {free_gb:.1f} GB ({100-used_percent:.1f}%)"
            else:
                status = "ok"
                error_message = None
            
            return ComponentHealth(
                name="disk",
                status=status,
                error_message=error_message,
                meta={
                    "free_gb": round(free_gb, 1),
                    "total_gb": round(total_gb, 1),
                    "used_percent": round(used_percent, 1),
                },
            )
        except Exception as e:
            return ComponentHealth(
                name="disk",
                status="error",
                error_message=str(e)[:200],
            )
