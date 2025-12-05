"""
TTS Jobs API 测试

Note: These tests require proper database session setup and TTS service mocking.
      Skipped by default in CI - requires VABHUB_ENABLE_TTS_TESTS=1 to run.
"""

import os
import pytest
from datetime import datetime
from unittest.mock import patch, AsyncMock

# Skip tests that require complex TTS setup unless explicitly enabled
pytestmark = pytest.mark.skipif(
    not os.getenv("VABHUB_ENABLE_TTS_TESTS"),
    reason="TTS Jobs API tests require VABHUB_ENABLE_TTS_TESTS=1"
)

from app.models.tts_job import TTSJob
from app.models.ebook import EBook
from app.api.tts_jobs import (
    enqueue_job_for_work,
    run_next_job,
    list_jobs,
    get_job
)
from app.core.config import Settings


@pytest.mark.asyncio
async def test_enqueue_for_work_creates_job(db_session, monkeypatch):
    """测试 enqueue-for-work 正常创建 job"""
    # 设置 DEBUG 模式
    monkeypatch.setattr("app.api.tts_jobs.settings.DEBUG", True)
    
    # 创建测试 EBook
    ebook = EBook(id=1, title="测试小说", author="测试作者")
    db_session.add(ebook)
    await db_session.commit()
    
    # 调用 API
    result = await enqueue_job_for_work(ebook_id=1, db=db_session)
    
    # 验证
    assert result.id > 0
    assert result.ebook_id == 1
    assert result.status == "queued"
    assert result.created_by == "dev-api"


@pytest.mark.asyncio
async def test_enqueue_for_work_returns_404_when_ebook_not_found(db_session, monkeypatch):
    """测试当 EBook 不存在时返回 404"""
    from fastapi.testclient import TestClient
    from main import app
    
    # 设置 DEBUG 模式
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    
    # 使用 TestClient 调用 API
    client = TestClient(app)
    response = client.post("/api/dev/tts/jobs/enqueue-for-work/99999")
    
    # 验证
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_run_next_returns_no_queued_when_empty(db_session, monkeypatch):
    """测试 run-next 在没有 queued job 时返回相应状态"""
    from fastapi.testclient import TestClient
    from main import app
    
    # 设置 DEBUG 模式
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    
    # 使用 TestClient 调用 API
    client = TestClient(app)
    response = client.post("/api/dev/tts/jobs/run-next")
    
    # 验证
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["reason"] == "no_queued_job"


