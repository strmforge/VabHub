"""
漫画导入器测试
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.comic.importer import ComicImporter, SUPPORTED_COMIC_FORMATS
from app.models.comic import Comic, ComicFile
from app.modules.inbox.models import InboxItem


@pytest.fixture
def mock_db_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.COMIC_LIBRARY_ROOT", "./data/library/comic_test")
    monkeypatch.setattr("app.core.config.settings.INBOX_ROOT", "./data/inbox_test")


@pytest.fixture
def comic_importer(mock_db_session, mock_settings):
    return ComicImporter(db=mock_db_session)


def test_is_comic_file():
    """测试 is_comic_file 方法"""
    assert ComicImporter.is_comic_file("comic.cbz") is True
    assert ComicImporter.is_comic_file("comic.cbr") is True
    assert ComicImporter.is_comic_file("comic.zip") is True
    assert ComicImporter.is_comic_file("comic.rar") is True
    assert ComicImporter.is_comic_file("video.mp4") is False
    assert ComicImporter.is_comic_file("document.pdf") is False


def test_parse_filename_simple():
    """测试解析简单文件名"""
    info = ComicImporter(None).parse_filename("系列名_v01.cbz")
    assert info["series"] == "系列名"
    assert info["volume_index"] == 1
    assert info["title"] is None


def test_parse_filename_with_title():
    """测试解析包含标题的文件名"""
    info = ComicImporter(None).parse_filename("系列名 - 第01卷 - 标题.cbz")
    assert info["series"] == "系列名"
    assert info["volume_index"] == 1
    assert info["title"] == "标题"


def test_parse_filename_default():
    """测试解析默认文件名（无法匹配模式）"""
    info = ComicImporter(None).parse_filename("未知文件.cbz")
    assert info["series"] == "未知文件"
    assert info["volume_index"] is None
    assert info["title"] is None


@pytest.mark.asyncio
@patch("app.modules.comic.importer.shutil.move")
async def test_import_comic_file_not_exists(mock_move, comic_importer, tmp_path):
    """测试导入不存在的文件"""
    non_existent_file = tmp_path / "non_existent.cbz"
    result = await comic_importer.import_comic_from_path(non_existent_file)
    assert result is None
    mock_move.assert_not_called()


@pytest.mark.asyncio
@patch("app.modules.comic.importer.shutil.move")
async def test_import_comic_invalid_format(mock_move, comic_importer, tmp_path):
    """测试导入不支持的文件格式"""
    invalid_file = tmp_path / "document.pdf"
    invalid_file.write_text("dummy content")
    result = await comic_importer.import_comic_from_path(invalid_file)
    assert result is None
    mock_move.assert_not_called()

