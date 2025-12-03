"""
AI 整理顾问 API

FUTURE-AI-CLEANUP-ADVISOR-1 P3 实现
提供媒体库清理建议的 HTTP 接口
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.config import settings
from app.services.ai_cleanup_advisor import AICleanupAdvisorService
from app.schemas.ai_cleanup_advisor import (
    CleanupRequest,
    CleanupResponse,
    PresetCleanupPromptsResponse,
    PresetCleanupPrompt,
    CleanupScope,
    CleanupFocus,
)

router = APIRouter(prefix="/ai/cleanup-advisor", tags=["AI 整理顾问"])


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
    "/generate",
    response_model=CleanupResponse,
    summary="生成清理计划草案",
    description="根据用户需求和存储情况，调用 AI 生成清理建议",
    dependencies=[Depends(check_orchestrator_enabled)],
)
async def generate_cleanup_plan(
    request: CleanupRequest,
    db: AsyncSession = Depends(get_async_session),
    user_id: int = Depends(get_current_user_id),
):
    """
    生成清理计划草案
    
    流程：
    1. 构建清理范围（聚焦类型、大小过滤）
    2. 调用 AIOrchestratorService (CLEANUP_ADVISOR 模式)
    3. 解析 LLM 返回的清理计划草案
    4. 返回结构化的清理建议
    
    注意：此接口只读，不会执行任何删除或移动操作
    """
    try:
        # 构建清理范围
        scope = None
        if request.focus or request.min_size_gb is not None:
            focus = CleanupFocus.ALL
            if request.focus:
                try:
                    focus = CleanupFocus(request.focus)
                except ValueError:
                    pass
            
            scope = CleanupScope(
                focus=focus,
                min_size_gb=request.min_size_gb,
                include_risky=request.include_risky,
            )
        
        # 生成清理计划
        service = AICleanupAdvisorService(db)
        draft = await service.generate_cleanup_plan(
            prompt=request.prompt,
            scope=scope,
            user_id=user_id,
        )
        
        return CleanupResponse(
            success=True,
            draft=draft,
        )
        
    except Exception as e:
        logger.error(f"[ai_cleanup_advisor] 生成清理计划失败: {e}")
        return CleanupResponse(
            success=False,
            error=str(e)[:200],
        )


@router.get(
    "/preset-prompts",
    response_model=PresetCleanupPromptsResponse,
    summary="获取预设提示词",
    description="返回常用清理场景的预设提示词",
)
async def get_preset_prompts():
    """获取预设提示词"""
    raw_prompts = AICleanupAdvisorService.get_preset_prompts()
    
    prompts = [
        PresetCleanupPrompt(
            id=p["id"],
            title=p["title"],
            prompt=p["prompt"],
            description=p["description"],
            focus=p.get("focus"),
        )
        for p in raw_prompts
    ]
    
    return PresetCleanupPromptsResponse(prompts=prompts)


@router.get(
    "/status",
    summary="检查服务状态",
    description="检查 AI 整理顾问服务是否可用",
)
async def check_service_status():
    """检查服务状态"""
    return {
        "enabled": settings.AI_ORCH_ENABLED,
        "service": "ai_cleanup_advisor",
        "version": "v1",
        "features": [
            "存储空间分析",
            "重复媒体识别",
            "保种状态检查",
            "清理风险评估",
        ],
        "constraints": [
            "只读操作，不会自动执行删除",
            "高风险内容需手动确认",
        ],
    }
