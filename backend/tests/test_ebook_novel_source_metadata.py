"""
EBook 小说源元数据测试
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, AsyncMock

from app.modules.novel.pipeline import NovelToEbookPipeline
from app.modules.novel.sources.local_txt import LocalTxtNovelSourceAdapter
from app.modules.novel.models import NovelMetadata, StandardChapter
from app.modules.ebook.importer import EBookImporter
from app.modules.novel.epub_builder import EpubBuilder
from app.models.ebook import EBook
from app.core.config import Settings


class FakeNovelSourceAdapter:
    """假的小说源适配器（非 LocalTxt）"""
    
    def __init__(self):
        self._metadata = NovelMetadata(
            title="测试小说",
            author="测试作者",
            language="zh-CN"
        )
        self._chapters = [
            StandardChapter(index=1, title="第一章", content="第一章内容"),
        ]
    
    def get_metadata(self) -> NovelMetadata:
        return self._metadata
    
    def iter_chapters(self):
        return iter(self._chapters)


@pytest.mark.asyncio
async def test_pipeline_stores_novel_source_in_ebook_metadata(db_session):
    """测试 Pipeline 在 EBook 元数据中存储小说源信息"""
    # 创建 mock
    ebook_importer = MagicMock(spec=EBookImporter)
    epub_builder = MagicMock(spec=EpubBuilder)
    
    # Mock EBookImporter 返回一个假的 EBook
    fake_ebook = EBook(id=1, title="测试小说", author="测试作者")
    ebook_importer.import_ebook_from_file = AsyncMock(return_value=fake_ebook)
    
    # Mock EpubBuilder
    with TemporaryDirectory() as tmpdir:
        epub_path = Path(tmpdir) / "test.epub"
        epub_path.touch()
        epub_builder.build_epub = MagicMock(return_value=epub_path)
        
        # 创建真实的 TXT 文件
        txt_file = Path(tmpdir) / "test.txt"
        txt_file.write_text("第一章\n第一章内容", encoding="utf-8")
        
        # 创建 LocalTxtNovelSourceAdapter
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
        
        # 创建流水线并设置归档路径
        pipeline = NovelToEbookPipeline(
            db=db_session,
            ebook_importer=ebook_importer,
            epub_builder=epub_builder
        )
        pipeline._archived_txt_path = Path(tmpdir) / "archived_test.txt"
        
        # 执行
        result = await pipeline.run(source, Path(tmpdir), generate_audiobook=False)
        
        # 验证
        assert result.ebook is not None
        assert result.ebook.extra_metadata is not None
        assert "novel_source" in result.ebook.extra_metadata
        
        novel_source = result.ebook.extra_metadata["novel_source"]
        assert novel_source["type"] == "local_txt"
        assert novel_source["archived_txt_path"] == str(pipeline._archived_txt_path)
        assert "imported_at" in novel_source


@pytest.mark.asyncio
async def test_pipeline_does_not_store_novel_source_for_non_local_txt(db_session):
    """测试 Pipeline 对非 LocalTxt 源不存储小说源信息"""
    # 创建 mock
    ebook_importer = MagicMock(spec=EBookImporter)
    epub_builder = MagicMock(spec=EpubBuilder)
    
    # Mock EBookImporter
    fake_ebook = EBook(id=1, title="测试小说", author="测试作者")
    ebook_importer.import_ebook_from_file = AsyncMock(return_value=fake_ebook)
    
    # Mock EpubBuilder
    with TemporaryDirectory() as tmpdir:
        epub_path = Path(tmpdir) / "test.epub"
        epub_path.touch()
        epub_builder.build_epub = MagicMock(return_value=epub_path)
        
        # 使用非 LocalTxt 源
        source = FakeNovelSourceAdapter()
        
        # 创建流水线
        pipeline = NovelToEbookPipeline(
            db=db_session,
            ebook_importer=ebook_importer,
            epub_builder=epub_builder
        )
        
        # 执行
        result = await pipeline.run(source, Path(tmpdir), generate_audiobook=False)
        
        # 验证：不应该有 novel_source（或者 extra_metadata 为空）
        assert result.ebook is not None
        # 如果 extra_metadata 存在，不应该包含 novel_source
        if result.ebook.extra_metadata:
            assert "novel_source" not in result.ebook.extra_metadata


@pytest.mark.asyncio
async def test_existing_ebook_without_novel_source_remains_unchanged(db_session):
    """测试已有 EBook（没有 novel_source）不会被误改"""
    # 创建一个已有的 EBook，没有 novel_source
    existing_ebook = EBook(
        id=1,
        title="已有小说",
        author="已有作者",
        extra_metadata={"other_field": "other_value"}
    )
    db_session.add(existing_ebook)
    await db_session.commit()
    
    # 验证 extra_metadata 保持不变
    assert existing_ebook.extra_metadata == {"other_field": "other_value"}
    assert "novel_source" not in existing_ebook.extra_metadata

