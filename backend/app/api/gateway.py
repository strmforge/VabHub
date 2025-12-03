"""
网关API
用于STRM网关签名等功能
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel
from typing import Optional
from loguru import logger

from app.core.database import get_db
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)

router = APIRouter(prefix="/gateway", tags=["网关"])


class GatewaySignRequest(BaseModel):
    """网关签名请求"""
    path: str  # 要签名的路径
    ttl: Optional[int] = 3600  # 有效期（秒，默认3600秒=1小时）


@router.post("/sign", response_model=BaseResponse)
async def sign_url(
    request: GatewaySignRequest
):
    """
    对URL路径进行HMAC签名
    
    返回统一响应格式：
    {
        "success": true,
        "message": "签名成功",
        "data": {
            "signed_url": "...",
            "path": "...",
            "timestamp": 1234567890,
            "signature": "...",
            "ttl": 3600
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.modules.strm.hmac_signer import get_hmac_signer
        import time
        
        # 获取HMAC签名器
        hmac_signer = get_hmac_signer()
        
        # 生成时间戳（当前时间 + TTL）
        timestamp = int(time.time()) + request.ttl
        
        # 生成签名
        signature = hmac_signer.sign_path(request.path, timestamp)
        
        # 构建签名URL（添加查询参数）
        signed_url = f"{request.path}?ts={timestamp}&sig={signature}"
        
        return success_response(
            data={
                "signed_url": signed_url,
                "path": request.path,
                "timestamp": timestamp,
                "signature": signature,
                "ttl": request.ttl
            },
            message="签名成功"
        )
    except Exception as e:
        logger.error(f"URL签名失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"URL签名时发生错误: {str(e)}"
            ).model_dump()
        )

