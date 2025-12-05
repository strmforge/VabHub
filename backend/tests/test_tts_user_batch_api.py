"""
测试用户批量 TTS API
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from main import app
from app.core.database import get_db
from app.models.ebook import EBook
from app.models.audiobook import AudiobookFile
from app.models.tts_job import TTSJob


@pytest.fixture(autouse=True)
async def override_get_db_dependency(db_session: AsyncSession, monkeypatch):
    """覆盖 get_db 依赖，使用测试数据库会话，并启用 TTS"""
    # 启用 TTS - 同时 patch 核心配置和 API 模块
    monkeypatch.setattr("app.core.config.settings.SMART_TTS_ENABLED", True)
    monkeypatch.setattr("app.api.tts_user_batch.settings.SMART_TTS_ENABLED", True)
    
    async def _override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_preview_basic_filter_and_limit(db_session: AsyncSession):
    """测试基础筛选和数量限制"""
    # 创建测试数据
    ebook1 = EBook(
        id=1, title="测试作品1", author="作者1", language="zh-CN",
        created_at=datetime.utcnow()
    )
    ebook2 = EBook(
        id=2, title="测试作品2", author="作者2", language="en",
        created_at=datetime.utcnow()
    )
    db_session.add_all([ebook1, ebook2])
    await db_session.commit()
    
    client = TestClient(app)
    response = client.post(
        "/api/tts/batch/preview",
        json={
            "language": "zh-CN",
            "only_without_audiobook": True,
            "only_without_active_job": True,
            "max_candidates": 100
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_candidates"] >= 1
    assert len(data["items"]) >= 1
    # 应该只返回中文作品
    assert all(item["language"] == "zh-CN" for item in data["items"])


@pytest.mark.asyncio
async def test_enqueue_respects_skip_if_has_tts_and_only_without_audiobook(db_session: AsyncSession):
    """测试跳过已有有声书和已有 TTS 有声书的作品"""
    # 创建测试数据
    ebook1 = EBook(id=3, title="无有声书", author="作者A", created_at=datetime.utcnow())
    ebook2 = EBook(id=4, title="有非TTS有声书", author="作者B", created_at=datetime.utcnow())
    ebook3 = EBook(id=5, title="有TTS有声书", author="作者C", created_at=datetime.utcnow())
    
    db_session.add_all([ebook1, ebook2, ebook3])
    await db_session.flush()
    
    # ebook2 有非 TTS 有声书
    audiobook2 = AudiobookFile(
        ebook_id=4, file_path="/test/audiobook2.mp3", format="mp3",
        is_tts_generated=False, is_deleted=False
    )
    # ebook3 有 TTS 有声书
    audiobook3 = AudiobookFile(
        ebook_id=5, file_path="/test/audiobook3.mp3", format="mp3",
        is_tts_generated=True, is_deleted=False
    )
    db_session.add_all([audiobook2, audiobook3])
    await db_session.commit()
    
    client = TestClient(app)
    # 注意：only_without_audiobook=False 才能在 enqueue 阶段测试跳过逻辑
    # 如果设为 True，有有声书的作品在 preview 阶段就会被过滤
    response = client.post(
        "/api/tts/batch/enqueue",
        json={
            "filter": {
                "only_without_audiobook": False,  # 允许有有声书的作品进入 enqueue 阶段
                "only_without_active_job": True,
                "max_candidates": 100
            },
            "max_new_jobs": 10,
            "skip_if_has_tts": True
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    # ebook1 应该被 enqueue
    # ebook2 和 ebook3 已经有有声书，但因为 filter.only_without_audiobook=False，它们会进入 enqueue 阶段
    # 然后因为 skip_if_has_tts=True，ebook3 会被跳过
    assert data["total_candidates"] >= 1
    assert data["enqueued_new_jobs"] >= 1  # ebook1
    assert data["skipped_has_tts"] >= 1  # ebook3 (因为 has_tts_audiobook=True)


@pytest.mark.asyncio
async def test_enqueue_respects_max_new_jobs(db_session: AsyncSession):
    """测试 max_new_jobs 限制"""
    # 创建多个测试作品
    ebooks = [
        EBook(id=10+i, title=f"作品{i}", author="作者", created_at=datetime.utcnow())
        for i in range(5)
    ]
    db_session.add_all(ebooks)
    await db_session.commit()
    
    client = TestClient(app)
    response = client.post(
        "/api/tts/batch/enqueue",
        json={
            "filter": {
                "only_without_audiobook": True,
                "only_without_active_job": True,
                "max_candidates": 100
            },
            "max_new_jobs": 2,
            "skip_if_has_tts": True
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["enqueued_new_jobs"] <= 2


@pytest.mark.asyncio
async def test_enqueue_skips_when_active_job_exists(db_session: AsyncSession):
    """测试当存在活跃 Job 时跳过"""
    ebook = EBook(id=20, title="有活跃Job", author="作者", created_at=datetime.utcnow())
    db_session.add(ebook)
    await db_session.flush()
    
    # 创建活跃 Job
    job = TTSJob(
        ebook_id=20, status="queued", requested_at=datetime.utcnow(),
        processed_chapters=0, created_files_count=0, created_by="test"
    )
    db_session.add(job)
    await db_session.commit()
    
    client = TestClient(app)
    # 注意：only_without_active_job=False 才能在 enqueue 阶段测试活跃 job 跳过逻辑
    # 如果设为 True，有活跃 job 的作品在 preview 阶段就会被过滤
    response = client.post(
        "/api/tts/batch/enqueue",
        json={
            "filter": {
                "only_without_audiobook": True,
                "only_without_active_job": False,  # 允许有活跃 job 的作品进入 enqueue 阶段
                "max_candidates": 100
            },
            "max_new_jobs": 10,
            "skip_if_has_tts": True
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    # ebook id=20 已经有活跃 job，应该被计入 already_had_jobs
    assert data["total_candidates"] >= 1
    assert data["already_had_jobs"] >= 1


@pytest.mark.asyncio
async def test_preview_and_enqueue_require_tts_enabled(db_session: AsyncSession, monkeypatch):
    """测试 TTS 未启用时返回错误"""
    # 临时禁用 TTS
    monkeypatch.setattr("app.api.tts_user_batch.settings.SMART_TTS_ENABLED", False)
    
    client = TestClient(app)
    
    # 测试 preview
    response = client.post(
        "/api/tts/batch/preview",
        json={
            "only_without_audiobook": True,
            "only_without_active_job": True,
            "max_candidates": 100
        }
    )
    assert response.status_code == 400
    assert "disabled" in response.json()["detail"].lower()
    
    # 测试 enqueue
    response = client.post(
        "/api/tts/batch/enqueue",
        json={
            "filter": {
                "only_without_audiobook": True,
                "only_without_active_job": True,
                "max_candidates": 100
            },
            "max_new_jobs": 10,
            "skip_if_has_tts": True
        }
    )
    assert response.status_code == 400
    assert "disabled" in response.json()["detail"].lower()

