"""
视频导入器测试
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
import shutil

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.database import Base

from app.modules.video.importer import VideoImporter
from app.constants.media_types import MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV, MEDIA_TYPE_ANIME, MEDIA_TYPE_SHORT_DRAMA
import app.core.config as config_module
import app.modules.video.importer as importer_module


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
async def test_video_importer_uses_movie_library_root_for_movie(tmp_path, db_session, temp_video_file, monkeypatch):
    """测试电影使用 MOVIE_LIBRARY_ROOT"""
    movie_root = tmp_path / "movies"
    monkeypatch.setattr(config_module.settings, "MOVIE_LIBRARY_ROOT", str(movie_root))
    monkeypatch.setattr(importer_module.settings, "MOVIE_LIBRARY_ROOT", str(movie_root))
    
    importer = VideoImporter(db_session)
    library_root = importer._get_library_root_for_media_type(MEDIA_TYPE_MOVIE)
    
    assert library_root == movie_root


@pytest.mark.asyncio
async def test_video_importer_tv_uses_tv_library_root(tmp_path, db_session, monkeypatch):
    """测试电视剧使用 TV_LIBRARY_ROOT"""
    tv_root = tmp_path / "tv"
    monkeypatch.setattr(config_module.settings, "TV_LIBRARY_ROOT", str(tv_root))
    monkeypatch.setattr(importer_module.settings, "TV_LIBRARY_ROOT", str(tv_root))
    
    importer = VideoImporter(db_session)
    library_root = importer._get_library_root_for_media_type(MEDIA_TYPE_TV)
    
    assert library_root == tv_root


@pytest.mark.asyncio
async def test_video_importer_anime_uses_anime_library_root_or_tv(tmp_path, db_session, monkeypatch):
    """测试动漫使用 ANIME_LIBRARY_ROOT 或回退到 TV_LIBRARY_ROOT"""
    anime_root = tmp_path / "anime"
    tv_root = tmp_path / "tv"
    
    # 测试配置了 ANIME_LIBRARY_ROOT
    monkeypatch.setattr(config_module.settings, "ANIME_LIBRARY_ROOT", str(anime_root))
    monkeypatch.setattr(config_module.settings, "TV_LIBRARY_ROOT", str(tv_root))
    monkeypatch.setattr(importer_module.settings, "ANIME_LIBRARY_ROOT", str(anime_root))
    monkeypatch.setattr(importer_module.settings, "TV_LIBRARY_ROOT", str(tv_root))
    
    importer = VideoImporter(db_session)
    library_root = importer._get_library_root_for_media_type(MEDIA_TYPE_ANIME)
    
    assert library_root == anime_root
    
    # 测试未配置 ANIME_LIBRARY_ROOT 时回退到 TV_LIBRARY_ROOT
    monkeypatch.setattr(config_module.settings, "ANIME_LIBRARY_ROOT", None)
    monkeypatch.setattr(importer_module.settings, "ANIME_LIBRARY_ROOT", None)
    
    library_root = importer._get_library_root_for_media_type(MEDIA_TYPE_ANIME)
    assert library_root == tv_root


@pytest.mark.asyncio
async def test_video_importer_short_drama_uses_tv_or_short_drama_root(tmp_path, db_session, monkeypatch):
    """测试短剧使用 SHORT_DRAMA_LIBRARY_ROOT 或回退到 TV_LIBRARY_ROOT"""
    short_drama_root = tmp_path / "short_drama"
    tv_root = tmp_path / "tv"
    
    # 测试配置了 SHORT_DRAMA_LIBRARY_ROOT
    monkeypatch.setattr(config_module.settings, "SHORT_DRAMA_LIBRARY_ROOT", str(short_drama_root))
    monkeypatch.setattr(config_module.settings, "TV_LIBRARY_ROOT", str(tv_root))
    monkeypatch.setattr(importer_module.settings, "SHORT_DRAMA_LIBRARY_ROOT", str(short_drama_root))
    monkeypatch.setattr(importer_module.settings, "TV_LIBRARY_ROOT", str(tv_root))
    
    importer = VideoImporter(db_session)
    library_root = importer._get_library_root_for_media_type(MEDIA_TYPE_SHORT_DRAMA)
    
    assert library_root == short_drama_root
    
    # 测试未配置 SHORT_DRAMA_LIBRARY_ROOT 时回退到 TV_LIBRARY_ROOT
    monkeypatch.setattr(config_module.settings, "SHORT_DRAMA_LIBRARY_ROOT", None)
    monkeypatch.setattr(importer_module.settings, "SHORT_DRAMA_LIBRARY_ROOT", None)
    
    library_root = importer._get_library_root_for_media_type(MEDIA_TYPE_SHORT_DRAMA)
    assert library_root == tv_root


@pytest.mark.asyncio
async def test_video_importer_calls_organizer(tmp_path, db_session, temp_video_file, monkeypatch):
    """测试 VideoImporter 调用 MediaOrganizer"""
    movie_root = tmp_path / "movies"
    monkeypatch.setattr(config_module.settings, "MOVIE_LIBRARY_ROOT", str(movie_root))
    monkeypatch.setattr(importer_module.settings, "MOVIE_LIBRARY_ROOT", str(movie_root))
    
    importer = VideoImporter(db_session)
    
    # Mock MediaOrganizer
    mock_organizer = AsyncMock()
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.new_path = str(movie_root / "test_movie.mkv")
    mock_organizer.organize_file = AsyncMock(return_value=mock_result)
    
    with patch.object(importer, '_get_organizer', return_value=mock_organizer):
        result = await importer.import_video_from_path(
            file_path=temp_video_file,
            media_type=MEDIA_TYPE_MOVIE
        )
        
        # 验证调用了 organize_file
        mock_organizer.organize_file.assert_called_once()
        call_args = mock_organizer.organize_file.call_args
        
        # call_args 是 ((位置参数), {关键字参数}) 的元组
        # 检查位置参数或关键字参数
        if len(call_args[0]) >= 2:
            # 位置参数
            assert call_args[0][0] == str(temp_video_file)  # file_path
            assert call_args[0][1] == str(movie_root)  # target_base_dir
        else:
            # 关键字参数
            assert call_args.kwargs.get("file_path") == str(temp_video_file)
            assert call_args.kwargs.get("target_base_dir") == str(movie_root)
        
        # 检查关键字参数
        assert call_args.kwargs.get("move_file") is True
        assert call_args.kwargs.get("use_classification") is True
        assert call_args.kwargs.get("write_nfo") is True
        
        # 验证返回了新路径
        assert result == Path(mock_result.new_path)


@pytest.mark.asyncio
async def test_video_importer_handles_organizer_failure(tmp_path, db_session, temp_video_file, monkeypatch):
    """测试 VideoImporter 处理 MediaOrganizer 失败的情况"""
    movie_root = tmp_path / "movies"
    monkeypatch.setattr(config_module.settings, "MOVIE_LIBRARY_ROOT", str(movie_root))
    monkeypatch.setattr(importer_module.settings, "MOVIE_LIBRARY_ROOT", str(movie_root))
    
    importer = VideoImporter(db_session)
    
    # Mock MediaOrganizer 返回失败结果
    mock_organizer = AsyncMock()
    mock_result = MagicMock()
    mock_result.success = False
    mock_result.error = "Organizer failed"
    mock_organizer.organize_file = AsyncMock(return_value=mock_result)
    
    with patch.object(importer, '_get_organizer', return_value=mock_organizer):
        result = await importer.import_video_from_path(
            file_path=temp_video_file,
            media_type=MEDIA_TYPE_MOVIE
        )
        
        # 验证返回 None
        assert result is None


@pytest.mark.asyncio
async def test_video_importer_handles_exception(tmp_path, db_session, temp_video_file, monkeypatch):
    """测试 VideoImporter 处理异常"""
    movie_root = tmp_path / "movies"
    monkeypatch.setattr(config_module.settings, "MOVIE_LIBRARY_ROOT", str(movie_root))
    monkeypatch.setattr(importer_module.settings, "MOVIE_LIBRARY_ROOT", str(movie_root))
    
    importer = VideoImporter(db_session)
    
    # Mock MediaOrganizer 抛出异常
    mock_organizer = AsyncMock()
    mock_organizer.organize_file = AsyncMock(side_effect=Exception("Test error"))
    
    with patch.object(importer, '_get_organizer', return_value=mock_organizer):
        result = await importer.import_video_from_path(
            file_path=temp_video_file,
            media_type=MEDIA_TYPE_MOVIE
        )
        
        # 验证返回 None（异常被捕获）
        assert result is None

