"""
AI Orchestrator HTTP API

FUTURE-AI-ORCHESTRATOR-1 P4 实现
提供 AI 总控层的 HTTP 接口
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.deps import DbSessionDep
from app.core.ai_orchestrator.service import (
    AIOrchestratorService,
    OrchestratorMode,
    OrchestratorResult,
)
from app.core.ai_orchestrator.factory import get_llm_client
from app.core.ai_orchestrator.tools.base import OrchestratorContext
from app.core.ai_orchestrator.tools.registry import get_tool_registry


router = APIRouter()


# ==================== 请求/响应模型 ====================

class OrchestratorPlanRequest(BaseModel):
    """Orchestrator 计划请求"""
    mode: OrchestratorMode = Field(
        default=OrchestratorMode.GENERIC,
        description="运行模式: generic/subs_advisor/diagnose/cleanup_advisor"
    )
    prompt: str = Field(..., description="用户自然语言请求", min_length=1, max_length=2000)


class OrchestratorExecuteRequest(BaseModel):
    """Orchestrator 执行请求"""
    mode: OrchestratorMode = Field(
        default=OrchestratorMode.GENERIC,
        description="运行模式"
    )
    prompt: str = Field(..., description="用户自然语言请求", min_length=1, max_length=2000)
    debug: bool = Field(default=False, description="是否启用调试模式")
    force_dummy: bool = Field(default=False, description="是否强制使用 Dummy LLM（测试用）")


class ToolInfo(BaseModel):
    """工具信息"""
    name: str
    description: str


class PlanResponse(BaseModel):
    """计划响应"""
    allowed_tools: list[ToolInfo]
    planned_calls: list[dict]
    summary: str


class ExecuteResponse(BaseModel):
    """执行响应"""
    success: bool
    result: Optional[OrchestratorResult] = None
    error: Optional[str] = None


class StatusResponse(BaseModel):
    """状态响应"""
    enabled: bool
    llm_configured: bool
    available_tools: list[str]
    modes: list[str]


# ==================== 依赖项 ====================

async def check_orchestrator_enabled():
    """检查 Orchestrator 是否启用"""
    from app.core.config import settings
    
    if not settings.AI_ORCH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "AI Orchestrator 未启用",
                "message": "请在配置中设置 AI_ORCH_ENABLED=true 以启用此功能",
            }
        )


async def get_current_user_optional(db: DbSessionDep):
    """
    获取当前用户（可选）
    
    TODO: 集成实际的认证系统
    """
    # 暂时返回 None，后续需要集成实际认证
    return None


async def check_admin_permission(user = Depends(get_current_user_optional)):
    """
    检查管理员权限
    
    TODO: 实现实际的权限检查
    """
    # 暂时跳过权限检查，后续需要实现
    # if user is None or not getattr(user, "is_admin", False):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="需要管理员权限"
    #     )
    pass


# ==================== API 端点 ====================

@router.get("/status", response_model=StatusResponse)
async def get_orchestrator_status():
    """
    获取 Orchestrator 状态
    
    返回是否启用、LLM 配置状态、可用工具列表等
    """
    from app.core.config import settings
    
    registry = get_tool_registry()
    
    return StatusResponse(
        enabled=settings.AI_ORCH_ENABLED,
        llm_configured=bool(settings.AI_ORCH_LLM_ENDPOINT),
        available_tools=registry.list_tool_names(),
        modes=[m.value for m in OrchestratorMode],
    )


@router.post(
    "/plan",
    response_model=PlanResponse,
    dependencies=[Depends(check_orchestrator_enabled), Depends(check_admin_permission)],
)
async def create_plan(
    request: OrchestratorPlanRequest,
    db: DbSessionDep,
    user = Depends(get_current_user_optional),
):
    """
    生成执行计划
    
    只规划不执行，返回允许的工具和计划的调用序列
    """
    try:
        # 创建上下文
        context = OrchestratorContext.from_request(db=db, user=user, debug=False)
        
        # 获取 LLM 客户端
        llm_client = get_llm_client()
        
        # 创建服务
        service = AIOrchestratorService(llm_client)
        
        # 生成计划
        result = await service.plan_only(
            context=context,
            mode=request.mode,
            prompt=request.prompt,
        )
        
        # 获取允许的工具信息
        registry = get_tool_registry()
        from app.core.ai_orchestrator.service import MODE_ALLOWED_TOOLS
        allowed_names = MODE_ALLOWED_TOOLS.get(request.mode, [])
        allowed_tools = [
            ToolInfo(name=t.name, description=t.description)
            for t in registry.list_tools()
            if t.name in allowed_names
        ]
        
        return PlanResponse(
            allowed_tools=allowed_tools,
            planned_calls=[p.model_dump() for p in result.plan],
            summary=result.llm_summary,
        )
        
    except Exception as e:
        logger.error(f"[api/orchestrator] 计划生成失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"计划生成失败: {str(e)[:100]}"
        )


@router.post(
    "/execute",
    response_model=ExecuteResponse,
    dependencies=[Depends(check_orchestrator_enabled), Depends(check_admin_permission)],
)
async def execute_orchestrator(
    request: OrchestratorExecuteRequest,
    db: DbSessionDep,
    user = Depends(get_current_user_optional),
):
    """
    执行 Orchestrator 流程
    
    完整执行：LLM 规划 → 工具执行 → LLM 总结
    
    注意：所有 llm_suggested_changes 仅为建议，不会自动执行
    """
    try:
        # 创建上下文
        context = OrchestratorContext.from_request(
            db=db,
            user=user,
            debug=request.debug,
        )
        
        # 获取 LLM 客户端
        llm_client = get_llm_client(force_dummy=request.force_dummy)
        
        # 创建服务
        service = AIOrchestratorService(llm_client)
        
        # 执行
        result = await service.run(
            context=context,
            mode=request.mode,
            prompt=request.prompt,
        )
        
        return ExecuteResponse(
            success=result.error is None,
            result=result,
            error=result.error,
        )
        
    except Exception as e:
        logger.error(f"[api/orchestrator] 执行失败: {e}")
        return ExecuteResponse(
            success=False,
            error=f"执行失败: {str(e)[:100]}",
        )


@router.get("/tools")
async def list_tools():
    """
    列出所有可用工具
    
    返回工具名称、描述和参数定义
    """
    registry = get_tool_registry()
    
    tools = []
    for tool in registry.list_tools():
        tools.append({
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.get_json_schema(),
        })
    
    return {"tools": tools}


@router.get("/modes")
async def list_modes():
    """
    列出所有运行模式
    
    返回模式名称和允许的工具列表
    """
    from app.core.ai_orchestrator.service import MODE_ALLOWED_TOOLS
    
    modes = []
    for mode in OrchestratorMode:
        modes.append({
            "name": mode.value,
            "description": {
                "generic": "通用模式 - 基础系统查询",
                "subs_advisor": "订阅顾问 - 分析站点/订阅/RSSHub 配置",
                "diagnose": "系统诊断 - 排查故障和错误",
                "cleanup_advisor": "整理顾问 - HR 风险和存储优化",
            }.get(mode.value, mode.value),
            "allowed_tools": MODE_ALLOWED_TOOLS.get(mode, []),
        })
    
    return {"modes": modes}
