"""
Audiobook TTS 标记测试
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.audiobook.importer import AudiobookImporter
from app.models.ebook import EBook
from app.models.audiobook import AudiobookFile


@pytest.mark.asyncio
async def test_importer_sets_tts_flag_and_provider_when_hints_true(db_session):
    """测试当 hints 中包含 TTS 信息时，正确设置标记"""
    importer = AudiobookImporter(db_session)
    
    # 创建一个测试 EBook
    ebook = EBook(
        title="测试小说",
        author="测试作者",
        language="zh-CN"
    )
    db_session.add(ebook)
    await db_session.flush()
    
    # 创建测试音频文件
    with TemporaryDirectory() as tmpdir:
        test_audio = Path(tmpdir) / "test.mp3"
        test_audio.write_bytes(b"FAKEAUDIO")
        
        # 准备 hints
        hints = {
            "tts_generated": True,
            "tts_provider": "dummy"
        }
        
        # Mock probe_audio_file 返回元数据
        with patch("app.modules.audiobook.importer.probe_audio_file") as mock_probe:
            from app.modules.audiobook.media_info import AudioMeta
            mock_probe.return_value = AudioMeta(
                duration_seconds=100,
                bitrate_kbps=128,
                channels=2,
                sample_rate_hz=44100
            )
            
            # 调用导入器
            result = await importer.import_audiobook_from_file(
                file_path=str(test_audio),
                media_type="audiobook",
                ebook=ebook,
                hints=hints
            )
            
            # 断言
            assert result is not None
            assert result.is_tts_generated is True
            assert result.tts_provider == "dummy"
            assert result.ebook_id == ebook.id


@pytest.mark.asyncio
async def test_importer_defaults_to_non_tts_when_no_hints(db_session):
    """测试不传 hints 时默认为非 TTS"""
    importer = AudiobookImporter(db_session)
    
    # 创建一个测试 EBook
    ebook = EBook(
        title="测试小说",
        author="测试作者",
        language="zh-CN"
    )
    db_session.add(ebook)
    await db_session.flush()
    
    # 创建测试音频文件
    with TemporaryDirectory() as tmpdir:
        test_audio = Path(tmpdir) / "test.mp3"
        test_audio.write_bytes(b"FAKEAUDIO")
        
        # Mock probe_audio_file
        with patch("app.modules.audiobook.importer.probe_audio_file") as mock_probe:
            from app.modules.audiobook.media_info import AudioMeta
            mock_probe.return_value = AudioMeta(
                duration_seconds=100,
                bitrate_kbps=128,
                channels=2,
                sample_rate_hz=44100
            )
            
            # 调用导入器（不传 hints）
            result = await importer.import_audiobook_from_file(
                file_path=str(test_audio),
                media_type="audiobook",
                ebook=ebook
            )
            
            # 断言
            assert result is not None
            assert result.is_tts_generated is False
            assert result.tts_provider is None


@pytest.mark.asyncio
async def test_novel_pipeline_tts_marks_imported_files_as_tts(db_session):
    """测试 NovelToEbookPipeline 在 TTS 支路中正确标记有声书文件"""
    from app.modules.novel.pipeline import NovelToEbookPipeline
    from app.modules.novel.models import NovelMetadata, StandardChapter
    from app.modules.novel.epub_builder import EpubBuilder
    from app.modules.ebook.importer import EBookImporter
    from app.modules.audiobook.importer import AudiobookImporter
    from app.modules.tts.dummy import DummyTTSEngine
    from app.core.config import Settings
    
    # 创建测试 EBook
    ebook = EBook(
        title="测试小说",
        author="测试作者",
        language="zh-CN"
    )
    db_session.add(ebook)
    await db_session.flush()
    
    # 创建测试章节
    chapters = [
        StandardChapter(index=1, title="第一章", content="第一章内容"),
    ]
    
    # 创建测试元数据
    metadata = NovelMetadata(
        title="测试小说",
        author="测试作者",
        language="zh-CN"
    )
    
    # 创建设置
    settings = Settings()
    settings.SMART_TTS_ENABLED = True
    settings.SMART_TTS_PROVIDER = "dummy"
    settings.SMART_TTS_OUTPUT_ROOT = "./data/tts_output"
    settings.SMART_TTS_CHAPTER_STRATEGY = "per_chapter"
    
    # 创建导入器和流水线
    ebook_importer = EBookImporter(db_session)
    epub_builder = EpubBuilder()
    tts_engine = DummyTTSEngine()
    audiobook_importer = AudiobookImporter(db_session)
    
    pipeline = NovelToEbookPipeline(
        db=db_session,
        ebook_importer=ebook_importer,
        epub_builder=epub_builder,
        tts_engine=tts_engine,
        audiobook_importer=audiobook_importer,
        settings=settings
    )
    
    # Mock source adapter
    class FakeSource:
        def get_metadata(self):
            return metadata
        def iter_chapters(self):
            return iter(chapters)
    
    source = FakeSource()
    
    with TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        # 先手动创建 ebook（因为 pipeline 会创建）
        # 这里我们直接测试 _generate_audiobook_from_chapters
        await pipeline._generate_audiobook_from_chapters(
            ebook=ebook,
            chapters=chapters,
            metadata=metadata,
            settings=settings
        )
        
        # 查询数据库中的 AudiobookFile
        from sqlalchemy import select
        stmt = select(AudiobookFile).where(AudiobookFile.ebook_id == ebook.id)
        result = await db_session.execute(stmt)
        audiobook_files = result.scalars().all()
        
        # 断言至少有一个文件被标记为 TTS
        assert len(audiobook_files) > 0
        for af in audiobook_files:
            assert af.is_tts_generated is True
            assert af.tts_provider == "dummy"


@pytest.mark.asyncio
async def test_work_detail_includes_tts_flags(db_session):
    """测试 WorkDetail API 返回包含 TTS 标记"""
    from app.api.work import get_work_detail
    from app.models.ebook import EBook
    from app.models.audiobook import AudiobookFile
    
    # 创建测试 EBook
    ebook = EBook(
        title="测试小说",
        author="测试作者",
        language="zh-CN"
    )
    db_session.add(ebook)
    await db_session.flush()
    
    # 创建一个 TTS 生成的有声书文件
    audiobook_file = AudiobookFile(
        ebook_id=ebook.id,
        file_path="/test/audio.mp3",
        format="mp3",
        is_tts_generated=True,
        tts_provider="dummy"
    )
    db_session.add(audiobook_file)
    await db_session.commit()
    
    # 调用 API（get_work_detail 返回 BaseResponse 格式）
    result = await get_work_detail(ebook.id, db_session)
    
    # 解析响应（success_response 返回字典）
    assert isinstance(result, dict)
    assert result["success"] is True
    response_data = result["data"]
    audiobooks = response_data["audiobooks"]
    
    # 断言
    assert len(audiobooks) > 0
    tts_audiobook = audiobooks[0]
    assert tts_audiobook["is_tts_generated"] is True
    assert tts_audiobook["tts_provider"] == "dummy"
