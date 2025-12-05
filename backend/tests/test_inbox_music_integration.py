"""
统一收件箱音乐集成测试
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from app.modules.inbox.router import InboxRouter
from app.modules.inbox.models import InboxItem
from app.modules.inbox.media_detection.base import MediaTypeGuess
from app.constants.media_types import MEDIA_TYPE_MUSIC


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return AsyncMock()


@pytest.fixture
def inbox_router(mock_db):
    """创建 InboxRouter 实例"""
    return InboxRouter(db=mock_db)


@pytest.mark.asyncio
async def test_music_routing_disabled(inbox_router, tmp_path, monkeypatch):
    """测试音乐处理禁用时跳过"""
    from app.core.config import settings
    monkeypatch.setattr(settings, "INBOX_ENABLE_MUSIC", False)
    
    test_file = tmp_path / "test.mp3"
    test_file.write_bytes(b"fake audio")
    
    item = InboxItem(path=test_file)
    guess = MediaTypeGuess(
        media_type=MEDIA_TYPE_MUSIC,
        score=0.9,
        reason="extension_mp3"
    )
    
    result = await inbox_router.route(item, guess)
    assert result == "skipped:music_disabled"


@pytest.mark.asyncio
async def test_music_routing_enabled(inbox_router, tmp_path, monkeypatch):
    """测试音乐处理启用时调用导入器"""
    # Patch router 模块中导入的 settings
    monkeypatch.setattr("app.modules.inbox.router.settings.INBOX_ENABLE_MUSIC", True)
    
    test_file = tmp_path / "test.mp3"
    test_file.write_bytes(b"fake audio")
    
    item = InboxItem(path=test_file)
    guess = MediaTypeGuess(
        media_type=MEDIA_TYPE_MUSIC,
        score=0.9,
        reason="extension_mp3"
    )
    
    # 模拟 MusicImporter
    mock_importer = MagicMock()
    mock_importer.import_music_from_path = AsyncMock(return_value=Path("/target/test.mp3"))
    inbox_router.music_importer = mock_importer
    
    result = await inbox_router.route(item, guess)
    assert result == "handled:music"
    mock_importer.import_music_from_path.assert_called_once()


@pytest.mark.asyncio
async def test_music_import_failure(inbox_router, tmp_path, monkeypatch):
    """测试音乐导入失败"""
    # Patch router 模块中导入的 settings
    monkeypatch.setattr("app.modules.inbox.router.settings.INBOX_ENABLE_MUSIC", True)
    
    test_file = tmp_path / "test.mp3"
    test_file.write_bytes(b"fake audio")
    
    item = InboxItem(path=test_file)
    guess = MediaTypeGuess(
        media_type=MEDIA_TYPE_MUSIC,
        score=0.9,
        reason="extension_mp3"
    )
    
    # 模拟 MusicImporter 返回 None（导入失败）
    mock_importer = MagicMock()
    mock_importer.import_music_from_path = AsyncMock(return_value=None)
    inbox_router.music_importer = mock_importer
    
    result = await inbox_router.route(item, guess)
    assert result == "failed:music_import_failed"


@pytest.mark.asyncio
async def test_music_import_exception(inbox_router, tmp_path, monkeypatch):
    """测试音乐导入异常"""
    # Patch router 模块中导入的 settings
    monkeypatch.setattr("app.modules.inbox.router.settings.INBOX_ENABLE_MUSIC", True)
    
    test_file = tmp_path / "test.mp3"
    test_file.write_bytes(b"fake audio")
    
    item = InboxItem(path=test_file)
    guess = MediaTypeGuess(
        media_type=MEDIA_TYPE_MUSIC,
        score=0.9,
        reason="extension_mp3"
    )
    
    # 模拟 MusicImporter 抛出异常
    mock_importer = MagicMock()
    mock_importer.import_music_from_path = AsyncMock(side_effect=Exception("Test error"))
    inbox_router.music_importer = mock_importer
    
    result = await inbox_router.route(item, guess)
    assert result == "failed:music_import_error"

