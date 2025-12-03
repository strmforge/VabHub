"""
TTS Rate Limiter 测试
"""

import pytest
from datetime import date, datetime
from app.modules.tts.rate_limiter import (
    RunContext,
    TTSRateState,
    should_allow,
    record_request,
    get_state,
    reset
)
from app.core.config import Settings


def test_allow_when_limits_disabled():
    """测试限流未启用时，总是允许"""
    reset()
    
    settings = Settings()
    settings.SMART_TTS_RATE_LIMIT_ENABLED = False
    settings.SMART_TTS_MAX_DAILY_REQUESTS = 0
    settings.SMART_TTS_MAX_DAILY_CHARACTERS = 0
    settings.SMART_TTS_MAX_REQUESTS_PER_RUN = 0
    
    # 多次调用都应该允许
    assert should_allow(100, settings=settings) is True
    assert should_allow(200, settings=settings) is True
    assert should_allow(300, settings=settings) is True


def test_daily_requests_limit_blocks_after_reaching_max():
    """测试每日请求数限制在达到上限后阻止"""
    reset()
    
    settings = Settings()
    settings.SMART_TTS_RATE_LIMIT_ENABLED = True
    settings.SMART_TTS_MAX_DAILY_REQUESTS = 2
    settings.SMART_TTS_MAX_DAILY_CHARACTERS = 0
    settings.SMART_TTS_MAX_REQUESTS_PER_RUN = 0
    
    # 前 2 次应该允许
    assert should_allow(100, settings=settings) is True
    record_request(100, settings=settings)
    
    assert should_allow(100, settings=settings) is True
    record_request(100, settings=settings)
    
    # 第 3 次应该被阻止
    assert should_allow(100, settings=settings) is False
    
    # 检查状态
    state = get_state()
    assert state.daily_requests == 2
    assert state.last_limited_reason == "daily_requests_exceeded"


def test_daily_characters_limit_blocks_after_reaching_max():
    """测试每日字符数限制在达到上限后阻止"""
    reset()
    
    settings = Settings()
    settings.SMART_TTS_RATE_LIMIT_ENABLED = True
    settings.SMART_TTS_MAX_DAILY_REQUESTS = 0
    settings.SMART_TTS_MAX_DAILY_CHARACTERS = 500
    settings.SMART_TTS_MAX_REQUESTS_PER_RUN = 0
    
    # 第一次请求（300 字符）应该允许
    assert should_allow(300, settings=settings) is True
    record_request(300, settings=settings)
    
    # 第二次请求（200 字符，总共 500）应该允许
    assert should_allow(200, settings=settings) is True
    record_request(200, settings=settings)
    
    # 第三次请求（100 字符，总共 600）应该被阻止
    assert should_allow(100, settings=settings) is False
    
    # 检查状态
    state = get_state()
    assert state.daily_characters == 500
    assert state.last_limited_reason == "daily_characters_exceeded"


def test_per_run_limit_blocks_within_same_run():
    """测试 per-run 限制在同一运行内阻止"""
    reset()
    
    settings = Settings()
    settings.SMART_TTS_RATE_LIMIT_ENABLED = True
    settings.SMART_TTS_MAX_DAILY_REQUESTS = 0
    settings.SMART_TTS_MAX_DAILY_CHARACTERS = 0
    settings.SMART_TTS_MAX_REQUESTS_PER_RUN = 1
    
    run_context1 = RunContext()
    
    # 第一次请求应该允许
    assert should_allow(100, settings=settings, run_context=run_context1) is True
    record_request(100, settings=settings, run_context=run_context1)
    
    # 第二次请求（同一 run_context）应该被阻止
    assert should_allow(100, settings=settings, run_context=run_context1) is False
    
    # 新的 run_context 应该允许
    run_context2 = RunContext()
    assert should_allow(100, settings=settings, run_context=run_context2) is True
    
    # 检查状态
    state = get_state()
    assert state.last_limited_reason == "per_run_requests_exceeded"


def test_last_limited_state_is_updated():
    """测试被限流时，last_limited 状态会被更新"""
    reset()
    
    settings = Settings()
    settings.SMART_TTS_RATE_LIMIT_ENABLED = True
    settings.SMART_TTS_MAX_DAILY_REQUESTS = 1
    settings.SMART_TTS_MAX_DAILY_CHARACTERS = 0
    settings.SMART_TTS_MAX_REQUESTS_PER_RUN = 0
    
    # 第一次允许并记录
    assert should_allow(100, settings=settings) is True
    record_request(100, settings=settings)
    
    # 第二次被限流
    assert should_allow(100, settings=settings) is False
    
    # 检查状态
    state = get_state()
    assert state.last_limited_at is not None
    assert isinstance(state.last_limited_at, datetime)
    assert state.last_limited_reason == "daily_requests_exceeded"


def test_reset_clears_state():
    """测试 reset 能清除状态"""
    reset()
    
    settings = Settings()
    settings.SMART_TTS_RATE_LIMIT_ENABLED = True
    settings.SMART_TTS_MAX_DAILY_REQUESTS = 1
    
    # 记录一次请求
    record_request(100, settings=settings)
    
    state1 = get_state()
    assert state1.daily_requests == 1
    
    # 重置
    reset()
    
    state2 = get_state()
    assert state2.daily_requests == 0
    assert state2.daily_characters == 0


def test_multiple_limits_checked_in_order():
    """测试多个限制按顺序检查"""
    reset()
    
    settings = Settings()
    settings.SMART_TTS_RATE_LIMIT_ENABLED = True
    settings.SMART_TTS_MAX_DAILY_REQUESTS = 2
    settings.SMART_TTS_MAX_DAILY_CHARACTERS = 1000
    settings.SMART_TTS_MAX_REQUESTS_PER_RUN = 1
    
    run_context = RunContext()
    
    # 第一次应该允许（所有限制都未达到）
    assert should_allow(100, settings=settings, run_context=run_context) is True
    record_request(100, settings=settings, run_context=run_context)
    
    # 第二次应该被 per-run 限制阻止
    assert should_allow(100, settings=settings, run_context=run_context) is False
    
    state = get_state()
    assert state.last_limited_reason == "per_run_requests_exceeded"