@pytest.mark.asyncio
async def test_run_next_executes_queued_job(db_session, monkeypatch):
    """测试 run-next 正常执行一个 queued job"""
    from fastapi.testclient import TestClient
    from main import app
    from app.modules.tts.rate_limiter import reset
    from app.core.database import get_db
    from pathlib import Path
    from tempfile import TemporaryDirectory
    
    reset()
    
    # 设置 DEBUG 和 TTS 启用 - 同时打补丁到 API 模块
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    monkeypatch.setattr("app.api.tts_jobs.settings.DEBUG", True)
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_ENABLED", True)
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_PROVIDER", "dummy")
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_OUTPUT_ROOT", "./data/tts_output")
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_CHAPTER_STRATEGY", "per_chapter")
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_MAX_CHAPTERS", 10)
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_RATE_LIMIT_ENABLED", False)
    
    # 创建测试 EBook（有 novel_source）
    with TemporaryDirectory() as tmpdir:
        txt_file = Path(tmpdir) / "test.txt"
        txt_file.write_text("第一章\n第一章内容", encoding="utf-8")
        
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
        
        # 创建 queued job
        job = TTSJob(
            ebook_id=1,
            status="queued",
            requested_at=datetime.utcnow(),
            processed_chapters=0,
            created_files_count=0,
            error_count=0
        )
        db_session.add(job)
        await db_session.commit()
        
        # 覆盖 get_db 依赖
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            # 使用 TestClient 调用 API
            client = TestClient(app)
            response = client.post("/api/dev/tts/jobs/run-next")
            
            # 验证
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "job" in data
            assert data["job"]["status"] in ["success", "partial", "failed"]
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_jobs_returns_jobs(db_session, monkeypatch):
    """测试 list 返回 job 列表"""
    from fastapi.testclient import TestClient
    from main import app
    from app.core.database import get_db
    
    # 设置 DEBUG 模式 - 同时打补丁到 API 模块
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    monkeypatch.setattr("app.api.tts_jobs.settings.DEBUG", True)
    
    # 创建测试 EBook
    ebook = EBook(id=1, title="测试小说", author="测试作者")
    db_session.add(ebook)
    
    # 创建多个 Job
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
        status="success",
        requested_at=datetime.utcnow(),
        processed_chapters=0,
        created_files_count=0,
        error_count=0
    )
    db_session.add_all([job1, job2])
    await db_session.commit()
    
    # 覆盖 get_db 依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        # 使用 TestClient 调用 API
        client = TestClient(app)
        response = client.get("/api/dev/tts/jobs")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        job_ids = [job["id"] for job in data]
        assert job1.id in job_ids or job2.id in job_ids
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_jobs_filters_by_status(db_session, monkeypatch):
    """测试 list 按状态筛选"""
    from fastapi.testclient import TestClient
    from main import app
    from app.core.database import get_db
    
    # 设置 DEBUG 模式 - 同时打补丁到 API 模块
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    monkeypatch.setattr("app.api.tts_jobs.settings.DEBUG", True)
    
    # 创建测试 EBook
    ebook = EBook(id=1, title="测试小说", author="测试作者")
    db_session.add(ebook)
    
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
        status="success",
        requested_at=datetime.utcnow(),
        processed_chapters=0,
        created_files_count=0,
        error_count=0
    )
    db_session.add_all([job1, job2])
    await db_session.commit()
    
    # 覆盖 get_db 依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        # 使用 TestClient 调用 API（筛选 queued）
        client = TestClient(app)
        response = client.get("/api/dev/tts/jobs?status=queued")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(job["status"] == "queued" for job in data)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_job_returns_job_detail(db_session, monkeypatch):
    """测试 get 返回 job 详情"""
    from fastapi.testclient import TestClient
    from main import app
    from app.core.database import get_db
    
    # 设置 DEBUG 模式 - 同时打补丁到 API 模块
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    monkeypatch.setattr("app.api.tts_jobs.settings.DEBUG", True)
    
    # 创建测试 EBook
    ebook = EBook(id=1, title="测试小说", author="测试作者")
    db_session.add(ebook)
    
    # 创建 Job
    job = TTSJob(
        ebook_id=1,
        status="queued",
        requested_at=datetime.utcnow(),
        processed_chapters=0,
        created_files_count=0,
        error_count=0
    )
    db_session.add(job)
    await db_session.commit()
    
    # 覆盖 get_db 依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        # 使用 TestClient 调用 API
        client = TestClient(app)
        response = client.get(f"/api/dev/tts/jobs/{job.id}")
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job.id
        assert data["ebook_id"] == 1
        assert data["status"] == "queued"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_job_returns_404_when_not_found(db_session, monkeypatch):
    """测试当 Job 不存在时返回 404"""
    from fastapi.testclient import TestClient
    from main import app
    
    # 设置 DEBUG 模式
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    
    # 使用 TestClient 调用 API
    client = TestClient(app)
    response = client.get("/api/dev/tts/jobs/99999")
    
    # 验证
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_run_batch_jobs_api_basic(db_session, monkeypatch):
    """测试批量执行 API 基本功能（DEBUG=True 时 200）"""
    from fastapi.testclient import TestClient
    from main import app
    from app.core.database import Base, engine
    
    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 设置 DEBUG 模式
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_JOB_RUNNER_MAX_JOBS_PER_RUN", 5)
    
    # 使用 TestClient 调用 API
    client = TestClient(app)
    response = client.post("/api/dev/tts/jobs/run-batch", json={"max_jobs": None})
    
    # 验证
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    # API 直接返回 TTSBatchJobsResponse
    assert "total_jobs" in data
    assert "run_jobs" in data
    assert "succeeded_jobs" in data
    assert "partial_jobs" in data
    assert "failed_jobs" in data
    assert "message" in data


@pytest.mark.asyncio
async def test_run_batch_jobs_api_rejects_without_debug(db_session, monkeypatch):
    """测试批量执行 API 在 DEBUG=False 时返回 403"""
    from fastapi.testclient import TestClient
    from main import app
    
    # 设置 DEBUG 模式为 False - 同时打补丁到 API 模块
    monkeypatch.setattr("app.core.config.settings.DEBUG", False)
    monkeypatch.setattr("app.api.tts_jobs.settings.DEBUG", False)
    
    # 使用 TestClient 调用 API
    client = TestClient(app)
    response = client.post("/api/dev/tts/jobs/run-batch", json={"max_jobs": 5})
    
    # 验证
    assert response.status_code == 403
    assert "Dev only" in response.json()["detail"] or "DEBUG" in response.json()["detail"]

