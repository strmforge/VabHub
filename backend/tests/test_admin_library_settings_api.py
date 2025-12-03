"""
媒体库设置 API 测试
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.inbox import InboxRunLog
from app.api.admin_library_settings import get_library_settings


@pytest.mark.asyncio
async def test_get_library_settings_basic(db_session: AsyncSession, monkeypatch):
    """测试基本配置返回"""
    from app.core.config import settings
    
    # 设置自定义库根路径
    monkeypatch.setattr(settings, "MOVIE_LIBRARY_ROOT", "/custom/movies")
    monkeypatch.setattr(settings, "TV_LIBRARY_ROOT", "/custom/tv")
    monkeypatch.setattr(settings, "EBOOK_LIBRARY_ROOT", "/custom/ebooks")
    monkeypatch.setattr(settings, "INBOX_ROOT", "/custom/inbox")
    
    response = await get_library_settings(db_session)
    
    assert response.library_roots.movie == "/custom/movies"
    assert response.library_roots.tv == "/custom/tv"
    assert response.library_roots.ebook == "/custom/ebooks"
    assert response.inbox.inbox_root == "/custom/inbox"
    assert response.inbox.detection_min_score == settings.INBOX_DETECTION_MIN_SCORE
    assert response.inbox.scan_max_items == settings.INBOX_SCAN_MAX_ITEMS


@pytest.mark.asyncio
async def test_get_library_settings_inbox_enabled_types(db_session: AsyncSession, monkeypatch):
    """测试不同的 INBOX_ENABLE_* 配置"""
    from app.core.config import settings
    
    # 启用部分类型
    monkeypatch.setattr(settings, "INBOX_ENABLE_VIDEO", True)
    monkeypatch.setattr(settings, "INBOX_ENABLE_EBOOK", True)
    monkeypatch.setattr(settings, "INBOX_ENABLE_AUDIOBOOK", False)
    monkeypatch.setattr(settings, "INBOX_ENABLE_NOVEL_TXT", False)
    monkeypatch.setattr(settings, "INBOX_ENABLE_COMIC", False)
    monkeypatch.setattr(settings, "INBOX_ENABLE_MUSIC", False)
    
    response = await get_library_settings(db_session)
    
    assert response.inbox.enabled is True
    assert "video" in response.inbox.enabled_media_types
    assert "ebook" in response.inbox.enabled_media_types
    assert "audiobook" not in response.inbox.enabled_media_types
    assert len(response.inbox.enabled_media_types) == 2


@pytest.mark.asyncio
async def test_get_library_settings_inbox_all_disabled(db_session: AsyncSession, monkeypatch):
    """测试所有 INBOX_ENABLE_* 为 False"""
    from app.core.config import settings
    
    # 禁用所有类型
    monkeypatch.setattr(settings, "INBOX_ENABLE_VIDEO", False)
    monkeypatch.setattr(settings, "INBOX_ENABLE_EBOOK", False)
    monkeypatch.setattr(settings, "INBOX_ENABLE_AUDIOBOOK", False)
    monkeypatch.setattr(settings, "INBOX_ENABLE_NOVEL_TXT", False)
    monkeypatch.setattr(settings, "INBOX_ENABLE_COMIC", False)
    monkeypatch.setattr(settings, "INBOX_ENABLE_MUSIC", False)
    
    response = await get_library_settings(db_session)
    
    assert response.inbox.enabled is False
    assert len(response.inbox.enabled_media_types) == 0
    assert response.inbox.last_run_status == "never"


@pytest.mark.asyncio
async def test_get_library_settings_inbox_last_run_info(db_session: AsyncSession, monkeypatch):
    """测试插入 InboxRunLog 后返回正确的 last_run_* 字段"""
    from app.core.config import settings
    
    # 启用部分类型
    monkeypatch.setattr(settings, "INBOX_ENABLE_VIDEO", True)
    
    # 创建一条运行日志
    finished_at = datetime.utcnow() - timedelta(hours=1)
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
    
    response = await get_library_settings(db_session)
    
    assert response.inbox.enabled is True
    assert response.inbox.last_run_status == "success"
    assert response.inbox.last_run_at is not None
    assert response.inbox.last_run_summary == "处理完成：成功 10，跳过 0，失败 0"
    assert response.inbox.pending_warning is None


@pytest.mark.asyncio
async def test_get_library_settings_inbox_last_run_failed(db_session: AsyncSession, monkeypatch):
    """测试最近一次运行失败的情况"""
    from app.core.config import settings
    
    # 启用部分类型
    monkeypatch.setattr(settings, "INBOX_ENABLE_VIDEO", True)
    
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
    
    response = await get_library_settings(db_session)
    
    assert response.inbox.last_run_status == "failed"
    assert response.inbox.pending_warning == "last_run_failed"


@pytest.mark.asyncio
async def test_get_library_settings_library_roots_optional_fields(db_session: AsyncSession):
    """测试可选库根路径字段"""
    response = await get_library_settings(db_session)
    
    # 必填字段
    assert response.library_roots.movie is not None
    assert response.library_roots.tv is not None
    assert response.library_roots.anime is not None
    assert response.library_roots.ebook is not None
    
    # 可选字段（可能为 None）
    # short_drama, comic, music 都是可选的
    assert isinstance(response.library_roots.short_drama, (str, type(None)))
    assert isinstance(response.library_roots.comic, (str, type(None)))
    assert isinstance(response.library_roots.music, (str, type(None)))

