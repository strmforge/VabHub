"""
工作流相关API
使用统一响应模型
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import json
from loguru import logger

from app.core.database import get_db
from app.modules.workflow.service import WorkflowService
from app.core.schemas import (
    BaseResponse,
    PaginatedResponse,
    NotFoundResponse,
    success_response,
    error_response
)

router = APIRouter()


class WorkflowCreate(BaseModel):
    """创建工作流请求"""
    name: str
    description: Optional[str] = None
    trigger_event: str
    conditions: Optional[Dict] = None
    actions: List[Dict]
    is_active: bool = True


class WorkflowUpdate(BaseModel):
    """更新工作流请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_event: Optional[str] = None
    conditions: Optional[Dict] = None
    actions: Optional[List[Dict]] = None
    is_active: Optional[bool] = None


class WorkflowResponse(BaseModel):
    """工作流响应"""
    id: int
    name: str
    description: Optional[str]
    trigger_event: str
    conditions: Optional[Dict] = None
    actions: List[Dict]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_orm(cls, workflow: Any):
        """从ORM对象创建响应"""
        return cls(
            id=workflow.id,
            name=workflow.name,
            description=workflow.description,
            trigger_event=workflow.trigger_event,
            conditions=json.loads(workflow.conditions) if workflow.conditions else None,
            actions=json.loads(workflow.actions) if isinstance(workflow.actions, str) else (workflow.actions or []),
            is_active=workflow.is_active,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at
        )
    
    class Config:
        from_attributes = True


class WorkflowExecutionResponse(BaseModel):
    """工作流执行响应"""
    id: int
    workflow_id: int
    status: str
    result: Optional[Dict] = None
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    @classmethod
    def from_orm(cls, execution: Any):
        """从ORM对象创建响应"""
        return cls(
            id=execution.id,
            workflow_id=execution.workflow_id,
            status=execution.status,
            result=json.loads(execution.result) if execution.result else None,
            error_message=execution.error_message,
            started_at=execution.started_at,
            completed_at=execution.completed_at
        )
    
    class Config:
        from_attributes = True


class ExecuteWorkflowRequest(BaseModel):
    """执行工作流请求"""
    context: Optional[Dict] = None


@router.post("/", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow: WorkflowCreate,
    db = Depends(get_db)
):
    """
    创建工作流
    
    返回统一响应格式：
    {
        "success": true,
        "message": "创建成功",
        "data": WorkflowResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = WorkflowService(db)
        result = await service.create_workflow(workflow.model_dump())
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="CREATE_FAILED",
                    error_message="创建工作流失败"
                ).model_dump()
            )
        return success_response(
            data=WorkflowResponse.from_orm(result).model_dump(),
            message="创建成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建工作流失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"创建工作流时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/", response_model=BaseResponse)
async def list_workflows(
    active_only: bool = Query(False, description="是否只返回激活的工作流"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db = Depends(get_db)
):
    """
    获取工作流列表（支持分页）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "items": [WorkflowResponse, ...],
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = WorkflowService(db)
        workflows = await service.list_workflows(active_only=active_only)
        workflow_responses = [WorkflowResponse.from_orm(w).model_dump() for w in workflows]
        
        # 计算分页
        total = len(workflow_responses)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_items = workflow_responses[start:end]
        
        # 使用PaginatedResponse
        paginated_data = PaginatedResponse.create(
            items=paginated_items,
            total=total,
            page=page,
            page_size=page_size
        )
        
        return success_response(data=paginated_data.model_dump(), message="获取成功")
    except Exception as e:
        logger.error(f"获取工作流列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取工作流列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/{workflow_id}", response_model=BaseResponse)
async def get_workflow(
    workflow_id: int,
    db = Depends(get_db)
):
    """
    获取工作流详情
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": WorkflowResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = WorkflowService(db)
        workflow = await service.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"工作流不存在 (ID: {workflow_id})"
                ).model_dump()
            )
        return success_response(
            data=WorkflowResponse.from_orm(workflow).model_dump(),
            message="获取成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工作流详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取工作流详情时发生错误: {str(e)}"
            ).model_dump()
        )


@router.put("/{workflow_id}", response_model=BaseResponse)
async def update_workflow(
    workflow_id: int,
    workflow: WorkflowUpdate,
    db = Depends(get_db)
):
    """
    更新工作流
    
    返回统一响应格式：
    {
        "success": true,
        "message": "更新成功",
        "data": WorkflowResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = WorkflowService(db)
        result = await service.update_workflow(workflow_id, workflow.model_dump(exclude_unset=True))
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"工作流不存在 (ID: {workflow_id})"
                ).model_dump()
            )
        return success_response(
            data=WorkflowResponse.from_orm(result).model_dump(),
            message="更新成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新工作流失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新工作流时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/{workflow_id}", response_model=BaseResponse)
async def delete_workflow(
    workflow_id: int,
    db = Depends(get_db)
):
    """
    删除工作流
    
    返回统一响应格式：
    {
        "success": true,
        "message": "删除成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = WorkflowService(db)
        success = await service.delete_workflow(workflow_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"工作流不存在 (ID: {workflow_id})"
                ).model_dump()
            )
        return success_response(message="删除成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除工作流失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除工作流时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/{workflow_id}/execute", response_model=BaseResponse)
async def execute_workflow(
    workflow_id: int,
    request: ExecuteWorkflowRequest,
    db = Depends(get_db)
):
    """
    执行工作流
    
    返回统一响应格式：
    {
        "success": true,
        "message": "执行成功",
        "data": {
            "execution_id": 1,
            "status": "completed",
            "result": {...}
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = WorkflowService(db)
        result = await service.execute_workflow(workflow_id, request.context)
        if not result or not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="EXECUTE_FAILED",
                    error_message=result.get("message", "执行工作流失败") if result else "执行工作流失败",
                    details=result
                ).model_dump()
            )
        return success_response(data=result, message="执行成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行工作流失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"执行工作流时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/{workflow_id}/executions", response_model=BaseResponse)
async def get_workflow_executions(
    workflow_id: int,
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    db = Depends(get_db)
):
    """
    获取工作流执行记录
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": [WorkflowExecutionResponse, ...],
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = WorkflowService(db)
        executions = await service.get_executions(workflow_id=workflow_id, limit=limit)
        execution_responses = [WorkflowExecutionResponse.from_orm(e).model_dump() for e in executions]
        return success_response(data=execution_responses, message="获取成功")
    except Exception as e:
        logger.error(f"获取工作流执行记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取工作流执行记录时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/executions/{execution_id}", response_model=BaseResponse)
async def get_execution(
    execution_id: int,
    db = Depends(get_db)
):
    """
    获取执行记录详情
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": WorkflowExecutionResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = WorkflowService(db)
        execution = await service.get_execution(execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"执行记录不存在 (ID: {execution_id})"
                ).model_dump()
            )
        return success_response(
            data=WorkflowExecutionResponse.from_orm(execution).model_dump(),
            message="获取成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取执行记录详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取执行记录详情时发生错误: {str(e)}"
            ).model_dump()
        )

