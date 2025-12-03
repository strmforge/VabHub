"""
存储快照工具

FUTURE-AI-CLEANUP-ADVISOR-1 P1 实现
获取存储目录使用情况，用于清理建议
"""

from typing import Optional
from pydantic import BaseModel, Field
from loguru import logger

from .base import AITool, OrchestratorContext, EmptyInput


class DirectoryUsage(BaseModel):
    """目录使用情况"""
    name: str
    path: str
    total_gb: float
    used_gb: float
    free_gb: float
    usage_percent: float
    alert_threshold: float
    has_alert: bool = False


class StorageSnapshotOutput(BaseModel):
    """存储快照输出"""
    directories: list[DirectoryUsage] = Field(default_factory=list)
    total_space_gb: float = 0.0
    total_used_gb: float = 0.0
    total_free_gb: float = 0.0
    overall_usage_percent: float = 0.0
    unresolved_alerts: int = 0
    summary_text: str = ""


class GetStorageSnapshotTool(AITool):
    """
    存储快照工具
    
    获取存储目录使用情况，用于分析可释放空间
    """
    
    name = "get_storage_snapshot"
    description = (
        "获取系统存储目录的使用情况快照。"
        "包括各监控目录的总空间、已用空间、剩余空间、使用率和预警状态。"
        "用于分析存储压力和可释放空间。"
    )
    input_model = EmptyInput
    output_model = StorageSnapshotOutput
    
    async def run(
        self,
        params: EmptyInput,
        context: OrchestratorContext,
    ) -> StorageSnapshotOutput:
        """获取存储快照"""
        try:
            directories = await self._get_directory_usage(context)
            alerts_count = await self._get_unresolved_alerts(context)
            
            # 汇总统计
            total_space = sum(d.total_gb for d in directories)
            total_used = sum(d.used_gb for d in directories)
            total_free = sum(d.free_gb for d in directories)
            overall_percent = (total_used / total_space * 100) if total_space > 0 else 0.0
            
            # 生成摘要
            if not directories:
                summary_text = "未配置存储监控目录，无法获取存储快照。"
            elif overall_percent >= 90:
                summary_text = f"存储空间紧张！总使用率 {overall_percent:.1f}%，剩余 {total_free:.1f} GB。"
            elif overall_percent >= 80:
                summary_text = f"存储空间较紧，总使用率 {overall_percent:.1f}%，剩余 {total_free:.1f} GB。"
            else:
                summary_text = f"存储空间充足，总使用率 {overall_percent:.1f}%，剩余 {total_free:.1f} GB。"
            
            if alerts_count > 0:
                summary_text += f" 有 {alerts_count} 个未解决的存储预警。"
            
            return StorageSnapshotOutput(
                directories=directories,
                total_space_gb=round(total_space, 2),
                total_used_gb=round(total_used, 2),
                total_free_gb=round(total_free, 2),
                overall_usage_percent=round(overall_percent, 1),
                unresolved_alerts=alerts_count,
                summary_text=summary_text,
            )
            
        except Exception as e:
            logger.error(f"[storage_snapshot] 获取存储快照失败: {e}")
            return StorageSnapshotOutput(
                summary_text=f"获取存储快照时发生错误: {str(e)[:100]}"
            )
    
    async def _get_directory_usage(
        self,
        context: OrchestratorContext,
    ) -> list[DirectoryUsage]:
        """获取目录使用情况"""
        directories: list[DirectoryUsage] = []
        
        try:
            from app.modules.storage_monitor.service import StorageMonitorService
            
            service = StorageMonitorService(context.db)
            usage_list = await service.get_all_directories_usage()
            
            for usage in usage_list:
                directories.append(DirectoryUsage(
                    name=usage.get("name", "未命名"),
                    path=usage.get("path", ""),
                    total_gb=round(usage.get("total_bytes", 0) / (1024**3), 2),
                    used_gb=round(usage.get("used_bytes", 0) / (1024**3), 2),
                    free_gb=round(usage.get("free_bytes", 0) / (1024**3), 2),
                    usage_percent=usage.get("usage_percent", 0.0),
                    alert_threshold=usage.get("alert_threshold", 80.0),
                    has_alert=usage.get("usage_percent", 0) >= usage.get("alert_threshold", 80),
                ))
            
        except ImportError:
            logger.warning("[storage_snapshot] StorageMonitorService 不可用")
        except Exception as e:
            logger.warning(f"[storage_snapshot] 获取目录使用情况失败: {e}")
        
        return directories
    
    async def _get_unresolved_alerts(self, context: OrchestratorContext) -> int:
        """获取未解决预警数"""
        try:
            from app.modules.storage_monitor.service import StorageMonitorService
            
            service = StorageMonitorService(context.db)
            alerts = await service.get_alerts(resolved=False)
            return len(alerts)
        except Exception:
            return 0
