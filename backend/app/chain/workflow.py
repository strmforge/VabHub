"""
工作流处理链
统一处理工作流相关操作
"""

from typing import List, Optional, Dict, Any
from app.chain.base import ChainBase
from app.core.database import AsyncSessionLocal
from loguru import logger


class WorkflowChain(ChainBase):
    """工作流处理链"""
    
    def __init__(self):
        super().__init__()
    
    def _get_service(self, session):
        """
        获取工作流服务实例
        
        Args:
            session: 数据库会话
        
        Returns:
            WorkflowService 实例
        """
        from app.modules.workflow.service import WorkflowService
        return WorkflowService(session)
    
    # ========== 工作流管理 ==========
    
    async def list_workflows(
        self,
        active_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        列出工作流
        
        Args:
            active_only: 是否只返回激活的工作流
        
        Returns:
            工作流列表
        """
        # 检查缓存
        cache_key = self._get_cache_key("list_workflows", active_only)
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug(f"从缓存获取工作流列表: active_only={active_only}")
            return cached_result
        
        # 执行操作
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            workflows = await service.list_workflows(active_only)
            
            # 转换为字典
            result = [self._workflow_to_dict(wf) for wf in workflows]
            
            # 缓存结果（1分钟）
            await self._set_to_cache(cache_key, result, ttl=60)
            
            return result
    
    async def get_workflow(self, workflow_id: int) -> Optional[Dict[str, Any]]:
        """
        获取工作流详情
        
        Args:
            workflow_id: 工作流ID
        
        Returns:
            工作流详情
        """
        # 检查缓存
        cache_key = self._get_cache_key("get_workflow", workflow_id)
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug(f"从缓存获取工作流详情: workflow_id={workflow_id}")
            return cached_result
        
        # 执行操作
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            workflow = await service.get_workflow(workflow_id)
            
            if workflow:
                result = self._workflow_to_dict(workflow)
                # 缓存结果（1分钟）
                await self._set_to_cache(cache_key, result, ttl=60)
                return result
            
            return None
    
    async def create_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建工作流
        
        Args:
            workflow_data: 工作流数据
        
        Returns:
            创建的工作流
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            workflow = await service.create_workflow(workflow_data)
            
            # 清除工作流列表缓存
            await self._clear_workflow_cache()
            
            return self._workflow_to_dict(workflow)
    
    async def update_workflow(
        self,
        workflow_id: int,
        workflow_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        更新工作流
        
        Args:
            workflow_id: 工作流ID
            workflow_data: 工作流数据
        
        Returns:
            更新后的工作流
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            workflow = await service.update_workflow(workflow_id, workflow_data)
            
            if workflow:
                # 清除相关缓存
                await self._clear_workflow_cache(workflow_id)
                return self._workflow_to_dict(workflow)
            
            return None
    
    async def delete_workflow(self, workflow_id: int) -> bool:
        """
        删除工作流
        
        Args:
            workflow_id: 工作流ID
        
        Returns:
            是否成功
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            success = await service.delete_workflow(workflow_id)
            
            if success:
                # 清除相关缓存
                await self._clear_workflow_cache(workflow_id)
            
            return success
    
    async def execute_workflow(
        self,
        workflow_id: int,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行工作流
        
        Args:
            workflow_id: 工作流ID
            context: 执行上下文
        
        Returns:
            执行结果
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            result = await service.execute_workflow(workflow_id, context)
            
            # 清除工作流详情缓存（因为执行历史可能改变）
            await self._clear_workflow_cache(workflow_id)
            
            return result
    
    async def get_execution_history(
        self,
        workflow_id: int,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取工作流执行历史
        
        Args:
            workflow_id: 工作流ID
            limit: 返回数量限制
        
        Returns:
            执行历史列表
        """
        async with AsyncSessionLocal() as session:
            service = self._get_service(session)
            # 使用get_executions方法
            history = await service.get_executions(workflow_id=workflow_id, limit=limit)
            
            # 转换为字典
            return [self._execution_to_dict(execution) for execution in history]
    
    # ========== 辅助方法 ==========
    
    def _workflow_to_dict(self, workflow) -> Dict[str, Any]:
        """将工作流对象转换为字典"""
        import json
        return {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "trigger_event": workflow.trigger_event,
            "conditions": json.loads(workflow.conditions) if workflow.conditions else None,
            "actions": json.loads(workflow.actions) if workflow.actions else [],
            "is_active": workflow.is_active,
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
        }
    
    def _execution_to_dict(self, execution) -> Dict[str, Any]:
        """将执行历史对象转换为字典"""
        import json
        return {
            "id": execution.id,
            "workflow_id": execution.workflow_id,
            "status": execution.status,
            "result": json.loads(execution.result) if execution.result else None,
            "error_message": execution.error_message,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        }
    
    async def _clear_workflow_cache(self, workflow_id: Optional[int] = None):
        """
        清除工作流缓存
        
        Args:
            workflow_id: 工作流ID（如果指定，只清除该工作流的缓存；否则清除所有缓存）
        """
        if workflow_id:
            # 清除特定工作流的缓存
            cache_key = self._get_cache_key("get_workflow", workflow_id)
            if cache_key in self._cache:
                del self._cache[cache_key]
        else:
            # 清除所有工作流相关缓存
            keys_to_remove = [
                key for key in self._cache.keys()
                if "list_workflows" in key or "get_workflow" in key
            ]
            for key in keys_to_remove:
                del self._cache[key]
        
        logger.debug(f"已清除工作流缓存: workflow_id={workflow_id}")

