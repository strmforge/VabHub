"""
TTS Job 断点续跑测试
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

from app.models.tts_job import TTSJob
from app.models.ebook import EBook
from app.modules.tts.job_service import (
    create_job_for_ebook,
    run_job,
    find_next_queued_job
)
from app.modules.tts.rate_limiter import reset
from app.core.config import Settings


@pytest.mark.asyncio
async def test_job_becomes_partial_when_rate_limited_and_stores_resume_index(db_session, monkeypatch):
    """测试限流时 Job 变为 partial 并存储 resume_from_chapter_index"""
    reset()
    
    # 设置 TTS 启用，限流只允许 2 个请求（总共 5 章）
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_ENABLED", True)
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_PROVIDER", "dummy")
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_OUTPUT_ROOT", "./data/tts_output")
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_CHAPTER_STRATEGY", "per_chapter")
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_MAX_CHAPTERS", 10)
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_MAX_REQUESTS_PER_RUN", 2)
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_MAX_DAILY_REQUESTS", 100)
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_MAX_DAILY_CHARACTERS", 100000)
    
    # 创建测试 EBook（有 novel_source，5 章）
    from pathlib import Path
    from tempfile import TemporaryDirectory
    
    with TemporaryDirectory() as tmpdir:
        txt_file = Path(tmpdir) / "test.txt"
        txt_file.write_text(
            "第一章\n第一章内容\n\n"
            "第二章\n第二章内容\n\n"
            "第三章\n第三章内容\n\n"
            "第四章\n第四章内容\n\n"
            "第五章\n第五章内容",
            encoding="utf-8"
        )
        
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
        
        # 创建 Job
        job = await create_job_for_ebook(
            db=db_session,
            ebook_id=1,
            created_by="test"
        )
        await db_session.commit()
        
        # 执行 Job
        updated_job = await run_job(
            db=db_session,
            settings=Settings(),
            job_id=job.id
        )
        await db_session.commit()
        
        # 验证：应该是 partial 状态，且存储了 resume_from_chapter_index
        assert updated_job.status == "partial"
        assert updated_job.details is not None
        assert "tts" in updated_job.details
        tts_details = updated_job.details["tts"]
        assert tts_details["resume_from_chapter_index"] == 3  # 从第 3 章继续
        assert tts_details["generated_chapters"] == 2  # 已生成 2 章
        assert tts_details["total_chapters"] == 5


@pytest.mark.asyncio
async def test_job_rerun_uses_resume_index_and_eventually_success(db_session, monkeypatch):
    """测试 Job 续跑使用 resume_index，最终成功"""
    reset()
    
    # 设置 TTS 启用，第一次限流只允许 2 个请求
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_ENABLED", True)
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_PROVIDER", "dummy")
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_OUTPUT_ROOT", "./data/tts_output")
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_CHAPTER_STRATEGY", "per_chapter")
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_MAX_CHAPTERS", 10)
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_MAX_REQUESTS_PER_RUN", 2)
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_MAX_DAILY_REQUESTS", 100)
    monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_MAX_DAILY_CHARACTERS", 100000)
    
    # 创建测试 EBook（3 章）
    from pathlib import Path
    from tempfile import TemporaryDirectory
    
    with TemporaryDirectory() as tmpdir:
        txt_file = Path(tmpdir) / "test.txt"
        txt_file.write_text(
            "第一章\n第一章内容\n\n"
            "第二章\n第二章内容\n\n"
            "第三章\n第三章内容",
            encoding="utf-8"
        )
        
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
        
        # 创建 Job
        job = await create_job_for_ebook(
            db=db_session,
            ebook_id=1,
            created_by="test"
        )
        await db_session.commit()
        
        # 第一次执行（会被限流）
        updated_job = await run_job(
            db=db_session,
            settings=Settings(),
            job_id=job.id
        )
        await db_session.commit()
        
        assert updated_job.status == "partial"
        assert updated_job.details["tts"]["resume_from_chapter_index"] == 3
        
        # 调整限流配置（允许更多请求）
        monkeypatch.setattr("app.modules.tts.job_service.settings.SMART_TTS_MAX_REQUESTS_PER_RUN", 10)
        reset()  # 重置限流状态
        
        # 第二次执行（应该完成剩余章节）
        updated_job = await run_job(
            db=db_session,
            settings=Settings(),
            job_id=updated_job.id
        )
        await db_session.commit()
        
        # 验证：应该变为 success
        assert updated_job.status == "success"
        # resume_from_chapter_index 应该被清空或为 None
        if "tts" in updated_job.details:
            assert updated_job.details["tts"].get("resume_from_chapter_index") is None


@pytest.mark.asyncio
async def test_find_next_queued_job_includes_partial(db_session):
    """测试 find_next_queued_job 包含 partial 状态的 Job"""
    # 创建测试 EBook
    ebook = EBook(id=1, title="测试小说", author="测试作者")
    db_session.add(ebook)
    await db_session.commit()
    
    # 创建不同状态的 Job
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
        status="partial",
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
    
    # 查找下一个待处理的 Job
    next_job = await find_next_queued_job(db_session)
    
    # 验证：应该返回 queued 或 partial 中的一个（按 requested_at 排序，应该是 job1）
    assert next_job is not None
    assert next_job.status in ["queued", "partial"]
    assert next_job.id in [job1.id, job2.id]

