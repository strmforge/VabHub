"""
调度器监控服务
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from app.models.scheduler_task import SchedulerTask, SchedulerTaskExecution
from app.core.scheduler import get_scheduler


class SchedulerMonitor:
    """调度器监控服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.scheduler = get_scheduler()

    async def _get_or_create_task(self, job_id: str) -> Optional[SchedulerTask]:
        """获取或自动创建任务记录，避免缺失导致的重复告警"""
        result_query = await self.db.execute(
            select(SchedulerTask).where(SchedulerTask.job_id == job_id)
        )
        task = result_query.scalar_one_or_none()
        if task:
            return task

        job = None
        if self.scheduler:
            try:
                job = self.scheduler.get_job(job_id)
            except Exception as e:
                logger.debug(f"获取调度任务 {job_id} 信息失败: {e}")

        # 安全地获取任务属性，避免 'dict' object has no attribute 'name' 错误
        name = job_id  # 默认使用job_id作为名称
        trigger_type = "unknown"
        trigger_config = {}
        next_run_time = None
        
        if job and hasattr(job, 'name'):
            name = job.name if job.name else job_id
        if job and hasattr(job, 'trigger'):
            trigger_type = self._get_trigger_type(job.trigger)
            trigger_config = self._get_trigger_config(job.trigger)
        if job and hasattr(job, 'next_run_time'):
            next_run_time = job.next_run_time

        task = SchedulerTask(
            job_id=job_id,
            name=name,
            task_type=self._get_task_type(name),
            status="pending",
            trigger_type=trigger_type,
            trigger_config=trigger_config,
            next_run_time=next_run_time,
            enabled=True,
        )
        self.db.add(task)
        await self.db.flush()
        logger.info(f"自动创建调度任务记录: {job_id}")
        return task
    
    async def sync_tasks(self):
        """同步任务到数据库"""
        try:
            jobs = self.scheduler.get_jobs()
            
            for job in jobs:
                # 安全地获取任务属性，避免 'dict' object has no attribute 'name' 错误
                if not hasattr(job, 'id') or not hasattr(job, 'name'):
                    logger.warning(f"跳过无效的调度任务对象: {job}")
                    continue
                    
                # 查找或创建任务记录
                result = await self.db.execute(
                    select(SchedulerTask).where(SchedulerTask.job_id == job.id)
                )
                task = result.scalar_one_or_none()
                
                if not task:
                    # 创建新任务
                    task = SchedulerTask(
                        job_id=job.id,
                        name=job.name,
                        task_type=self._get_task_type(job.name),
                        status="pending",
                        trigger_type=self._get_trigger_type(job.trigger),
                        trigger_config=self._get_trigger_config(job.trigger),
                        next_run_time=job.next_run_time,
                        enabled=True
                    )
                    self.db.add(task)
                else:
                    # 更新任务
                    task.name = job.name
                    task.next_run_time = job.next_run_time
                    task.trigger_type = self._get_trigger_type(job.trigger)
                    task.trigger_config = self._get_trigger_config(job.trigger)
                    task.updated_at = datetime.utcnow()
                
                await self.db.flush()
            
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"同步任务失败: {e}")
    
    async def record_execution(
        self,
        job_id: str,
        status: str,
        started_at: datetime,
        completed_at: Optional[datetime] = None,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        error_traceback: Optional[str] = None
    ):
        """记录任务执行"""
        try:
            task = await self._get_or_create_task(job_id)
            if not task:
                logger.warning(f"无法找到或创建任务记录: {job_id}")
                return
            
            # 计算执行耗时
            duration = None
            if completed_at:
                duration = (completed_at - started_at).total_seconds()
            
            # 创建执行记录
            execution = SchedulerTaskExecution(
                task_id=task.id,
                job_id=job_id,
                status=status,
                started_at=started_at,
                completed_at=completed_at,
                duration=duration,
                result=result,
                error_message=error_message,
                error_traceback=error_traceback
            )
            self.db.add(execution)
            
            # 更新任务统计
            task.last_run_time = started_at
            task.run_count += 1
            if status == "completed":
                task.success_count += 1
                task.status = "completed"
            elif status == "failed":
                task.fail_count += 1
                task.status = "failed"
            else:
                task.status = "running"
            
            task.updated_at = datetime.utcnow()
            
            await self.db.flush()
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"记录任务执行失败: {e}")
    
    async def get_tasks(
        self,
        status: Optional[str] = None,
        enabled: Optional[bool] = None,
        task_type: Optional[str] = None
    ) -> List[SchedulerTask]:
        """获取任务列表"""
        query = select(SchedulerTask)
        if status:
            query = query.where(SchedulerTask.status == status)
        if enabled is not None:
            query = query.where(SchedulerTask.enabled == enabled)
        if task_type:
            query = query.where(SchedulerTask.task_type == task_type)
        
        query = query.order_by(SchedulerTask.next_run_time.asc())
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_task(self, job_id: str) -> Optional[SchedulerTask]:
        """获取任务详情"""
        result = await self.db.execute(
            select(SchedulerTask).where(SchedulerTask.job_id == job_id)
        )
        return result.scalar_one_or_none()
    
    async def get_execution_history(
        self,
        job_id: Optional[str] = None,
        task_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[SchedulerTaskExecution]:
        """获取执行历史"""
        query = select(SchedulerTaskExecution)
        if job_id:
            query = query.where(SchedulerTaskExecution.job_id == job_id)
        if task_id:
            query = query.where(SchedulerTaskExecution.task_id == task_id)
        if status:
            query = query.where(SchedulerTaskExecution.status == status)
        
        query = query.order_by(desc(SchedulerTaskExecution.started_at)).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_task_statistics(self, job_id: str) -> Dict[str, Any]:
        """获取任务统计信息"""
        task = await self.get_task(job_id)
        if not task:
            return {}
        
        # 获取最近的执行记录
        recent_executions = await self.get_execution_history(job_id=job_id, limit=10)
        
        # 计算平均执行时间
        completed_executions = [e for e in recent_executions if e.status == "completed" and e.duration]
        avg_duration = sum(e.duration for e in completed_executions) / len(completed_executions) if completed_executions else None
        
        # 计算成功率
        total = task.run_count
        success_rate = (task.success_count / total * 100) if total > 0 else 0
        
        return {
            "task_id": task.id,
            "job_id": task.job_id,
            "name": task.name,
            "status": task.status,
            "run_count": task.run_count,
            "success_count": task.success_count,
            "fail_count": task.fail_count,
            "success_rate": success_rate,
            "avg_duration": avg_duration,
            "last_run_time": task.last_run_time.isoformat() if task.last_run_time else None,
            "next_run_time": task.next_run_time.isoformat() if task.next_run_time else None,
            "recent_executions": [{
                "id": e.id,
                "status": e.status,
                "started_at": e.started_at.isoformat(),
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                "duration": e.duration,
                "error_message": e.error_message
            } for e in recent_executions]
        }
    
    async def get_overall_statistics(self) -> Dict[str, Any]:
        """获取整体统计信息"""
        # 获取所有任务
        tasks = await self.get_tasks()
        
        total_tasks = len(tasks)
        enabled_tasks = len([t for t in tasks if t.enabled])
        running_tasks = len([t for t in tasks if t.status == "running"])
        failed_tasks = len([t for t in tasks if t.status == "failed"])
        
        # 计算总执行次数
        total_runs = sum(t.run_count for t in tasks)
        total_success = sum(t.success_count for t in tasks)
        total_fail = sum(t.fail_count for t in tasks)
        
        # 计算总体成功率
        overall_success_rate = (total_success / total_runs * 100) if total_runs > 0 else 0
        
        return {
            "total_tasks": total_tasks,
            "enabled_tasks": enabled_tasks,
            "running_tasks": running_tasks,
            "failed_tasks": failed_tasks,
            "total_runs": total_runs,
            "total_success": total_success,
            "total_fail": total_fail,
            "overall_success_rate": overall_success_rate
        }
    
    def _get_task_type(self, job_name: str) -> str:
        """获取任务类型"""
        if "subscription" in job_name.lower() or "订阅" in job_name:
            return "subscription"
        elif "download" in job_name.lower() or "下载" in job_name:
            return "download"
        elif "rss" in job_name.lower():
            return "rss"
        elif "hnr" in job_name.lower():
            return "hnr"
        elif "cache" in job_name.lower() or "缓存" in job_name:
            return "cache"
        elif "checkin" in job_name.lower() or "签到" in job_name:
            return "checkin"
        else:
            return "other"
    
    def _get_trigger_type(self, trigger) -> str:
        """获取触发器类型"""
        trigger_str = str(trigger)
        if "interval" in trigger_str.lower():
            return "interval"
        elif "cron" in trigger_str.lower():
            return "cron"
        elif "date" in trigger_str.lower():
            return "date"
        else:
            return "unknown"
    
    def _get_trigger_config(self, trigger) -> Dict[str, Any]:
        """获取触发器配置"""
        try:
            if hasattr(trigger, "interval"):
                return {
                    "type": "interval",
                    "seconds": trigger.interval.total_seconds() if hasattr(trigger.interval, "total_seconds") else None
                }
            elif hasattr(trigger, "fields"):
                return {
                    "type": "cron",
                    "fields": str(trigger.fields)
                }
            else:
                return {
                    "type": "unknown",
                    "trigger": str(trigger)
                }
        except:
            return {
                "type": "unknown",
                "trigger": str(trigger)
            }

