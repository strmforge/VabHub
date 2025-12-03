"""
用户版 TTS Flow API 测试
"""

import pytest
from fastapi.testclient import TestClient
from main import app

from app.models.ebook import EBook
from app.models.tts_job import TTSJob
from app.models.audiobook import AudiobookFile
from app.core.database import get_db
from datetime import datetime


@pytest.mark.asyncio
async def test_enqueue_tts_job_for_work_basic(db_session, monkeypatch):
    """测试基本的创建 TTS Job"""
    from fastapi.testclient import TestClient
    
    # 覆盖数据库依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        # 设置 TTS 启用
        monkeypatch.setattr("app.core.config.settings.SMART_TTS_ENABLED", True)
        
        # 创建测试 EBook
        ebook = EBook(id=1, title="测试小说", author="测试作者", language="zh-CN")
        db_session.add(ebook)
        await db_session.flush()
        await db_session.commit()
        
        client = TestClient(app)
        response = client.post("/api/tts/jobs/enqueue-for-work/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["job_id"] > 0
        assert data["ebook_id"] == 1
        assert data["status"] == "queued"
        assert data["already_exists"] is False
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_enqueue_tts_job_skips_when_existing_active_job(db_session, monkeypatch):
    """测试存在活跃 Job 时复用现有 Job"""
    from fastapi.testclient import TestClient
    
    # 覆盖数据库依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        # 设置 TTS 启用
        monkeypatch.setattr("app.core.config.settings.SMART_TTS_ENABLED", True)
        
        # 创建测试 EBook
        ebook = EBook(id=1, title="测试小说", author="测试作者", language="zh-CN")
        db_session.add(ebook)
        await db_session.flush()
        
        # 创建已有的 queued Job
        existing_job = TTSJob(
            ebook_id=1,
            status="queued",
            requested_at=datetime.utcnow(),
            processed_chapters=0,
            created_files_count=0,
            error_count=0,
            created_by="test"
        )
        db_session.add(existing_job)
        await db_session.flush()
        await db_session.commit()
        
        client = TestClient(app)
        response = client.post("/api/tts/jobs/enqueue-for-work/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["job_id"] == existing_job.id
        assert data["already_exists"] is True
        
        # 验证没有创建新的 Job
        from sqlalchemy import select, func
        job_count_result = await db_session.execute(
            select(func.count(TTSJob.id)).where(TTSJob.ebook_id == 1)
        )
        job_count = job_count_result.scalar()
        assert job_count == 1  # 只有原来的一个
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_enqueue_tts_job_requires_tts_enabled(db_session, monkeypatch):
    """测试 TTS 未启用时返回错误"""
    from fastapi.testclient import TestClient
    
    # 覆盖数据库依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        # 设置 TTS 禁用
        monkeypatch.setattr("app.core.config.settings.SMART_TTS_ENABLED", False)
        
        # 创建测试 EBook
        ebook = EBook(id=1, title="测试小说", author="测试作者", language="zh-CN")
        db_session.add(ebook)
        await db_session.flush()
        await db_session.commit()
        
        client = TestClient(app)
        response = client.post("/api/tts/jobs/enqueue-for-work/1")
        
        assert response.status_code == 400
        assert "disabled" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_enqueue_tts_job_ebook_not_found(db_session, monkeypatch):
    """测试 EBook 不存在时返回 404"""
    from fastapi.testclient import TestClient
    
    # 覆盖数据库依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        # 设置 TTS 启用
        monkeypatch.setattr("app.core.config.settings.SMART_TTS_ENABLED", True)
        
        client = TestClient(app)
        response = client.post("/api/tts/jobs/enqueue-for-work/99999")
        
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_tts_status_for_ebook_with_tts_audiobook(db_session):
    """测试获取有 TTS 有声书的作品状态"""
    from fastapi.testclient import TestClient
    
    # 覆盖数据库依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        # 创建测试 EBook
        ebook = EBook(id=1, title="测试小说", author="测试作者", language="zh-CN")
        db_session.add(ebook)
        await db_session.flush()
        
        # 创建 TTS 生成的有声书
        audiobook = AudiobookFile(
            ebook_id=1,
            file_path="/test.wav",
            format="wav",
            is_tts_generated=True,
            tts_provider="dummy"
        )
        db_session.add(audiobook)
        await db_session.flush()
        
        # 创建最近的 Job
        job = TTSJob(
            ebook_id=1,
            status="success",
            requested_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
            processed_chapters=10,
            created_files_count=10,
            error_count=0,
            created_by="test",
            details={
                "tts": {
                    "total_chapters": 10,
                    "generated_chapters": 10
                }
            }
        )
        db_session.add(job)
        await db_session.flush()
        await db_session.commit()
        
        client = TestClient(app)
        response = client.get("/api/tts/jobs/status/by-ebook/1")
    
        assert response.status_code == 200
        data = response.json()
        assert data["ebook_id"] == 1
        assert data["has_tts_audiobook"] is True
        assert data["last_job_status"] == "success"
        assert data["total_chapters"] == 10
        assert data["generated_chapters"] == 10
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_tts_status_for_ebook_without_job(db_session):
    """测试没有 Job 的作品状态"""
    from fastapi.testclient import TestClient
    
    # 覆盖数据库依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        # 创建测试 EBook（没有 Job 和 Audiobook）
        ebook = EBook(id=1, title="测试小说", author="测试作者", language="zh-CN")
        db_session.add(ebook)
        await db_session.flush()
        await db_session.commit()
        
        client = TestClient(app)
        response = client.get("/api/tts/jobs/status/by-ebook/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ebook_id"] == 1
        assert data["has_tts_audiobook"] is False
        assert data["last_job_status"] is None
        assert data["last_job_requested_at"] is None
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_tts_status_ebook_not_found(db_session):
    """测试获取不存在的作品状态返回 404"""
    from fastapi.testclient import TestClient
    
    # 覆盖数据库依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        client = TestClient(app)
        response = client.get("/api/tts/jobs/status/by-ebook/99999")
        
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_overview_api_basic(db_session):
    """测试概览 API 基本功能"""
    from fastapi.testclient import TestClient
    
    # 覆盖数据库依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        # 创建多个 EBook 和 Job
        ebooks = [
            EBook(id=1, title="小说1", author="作者1", language="zh-CN"),
            EBook(id=2, title="小说2", author="作者2", language="zh-CN"),
            EBook(id=3, title="小说3", author="作者3", language="zh-CN"),
        ]
        for ebook in ebooks:
            db_session.add(ebook)
        await db_session.flush()
        
        jobs = [
            TTSJob(
                ebook_id=1,
                status="queued",
                requested_at=datetime.utcnow(),
                processed_chapters=0,
                created_files_count=0,
                error_count=0,
                created_by="test"
            ),
            TTSJob(
                ebook_id=2,
                status="running",
                requested_at=datetime.utcnow(),
                processed_chapters=5,
                created_files_count=5,
                error_count=0,
                created_by="test",
                details={
                    "tts": {
                        "total_chapters": 10,
                        "generated_chapters": 5
                    }
                }
            ),
            TTSJob(
                ebook_id=3,
                status="partial",
                requested_at=datetime.utcnow(),
                finished_at=datetime.utcnow(),
                processed_chapters=8,
                created_files_count=8,
                error_count=0,
                created_by="test",
                details={
                    "tts": {
                        "total_chapters": 10,
                        "generated_chapters": 8
                    }
                }
            ),
        ]
        for job in jobs:
            db_session.add(job)
        await db_session.flush()
        await db_session.commit()
        
        client = TestClient(app)
        response = client.get("/api/tts/jobs/overview?limit=10")
    
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        
        # 验证排序（按 requested_at DESC）
        assert data[0]["status"] in ["queued", "running", "partial"]
        
        # 验证字段
        for item in data:
            assert "job_id" in item
            assert "ebook_id" in item
            assert "ebook_title" in item
            assert "status" in item
            assert "requested_at" in item
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_overview_api_status_filter(db_session):
    """测试概览 API 状态过滤"""
    from fastapi.testclient import TestClient
    
    # 覆盖数据库依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        # 创建 EBook
        ebook = EBook(id=1, title="测试小说", author="测试作者", language="zh-CN")
        db_session.add(ebook)
        await db_session.flush()
        
        # 创建不同状态的 Job
        jobs = [
            TTSJob(
                ebook_id=1,
                status="queued",
                requested_at=datetime.utcnow(),
                processed_chapters=0,
                created_files_count=0,
                error_count=0,
                created_by="test"
            ),
            TTSJob(
                ebook_id=1,
                status="success",
                requested_at=datetime.utcnow(),
                finished_at=datetime.utcnow(),
                processed_chapters=10,
                created_files_count=10,
                error_count=0,
                created_by="test"
            ),
        ]
        for job in jobs:
            db_session.add(job)
        await db_session.flush()
        await db_session.commit()
        
        client = TestClient(app)
        
        # 只查询 queued
        response = client.get("/api/tts/jobs/overview?status=queued")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "queued"
        
        # 查询多个状态
        response = client.get("/api/tts/jobs/overview?status=queued,success")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    finally:
        app.dependency_overrides.clear()

