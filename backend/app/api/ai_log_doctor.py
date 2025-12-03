"""
AI 故障医生 API

FUTURE-AI-LOG-DOCTOR-1 P3 实现
提供系统健康诊断的 HTTP 接口
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.config import settings
from app.services.ai_log_doctor import AILogDoctorService
from app.schemas.ai_log_doctor import (
    DiagnoseRequest,
    DiagnoseResponse,
    PresetPromptsResponse,
    PresetPrompt,
    DiagnosisScope,
    DiagnosisTimeWindow,
    DiagnosisFocus,
)

router = APIRouter(prefix="/ai/log-doctor", tags=["AI 故障医生"])


# ==================== 依赖项 ====================

async def check_orchestrator_enabled():
    """检查 Orchestrator 是否启用"""
    if not settings.AI_ORCH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Orchestrator 未启用，请在配置中设置 AI_ORCH_ENABLED=true",
        )


async def get_current_user_id() -> int:
    """
    获取当前用户 ID
    
    TODO: 实际实现应从 JWT token 或 session 中获取
    v1 暂时返回固定值
    """
    return 1


# ==================== API 端点 ====================

@router.post(
    "/diagnose",
    response_model=DiagnoseResponse,
    summary="执行系统诊断",
    description="根据用户描述或预设场景，调用 AI 进行系统健康诊断",
    dependencies=[Depends(check_orchestrator_enabled)],
)
async def diagnose_system(
    request: DiagnoseRequest,
    db: AsyncSession = Depends(get_async_session),
    user_id: int = Depends(get_current_user_id),
):
    """
    执行系统诊断
    
    流程：
    1. 构建诊断范围（时间窗口、聚焦组件）
    2. 调用 AIOrchestratorService (DIAGNOSE 模式)
    3. 解析 LLM 返回的诊断报告
    4. 返回结构化的诊断结果
    
    注意：此接口只读，不会执行任何修复操作
    """
    try:
        # 构建诊断范围
        scope = None
        if request.time_window or request.focus:
            time_window = DiagnosisTimeWindow.HOUR_24
            if request.time_window:
                try:
                    time_window = DiagnosisTimeWindow(request.time_window)
                except ValueError:
                    pass
            
            focus = DiagnosisFocus.ALL
            if request.focus:
                try:
                    focus = DiagnosisFocus(request.focus)
                except ValueError:
                    pass
            
            scope = DiagnosisScope(time_window=time_window, focus=focus)
        
        # 执行诊断
        service = AILogDoctorService(db)
        report = await service.diagnose_system(
            prompt=request.prompt,
            scope=scope,
            user_id=user_id,
        )
        
        return DiagnoseResponse(
            success=True,
            report=report,
        )
        
    except Exception as e:
        logger.error(f"[ai_log_doctor] 诊断失败: {e}")
        return DiagnoseResponse(
            success=False,
            error=str(e)[:200],
        )


@router.get(
    "/preset-prompts",
    response_model=PresetPromptsResponse,
    summary="获取预设提示词",
    description="返回常用诊断场景的预设提示词",
)
async def get_preset_prompts():
    """获取预设提示词"""
    raw_prompts = AILogDoctorService.get_preset_prompts()
    
    prompts = [
        PresetPrompt(
            id=p["id"],
            title=p["title"],
            prompt=p["prompt"],
            description=p["description"],
            focus=p.get("focus"),
        )
        for p in raw_prompts
    ]
    
    return PresetPromptsResponse(prompts=prompts)


@router.get(
    "/status",
    summary="检查服务状态",
    description="检查 AI 故障医生服务是否可用",
)
async def check_service_status():
    """检查服务状态"""
    return {
        "enabled": settings.AI_ORCH_ENABLED,
        "service": "ai_log_doctor",
        "version": "v1",
        "features": [
            "系统健康检查",
            "日志分析",
            "Runner 状态监控",
            "站点连通性检查",
        ],
    }
