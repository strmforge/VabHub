"""
TTS 限流器

轻量级的进程内限流工具，用于防止 TTS 请求过载。
"""

from dataclasses import dataclass, replace
from datetime import date, datetime
from typing import Optional
from loguru import logger


@dataclass
class RunContext:
    """单次 pipeline 运行的上下文（用于 per-run 限制）"""
    requests: int = 0
    characters: int = 0


@dataclass(frozen=True)
class TTSRateState:
    """TTS 限流状态（不可变）"""
    day: date
    daily_requests: int = 0
    daily_characters: int = 0
    last_limited_at: Optional[datetime] = None
    last_limited_reason: Optional[str] = None


# 全局单例状态
_state: TTSRateState = TTSRateState(day=date.today())


def _get_today() -> date:
    """获取今天的日期（用于测试时可以 mock）"""
    return date.today()


def _check_and_reset_if_new_day() -> None:
    """检查日期是否变化，如果变化则重置计数"""
    global _state
    try:
        today = _get_today()
        if _state.day != today:
            _state = TTSRateState(day=today)
            logger.debug(f"TTS rate limiter: day changed, reset counters (new day: {today})")
    except Exception as e:
        logger.warning(f"TTS rate limiter: failed to check/reset day: {e}")


def should_allow(
    request_chars: int,
    *,
    settings,
    run_context: Optional[RunContext] = None
) -> bool:
    """
    检查这次调用是否被允许
    
    Args:
        request_chars: 本次请求的字符数
        settings: 应用配置对象
        run_context: 可选的运行上下文（用于 per-run 限制）
    
    Returns:
        bool: True 表示允许，False 表示被限流
    """
    global _state
    
    try:
        # 检查是否启用限流
        if not getattr(settings, 'SMART_TTS_RATE_LIMIT_ENABLED', False):
            return True
        
        # 检查日期变化并重置
        _check_and_reset_if_new_day()
        
        # 获取配置限制
        max_daily_requests = getattr(settings, 'SMART_TTS_MAX_DAILY_REQUESTS', 0)
        max_daily_characters = getattr(settings, 'SMART_TTS_MAX_DAILY_CHARACTERS', 0)
        max_per_run = getattr(settings, 'SMART_TTS_MAX_REQUESTS_PER_RUN', 0)
        
        # 检查每日请求数限制
        if max_daily_requests > 0 and _state.daily_requests >= max_daily_requests:
            _state = replace(
                _state,
                last_limited_at=datetime.utcnow(),
                last_limited_reason="daily_requests_exceeded"
            )
            logger.debug(f"TTS rate limited: daily_requests_exceeded ({_state.daily_requests}/{max_daily_requests})")
            return False
        
        # 检查每日字符数限制
        if max_daily_characters > 0 and _state.daily_characters + request_chars > max_daily_characters:
            _state = replace(
                _state,
                last_limited_at=datetime.utcnow(),
                last_limited_reason="daily_characters_exceeded"
            )
            logger.debug(
                f"TTS rate limited: daily_characters_exceeded "
                f"({_state.daily_characters + request_chars}/{max_daily_characters})"
            )
            return False
        
        # 检查 per-run 限制
        if max_per_run > 0 and run_context is not None:
            if run_context.requests >= max_per_run:
                _state = replace(
                    _state,
                    last_limited_at=datetime.utcnow(),
                    last_limited_reason="per_run_requests_exceeded"
                )
                logger.debug(f"TTS rate limited: per_run_requests_exceeded ({run_context.requests}/{max_per_run})")
                return False
        
        return True
        
    except Exception as e:
        # 绝对不能因为限流检查失败而影响主流程
        logger.warning(f"TTS rate limiter: failed to check allow: {e}")
        # 出错时默认允许（fail-open）
        return True


def record_request(
    request_chars: int,
    *,
    settings,
    run_context: Optional[RunContext] = None
) -> None:
    """
    记录本次请求的消耗
    
    Args:
        request_chars: 本次请求的字符数
        settings: 应用配置对象
        run_context: 可选的运行上下文（用于 per-run 限制）
    """
    global _state
    
    try:
        # 检查日期变化并重置
        _check_and_reset_if_new_day()
        
        # 更新每日计数
        _state = replace(
            _state,
            daily_requests=_state.daily_requests + 1,
            daily_characters=_state.daily_characters + request_chars
        )
        
        # 更新 per-run 计数
        if run_context is not None:
            run_context.requests += 1
            run_context.characters += request_chars
        
        logger.debug(
            f"TTS rate limiter: recorded request "
            f"(daily: {_state.daily_requests} requests, {_state.daily_characters} chars)"
        )
        
    except Exception as e:
        # 绝对不能因为记录失败而影响主流程
        logger.warning(f"TTS rate limiter: failed to record request: {e}")


def get_state() -> TTSRateState:
    """
    获取当前限流状态（返回不可变拷贝）
    
    Returns:
        TTSRateState: 当前状态的不可变拷贝
    """
    try:
        # 检查日期变化
        _check_and_reset_if_new_day()
        # 返回不可变拷贝
        return _state
    except Exception as e:
        # 如果获取状态失败，返回空状态
        logger.warning(f"TTS rate limiter: failed to get state: {e}")
        return TTSRateState(day=_get_today())


def reset() -> None:
    """
    重置状态（主要用于测试）
    """
    global _state
    try:
        _state = TTSRateState(day=_get_today())
        logger.debug("TTS rate limiter: state reset")
    except Exception as e:
        logger.warning(f"TTS rate limiter: failed to reset state: {e}")

