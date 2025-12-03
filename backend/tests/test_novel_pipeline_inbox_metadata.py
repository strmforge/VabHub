"""
小说流水线 Inbox 元数据测试
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inbox.models import InboxItem
from app.modules.inbox.router import InboxRouter
from app.modules.novel.models import NovelMetadata
from app.modules.novel.sources.local_txt import LocalTxtNovelSourceAdapter


@pytest.fixture
def mock_db_session():
    return AsyncMock(spec=AsyncSession)


@pytest.mark.asyncio
async def test_clean_title_for_display():
    """测试标题清洗功能"""
    router = InboxRouter(db=AsyncMock())
    
    # 测试移除 [精校] 标记
    assert router._clean_title_for_display("三体 [精校版]") == "三体"
    assert router._clean_title_for_display("三体[全本]") == "三体"
    assert router._clean_title_for_display("三体(完本)") == "三体"
    
    # 测试保留正常标题
    assert router._clean_title_for_display("三体") == "三体"
    assert router._clean_title_for_display("平凡的世界") == "平凡的世界"
    
    # 测试空字符串
    assert router._clean_title_for_display("") == ""
    assert router._clean_title_for_display("   ") == ""


@pytest.mark.asyncio
async def test_create_safe_filename():
    """测试安全文件名生成"""
    router = InboxRouter(db=AsyncMock())
    
    # 测试正常文件名
    safe = router._create_safe_filename("test_novel.txt")
    assert safe.endswith(".txt")
    assert "test_novel" in safe
    
    # 测试包含特殊字符的文件名
    safe = router._create_safe_filename("test/novel[1].txt")
    assert safe.endswith(".txt")
    assert "/" not in safe
    assert "[" not in safe
    
    # 测试中文文件名
    safe = router._create_safe_filename("测试小说.txt")
    assert safe.endswith(".txt")
    assert "测试小说" in safe or "_" in safe


@pytest.mark.asyncio
async def test_handle_novel_txt_metadata_construction(mock_db_session, tmp_path, monkeypatch):
    """测试从 InboxItem 构造的 NovelMetadata 包含正确的字段"""
    from app.modules.novel.pipeline import NovelToEbookPipeline
    from app.modules.novel.epub_builder import EpubBuilder
    from app.modules.ebook.importer import EBookImporter
    from app.core.config import settings
    
    monkeypatch.setattr(settings, "INBOX_ENABLE_NOVEL_TXT", True)
    monkeypatch.setattr(settings, "NOVEL_UPLOAD_ROOT", str(tmp_path / "novel_uploads"))
    monkeypatch.setattr(settings, "EBOOK_LIBRARY_ROOT", str(tmp_path / "ebook_library"))
    
    # 创建测试文件
    test_file = tmp_path / "测试小说[精校].txt"
    test_file.write_text("第一章 测试\n这是测试内容。")
    
    item = InboxItem(
        path=test_file,
        source_tags=["tag1", "tag2"]
    )
    
    router = InboxRouter(db=mock_db_session)
    
    # Mock pipeline.run 返回成功
    with patch.object(router.novel_pipeline, 'run', new_callable=AsyncMock) as mock_run:
        mock_run.return_value = Path("/mock/epub.epub")
        
        with patch("app.modules.inbox.router.shutil.move") as mock_move:
            result = await router._handle_novel_txt(item)
            
            # 验证 pipeline 被调用
            assert mock_run.called
            call_args = mock_run.call_args
            
            # 获取传入的 source
            source = call_args[0][0]  # 第一个参数是 source
            assert isinstance(source, LocalTxtNovelSourceAdapter)
            
            # 验证 metadata
            metadata = source.get_metadata()
            assert isinstance(metadata, NovelMetadata)
            assert metadata.title == "测试小说"  # 应该清洗掉 [精校]
            assert metadata.language == "zh-CN"
            assert "from_inbox_novel_txt" in metadata.tags
            assert "tag1" in metadata.tags or "tag2" in metadata.tags
            assert metadata.description == "Imported from INBOX"
            assert metadata.author is None  # 暂时留空


@pytest.mark.asyncio
async def test_handle_novel_txt_with_source_tags_string(mock_db_session, tmp_path, monkeypatch):
    """测试 source_tags 是字符串时的处理"""
    from app.modules.novel.pipeline import NovelToEbookPipeline
    from app.modules.novel.epub_builder import EpubBuilder
    from app.modules.ebook.importer import EBookImporter
    from app.core.config import settings
    
    monkeypatch.setattr(settings, "INBOX_ENABLE_NOVEL_TXT", True)
    monkeypatch.setattr(settings, "NOVEL_UPLOAD_ROOT", str(tmp_path / "novel_uploads"))
    monkeypatch.setattr(settings, "EBOOK_LIBRARY_ROOT", str(tmp_path / "ebook_library"))
    
    test_file = tmp_path / "test.txt"
    test_file.write_text("第一章 测试\n这是测试内容。")
    
    item = InboxItem(
        path=test_file,
        source_tags="tag1,tag2,tag3"  # 逗号分隔的字符串
    )
    
    router = InboxRouter(db=mock_db_session)
    
    with patch.object(router.novel_pipeline, 'run', new_callable=AsyncMock) as mock_run:
        mock_run.return_value = Path("/mock/epub.epub")
        
        with patch("app.modules.inbox.router.shutil.move"):
            result = await router._handle_novel_txt(item)
            
            call_args = mock_run.call_args
            source = call_args[0][0]
            metadata = source.get_metadata()
            
            # 验证 tags 包含分割后的标签
            assert "from_inbox_novel_txt" in metadata.tags
            # tag1, tag2, tag3 应该被分割并添加到 tags 中
            assert any("tag1" in tag or tag == "tag1" for tag in metadata.tags)

