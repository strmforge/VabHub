"""
有声书元数据解析测试
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from app.modules.audiobook.media_info import probe_audio_file, AudioMeta


def test_probe_audio_file_import_error():
    """测试 mutagen 未安装时的行为（简化版）"""
    test_path = Path("/fake/path/audio.mp3")
    
    # 直接测试函数，如果 mutagen 未安装应该返回空元数据
    # 这个测试主要验证函数不会因为 ImportError 而崩溃
    result = probe_audio_file(test_path)
    
    # 如果 mutagen 未安装，应该返回空元数据
    # 如果已安装但文件不存在，也应该返回空元数据
    assert isinstance(result, AudioMeta)
    assert result.duration_seconds is None or isinstance(result.duration_seconds, int)
    assert result.bitrate_kbps is None or isinstance(result.bitrate_kbps, int)
    assert result.sample_rate_hz is None or isinstance(result.sample_rate_hz, int)
    assert result.channels is None or isinstance(result.channels, int)


def test_probe_audio_file_with_mock(monkeypatch):
    """测试音频元数据解析（使用 mock）"""
    test_path = Path("/fake/path/audio.mp3")
    
    # Mock mutagen.File 和 audio.info
    mock_info = MagicMock()
    mock_info.length = 3600.5  # 1小时0.5秒
    mock_info.bitrate = 128000  # 128 kbps (以 bps 表示)
    mock_info.sample_rate = 44100  # 44.1 kHz
    mock_info.channels = 2  # 立体声
    
    mock_audio = MagicMock()
    mock_audio.info = mock_info
    
    # 创建一个 mock 的 mutagen 模块
    mock_mutagen = MagicMock()
    mock_mutagen.File.return_value = mock_audio
    
    # 使用 monkeypatch 来模拟 mutagen 模块
    import sys
    original_modules = sys.modules.copy()
    sys.modules['mutagen'] = mock_mutagen
    
    try:
        # 重新导入模块以使用 mock
        import importlib
        import app.modules.audiobook.media_info as media_info_module
        importlib.reload(media_info_module)
        from app.modules.audiobook.media_info import probe_audio_file
        
        result = probe_audio_file(test_path)
        
        assert result.duration_seconds == 3600
        assert result.bitrate_kbps == 128  # 128000 / 1000
        assert result.sample_rate_hz == 44100
        assert result.channels == 2
    finally:
        # 恢复原始模块
        sys.modules.clear()
        sys.modules.update(original_modules)


def test_probe_audio_file_none_result():
    """测试 mutagen.File 返回 None 的情况"""
    test_path = Path("/fake/path/unknown.xyz")
    
    mock_mutagen = MagicMock()
    mock_mutagen.File.return_value = None
    
    with patch('app.modules.audiobook.media_info.mutagen', mock_mutagen, create=True):
        import importlib
        import app.modules.audiobook.media_info as media_info_module
        importlib.reload(media_info_module)
        from app.modules.audiobook.media_info import probe_audio_file
        
        result = probe_audio_file(test_path)
        
        assert result == AudioMeta(None, None, None, None)


def test_probe_audio_file_exception_handling():
    """测试解析过程中抛出异常时的行为"""
    test_path = Path("/fake/path/audio.mp3")
    
    mock_mutagen = MagicMock()
    mock_mutagen.File.side_effect = Exception("Unexpected error")
    
    with patch('app.modules.audiobook.media_info.mutagen', mock_mutagen, create=True):
        import importlib
        import app.modules.audiobook.media_info as media_info_module
        importlib.reload(media_info_module)
        from app.modules.audiobook.media_info import probe_audio_file
        
        result = probe_audio_file(test_path)
        
        # 应该返回空元数据，不抛异常
        assert result == AudioMeta(None, None, None, None)


@pytest.mark.asyncio
async def test_audiobook_importer_sets_meta_fields(tmp_path):
    """测试 AudiobookImporter 在导入时设置元数据字段"""
    from app.modules.audiobook.importer import AudiobookImporter
    from app.models.audiobook import AudiobookFile
    from app.core.database import Base
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    
    # 创建测试数据库
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as db_session:
        # 创建临时音频文件（模拟）
        test_file = tmp_path / "test_audiobook.mp3"
        test_file.write_bytes(b"fake audio content" * 100)  # 创建一个小文件
        
        # Mock probe_audio_file 返回固定的元数据
        mock_meta = AudioMeta(
            duration_seconds=7200,  # 2小时
            bitrate_kbps=192,
            sample_rate_hz=48000,
            channels=2
        )
        
        importer = AudiobookImporter(db_session)
        
        with patch('app.modules.audiobook.importer.probe_audio_file', return_value=mock_meta):
            # 设置临时库目录
            import app.core.config as config_module
            original_root = config_module.settings.EBOOK_LIBRARY_ROOT
            config_module.settings.EBOOK_LIBRARY_ROOT = str(tmp_path)
            
            try:
                result = await importer.import_audiobook_from_file(
                    file_path=str(test_file),
                    media_type="audiobook"
                )
                
                assert result is not None
                assert result.duration_seconds == 7200
                assert result.bitrate_kbps == 192
                assert result.sample_rate_hz == 48000
                assert result.channels == 2
                
                # 验证数据库中的记录
                stmt = select(AudiobookFile).where(AudiobookFile.id == result.id)
                db_result = await db_session.execute(stmt)
                saved_file = db_result.scalar_one()
                
                assert saved_file.duration_seconds == 7200
                assert saved_file.bitrate_kbps == 192
                assert saved_file.sample_rate_hz == 48000
                assert saved_file.channels == 2
                
            finally:
                config_module.settings.EBOOK_LIBRARY_ROOT = original_root
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
