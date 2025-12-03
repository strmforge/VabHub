"""
统一收件箱漫画集成测试
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.config import settings
from app.modules.inbox.models import InboxItem
from app.modules.inbox.media_detection.base import MediaTypeGuess
from app.modules.inbox.router import InboxRouter
from app.modules.comic.importer import ComicImporter


@pytest.fixture(autouse=True)
def setup_inbox_settings(monkeypatch):
    """为测试设置临时的收件箱配置"""
    monkeypatch.setattr(settings, "INBOX_ENABLE_COMIC", False)  # 默认禁用
    monkeypatch.setattr(settings, "COMIC_LIBRARY_ROOT", "./data/library/comic_test")


@pytest.fixture
def mock_db_session():
    return AsyncMock()


@pytest.fixture
def mock_comic_importer():
    importer = AsyncMock(spec=ComicImporter)
    importer.import_comic_from_path.return_value = Path("/mock/comic/path/comic.cbz")
    return importer


@pytest.mark.asyncio
async def test_comic_routing_disabled(mock_db_session, mock_comic_importer, tmp_path):
    """测试当漫画处理禁用时，InboxRouter 跳过漫画文件"""
    test_file = tmp_path / "test_comic.cbz"
    test_file.write_text("dummy comic content")
    item = InboxItem(path=test_file)
    guess = MediaTypeGuess(media_type="comic", score=0.8, reason="extension")

    router = InboxRouter(db=mock_db_session, comic_importer=mock_comic_importer)
    result = await router.route(item, guess)

    assert result == "skipped:comic_disabled"
    mock_comic_importer.import_comic_from_path.assert_not_called()


@pytest.mark.asyncio
async def test_comic_routing_enabled(mock_db_session, mock_comic_importer, tmp_path, monkeypatch):
    """测试当漫画处理启用时，InboxRouter 调用 ComicImporter"""
    monkeypatch.setattr(settings, "INBOX_ENABLE_COMIC", True)
    test_file = tmp_path / "test_comic.cbz"
    test_file.write_text("dummy comic content")
    item = InboxItem(path=test_file, download_task_id=123)
    guess = MediaTypeGuess(media_type="comic", score=0.8, reason="extension")

    router = InboxRouter(db=mock_db_session, comic_importer=mock_comic_importer)
    result = await router.route(item, guess)

    assert result == "handled:comic"
    mock_comic_importer.import_comic_from_path.assert_called_once_with(
        file_path=test_file,
        hints=item
    )


@pytest.mark.asyncio
async def test_comic_import_failure(mock_db_session, mock_comic_importer, tmp_path, monkeypatch):
    """测试 ComicImporter 返回 None 时，InboxRouter 报告失败"""
    monkeypatch.setattr(settings, "INBOX_ENABLE_COMIC", True)
    mock_comic_importer.import_comic_from_path.return_value = None  # 模拟导入失败
    test_file = tmp_path / "failed_comic.cbz"
    test_file.write_text("dummy comic content")
    item = InboxItem(path=test_file)
    guess = MediaTypeGuess(media_type="comic", score=0.8, reason="extension")

    router = InboxRouter(db=mock_db_session, comic_importer=mock_comic_importer)
    result = await router.route(item, guess)

    assert result == "failed:comic_import_error"
    mock_comic_importer.import_comic_from_path.assert_called_once()


@pytest.mark.asyncio
async def test_comic_import_exception(mock_db_session, mock_comic_importer, tmp_path, monkeypatch):
    """测试 ComicImporter 抛出异常时，InboxRouter 报告错误"""
    monkeypatch.setattr(settings, "INBOX_ENABLE_COMIC", True)
    mock_comic_importer.import_comic_from_path.side_effect = Exception("Test import error")
    test_file = tmp_path / "error_comic.cbz"
    test_file.write_text("dummy comic content")
    item = InboxItem(path=test_file)
    guess = MediaTypeGuess(media_type="comic", score=0.8, reason="extension")

    router = InboxRouter(db=mock_db_session, comic_importer=mock_comic_importer)
    result = await router.route(item, guess)

    assert result == "failed:comic_import_error"
    mock_comic_importer.import_comic_from_path.assert_called_once()

