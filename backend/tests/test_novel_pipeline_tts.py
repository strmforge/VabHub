"""
小说 TTS 流水线测试（包含 TTSSummary 和断点续跑）
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, AsyncMock, patch

from app.modules.novel.pipeline import NovelToEbookPipeline, TTSSummary
from app.modules.novel.sources.local_txt import LocalTxtNovelSourceAdapter
from app.modules.novel.models import NovelMetadata, StandardChapter
from app.modules.ebook.importer import EBookImporter
from app.modules.novel.epub_builder import EpubBuilder
from app.modules.tts.rate_limiter import reset, should_allow, record_request
from app.core.config import Settings
from app.models.ebook import EBook


@pytest.mark.asyncio
async def test_tts_summary_basic_counts_and_no_rate_limit(db_session, monkeypatch):
    """测试 TTS 汇总信息：基本计数且无限流"""
    reset()
    
    # 创建测试用 Settings 实例
    test_settings = Settings()
    monkeypatch.setattr(test_settings, "SMART_TTS_ENABLED", True)
    monkeypatch.setattr(test_settings, "SMART_TTS_PROVIDER", "dummy")
    monkeypatch.setattr(test_settings, "SMART_TTS_OUTPUT_ROOT", "./data/tts_output")
    monkeypatch.setattr(test_settings, "SMART_TTS_CHAPTER_STRATEGY", "per_chapter")
    monkeypatch.setattr(test_settings, "SMART_TTS_MAX_CHAPTERS", 10)
    monkeypatch.setattr(test_settings, "SMART_TTS_RATE_LIMIT_ENABLED", False)
    
    # 创建测试 TXT 文件（3 章）
    with TemporaryDirectory() as tmpdir:
        txt_file = Path(tmpdir) / "test.txt"
        txt_file.write_text("第一章\n第一章内容\n\n第二章\n第二章内容\n\n第三章\n第三章内容", encoding="utf-8")
        
        # 创建 mock
        ebook_importer = MagicMock(spec=EBookImporter)
        epub_builder = MagicMock(spec=EpubBuilder)
        
        fake_ebook = EBook(id=1, title="测试小说", author="测试作者")
        ebook_importer.import_ebook_from_file = AsyncMock(return_value=fake_ebook)
        
        epub_path = Path(tmpdir) / "test.epub"
        epub_path.touch()
        epub_builder.build_epub = MagicMock(return_value=epub_path)
        
        # 创建 source adapter
        metadata = NovelMetadata(
            title="测试小说",
            author="测试作者",
            language="zh-CN"
        )
        source = LocalTxtNovelSourceAdapter(
            file_path=txt_file,
            metadata=metadata,
            encoding="utf-8"
        )
        
        # 创建 pipeline（需要真实的 TTS 引擎）
        from app.modules.tts.factory import get_tts_engine
        tts_engine = get_tts_engine(settings=test_settings)
        
        from app.modules.audiobook.importer import AudiobookImporter
        audiobook_importer = AudiobookImporter(db=db_session)
        
        pipeline = NovelToEbookPipeline(
            db=db_session,
            ebook_importer=ebook_importer,
            epub_builder=epub_builder,
            tts_engine=tts_engine,
            audiobook_importer=audiobook_importer,
            settings=test_settings
        )
        
        # 执行
        result = await pipeline.run(source, Path(tmpdir), generate_audiobook=True)
        
        # 验证
        assert result.tts_summary is not None
        assert result.tts_summary.total_chapters == 3
        assert result.tts_summary.generated_chapters == 3
        assert result.tts_summary.rate_limited_chapters == 0
        assert result.tts_summary.first_rate_limited_chapter_index is None


@pytest.mark.asyncio
async def test_tts_summary_with_rate_limit_sets_first_rate_limited_index(db_session, monkeypatch):
    """测试限流时设置 first_rate_limited_chapter_index"""
    reset()
    
    # 创建测试用 Settings 实例
    test_settings = Settings()
    monkeypatch.setattr(test_settings, "SMART_TTS_ENABLED", True)
    monkeypatch.setattr(test_settings, "SMART_TTS_PROVIDER", "dummy")
    monkeypatch.setattr(test_settings, "SMART_TTS_OUTPUT_ROOT", "./data/tts_output")
    monkeypatch.setattr(test_settings, "SMART_TTS_CHAPTER_STRATEGY", "per_chapter")
    monkeypatch.setattr(test_settings, "SMART_TTS_MAX_CHAPTERS", 10)
    monkeypatch.setattr(test_settings, "SMART_TTS_RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(test_settings, "SMART_TTS_MAX_REQUESTS_PER_RUN", 2)
    monkeypatch.setattr(test_settings, "SMART_TTS_MAX_DAILY_REQUESTS", 100)
    monkeypatch.setattr(test_settings, "SMART_TTS_MAX_DAILY_CHARACTERS", 100000)
    
    # 创建测试 TXT 文件（3 章）
    with TemporaryDirectory() as tmpdir:
        txt_file = Path(tmpdir) / "test.txt"
        txt_file.write_text("第一章\n第一章内容\n\n第二章\n第二章内容\n\n第三章\n第三章内容", encoding="utf-8")
        
        # 创建 mock
        ebook_importer = MagicMock(spec=EBookImporter)
        epub_builder = MagicMock(spec=EpubBuilder)
        
        fake_ebook = EBook(id=1, title="测试小说", author="测试作者")
        ebook_importer.import_ebook_from_file = AsyncMock(return_value=fake_ebook)
        
        epub_path = Path(tmpdir) / "test.epub"
        epub_path.touch()
        epub_builder.build_epub = MagicMock(return_value=epub_path)
        
        # 创建 source adapter
        metadata = NovelMetadata(
            title="测试小说",
            author="测试作者",
            language="zh-CN"
        )
        source = LocalTxtNovelSourceAdapter(
            file_path=txt_file,
            metadata=metadata,
            encoding="utf-8"
        )
        
        # 创建 pipeline
        from app.modules.tts.factory import get_tts_engine
        tts_engine = get_tts_engine(settings=test_settings)
        
        from app.modules.audiobook.importer import AudiobookImporter
        audiobook_importer = AudiobookImporter(db=db_session)
        
        pipeline = NovelToEbookPipeline(
            db=db_session,
            ebook_importer=ebook_importer,
            epub_builder=epub_builder,
            tts_engine=tts_engine,
            audiobook_importer=audiobook_importer,
            settings=test_settings
        )
        
        # 执行
        result = await pipeline.run(source, Path(tmpdir), generate_audiobook=True)
        
        # 验证
        assert result.tts_summary is not None
        assert result.tts_summary.total_chapters == 3
        assert result.tts_summary.generated_chapters == 2  # 只生成了前 2 章
        assert result.tts_summary.rate_limited_chapters == 1  # 第 3 章被限流
        assert result.tts_summary.first_rate_limited_chapter_index == 3


@pytest.mark.asyncio
async def test_start_chapter_index_skips_earlier_chapters(db_session, monkeypatch):
    """测试 start_chapter_index 跳过前面的章节"""
    reset()
    
    # 创建测试用 Settings 实例
    test_settings = Settings()
    monkeypatch.setattr(test_settings, "SMART_TTS_ENABLED", True)
    monkeypatch.setattr(test_settings, "SMART_TTS_PROVIDER", "dummy")
    monkeypatch.setattr(test_settings, "SMART_TTS_OUTPUT_ROOT", "./data/tts_output")
    monkeypatch.setattr(test_settings, "SMART_TTS_CHAPTER_STRATEGY", "per_chapter")
    monkeypatch.setattr(test_settings, "SMART_TTS_MAX_CHAPTERS", 10)
    monkeypatch.setattr(test_settings, "SMART_TTS_RATE_LIMIT_ENABLED", False)
    
    # 创建测试 TXT 文件（3 章）
    with TemporaryDirectory() as tmpdir:
        txt_file = Path(tmpdir) / "test.txt"
        txt_file.write_text("第一章\n第一章内容\n\n第二章\n第二章内容\n\n第三章\n第三章内容", encoding="utf-8")
        
        # 创建 mock
        ebook_importer = MagicMock(spec=EBookImporter)
        epub_builder = MagicMock(spec=EpubBuilder)
        
        fake_ebook = EBook(id=1, title="测试小说", author="测试作者")
        ebook_importer.import_ebook_from_file = AsyncMock(return_value=fake_ebook)
        
        epub_path = Path(tmpdir) / "test.epub"
        epub_path.touch()
        epub_builder.build_epub = MagicMock(return_value=epub_path)
        
        # 创建 source adapter
        metadata = NovelMetadata(
            title="测试小说",
            author="测试作者",
            language="zh-CN"
        )
        source = LocalTxtNovelSourceAdapter(
            file_path=txt_file,
            metadata=metadata,
            encoding="utf-8"
        )
        
        # 创建 pipeline
        from app.modules.tts.factory import get_tts_engine
        tts_engine = get_tts_engine(settings=test_settings)
        
        from app.modules.audiobook.importer import AudiobookImporter
        audiobook_importer = AudiobookImporter(db=db_session)
        
        pipeline = NovelToEbookPipeline(
            db=db_session,
            ebook_importer=ebook_importer,
            epub_builder=epub_builder,
            tts_engine=tts_engine,
            audiobook_importer=audiobook_importer,
            settings=test_settings
        )
        
        # 执行（从第 3 章开始）
        result = await pipeline.run(source, Path(tmpdir), generate_audiobook=True, start_chapter_index=3)
        
        # 验证：应该只生成第 3 章
        assert result.tts_summary is not None
        assert result.tts_summary.total_chapters == 3
        assert result.tts_summary.generated_chapters == 1  # 只生成了第 3 章
        assert len(result.audiobook_files) == 1
