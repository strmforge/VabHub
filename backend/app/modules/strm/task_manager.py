"""
STRM同步任务管理器
跟踪和管理正在运行的STRM同步任务
"""

import asyncio
import uuid
from typing import Dict, Optional, Any, List
from datetime import datetime
from loguru import logger
from enum import Enum

from .sync_manager import STRMSyncManager


class SyncTaskStatus(str, Enum):
    """同步任务状态"""
    PENDING = "pending"  # 等待中
    RUNNING = "running"  # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


class STRMSyncTaskManager:
    """STRM同步任务管理器（单例）"""
    
    _instance: Optional['STRMSyncTaskManager'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.running_tasks: Dict[str, Dict[str, Any]] = {}  # task_id -> task_info
        self.task_history: Dict[str, Dict[str, Any]] = {}  # task_id -> task_result
        self._max_history_size = 100  # 最多保留100条历史记录
    
    async def start_sync_task(
        self,
        task_id: Optional[str] = None,
        sync_type: str = "full",  # full/incremental
        cloud_storage: str = "115",
        sync_manager: Optional[STRMSyncManager] = None,
        **kwargs
    ) -> str:
        """
        启动同步任务
        
        Args:
            task_id: 任务ID（如果为None则自动生成）
            sync_type: 同步类型（full/incremental）
            cloud_storage: 云存储类型
            sync_manager: STRM同步管理器实例（如果为None则需要在kwargs中提供必要参数）
            **kwargs: 其他参数（用于创建sync_manager）
        
        Returns:
            任务ID
        """
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        # 检查是否已有运行中的任务
        if task_id in self.running_tasks:
            logger.warning(f"任务 {task_id} 已在运行中")
            return task_id
        
        # 创建任务信息
        task_info = {
            "task_id": task_id,
            "sync_type": sync_type,
            "cloud_storage": cloud_storage,
            "status": SyncTaskStatus.PENDING.value,
            "progress": 0.0,
            "started_at": datetime.utcnow().isoformat(),
            "message": "任务已创建，等待执行...",
            "result": None,
            "error": None,
            "sync_manager": sync_manager,
            "task": None  # asyncio.Task对象
        }
        
        # 添加到运行中任务列表
        self.running_tasks[task_id] = task_info
        
        # 创建异步任务
        task = asyncio.create_task(
            self._execute_sync_task(task_id, sync_type, sync_manager, **kwargs)
        )
        task_info["task"] = task
        
        logger.info(f"STRM同步任务已启动: {task_id} (类型: {sync_type})")
        
        return task_id
    
    async def _execute_sync_task(
        self,
        task_id: str,
        sync_type: str,
        sync_manager: Optional[STRMSyncManager],
        **kwargs
    ):
        """执行同步任务"""
        task_info = self.running_tasks.get(task_id)
        if not task_info:
            logger.error(f"任务 {task_id} 不存在")
            return
        
        try:
            # 更新状态为运行中
            task_info["status"] = SyncTaskStatus.RUNNING.value
            task_info["progress"] = 10.0
            task_info["message"] = "同步任务正在执行..."
            
            # 如果没有提供sync_manager，需要创建
            if sync_manager is None:
                # 这里需要从kwargs中获取必要参数
                # 但通常应该在调用start_sync_task之前创建sync_manager
                logger.error(f"任务 {task_id} 缺少sync_manager")
                raise ValueError("缺少sync_manager参数")
            
            # 执行同步
            if sync_type == "full":
                result = await sync_manager.full_sync(
                    cloud_media_library_path=kwargs.get("cloud_media_library_path"),
                    check_local_missing_only=kwargs.get("check_local_missing_only", False)
                )
            elif sync_type == "incremental":
                result = await sync_manager.incremental_sync()
            elif sync_type == "auto":
                # 自动判断：调用start_sync，它会自动判断是全量还是增量
                await sync_manager.start_sync()
                # start_sync不返回result，需要从sync_manager获取
                result = {"status": "completed", "message": "同步任务已完成"}
            else:
                raise ValueError(f"不支持的同步类型: {sync_type}")
            
            # 更新任务信息
            task_info["status"] = SyncTaskStatus.COMPLETED.value
            task_info["progress"] = 100.0
            task_info["message"] = "同步任务已完成"
            task_info["result"] = result
            task_info["completed_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"STRM同步任务完成: {task_id}")
            
        except asyncio.CancelledError:
            # 任务被取消
            task_info["status"] = SyncTaskStatus.CANCELLED.value
            task_info["message"] = "同步任务已取消"
            task_info["cancelled_at"] = datetime.utcnow().isoformat()
            logger.info(f"STRM同步任务已取消: {task_id}")
            
        except Exception as e:
            # 任务失败
            task_info["status"] = SyncTaskStatus.FAILED.value
            task_info["message"] = f"同步任务失败: {str(e)}"
            task_info["error"] = str(e)
            task_info["failed_at"] = datetime.utcnow().isoformat()
            logger.error(f"STRM同步任务失败: {task_id}, 错误: {e}")
            
        finally:
            # 将任务移到历史记录
            await self._move_to_history(task_id)
    
    async def _move_to_history(self, task_id: str):
        """将任务移到历史记录"""
        task_info = self.running_tasks.get(task_id)
        if not task_info:
            return
        
        # 创建历史记录（不包含sync_manager和task对象）
        history_item = {
            "task_id": task_info["task_id"],
            "sync_type": task_info["sync_type"],
            "cloud_storage": task_info["cloud_storage"],
            "status": task_info["status"],
            "progress": task_info["progress"],
            "started_at": task_info["started_at"],
            "message": task_info["message"],
            "result": task_info.get("result"),
            "error": task_info.get("error"),
            "completed_at": task_info.get("completed_at"),
            "cancelled_at": task_info.get("cancelled_at"),
            "failed_at": task_info.get("failed_at")
        }
        
        # 添加到历史记录
        self.task_history[task_id] = history_item
        
        # 限制历史记录大小
        if len(self.task_history) > self._max_history_size:
            # 删除最旧的记录
            oldest_task_id = min(
                self.task_history.keys(),
                key=lambda tid: self.task_history[tid].get("started_at", "")
            )
            del self.task_history[oldest_task_id]
        
        # 从运行中任务列表移除
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]
    
    async def stop_sync_task(self, task_id: str) -> bool:
        """
        停止同步任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否成功停止
        """
        task_info = self.running_tasks.get(task_id)
        if not task_info:
            logger.warning(f"任务 {task_id} 不存在或已完成")
            return False
        
        # 取消异步任务
        task = task_info.get("task")
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # 停止sync_manager
        sync_manager = task_info.get("sync_manager")
        if sync_manager:
            try:
                await sync_manager.stop_sync()
            except Exception as e:
                logger.warning(f"停止sync_manager失败: {e}")
        
        logger.info(f"STRM同步任务已停止: {task_id}")
        return True
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务状态信息，如果任务不存在则返回None
        """
        # 先检查运行中的任务
        if task_id in self.running_tasks:
            task_info = self.running_tasks[task_id]
            # 返回任务信息（不包含sync_manager和task对象）
            return {
                "task_id": task_info["task_id"],
                "sync_type": task_info["sync_type"],
                "cloud_storage": task_info["cloud_storage"],
                "status": task_info["status"],
                "progress": task_info["progress"],
                "started_at": task_info["started_at"],
                "message": task_info["message"],
                "result": task_info.get("result"),
                "error": task_info.get("error")
            }
        
        # 检查历史记录
        if task_id in self.task_history:
            return self.task_history[task_id]
        
        return None
    
    async def list_running_tasks(self) -> List[Dict[str, Any]]:
        """
        列出所有运行中的任务
        
        Returns:
            运行中的任务列表
        """
        tasks = []
        for task_id, task_info in self.running_tasks.items():
            tasks.append({
                "task_id": task_info["task_id"],
                "sync_type": task_info["sync_type"],
                "cloud_storage": task_info["cloud_storage"],
                "status": task_info["status"],
                "progress": task_info["progress"],
                "started_at": task_info["started_at"],
                "message": task_info["message"]
            })
        return tasks
    
    async def list_task_history(
        self,
        limit: int = 20,
        sync_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        列出任务历史
        
        Args:
            limit: 返回数量限制
            sync_type: 同步类型过滤
            status: 状态过滤
        
        Returns:
            任务历史列表
        """
        history = list(self.task_history.values())
        
        # 过滤
        if sync_type:
            history = [h for h in history if h.get("sync_type") == sync_type]
        if status:
            history = [h for h in history if h.get("status") == status]
        
        # 排序（按开始时间倒序）
        history.sort(key=lambda h: h.get("started_at", ""), reverse=True)
        
        # 限制数量
        return history[:limit]
    
    async def clear_history(self):
        """清空历史记录"""
        self.task_history.clear()
        logger.info("STRM同步任务历史记录已清空")
    
    async def stop_all_tasks(self):
        """停止所有运行中的任务"""
        task_ids = list(self.running_tasks.keys())
        for task_id in task_ids:
            await self.stop_sync_task(task_id)
        logger.info(f"已停止 {len(task_ids)} 个STRM同步任务")


# 全局单例实例
_sync_task_manager: Optional[STRMSyncTaskManager] = None


def get_sync_task_manager() -> STRMSyncTaskManager:
    """获取STRM同步任务管理器单例"""
    global _sync_task_manager
    if _sync_task_manager is None:
        _sync_task_manager = STRMSyncTaskManager()
    return _sync_task_manager

