"""
小说流水线结构测试

验证 novel 模块的基础结构和接口定义。
"""

import pytest
from pathlib import Path
from typing import Iterable
from unittest.mock import MagicMock, AsyncMock

from app.modules.novel.models import StandardChapter, NovelMetadata
from app.modules.novel.source_base import NovelSourceAdapter
from app.modules.novel.epub_builder import EpubBuilder
from app.modules.novel.pipeline import NovelToEbookPipeline


def test_standard_chapter_instantiation():
    """测试 StandardChapter 可以正常实例化"""
    chapter = StandardChapter(
        index=1,
        title="第一章",
        content="这是第一章的内容。"
    )
    
    assert chapter.index == 1
    assert chapter.title == "第一章"
    assert chapter.content == "这是第一章的内容。"


def test_novel_metadata_instantiation():
    """测试 NovelMetadata 可以正常实例化"""
    metadata = NovelMetadata(
        title="测试小说",
        author="测试作者",
        description="这是一本测试小说",
        language="zh-CN",
        tags=["测试", "小说"]
    )
    
    assert metadata.title == "测试小说"
    assert metadata.author == "测试作者"
    assert metadata.description == "这是一本测试小说"
    assert metadata.language == "zh-CN"
    assert metadata.tags == ["测试", "小说"]


def test_novel_metadata_defaults():
    """测试 NovelMetadata 的默认值"""
    metadata = NovelMetadata(title="测试小说")
    
    assert metadata.title == "测试小说"
    assert metadata.author is None
    assert metadata.description is None
    assert metadata.language == "zh-CN"
    assert metadata.tags is None


def test_novel_source_adapter_is_abc():
    """测试 NovelSourceAdapter 是抽象基类"""
    # 尝试实例化应该失败
    with pytest.raises(TypeError):
        NovelSourceAdapter()


def test_novel_source_adapter_abstract_methods():
    """测试 NovelSourceAdapter 定义了抽象方法"""
    # 创建一个实现类
    class FakeSourceAdapter(NovelSourceAdapter):
        def get_metadata(self) -> NovelMetadata:
            return NovelMetadata(title="测试")
        
        def iter_chapters(self) -> Iterable[StandardChapter]:
            yield StandardChapter(index=1, title="第一章", content="内容")
    
    # 应该可以正常实例化
    adapter = FakeSourceAdapter()
    assert isinstance(adapter, NovelSourceAdapter)
    
    # 测试方法
    metadata = adapter.get_metadata()
    assert metadata.title == "测试"
    
    chapters = list(adapter.iter_chapters())
    assert len(chapters) == 1
    assert chapters[0].title == "第一章"


def test_epub_builder_instantiation():
    """测试 EpubBuilder 可以被构造"""
    builder = EpubBuilder()
    assert builder is not None


def test_epub_builder_build_epub_creates_file(tmp_path):
    """测试 EpubBuilder.build_epub 创建文件（占位实现）"""
    builder = EpubBuilder()
    
    metadata = NovelMetadata(
        title="测试小说",
        author="测试作者",
        description="测试简介"
    )
    
    chapters = [
        StandardChapter(index=1, title="第一章", content="第一章内容"),
        StandardChapter(index=2, title="第二章", content="第二章内容")
    ]
    
    output_path = builder.build_epub(
        output_dir=tmp_path,
        metadata=metadata,
        chapters=chapters
    )
    
    assert output_path.exists()
    assert output_path.suffix == ".txt"  # 当前是占位实现，生成 TXT
    
    # 验证文件内容
    content = output_path.read_text(encoding='utf-8')
    assert "测试小说" in content
    assert "测试作者" in content
    assert "第一章" in content
    assert "第二章" in content


def test_novel_to_ebook_pipeline_instantiation():
    """测试 NovelToEbookPipeline 可以被构造"""
    mock_db = MagicMock()
    mock_importer = MagicMock()
    mock_builder = MagicMock()
    
    pipeline = NovelToEbookPipeline(
        db=mock_db,
        ebook_importer=mock_importer,
        epub_builder=mock_builder
    )
    
    assert pipeline is not None
    assert pipeline.db == mock_db
    assert pipeline.ebook_importer == mock_importer
    assert pipeline.epub_builder == mock_builder


@pytest.mark.asyncio
async def test_novel_to_ebook_pipeline_run_basic_flow(tmp_path):
    """测试 pipeline.run 的基本调用流程（异步版本）"""
    from app.modules.ebook.importer import EBookImporter
    
    from app.modules.ebook.importer import EBookImporter
    from app.core.database import Base
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    
    # 创建测试数据库
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as db_session:
        # 使用真实的 EpubBuilder 和 EBookImporter
        mock_builder = EpubBuilder()
        ebook_importer = EBookImporter(db_session)
        
        # 创建 Fake Source Adapter
        class FakeSourceAdapter(NovelSourceAdapter):
            def get_metadata(self) -> NovelMetadata:
                return NovelMetadata(title="测试小说", author="测试作者")
            
            def iter_chapters(self) -> Iterable[StandardChapter]:
                yield StandardChapter(index=1, title="第一章", content="内容1")
                yield StandardChapter(index=2, title="第二章", content="内容2")
        
        # 设置临时库目录
        import app.core.config as config_module
        original_root = config_module.settings.EBOOK_LIBRARY_ROOT
        config_module.settings.EBOOK_LIBRARY_ROOT = str(tmp_path)
        
        try:
            pipeline = NovelToEbookPipeline(
                db=db_session,
                ebook_importer=ebook_importer,
                epub_builder=mock_builder
            )
            
            source = FakeSourceAdapter()
            result = await pipeline.run(source, output_dir=tmp_path)
            
            # 验证返回了文件路径
            assert result is not None
            assert result.exists()
            
            # 验证文件内容
            content = result.read_text(encoding='utf-8')
            assert "测试小说" in content
            assert "第一章" in content
            assert "第二章" in content
        finally:
            config_module.settings.EBOOK_LIBRARY_ROOT = original_root
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_novel_to_ebook_pipeline_run_empty_chapters(tmp_path):
    """测试 pipeline.run 处理空章节列表"""
    from sqlalchemy.ext.asyncio import AsyncSession
    from unittest.mock import MagicMock
    
    mock_db = MagicMock(spec=AsyncSession)
    mock_importer = MagicMock()
    mock_builder = MagicMock()
    
    class EmptySourceAdapter(NovelSourceAdapter):
        def get_metadata(self) -> NovelMetadata:
            return NovelMetadata(title="空小说")
        
        def iter_chapters(self) -> Iterable[StandardChapter]:
            return iter([])  # 空迭代器
    
    pipeline = NovelToEbookPipeline(
        db=mock_db,
        ebook_importer=mock_importer,
        epub_builder=mock_builder
    )
    
    source = EmptySourceAdapter()
    result = await pipeline.run(source, output_dir=tmp_path)
    
    # 应该返回 None（因为没有章节）
    assert result is None
    # builder 不应该被调用
    mock_builder.build_epub.assert_not_called()

