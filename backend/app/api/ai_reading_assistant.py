"""
AI 阅读助手 API

FUTURE-AI-READING-ASSISTANT-1 P3 实现
提供阅读规划建议的 HTTP 接口
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.config import settings
from app.services.ai_reading_assistant import AIReadingAssistantService
from app.schemas.ai_reading_assistant import (
    ReadingPlanRequest,
    ReadingPlanResponse,
    PresetReadingPromptsResponse,
    PresetReadingPrompt,
)

router = APIRouter(prefix="/ai/reading-assistant", tags=["AI 阅读助手"])


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
    response_model=ReadingPlanResponse,
    summary="生成阅读计划草案",
    description="根据用户阅读进度和书库，调用 AI 生成阅读规划建议",
    dependencies=[Depends(check_orchestrator_enabled)],
)
async def generate_reading_plan(
    request: ReadingPlanRequest,
    db: AsyncSession = Depends(get_async_session),
    user_id: int = Depends(get_current_user_id),
):
    """
    生成阅读计划草案
    
    流程：
    1. 获取用户阅读进度和书库信息
    2. 调用 AIOrchestratorService (READING_ASSISTANT 模式)
    3. 解析 LLM 返回的阅读计划草案
    4. 返回结构化的阅读建议
    
    注意：此接口只读，不会修改任何阅读进度
    """
    try:
        # 生成阅读计划
        service = AIReadingAssistantService(db)
        plan = await service.generate_reading_plan(
            prompt=request.prompt,
            focus=request.focus,
            goal_type=request.goal_type,
            user_id=user_id,
        )
        
        return ReadingPlanResponse(
            success=True,
            plan=plan,
        )
        
    except Exception as e:
        logger.error(f"[ai_reading_assistant] 生成阅读计划失败: {e}")
        return ReadingPlanResponse(
            success=False,
            error=str(e)[:200],
        )


@router.get(
    "/preset-prompts",
    response_model=PresetReadingPromptsResponse,
    summary="获取预设提示词",
    description="返回常用阅读场景的预设提示词",
)
async def get_preset_prompts():
    """获取预设提示词"""
    raw_prompts = AIReadingAssistantService.get_preset_prompts()
    
    prompts = [
        PresetReadingPrompt(
            id=p["id"],
            title=p["title"],
            prompt=p["prompt"],
            description=p["description"],
            focus=p.get("focus"),
        )
        for p in raw_prompts
    ]
    
    return PresetReadingPromptsResponse(prompts=prompts)


@router.get(
    "/status",
    summary="检查服务状态",
    description="检查 AI 阅读助手服务是否可用",
)
async def check_service_status():
    """检查服务状态"""
    return {
        "enabled": settings.AI_ORCH_ENABLED,
        "service": "ai_reading_assistant",
        "version": "v1",
        "features": [
            "阅读进度分析",
            "书库统计",
            "阅读目标规划",
            "个性化推荐",
        ],
        "supported_media_types": [
            "novel",
            "manga",
            "audiobook",
        ],
    }
