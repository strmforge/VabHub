"""
下载决策调试 API
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.schemas import BaseResponse, error_response, success_response
from app.modules.subscription.service import SubscriptionService

router = APIRouter()


class DecisionDryRunRequest(BaseModel):
    """决策 Dry-run 请求体。"""

    subscription_id: int = Field(..., description="需要评估的订阅 ID")
    candidate: Dict[str, Any] = Field(..., description="候选资源，通常来自搜索结果")
    debug: bool = Field(False, description="是否启用调试模式（返回 debug_context）")


@router.post("/dry-run", response_model=BaseResponse)
async def decision_dry_run(payload: DecisionDryRunRequest, db=Depends(get_db)):
    """
    对候选资源执行下载决策（Dry-run），用于调试或可视化。
    """
    service = SubscriptionService(db)
    subscription = await service.get_subscription(payload.subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                error_code="SUBSCRIPTION_NOT_FOUND",
                error_message=f"订阅 {payload.subscription_id} 不存在",
            ).model_dump(),
        )

    decision_result = await service.evaluate_candidate_with_decision(
        subscription,
        payload.candidate,
        debug=payload.debug,
    )
    if decision_result is None:
        logger.warning(
            "[decision] Dry-run 回退旧逻辑 subscription=%s candidate_title=%s",
            subscription.id,
            payload.candidate.get("title"),
        )
        return success_response(
            data={
                "available": False,
                "message": "决策层暂不可用，已回退旧逻辑",
            },
            message="决策层暂不可用",
        )

    result_dict = decision_result.model_dump()
    if not payload.debug:
        result_dict.pop("debug_context", None)

    return success_response(
        data={
            "subscription": {
                "id": subscription.id,
                "title": subscription.title,
                "media_type": subscription.media_type,
            },
            "result": result_dict,
        },
        message="决策评估完成",
    )


