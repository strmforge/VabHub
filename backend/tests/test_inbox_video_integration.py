"""
Inbox + VideoImporter 集成测试
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.database import Base

from app.modules.inbox.router import InboxRouter
from app.modules.inbox.models import InboxItem
from app.modules.inbox.media_detection.base import MediaTypeGuess
from app.constants.media_types import MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV
import app.core.config as config_module


@pytest.fixture(name="db_session")
async def db_session_fixture():
    """创建测试数据库会话"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def temp_video_file(tmp_path):
    """创建临时视频文件"""
    video_file = tmp_path / "test_movie.mkv"
    video_file.write_bytes(b"fake video content")
    return video_file


@pytest.mark.asyncio
async def test_inbox_router_calls_video_importer_for_movie(tmp_path, db_session, temp_video_file, monkeypatch):
    """测试 InboxRouter 对电影调用 VideoImporter"""
    # 配置
    monkeypatch.setattr(config_module.settings, "INBOX_ENABLE_VIDEO", True)
    monkeypatch.setattr(config_module.settings, "MOVIE_LIBRARY_ROOT", str(tmp_path / "movies"))
    
    # 创建 InboxItem 和 MediaTypeGuess
    item = InboxItem(path=temp_video_file)
    guess = MediaTypeGuess(
        media_type=MEDIA_TYPE_MOVIE,
        score=0.9,
        reason="extension=mkv => movie"
    )
    
    # Mock VideoImporter
    mock_importer = AsyncMock()
    mock_importer.import_video_from_path = AsyncMock(return_value=Path(tmp_path / "movies" / "test_movie.mkv"))
    
    router = InboxRouter(db=db_session, video_importer=mock_importer)
    
    # 调用 route
    result = await router.route(item, guess)
    
    # 验证
    assert result.startswith("handled:video")
    mock_importer.import_video_from_path.assert_called_once()
    call_args = mock_importer.import_video_from_path.call_args
    
    # 检查位置参数或关键字参数
    if len(call_args[0]) >= 2:
        assert call_args[0][0] == temp_video_file  # file_path
        assert call_args[0][1] == MEDIA_TYPE_MOVIE  # media_type
    else:
        # 如果使用关键字参数
        assert call_args.kwargs.get("file_path") == temp_video_file
        assert call_args.kwargs.get("media_type") == MEDIA_TYPE_MOVIE


@pytest.mark.asyncio
async def test_inbox_router_skip_video_when_disabled(tmp_path, db_session, temp_video_file, monkeypatch):
    """测试 INBOX_ENABLE_VIDEO=False 时跳过视频处理"""
    # 配置 - 需要 patch router 模块中导入的 settings
    monkeypatch.setattr("app.modules.inbox.router.settings.INBOX_ENABLE_VIDEO", False)
    
    # 创建 InboxItem 和 MediaTypeGuess
    item = InboxItem(path=temp_video_file)
    guess = MediaTypeGuess(
        media_type=MEDIA_TYPE_MOVIE,
        score=0.9,
        reason="extension=mkv => movie"
    )
    
    # Mock VideoImporter（不应该被调用）
    mock_importer = AsyncMock()
    mock_importer.import_video_from_path = AsyncMock()
    
    router = InboxRouter(db=db_session, video_importer=mock_importer)
    
    # 调用 route
    result = await router.route(item, guess)
    
    # 验证
    assert result == "skipped:video_disabled"
    mock_importer.import_video_from_path.assert_not_called()


@pytest.mark.asyncio
async def test_inbox_router_handles_video_import_error(tmp_path, db_session, temp_video_file, monkeypatch):
    """测试 InboxRouter 处理视频导入错误"""
    # 配置
    monkeypatch.setattr(config_module.settings, "INBOX_ENABLE_VIDEO", True)
    
    # 创建 InboxItem 和 MediaTypeGuess
    item = InboxItem(path=temp_video_file)
    guess = MediaTypeGuess(
        media_type=MEDIA_TYPE_MOVIE,
        score=0.9,
        reason="extension=mkv => movie"
    )
    
    # Mock VideoImporter 抛出异常
    mock_importer = AsyncMock()
    mock_importer.import_video_from_path = AsyncMock(side_effect=Exception("Import error"))
    
    router = InboxRouter(db=db_session, video_importer=mock_importer)
    
    # 调用 route
    result = await router.route(item, guess)
    
    # 验证返回错误结果
    assert result.startswith("error:video")


@pytest.mark.asyncio
async def test_inbox_router_handles_video_import_failure(tmp_path, db_session, temp_video_file, monkeypatch):
    """测试 InboxRouter 处理视频导入失败（返回 None）"""
    # 配置
    monkeypatch.setattr(config_module.settings, "INBOX_ENABLE_VIDEO", True)
    
    # 创建 InboxItem 和 MediaTypeGuess
    item = InboxItem(path=temp_video_file)
    guess = MediaTypeGuess(
        media_type=MEDIA_TYPE_TV,
        score=0.9,
        reason="extension=mkv => tv"
    )
    
    # Mock VideoImporter 返回 None（导入失败）
    mock_importer = AsyncMock()
    mock_importer.import_video_from_path = AsyncMock(return_value=None)
    
    router = InboxRouter(db=db_session, video_importer=mock_importer)
    
    # 调用 route
    result = await router.route(item, guess)
    
    # 验证返回失败结果
    assert result.startswith("failed:video")


@pytest.mark.asyncio
async def test_inbox_router_passes_hints_to_video_importer(tmp_path, db_session, temp_video_file, monkeypatch):
    """测试 InboxRouter 将 PT hint 传递给 VideoImporter"""
    # 配置
    monkeypatch.setattr(config_module.settings, "INBOX_ENABLE_VIDEO", True)
    
    # 创建带 hint 的 InboxItem
    item = InboxItem(
        path=temp_video_file,
        download_task_id=123,
        source_site_id=456,
        source_site_name="TestSite",
        source_category="电影",
        source_tags=["动作", "冒险"]
    )
    guess = MediaTypeGuess(
        media_type=MEDIA_TYPE_MOVIE,
        score=0.95,
        reason="pt_category=电影 => movie"
    )
    
    # Mock VideoImporter
    mock_importer = AsyncMock()
    mock_importer.import_video_from_path = AsyncMock(return_value=Path(tmp_path / "movies" / "test.mkv"))
    
    router = InboxRouter(db=db_session, video_importer=mock_importer)
    
    # 调用 route
    result = await router.route(item, guess)
    
    # 验证传递了 hint 信息
    assert result.startswith("handled:video")
    call_args = mock_importer.import_video_from_path.call_args
    assert call_args.kwargs["download_task_id"] == 123
    assert call_args.kwargs["source_site_id"] == 456
    assert call_args.kwargs["extra_metadata"] is not None
    assert call_args.kwargs["extra_metadata"]["source_site_name"] == "TestSite"
    assert call_args.kwargs["extra_metadata"]["source_category"] == "电影"

