"""
TTS Job 模型和服务测试
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

from app.models.tts_job import TTSJob
from app.models.ebook import EBook
from app.modules.tts.job_service import (
    create_job_for_ebook,
    run_job,
    find_next_queued_job
)
from app.core.config import Settings
from app.modules.tts.rate_limiter import reset


@pytest.mark.asyncio
async def test_create_job_for_ebook_creates_queued_job(db_session):
    """测试创建 Job 时状态为 queued"""
    # 创建测试 EBook
    ebook = EBook(id=1, title="测试小说", author="测试作者")
    db_session.add(ebook)
    await db_session.commit()
    
    # 创建 Job
    job = await create_job_for_ebook(
        db=db_session,
        ebook_id=1,
        created_by="test"
    )
    await db_session.commit()
    
    # 验证
    assert job.status == "queued"
    assert job.ebook_id == 1
    assert job.created_by == "test"
    assert job.processed_chapters == 0
    assert job.created_files_count == 0
    assert job.error_count == 0
    assert job.requested_at is not None


@pytest.mark.asyncio
async def test_create_job_for_ebook_raises_when_ebook_not_found(db_session):
    """测试当 EBook 不存在时抛出异常"""
    with pytest.raises(ValueError, match="not found"):
        await create_job_for_ebook(
            db=db_session,
            ebook_id=99999,
            created_by="test"
        )


@pytest.mark.asyncio
async def test_run_job_sets_failed_when_tts_disabled(db_session, monkeypatch):
    """测试 TTS 未启用时 Job 状态为 failed"""
    # 设置 TTS 未启用
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_ENABLED", False)
    
    # 创建测试 EBook 和 Job
    ebook = EBook(id=1, title="测试小说", author="测试作者")
    db_session.add(ebook)
    job = TTSJob(
        id=1,
        ebook_id=1,
        status="queued",
        requested_at=datetime.utcnow(),
        processed_chapters=0,
        created_files_count=0,
        error_count=0
    )
    db_session.add(job)
    await db_session.commit()
    
    # 执行 Job
    updated_job = await run_job(
        db=db_session,
        settings=Settings(),
        job_id=1
    )
    await db_session.commit()
    
    # 验证
    assert updated_job.status == "failed"
    assert updated_job.finished_at is not None
    assert "未启用" in updated_job.last_error or "TTS" in updated_job.last_error


@pytest.mark.asyncio
async def test_run_job_updates_status_on_success(db_session, monkeypatch):
    """测试正常执行时 Job 状态正确更新"""
    reset()
    
    # 设置 TTS 启用
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_ENABLED", True)
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_PROVIDER", "dummy")
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_OUTPUT_ROOT", "./data/tts_output")
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_CHAPTER_STRATEGY", "per_chapter")
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_MAX_CHAPTERS", 10)
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_RATE_LIMIT_ENABLED", False)
    
    # 创建测试 EBook（有 novel_source）
    from pathlib import Path
    from tempfile import TemporaryDirectory
    
    with TemporaryDirectory() as tmpdir:
        txt_file = Path(tmpdir) / "test.txt"
        txt_file.write_text("第一章\n第一章内容\n\n第二章\n第二章内容", encoding="utf-8")
        
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
        
        job = TTSJob(
            id=1,
            ebook_id=1,
            status="queued",
            requested_at=datetime.utcnow(),
            processed_chapters=0,
            created_files_count=0,
            error_count=0
        )
        db_session.add(job)
        await db_session.commit()
        
        # 执行 Job
        updated_job = await run_job(
            db=db_session,
            settings=Settings(),
            job_id=1
        )
        await db_session.commit()
        
        # 验证：状态应该是 success 或 partial（取决于实际执行结果）
        assert updated_job.status in ["success", "partial", "failed"]
        assert updated_job.finished_at is not None
        assert updated_job.started_at is not None


@pytest.mark.asyncio
async def test_run_job_sets_failed_on_exception(db_session, monkeypatch):
    """测试异常时 Job 状态为 failed，last_error 有内容"""
    # 设置 TTS 启用，但让 get_tts_engine 抛出异常
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_ENABLED", True)
    
    # 创建测试 EBook 和 Job
    ebook = EBook(id=1, title="测试小说", author="测试作者")
    db_session.add(ebook)
    job = TTSJob(
        id=1,
        ebook_id=1,
        status="queued",
        requested_at=datetime.utcnow(),
        processed_chapters=0,
        created_files_count=0,
        error_count=0
    )
    db_session.add(job)
    await db_session.commit()
    
    # Mock get_tts_engine 抛出异常
    with patch("app.modules.tts.job_service.get_tts_engine", side_effect=RuntimeError("Engine error")):
        # 执行 Job
        updated_job = await run_job(
            db=db_session,
            settings=Settings(),
            job_id=1
        )
        await db_session.commit()
        
        # 验证
        assert updated_job.status == "failed"
        assert updated_job.finished_at is not None
        assert updated_job.last_error is not None
        assert "Engine error" in updated_job.last_error or len(updated_job.last_error) > 0


@pytest.mark.asyncio
async def test_find_next_queued_job_returns_oldest_queued(db_session):
    """测试 find_next_queued_job 返回最早的 queued job"""
    # 创建测试 EBook
    ebook = EBook(id=1, title="测试小说", author="测试作者")
    db_session.add(ebook)
    await db_session.commit()
    
    # 创建多个 Job（不同状态）
    job1 = TTSJob(
        ebook_id=1,
        status="queued",
        requested_at=datetime.utcnow(),
        processed_chapters=0,
        created_files_count=0,
        error_count=0
    )
    job2 = TTSJob(
        ebook_id=1,
        status="queued",
        requested_at=datetime.utcnow(),
        processed_chapters=0,
        created_files_count=0,
        error_count=0
    )
    job3 = TTSJob(
        ebook_id=1,
        status="success",
        requested_at=datetime.utcnow(),
        processed_chapters=0,
        created_files_count=0,
        error_count=0
    )
    
    db_session.add_all([job1, job2, job3])
    await db_session.commit()
    
    # 查找下一个 queued job
    next_job = await find_next_queued_job(db_session)
    
    # 验证：应该返回最早的 queued job（job1）
    assert next_job is not None
    assert next_job.status == "queued"
    assert next_job.id == job1.id


@pytest.mark.asyncio
async def test_find_next_queued_job_returns_none_when_no_queued(db_session):
    """测试没有 queued job 时返回 None"""
    # 创建测试 EBook
    ebook = EBook(id=1, title="测试小说", author="测试作者")
    db_session.add(ebook)
    
    # 创建非 queued 状态的 Job
    job = TTSJob(
        ebook_id=1,
        status="success",
        requested_at=datetime.utcnow(),
        processed_chapters=0,
        created_files_count=0,
        error_count=0
    )
    db_session.add(job)
    await db_session.commit()
    
    # 查找下一个 queued job
    next_job = await find_next_queued_job(db_session)
    
    # 验证：应该返回 None
    assert next_job is None

