"""
日志快照工具

FUTURE-AI-ORCHESTRATOR-1 P2 实现
从 LogCenter 获取最近日志的采样，用于诊断分析
"""

from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from loguru import logger

from .base import AITool, OrchestratorContext, LogFilterInput


class LogEntry(BaseModel):
    """日志条目（已脱敏）"""
    timestamp: str
    level: str
    source: Optional[str] = None
    component: Optional[str] = None
    message: str  # 已脱敏的消息


class LogStatistics(BaseModel):
    """日志统计"""
    total_count: int = 0
    by_level: dict[str, int] = Field(default_factory=dict)
    by_source: dict[str, int] = Field(default_factory=dict)


class LogSnapshotOutput(BaseModel):
    """日志快照输出"""
    entries: list[LogEntry] = Field(default_factory=list)
    statistics: LogStatistics = Field(default_factory=LogStatistics)
    time_range: str = ""
    summary_text: str = ""


class GetLogSnapshotTool(AITool):
    """
    日志快照工具
    
    从 LogCenter 获取最近日志的采样，用于诊断系统行为
    """
    
    name = "get_log_snapshot"
    description = (
        "获取最近一段时间的系统日志快照。"
        "可以按日志级别、来源、组件过滤。"
        "返回最近 N 条匹配日志（已脱敏）和各维度的统计信息。"
        "用于诊断系统最近发生了什么。"
    )
    input_model = LogFilterInput
    output_model = LogSnapshotOutput
    
    async def run(
        self,
        params: LogFilterInput,
        context: OrchestratorContext,
    ) -> LogSnapshotOutput:
        """获取日志快照"""
        try:
            # 获取日志
            entries, stats = await self._get_logs(
                context=context,
                level=params.level,
                source=params.source,
                component=params.component,
                limit=params.limit,
            )
            
            # 生成摘要
            if entries:
                error_count = stats.by_level.get("error", 0) + stats.by_level.get("critical", 0)
                if error_count > 0:
                    top_error_sources = sorted(
                        [(k, v) for k, v in stats.by_source.items()],
                        key=lambda x: -x[1]
                    )[:3]
                    source_text = ", ".join(f"{s[0]}({s[1]})" for s in top_error_sources)
                    summary_text = f"最近有 {error_count} 条错误日志，主要来源：{source_text}"
                else:
                    summary_text = f"最近 {len(entries)} 条日志，无明显错误。"
            else:
                summary_text = "未找到匹配的日志记录。"
            
            # 时间范围
            if entries:
                time_range = f"{entries[-1].timestamp} ~ {entries[0].timestamp}"
            else:
                time_range = "无"
            
            return LogSnapshotOutput(
                entries=entries,
                statistics=stats,
                time_range=time_range,
                summary_text=summary_text,
            )
            
        except Exception as e:
            logger.error(f"[log_snapshot] 获取日志快照失败: {e}")
            return LogSnapshotOutput(
                summary_text=f"获取日志时发生错误: {str(e)[:100]}"
            )
    
    async def _get_logs(
        self,
        context: OrchestratorContext,
        level: Optional[str],
        source: Optional[str],
        component: Optional[str],
        limit: int,
    ) -> tuple[list[LogEntry], LogStatistics]:
        """
        获取日志
        
        尝试调用 LogCenter 服务，如果不可用则返回空结果
        """
        entries: list[LogEntry] = []
        stats = LogStatistics()
        
        try:
            # 尝试使用 LogCenter 服务
            from app.modules.log_center.service import LogCenterService
            
            log_service = LogCenterService(context.db)
            
            # 查询日志
            logs = await log_service.get_logs(
                level=level,
                source=source,
                component=component,
                limit=limit,
                start_time=datetime.now() - timedelta(hours=24),  # 最近 24 小时
            )
            
            # 转换并脱敏
            for log in logs:
                entries.append(LogEntry(
                    timestamp=str(getattr(log, "timestamp", "")),
                    level=getattr(log, "level", "info"),
                    source=getattr(log, "source", None),
                    component=getattr(log, "component", None),
                    message=self._sanitize_message(getattr(log, "message", "")),
                ))
                
                # 统计
                level_key = getattr(log, "level", "info")
                stats.by_level[level_key] = stats.by_level.get(level_key, 0) + 1
                
                source_key = getattr(log, "source", "unknown")
                stats.by_source[source_key] = stats.by_source.get(source_key, 0) + 1
            
            stats.total_count = len(entries)
            
        except ImportError:
            logger.warning("[log_snapshot] LogCenterService 不可用")
        except AttributeError as e:
            logger.warning(f"[log_snapshot] LogCenter 接口不兼容: {e}")
        except Exception as e:
            logger.warning(f"[log_snapshot] 获取日志失败: {e}")
        
        return entries, stats
    
    def _sanitize_message(self, message: str) -> str:
        """
        脱敏日志消息
        
        移除敏感信息：
        - 文件路径
        - Cookie / Token
        - 密码
        - URL 中的认证信息
        """
        import re
        
        # 限制长度
        message = message[:500] if len(message) > 500 else message
        
        # 脱敏规则
        patterns = [
            # 文件路径
            (r'[A-Za-z]:\\[^\s"\']+', "[PATH]"),
            (r'/(?:home|root|var|tmp|data|mnt|media)/[^\s"\']+', "[PATH]"),
            
            # Cookie
            (r'cookie[=:]\s*[^\s;]+', "cookie=[REDACTED]"),
            
            # Token / API Key
            (r'(token|api_key|apikey|api-key)[=:]\s*[^\s&]+', r"\1=[REDACTED]"),
            
            # 密码
            (r'(password|passwd|pwd)[=:]\s*[^\s&]+', r"\1=[REDACTED]"),
            
            # URL 认证信息
            (r'://[^:]+:[^@]+@', "://[AUTH]@"),
        ]
        
        for pattern, replacement in patterns:
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
        
        return message
