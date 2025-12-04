"""
Workflow 扩展 API
DEV-SDK-1 实现

管理和执行插件注册的工作流
"""

import time
from fastapi import APIRouter, HTTPException
from loguru import logger

from app.core.deps import DbSessionDep, CurrentAdminUserDep
from app.schemas.plugin import (
    WorkflowExtensionInfo,
    WorkflowRunRequest,
    WorkflowRunResult,
)
from app.services.plugin_registry import get_plugin_registry


router = APIRouter(prefix="/dev/workflows", tags=["workflow-extensions"])


@router.get("", response_model=list[WorkflowExtensionInfo])
async def list_workflows(
    db: DbSessionDep,
    current_admin: CurrentAdminUserDep,
):
    """
    列出所有插件注册的 Workflow
    """
    registry = get_plugin_registry()
    workflows = []
    
    for plugin_id, loaded in registry.loaded_plugins.items():
        for wf in loaded.workflows:
            workflows.append(WorkflowExtensionInfo(
                id=wf.id,
                name=wf.name,
                description=wf.description,
                plugin_id=plugin_id,
                plugin_name=loaded.plugin.display_name,
            ))
    
    return workflows


@router.post("/{workflow_id}/run", response_model=WorkflowRunResult)
async def run_workflow(
    workflow_id: str,
    body: WorkflowRunRequest,
    db: DbSessionDep,
    current_admin: CurrentAdminUserDep,
):
    """
    执行 Workflow
    
    Args:
        workflow_id: Workflow ID
        body: 执行参数
    """
    registry = get_plugin_registry()
    
    result = registry.get_workflow_by_id(workflow_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Workflow 不存在: {workflow_id}")
    
    workflow, plugin_id = result
    
    logger.info(f"[workflow-api] Running {workflow_id} from {plugin_id}, payload={body.payload}")
    
    start = time.monotonic()
    
    try:
        output = await workflow.run(db, body.payload)
        duration_ms = int((time.monotonic() - start) * 1000)
        
        logger.info(f"[workflow-api] {workflow_id} completed in {duration_ms}ms")
        
        return WorkflowRunResult(
            workflow_id=workflow_id,
            success=True,
            result=output,
            duration_ms=duration_ms,
        )
    except Exception as e:
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.error(f"[workflow-api] {workflow_id} failed: {e}", exc_info=True)
        
        return WorkflowRunResult(
            workflow_id=workflow_id,
            success=False,
            error=str(e)[:500],
            duration_ms=duration_ms,
        )
