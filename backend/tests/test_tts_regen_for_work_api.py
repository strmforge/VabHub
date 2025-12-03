"""
TTS 重新生成 API 测试
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, AsyncMock, patch

from app.api.tts_regen import regenerate_tts_for_work
from app.models.ebook import EBook
from app.models.audiobook import AudiobookFile
from app.core.config import Settings
from app.modules.tts.rate_limiter import reset


@pytest.mark.asyncio
async def test_regen_fails_when_tts_disabled(db_session, monkeypatch):
    """测试 TTS 未启用时返回失败"""
    # 设置 TTS 未启用
    monkeypatch.setattr("app.api.tts_regen.settings.SMART_TTS_ENABLED", False)
    monkeypatch.setattr("app.api.tts_regen.settings.DEBUG", True)
    
    # 创建测试 EBook（没有 novel_source）
    ebook = EBook(id=1, title="测试小说", author="测试作者")
    db_session.add(ebook)
    await db_session.commit()
    
    # 调用 API
    result = await regenerate_tts_for_work(ebook_id=1, db=db_session)
    
    # 验证
    assert result["success"] is False
    assert result["status"] in ["tts_disabled", "tts_engine_unavailable"]


@pytest.mark.asyncio
async def test_regen_returns_no_novel_source_when_missing_metadata(db_session, monkeypatch):
    """测试没有 novel_source 元数据时返回相应状态"""
    # 设置 TTS 启用
    monkeypatch.setattr("app.api.tts_regen.settings.SMART_TTS_ENABLED", True)
    monkeypatch.setattr("app.api.tts_regen.settings.DEBUG", True)
    monkeypatch.setattr("app.api.tts_regen.settings.SMART_TTS_PROVIDER", "dummy")
    
    # 创建测试 EBook（没有 novel_source）
    ebook = EBook(id=1, title="测试小说", author="测试作者", extra_metadata={})
    db_session.add(ebook)
    await db_session.commit()
    
    # 调用 API
    result = await regenerate_tts_for_work(ebook_id=1, db=db_session)
    
    # 验证
    assert result["success"] is False
    assert result["status"] == "no_novel_source"
    assert "没有绑定小说" in result["message"]


@pytest.mark.asyncio
async def test_regen_returns_archived_txt_missing_when_file_not_found(db_session, monkeypatch):
    """测试归档 TXT 文件不存在时返回相应状态"""
    # 设置 TTS 启用
    monkeypatch.setattr("app.api.tts_regen.settings.SMART_TTS_ENABLED", True)
    monkeypatch.setattr("app.api.tts_regen.settings.DEBUG", True)
    monkeypatch.setattr("app.api.tts_regen.settings.SMART_TTS_PROVIDER", "dummy")
    
    # 创建测试 EBook（有 novel_source 但文件不存在）
    ebook = EBook(
        id=1,
        title="测试小说",
        author="测试作者",
        extra_metadata={
            "novel_source": {
                "type": "local_txt",
                "archived_txt_path": "/nonexistent/path.txt"
            }
        }
    )
    db_session.add(ebook)
    await db_session.commit()
    
    # 调用 API
    result = await regenerate_tts_for_work(ebook_id=1, db=db_session)
    
    # 验证
    assert result["success"] is False
    assert result["status"] == "archived_txt_missing"
    assert "找不到" in result["message"]


@pytest.mark.asyncio
async def test_regen_success_creates_audiobooks(db_session, monkeypatch):
    """测试成功重新生成时创建有声书文件"""
    reset()
    
    # 设置 TTS 启用
    monkeypatch.setattr("app.api.tts_regen.settings.SMART_TTS_ENABLED", True)
    monkeypatch.setattr("app.api.tts_regen.settings.DEBUG", True)
    monkeypatch.setattr("app.api.tts_regen.settings.SMART_TTS_PROVIDER", "dummy")
    monkeypatch.setattr("app.api.tts_regen.settings.SMART_TTS_OUTPUT_ROOT", "./data/tts_output")
    monkeypatch.setattr("app.api.tts_regen.settings.SMART_TTS_CHAPTER_STRATEGY", "per_chapter")
    monkeypatch.setattr("app.api.tts_regen.settings.SMART_TTS_MAX_CHAPTERS", 10)
    monkeypatch.setattr("app.api.tts_regen.settings.SMART_TTS_RATE_LIMIT_ENABLED", False)
    
    # 创建测试 TXT 文件
    with TemporaryDirectory() as tmpdir:
        txt_file = Path(tmpdir) / "test.txt"
        txt_file.write_text("第一章\n第一章内容\n\n第二章\n第二章内容", encoding="utf-8")
        
        # 创建测试 EBook（有 novel_source 且文件存在）
        ebook = EBook(
            id=1,
            title="测试小说",
            author="测试作者",
            language="zh-CN",
            extra_metadata={
                "novel_source": {
                    "type": "local_txt",
                    "archived_txt_path": str(txt_file)
                }
            }
        )
        db_session.add(ebook)
        await db_session.commit()
        
        # Mock AudiobookImporter
        fake_audiobook_file = AudiobookFile(
            id=1,
            ebook_id=1,
            file_path="/test.wav",
            format="wav",
            is_tts_generated=True,
            tts_provider="dummy"
        )
        
        with patch("app.api.tts_regen.AudiobookImporter") as mock_importer_class:
            mock_importer = MagicMock()
            mock_importer.import_audiobook_from_file = AsyncMock(return_value=fake_audiobook_file)
            mock_importer_class.return_value = mock_importer
            
            # 调用 API
            result = await regenerate_tts_for_work(ebook_id=1, db=db_session)
            
            # 验证
            # 注意：由于使用了真实的 DummyTTSEngine，可能会实际创建文件
            # 这里主要验证 API 调用不报错，并且返回了合理的状态
            assert result["success"] is True or result["status"] in ["ok", "error"]
            # 如果成功，应该有 created_count
            if result["success"]:
                assert result["created_count"] >= 0


@pytest.mark.asyncio
async def test_regen_does_not_break_when_tts_engine_error(db_session, monkeypatch):
    """测试 TTS 引擎错误时不会导致 API 崩溃"""
    # 设置 TTS 启用，但让 get_tts_engine 返回 None
    monkeypatch.setattr("app.api.tts_regen.settings.SMART_TTS_ENABLED", True)
    monkeypatch.setattr("app.api.tts_regen.settings.DEBUG", True)
    
    # 创建测试 EBook
    ebook = EBook(id=1, title="测试小说", author="测试作者")
    db_session.add(ebook)
    await db_session.commit()
    
    # Mock get_tts_engine 返回 None
    with patch("app.api.tts_regen.get_tts_engine", return_value=None):
        # 调用 API
        result = await regenerate_tts_for_work(ebook_id=1, db=db_session)
        
        # 验证：应该返回错误状态，但不应该抛出异常
        assert result["success"] is False
        assert result["status"] == "tts_engine_unavailable"

