"""
统一收件箱小说 TXT 集成测试
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.inbox.models import InboxItem
from app.modules.inbox.media_detection.base import MediaTypeGuess
from app.modules.inbox.router import InboxRouter
from app.modules.novel.pipeline import NovelToEbookPipeline


@pytest.fixture(autouse=True)
def setup_inbox_settings(monkeypatch):
    """为测试设置临时的收件箱配置"""
    monkeypatch.setattr(settings, "INBOX_ENABLE_NOVEL_TXT", False)  # 默认禁用
    monkeypatch.setattr(settings, "NOVEL_UPLOAD_ROOT", "./data/test_novel_uploads")
    monkeypatch.setattr(settings, "EBOOK_LIBRARY_ROOT", "./data/test_ebook_library")


@pytest.fixture
def mock_db_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_novel_pipeline():
    pipeline = AsyncMock(spec=NovelToEbookPipeline)
    pipeline.run.return_value = Path("/mock/epub/output.epub")
    return pipeline


@pytest.mark.asyncio
async def test_inbox_router_skip_novel_txt_when_disabled(mock_db_session, mock_novel_pipeline, tmp_path, monkeypatch):
    """测试当小说 TXT 处理禁用时，InboxRouter 跳过小说文件"""
    monkeypatch.setattr(settings, "INBOX_ENABLE_NOVEL_TXT", False)
    test_file = tmp_path / "test_novel.txt"
    test_file.write_text("第一章 测试内容\n这是测试内容。")
    item = InboxItem(path=test_file)
    guess = MediaTypeGuess(media_type="novel_txt", score=0.9, reason="novel_txt_detector")

    router = InboxRouter(db=mock_db_session, novel_pipeline=mock_novel_pipeline)
    result = await router.route(item, guess)

    assert result == "skipped:novel_txt_disabled"
    mock_novel_pipeline.run.assert_not_called()


@pytest.mark.asyncio
@patch("app.modules.inbox.router.shutil.move")
async def test_inbox_router_calls_novel_pipeline_when_enabled(
    mock_move, mock_db_session, mock_novel_pipeline, tmp_path, monkeypatch
):
    """测试当小说 TXT 处理启用时，InboxRouter 调用 NovelToEbookPipeline 并归档文件"""
    monkeypatch.setattr(settings, "INBOX_ENABLE_NOVEL_TXT", True)
    test_file = tmp_path / "test_novel[精校].txt"
    test_file.write_text("第一章 测试内容\n这是测试内容。")
    item = InboxItem(path=test_file, source_tags=["test_tag"])
    guess = MediaTypeGuess(media_type="novel_txt", score=0.9, reason="novel_txt_detector")

    router = InboxRouter(db=mock_db_session, novel_pipeline=mock_novel_pipeline)
    result = await router.route(item, guess)

    assert result == "handled:novel_txt"
    mock_novel_pipeline.run.assert_called_once()
    
    # 验证调用了 move 归档文件
    mock_move.assert_called_once()
    call_args = mock_move.call_args[0]
    assert str(call_args[0]) == str(test_file)
    assert "source_txt" in str(call_args[1])


@pytest.mark.asyncio
async def test_inbox_router_novel_pipeline_failure_marks_failed(
    mock_db_session, mock_novel_pipeline, tmp_path, monkeypatch
):
    """测试 NovelToEbookPipeline 失败时，返回 failed 且文件不移动"""
    monkeypatch.setattr(settings, "INBOX_ENABLE_NOVEL_TXT", True)
    mock_novel_pipeline.run.return_value = None  # 模拟失败
    test_file = tmp_path / "test_novel.txt"
    test_file.write_text("第一章 测试内容\n这是测试内容。")
    item = InboxItem(path=test_file)
    guess = MediaTypeGuess(media_type="novel_txt", score=0.9, reason="novel_txt_detector")

    router = InboxRouter(db=mock_db_session, novel_pipeline=mock_novel_pipeline)
    result = await router.route(item, guess)

    assert result.startswith("failed:novel_txt")
    mock_novel_pipeline.run.assert_called_once()
    # 文件应该还在原位置（未移动）
    assert test_file.exists()


@pytest.mark.asyncio
async def test_inbox_router_novel_txt_file_not_found(mock_db_session, mock_novel_pipeline, tmp_path, monkeypatch):
    """测试文件不存在时返回失败"""
    monkeypatch.setattr(settings, "INBOX_ENABLE_NOVEL_TXT", True)
    non_existent_file = tmp_path / "non_existent.txt"
    item = InboxItem(path=non_existent_file)
    guess = MediaTypeGuess(media_type="novel_txt", score=0.9, reason="novel_txt_detector")

    router = InboxRouter(db=mock_db_session, novel_pipeline=mock_novel_pipeline)
    result = await router.route(item, guess)

    assert result == "failed:novel_txt_file_not_found"
    mock_novel_pipeline.run.assert_not_called()


@pytest.mark.asyncio
async def test_inbox_router_novel_txt_exception_handling(mock_db_session, mock_novel_pipeline, tmp_path, monkeypatch):
    """测试 NovelToEbookPipeline 抛出异常时的处理"""
    monkeypatch.setattr(settings, "INBOX_ENABLE_NOVEL_TXT", True)
    mock_novel_pipeline.run.side_effect = Exception("Test pipeline error")
    test_file = tmp_path / "test_novel.txt"
    test_file.write_text("第一章 测试内容\n这是测试内容。")
    item = InboxItem(path=test_file)
    guess = MediaTypeGuess(media_type="novel_txt", score=0.9, reason="novel_txt_detector")

    router = InboxRouter(db=mock_db_session, novel_pipeline=mock_novel_pipeline)
    result = await router.route(item, guess)

    assert result == "failed:novel_txt_import_error"
    mock_novel_pipeline.run.assert_called_once()

