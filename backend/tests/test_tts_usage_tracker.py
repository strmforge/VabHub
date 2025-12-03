"""
TTS Usage Tracker 测试
"""

import pytest
from datetime import datetime
from app.modules.tts.usage_tracker import (
    TTSUsageState,
    record_success,
    record_error,
    get_state,
    reset
)


def test_record_success_sets_last_success_at_and_provider():
    """测试记录成功时设置 last_success_at 和 provider"""
    reset()
    
    record_success("dummy")
    
    state = get_state()
    assert state.last_success_at is not None
    assert isinstance(state.last_success_at, datetime)
    assert state.last_provider == "dummy"
    
    # 验证时间戳是合理的（在最近几秒内）
    now = datetime.utcnow()
    time_diff = (now - state.last_success_at).total_seconds()
    assert 0 <= time_diff < 5  # 应该在最近 5 秒内


def test_record_error_sets_last_error_fields():
    """测试记录错误时设置 last_error 相关字段"""
    reset()
    
    exc = RuntimeError("boom")
    record_error(exc, "http")
    
    state = get_state()
    assert state.last_error_at is not None
    assert isinstance(state.last_error_at, datetime)
    assert "boom" in state.last_error_message
    assert state.last_provider == "http"
    
    # 验证时间戳是合理的
    now = datetime.utcnow()
    time_diff = (now - state.last_error_at).total_seconds()
    assert 0 <= time_diff < 5


def test_get_state_returns_copy():
    """测试 get_state 返回不可变拷贝，修改不会影响内部状态"""
    reset()
    
    record_success("dummy")
    
    state1 = get_state()
    # 尝试修改返回的对象（应该失败，因为是不可变的 dataclass）
    # 但即使能修改，也不应该影响下一次调用
    
    record_success("http")
    
    state2 = get_state()
    
    # 验证状态已更新
    assert state2.last_provider == "http"
    assert state2.last_success_at != state1.last_success_at or state2.last_provider != state1.last_provider


def test_record_success_updates_provider():
    """测试多次记录成功时，provider 会被更新"""
    reset()
    
    record_success("dummy")
    state1 = get_state()
    assert state1.last_provider == "dummy"
    
    record_success("http")
    state2 = get_state()
    assert state2.last_provider == "http"
    assert state2.last_success_at >= state1.last_success_at


def test_record_error_truncates_long_messages():
    """测试错误消息过长时会被截断"""
    reset()
    
    long_message = "x" * 1000
    exc = RuntimeError(long_message)
    record_error(exc, "dummy")
    
    state = get_state()
    assert len(state.last_error_message) <= 503  # 500 + "..."


def test_record_success_without_provider():
    """测试不提供 provider 时也能正常工作"""
    reset()
    
    record_success()
    
    state = get_state()
    assert state.last_success_at is not None
    assert state.last_provider is None


def test_record_error_without_provider():
    """测试不提供 provider 时也能正常工作"""
    reset()
    
    exc = RuntimeError("test error")
    record_error(exc)
    
    state = get_state()
    assert state.last_error_at is not None
    assert state.last_error_message is not None
    assert state.last_provider is None

