"""
TTS 使用记录器

轻量级的进程内状态记录工具，用于记录 TTS 引擎的使用历史。
不依赖数据库，不影响主流程。
"""

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Optional
from loguru import logger


@dataclass(frozen=True)
class TTSUsageState:
    """TTS 使用状态（不可变）"""
    last_success_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None
    last_error_message: Optional[str] = None
    last_provider: Optional[str] = None


# 进程内全局状态（单例）
_state: TTSUsageState = TTSUsageState()


def record_success(provider: Optional[str] = None) -> None:
    """
    记录一次成功的 TTS 调用
    
    Args:
        provider: TTS 提供商名称（如 "dummy", "http"）
    """
    global _state
    try:
        _state = replace(
            _state,
            last_success_at=datetime.utcnow(),
            last_provider=provider
        )
        logger.debug(f"TTS usage tracker: recorded success (provider={provider})")
    except Exception as e:
        # 绝对不能因为记录失败影响主流程
        logger.warning(f"TTS usage tracker: failed to record success: {e}")


def record_error(exc: Exception, provider: Optional[str] = None) -> None:
    """
    记录一次失败的 TTS 调用
    
    Args:
        exc: 异常对象
        provider: TTS 提供商名称（如 "dummy", "http"）
    """
    global _state
    try:
        error_message = str(exc)
        # 如果异常消息太长，截断
        if len(error_message) > 500:
            error_message = error_message[:500] + "..."
        
        _state = replace(
            _state,
            last_error_at=datetime.utcnow(),
            last_error_message=error_message,
            last_provider=provider
        )
        logger.debug(f"TTS usage tracker: recorded error (provider={provider}): {error_message}")
    except Exception as e:
        # 绝对不能因为记录失败影响主流程
        logger.warning(f"TTS usage tracker: failed to record error: {e}")


def get_state() -> TTSUsageState:
    """
    获取当前 TTS 使用状态（返回不可变拷贝）
    
    Returns:
        TTSUsageState: 当前状态的不可变拷贝
    """
    try:
        # 返回不可变拷贝，避免外部修改内部状态
        return _state
    except Exception as e:
        # 如果获取状态失败，返回空状态
        logger.warning(f"TTS usage tracker: failed to get state: {e}")
        return TTSUsageState()


def reset() -> None:
    """
    重置状态（主要用于测试）
    """
    global _state
    try:
        _state = TTSUsageState()
        logger.debug("TTS usage tracker: state reset")
    except Exception as e:
        logger.warning(f"TTS usage tracker: failed to reset state: {e}")

