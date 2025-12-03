"""
Runner 状态工具

FUTURE-AI-LOG-DOCTOR-1 P1 实现
获取定时任务/Runner 的执行状态
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from loguru import logger

from .base import AITool, OrchestratorContext


class RunnerFilterInput(BaseModel):
    """Runner 过滤输入参数"""
    runner_names: Optional[list[str]] = Field(
        None,
        description="Runner 名称列表（可选，不填则返回全部）"
    )
    include_failed_only: bool = Field(
        False,
        description="是否仅返回失败的 Runner"
    )
    limit: int = Field(
        20,
        description="返回条数限制",
        ge=1,
        le=50
    )


class RunnerExecution(BaseModel):
    """Runner 最近执行记录"""
    status: str  # completed / failed / running
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None


class RunnerInfo(BaseModel):
    """Runner 信息"""
    job_id: str
    name: str
    task_type: str  # subscription / download / rss / hnr / cache / checkin / other
    status: str  # pending / running / completed / failed
    trigger_type: str  # interval / cron / date / unknown
    trigger_desc: str  # 触发器描述（如 "每30分钟"）
    next_run_time: Optional[str] = None
    last_run_time: Optional[str] = None
    run_count: int = 0
    success_count: int = 0
    fail_count: int = 0
    success_rate: float = 0.0
    recent_executions: list[RunnerExecution] = Field(default_factory=list)
    has_recent_error: bool = False  # 最近是否有执行失败


class RunnerStatusOutput(BaseModel):
    """Runner 状态输出"""
    total_runners: int = 0
    running_count: int = 0
    failed_count: int = 0
    healthy_count: int = 0
    runners: list[RunnerInfo] = Field(default_factory=list)
    summary_text: str = ""


class GetRunnerStatusTool(AITool):
    """
    Runner 状态工具
    
    获取定时任务/Runner 的执行状态，用于诊断调度问题
    """
    
    name = "get_runner_status"
    description = (
        "获取系统定时任务（Runner）的状态。"
        "包括订阅搜索、下载状态更新、RSS 检查、RSSHub 处理、漫画追更等关键任务。"
        "返回每个 Runner 的运行状态、成功率、最近执行记录和错误信息。"
        "用于诊断调度任务是否正常运行。"
    )
    input_model = RunnerFilterInput
    output_model = RunnerStatusOutput
    
    async def run(
        self,
        params: RunnerFilterInput,
        context: OrchestratorContext,
    ) -> RunnerStatusOutput:
        """获取 Runner 状态"""
        try:
            runners = await self._get_runner_status(
                context=context,
                runner_names=params.runner_names,
                include_failed_only=params.include_failed_only,
                limit=params.limit,
            )
            
            # 统计
            total = len(runners)
            running = sum(1 for r in runners if r.status == "running")
            failed = sum(1 for r in runners if r.has_recent_error or r.status == "failed")
            healthy = total - failed
            
            # 生成摘要
            if failed > 0:
                failed_names = [r.name for r in runners if r.has_recent_error or r.status == "failed"][:3]
                summary_text = f"共 {total} 个 Runner，{failed} 个有问题：{', '.join(failed_names)}"
            elif total == 0:
                summary_text = "未找到定时任务记录，可能调度器未初始化。"
            else:
                summary_text = f"共 {total} 个 Runner，全部正常运行。"
            
            return RunnerStatusOutput(
                total_runners=total,
                running_count=running,
                failed_count=failed,
                healthy_count=healthy,
                runners=runners,
                summary_text=summary_text,
            )
            
        except Exception as e:
            logger.error(f"[runner_status] 获取 Runner 状态失败: {e}")
            return RunnerStatusOutput(
                summary_text=f"获取 Runner 状态时发生错误: {str(e)[:100]}"
            )
    
    async def _get_runner_status(
        self,
        context: OrchestratorContext,
        runner_names: Optional[list[str]],
        include_failed_only: bool,
        limit: int,
    ) -> list[RunnerInfo]:
        """获取 Runner 状态列表"""
        runners: list[RunnerInfo] = []
        
        try:
            from app.modules.scheduler.monitor import SchedulerMonitor
            
            monitor = SchedulerMonitor(context.db)
            
            # 获取所有任务
            tasks = await monitor.get_tasks()
            
            for task in tasks[:limit]:
                # 过滤
                if runner_names and task.job_id not in runner_names:
                    continue
                
                # 获取最近执行记录
                executions = await monitor.get_execution_history(
                    job_id=task.job_id,
                    limit=5
                )
                
                recent_execs = []
                has_recent_error = False
                
                for exe in executions:
                    recent_execs.append(RunnerExecution(
                        status=exe.status,
                        started_at=exe.started_at.isoformat() if exe.started_at else None,
                        completed_at=exe.completed_at.isoformat() if exe.completed_at else None,
                        duration_seconds=exe.duration,
                        error_message=self._truncate(exe.error_message, 100) if exe.error_message else None,
                    ))
                    if exe.status == "failed":
                        has_recent_error = True
                
                # 如果只要失败的
                if include_failed_only and not has_recent_error and task.status != "failed":
                    continue
                
                # 计算成功率
                success_rate = 0.0
                if task.run_count > 0:
                    success_rate = round(task.success_count / task.run_count * 100, 1)
                
                # 触发器描述
                trigger_desc = self._get_trigger_desc(task.trigger_type, task.trigger_config)
                
                runners.append(RunnerInfo(
                    job_id=task.job_id,
                    name=task.name,
                    task_type=task.task_type or "other",
                    status=task.status,
                    trigger_type=task.trigger_type or "unknown",
                    trigger_desc=trigger_desc,
                    next_run_time=task.next_run_time.isoformat() if task.next_run_time else None,
                    last_run_time=task.last_run_time.isoformat() if task.last_run_time else None,
                    run_count=task.run_count,
                    success_count=task.success_count,
                    fail_count=task.fail_count,
                    success_rate=success_rate,
                    recent_executions=recent_execs,
                    has_recent_error=has_recent_error,
                ))
            
        except ImportError:
            logger.warning("[runner_status] SchedulerMonitor 不可用")
        except Exception as e:
            logger.warning(f"[runner_status] 获取任务状态失败: {e}")
        
        return runners
    
    def _get_trigger_desc(self, trigger_type: Optional[str], trigger_config: Optional[dict]) -> str:
        """生成触发器描述"""
        if not trigger_type or not trigger_config:
            return "未知"
        
        try:
            if trigger_type == "interval":
                seconds = trigger_config.get("seconds")
                if seconds:
                    if seconds >= 3600:
                        return f"每 {int(seconds / 3600)} 小时"
                    elif seconds >= 60:
                        return f"每 {int(seconds / 60)} 分钟"
                    else:
                        return f"每 {int(seconds)} 秒"
            elif trigger_type == "cron":
                return f"Cron: {trigger_config.get('fields', '?')}"
        except Exception:
            pass
        
        return str(trigger_config.get("trigger", "?"))[:30]
    
    def _truncate(self, text: str, max_len: int) -> str:
        """截断文本"""
        if len(text) <= max_len:
            return text
        return text[:max_len - 3] + "..."
