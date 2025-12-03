"""
AI 订阅工作流 API

FUTURE-AI-SUBS-WORKFLOW-1 P3 实现
提供订阅工作流草案的预览与应用接口
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.config import settings
from app.services.ai_subs_workflow import AISubsWorkflowService
from app.schemas.ai_subs_workflow import (
    SubsWorkflowDraft,
    SubsWorkflowPreviewRequest,
    SubsWorkflowPreviewResponse,
    SubsWorkflowApplyRequest,
    SubsWorkflowApplyResponse,
    SubsTargetMediaType,
)

router = APIRouter(prefix="/ai/subs-workflow", tags=["AI 订阅工作流"])


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
    "/preview",
    response_model=SubsWorkflowPreviewResponse,
    summary="预览订阅工作流草案",
    description="根据自然语言请求，调用 AI Orchestrator 生成订阅工作流草案",
    dependencies=[Depends(check_orchestrator_enabled)],
)
async def preview_subs_workflow(
    request: SubsWorkflowPreviewRequest,
    db: AsyncSession = Depends(get_async_session),
    user_id: int = Depends(get_current_user_id),
):
    """
    预览订阅工作流草案
    
    流程：
    1. 调用 AIOrchestratorService (SUBS_ADVISOR 模式)
    2. 解析 LLM 返回的草案 JSON
    3. 验证和补全草案数据
    4. 返回草案列表供用户确认
    
    注意：此接口只生成草案，不会创建实际订阅
    """
    try:
        service = AISubsWorkflowService(db)
        
        drafts, summary, notes, plan = await service.preview(
            user_id=user_id,
            prompt=request.prompt,
            force_dummy=request.force_dummy,
        )
        
        return SubsWorkflowPreviewResponse(
            success=True,
            drafts=drafts,
            summary=summary,
            notes=notes,
            orchestrator_plan=plan,
        )
        
    except Exception as e:
        logger.error(f"[ai_subs_workflow] 预览失败: {e}")
        return SubsWorkflowPreviewResponse(
            success=False,
            error=str(e)[:200],
        )


@router.post(
    "/apply",
    response_model=SubsWorkflowApplyResponse,
    summary="应用订阅工作流草案",
    description="将用户确认的草案应用到真实订阅模型，创建订阅记录",
    dependencies=[Depends(check_orchestrator_enabled)],
)
async def apply_subs_workflow(
    request: SubsWorkflowApplyRequest,
    db: AsyncSession = Depends(get_async_session),
    user_id: int = Depends(get_current_user_id),
):
    """
    应用订阅工作流草案
    
    流程：
    1. 验证草案数据
    2. 处理 RSSHub 订阅
    3. 创建媒体订阅（默认暂停状态）
    4. 返回创建结果
    
    安全策略：
    - 必须设置 confirm=True 才会执行
    - 创建的订阅默认处于暂停状态
    - 自动下载默认关闭
    """
    # 确认检查
    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须确认应用草案（confirm=true）",
        )
    
    try:
        service = AISubsWorkflowService(db)
        
        subscription_id, subscription_name, warnings, rsshub_count = await service.apply(
            user_id=user_id,
            draft=request.draft,
        )
        
        return SubsWorkflowApplyResponse(
            success=True,
            subscription_id=subscription_id,
            subscription_name=subscription_name,
            rsshub_subscriptions_created=rsshub_count,
            warnings=warnings,
        )
        
    except ValueError as e:
        return SubsWorkflowApplyResponse(
            success=False,
            error=str(e),
        )
    except Exception as e:
        logger.error(f"[ai_subs_workflow] 应用失败: {e}")
        return SubsWorkflowApplyResponse(
            success=False,
            error=f"应用草案时发生错误: {str(e)[:100]}",
        )


# ==================== 辅助端点 ====================

class MediaTypeInfo(BaseModel):
    """媒体类型信息"""
    value: str
    label: str
    supported: bool


@router.get(
    "/media-types",
    response_model=Dict[str, Any],
    summary="获取支持的媒体类型",
    description="返回 v1 支持的媒体类型列表",
)
async def get_supported_media_types():
    """获取支持的媒体类型"""
    return {
        "media_types": [
            {"value": "movie", "label": "电影", "supported": True},
            {"value": "tv", "label": "电视剧", "supported": True},
            {"value": "anime", "label": "动漫", "supported": True},
            {"value": "short_drama", "label": "短剧", "supported": False},
            {"value": "music", "label": "音乐", "supported": False},
            {"value": "book", "label": "小说", "supported": False},
            {"value": "comic", "label": "漫画", "supported": False},
        ],
        "version": "v1",
        "note": "v1 版本仅支持电影、电视剧、动漫类型",
    }


class PromptExample(BaseModel):
    """提示词示例"""
    prompt: str
    description: str
    media_type: str


@router.get(
    "/prompt-examples",
    response_model=Dict[str, Any],
    summary="获取提示词示例",
    description="返回一些示例提示词，帮助用户了解如何使用 AI 订阅助手",
)
async def get_prompt_examples():
    """获取提示词示例"""
    return {
        "examples": [
            {
                "prompt": "帮我订阅最近热门的韩剧，优先 1080p，要有中文字幕",
                "description": "韩剧热门订阅",
                "media_type": "tv",
            },
            {
                "prompt": "我想追新番动漫，不要 HR 种子，只要 1080p 以上",
                "description": "新番动漫订阅",
                "media_type": "anime",
            },
            {
                "prompt": "订阅豆瓣高分电影，评分 8 分以上，优先 4K HDR",
                "description": "高分电影订阅",
                "media_type": "movie",
            },
            {
                "prompt": "帮我做一套韩剧热门订阅工作流，含试跑预览",
                "description": "完整工作流示例",
                "media_type": "tv",
            },
        ],
        "tips": [
            "描述越具体，生成的订阅规则越精准",
            "可以指定分辨率、字幕语言、HR 策略等偏好",
            "生成的草案需要手动确认后才会创建订阅",
        ],
    }
