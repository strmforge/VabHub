"""
智能健康检查 inbox 区块测试
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.inbox import InboxRunLog
from app.api.smart_health import smart_health


@pytest.mark.asyncio
async def test_smart_health_inbox_disabled_all_types(db_session: AsyncSession, monkeypatch):
    """测试所有 INBOX_ENABLE_* 为 False 时"""
    # 禁用所有类型 - 需要 patch smart_health 模块中的 settings 引用
    monkeypatch.setattr("app.api.smart_health.settings.INBOX_ENABLE_VIDEO", False)
    monkeypatch.setattr("app.api.smart_health.settings.INBOX_ENABLE_EBOOK", False)
    monkeypatch.setattr("app.api.smart_health.settings.INBOX_ENABLE_AUDIOBOOK", False)
    monkeypatch.setattr("app.api.smart_health.settings.INBOX_ENABLE_NOVEL_TXT", False)
    monkeypatch.setattr("app.api.smart_health.settings.INBOX_ENABLE_COMIC", False)
    monkeypatch.setattr("app.api.smart_health.settings.INBOX_ENABLE_MUSIC", False)
    
    result = await smart_health(db_session)
    
    assert "inbox" in result["features"]
    inbox_status = result["features"]["inbox"]
    assert inbox_status["enabled"] is False
    assert inbox_status["enabled_media_types"] == []
    assert inbox_status["last_run_status"] == "never"
    assert inbox_status["last_run_at"] is None
    assert inbox_status["pending_warning"] is None


@pytest.mark.asyncio
async def test_smart_health_inbox_enabled_but_never_run(db_session: AsyncSession, monkeypatch):
    """测试某些类型启用，但 InboxRunLog 无记录"""
    # 启用部分类型 - 需要 patch smart_health 模块中的 settings 引用
    monkeypatch.setattr("app.api.smart_health.settings.INBOX_ENABLE_VIDEO", True)
    monkeypatch.setattr("app.api.smart_health.settings.INBOX_ENABLE_EBOOK", True)
    
    result = await smart_health(db_session)
    
    assert "inbox" in result["features"]
    inbox_status = result["features"]["inbox"]
    assert inbox_status["enabled"] is True
    assert "video" in inbox_status["enabled_media_types"]
    assert "ebook" in inbox_status["enabled_media_types"]
    assert inbox_status["last_run_status"] == "never"
    assert inbox_status["last_run_at"] is None
    assert inbox_status["pending_warning"] == "never_run"


@pytest.mark.asyncio
async def test_smart_health_inbox_with_recent_success_run(db_session: AsyncSession, monkeypatch):
    """测试构造一条最近的 success 记录"""
    # 启用部分类型
    monkeypatch.setattr("app.api.smart_health.settings.INBOX_ENABLE_VIDEO", True)
    
    # 创建一条成功的运行日志
    finished_at = datetime.utcnow() - timedelta(hours=1)  # 1 小时前
    log = InboxRunLog(
        started_at=finished_at - timedelta(minutes=5),
        finished_at=finished_at,
        status="success",
        total_items=10,
        handled_items=10,
        skipped_items=0,
        failed_items=0,
        message="处理完成：成功 10，跳过 0，失败 0"
    )
    db_session.add(log)
    await db_session.commit()
    
    result = await smart_health(db_session)
    
    assert "inbox" in result["features"]
    inbox_status = result["features"]["inbox"]
    assert inbox_status["enabled"] is True
    assert inbox_status["last_run_status"] == "success"
    assert inbox_status["last_run_at"] is not None
    assert inbox_status["last_run_summary"] == "处理完成：成功 10，跳过 0，失败 0"
    assert inbox_status["pending_warning"] is None


@pytest.mark.asyncio
async def test_smart_health_inbox_with_failed_run(db_session: AsyncSession, monkeypatch):
    """测试最近一条记录 status='failed'"""
    # 启用部分类型
    monkeypatch.setattr("app.api.smart_health.settings.INBOX_ENABLE_VIDEO", True)
    
    # 创建一条失败的运行日志
    finished_at = datetime.utcnow() - timedelta(hours=1)
    log = InboxRunLog(
        started_at=finished_at - timedelta(minutes=5),
        finished_at=finished_at,
        status="failed",
        total_items=5,
        handled_items=0,
        skipped_items=0,
        failed_items=5,
        message="处理完成：成功 0，跳过 0，失败 5"
    )
    db_session.add(log)
    await db_session.commit()
    
    result = await smart_health(db_session)
    
    assert "inbox" in result["features"]
    inbox_status = result["features"]["inbox"]
    assert inbox_status["enabled"] is True
    assert inbox_status["last_run_status"] == "failed"
    assert inbox_status["pending_warning"] == "last_run_failed"


@pytest.mark.asyncio
async def test_smart_health_inbox_too_long_without_run(db_session: AsyncSession, monkeypatch):
    """测试超过 24 小时没跑时给出警告"""
    # 启用部分类型
    monkeypatch.setattr("app.api.smart_health.settings.INBOX_ENABLE_VIDEO", True)
    
    # 创建一条 25 小时前的运行日志
    finished_at = datetime.utcnow() - timedelta(hours=25)
    log = InboxRunLog(
        started_at=finished_at - timedelta(minutes=5),
        finished_at=finished_at,
        status="success",
        total_items=10,
        handled_items=10,
        skipped_items=0,
        failed_items=0,
        message="处理完成：成功 10，跳过 0，失败 0"
    )
    db_session.add(log)
    await db_session.commit()
    
    result = await smart_health(db_session)
    
    assert "inbox" in result["features"]
    inbox_status = result["features"]["inbox"]
    assert inbox_status["enabled"] is True
    assert inbox_status["last_run_status"] == "success"
    assert inbox_status["pending_warning"] == "too_long_without_run"


@pytest.mark.asyncio
async def test_smart_health_inbox_all_media_types(db_session: AsyncSession, monkeypatch):
    """测试所有媒体类型都启用时的 enabled_media_types"""
    # 启用所有类型
    monkeypatch.setattr("app.api.smart_health.settings.INBOX_ENABLE_VIDEO", True)
    monkeypatch.setattr("app.api.smart_health.settings.INBOX_ENABLE_EBOOK", True)
    monkeypatch.setattr("app.api.smart_health.settings.INBOX_ENABLE_AUDIOBOOK", True)
    monkeypatch.setattr("app.api.smart_health.settings.INBOX_ENABLE_NOVEL_TXT", True)
    monkeypatch.setattr("app.api.smart_health.settings.INBOX_ENABLE_COMIC", True)
    monkeypatch.setattr("app.api.smart_health.settings.INBOX_ENABLE_MUSIC", True)
    
    result = await smart_health(db_session)
    
    assert "inbox" in result["features"]
    inbox_status = result["features"]["inbox"]
    assert inbox_status["enabled"] is True
    assert len(inbox_status["enabled_media_types"]) == 6
    assert "video" in inbox_status["enabled_media_types"]
    assert "ebook" in inbox_status["enabled_media_types"]
    assert "audiobook" in inbox_status["enabled_media_types"]
    assert "novel_txt" in inbox_status["enabled_media_types"]
    assert "comic" in inbox_status["enabled_media_types"]
    assert "music" in inbox_status["enabled_media_types"]


@pytest.mark.asyncio
async def test_smart_health_inbox_root_path(db_session: AsyncSession, monkeypatch):
    """测试 inbox_root 路径正确返回"""
    # 设置自定义路径
    custom_path = "/custom/inbox/path"
    monkeypatch.setattr("app.api.smart_health.settings.INBOX_ROOT", custom_path)
    monkeypatch.setattr("app.api.smart_health.settings.INBOX_ENABLE_VIDEO", True)
    
    result = await smart_health(db_session)
    
    assert "inbox" in result["features"]
    inbox_status = result["features"]["inbox"]
    assert inbox_status["inbox_root"] == custom_path

