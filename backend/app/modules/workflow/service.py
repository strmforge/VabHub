"""
工作流服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Optional, Dict
from datetime import datetime
from loguru import logger
import json

from app.models.workflow import Workflow, WorkflowExecution


class WorkflowService:
    """工作流服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_workflow(self, workflow_data: dict) -> Workflow:
        """创建工作流"""
        new_workflow = Workflow(
            name=workflow_data.get("name"),
            description=workflow_data.get("description"),
            trigger_event=workflow_data.get("trigger_event"),
            conditions=json.dumps(workflow_data.get("conditions") or {}) if workflow_data.get("conditions") else None,
            actions=json.dumps(workflow_data.get("actions") or []),
            is_active=workflow_data.get("is_active", True)
        )
        
        self.db.add(new_workflow)
        await self.db.commit()
        await self.db.refresh(new_workflow)
        
        logger.info(f"工作流已创建: {new_workflow.name} (ID: {new_workflow.id})")
        return new_workflow
    
    async def list_workflows(self, active_only: bool = False) -> List[Workflow]:
        """获取工作流列表"""
        query = select(Workflow)
        
        if active_only:
            query = query.where(Workflow.is_active == True)
        
        query = query.order_by(Workflow.created_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_workflow(self, workflow_id: int) -> Optional[Workflow]:
        """获取工作流详情"""
        result = await self.db.execute(
            select(Workflow).where(Workflow.id == workflow_id)
        )
        return result.scalar_one_or_none()
    
    async def update_workflow(self, workflow_id: int, workflow_data: dict) -> Optional[Workflow]:
        """更新工作流"""
        existing = await self.get_workflow(workflow_id)
        if not existing:
            return None
        
        if "name" in workflow_data:
            existing.name = workflow_data["name"]
        if "description" in workflow_data:
            existing.description = workflow_data["description"]
        if "trigger_event" in workflow_data:
            existing.trigger_event = workflow_data["trigger_event"]
        if "conditions" in workflow_data:
            existing.conditions = json.dumps(workflow_data["conditions"]) if workflow_data["conditions"] else None
        if "actions" in workflow_data:
            existing.actions = json.dumps(workflow_data["actions"]) if workflow_data["actions"] else "[]"
        if "is_active" in workflow_data:
            existing.is_active = workflow_data["is_active"]
        
        existing.updated_at = datetime.utcnow()
        
        self.db.add(existing)
        await self.db.commit()
        await self.db.refresh(existing)
        
        logger.info(f"工作流已更新: {existing.name} (ID: {workflow_id})")
        return existing
    
    async def delete_workflow(self, workflow_id: int) -> bool:
        """删除工作流"""
        result = await self.db.execute(
            delete(Workflow).where(Workflow.id == workflow_id)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def execute_workflow(self, workflow_id: int, context: Optional[Dict] = None) -> Dict:
        """执行工作流"""
        from app.modules.workflow.engine import WorkflowEngine
        
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return {
                "success": False,
                "message": "工作流不存在"
            }
        
        if not workflow.is_active:
            return {
                "success": False,
                "message": "工作流未启用"
            }
        
        # 创建执行记录
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            status="running",
            started_at=datetime.utcnow()
        )
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)
        
        try:
            # 解析工作流的actions和conditions
            workflow.actions = json.loads(workflow.actions) if isinstance(workflow.actions, str) else workflow.actions
            workflow.conditions = json.loads(workflow.conditions) if isinstance(workflow.conditions, str) and workflow.conditions else {}
            
            # 执行工作流
            engine = WorkflowEngine()
            result = await engine.execute(workflow, context or {})
            
            # 更新执行记录
            execution.status = "completed" if result.get("success") else "failed"
            execution.result = json.dumps(result) if result else None
            execution.completed_at = datetime.utcnow()
            if result.get("error"):
                execution.error_message = str(result.get("error"))
            
            await self.db.commit()
            
            logger.info(f"工作流执行完成: {workflow.name} (ID: {workflow_id})")
            
            return {
                "success": True,
                "execution_id": execution.id,
                "result": result
            }
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            
            # 更新执行记录
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            await self.db.commit()
            
            return {
                "success": False,
                "execution_id": execution.id,
                "error": str(e)
            }
    
    async def get_executions(self, workflow_id: Optional[int] = None, limit: int = 50) -> List[WorkflowExecution]:
        """获取执行记录"""
        query = select(WorkflowExecution)
        
        if workflow_id:
            query = query.where(WorkflowExecution.workflow_id == workflow_id)
        
        query = query.order_by(WorkflowExecution.started_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_execution(self, execution_id: int) -> Optional[WorkflowExecution]:
        """获取执行记录详情"""
        result = await self.db.execute(
            select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
        )
        return result.scalar_one_or_none()

