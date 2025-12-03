"""
外部授权桥接模块

用于检查外部站点的登录状态和风控状态。
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from loguru import logger

from app.core.ext_indexer.interfaces import ExternalAuthBridge


@dataclass
class ExternalAuthState:
    """
    外部站点授权状态
    """
    logged_in: bool
    last_checked_at: Optional[datetime]
    has_challenge: bool = False  # 人机验证 / 防火墙等挑战
    message: Optional[str] = None


class NoopExternalAuthBridge:
    """
    空操作授权桥接（默认实现）
    
    始终返回已登录状态，不进行实际检查。
    后续可以替换为真正的实现。
    """
    
    async def get_auth_state(
        self,
        site_id: str,
    ) -> ExternalAuthState:
        """
        获取站点授权状态（默认实现：始终返回已登录）
        
        Args:
            site_id: 站点 ID
            
        Returns:
            授权状态对象
        """
        return ExternalAuthState(
            logged_in=True,
            last_checked_at=datetime.utcnow(),
            has_challenge=False,
            message="No-op bridge: always logged in",
        )

