"""
TTS Work Profile API 测试
"""

import pytest
from fastapi.testclient import TestClient
from main import app

from app.models.tts_work_profile import TTSWorkProfile
from app.models.ebook import EBook
from app.core.database import Base, engine


@pytest.mark.asyncio
async def test_get_work_profile_dev_only(db_session, monkeypatch):
    """测试获取作品 Profile API（Dev 模式）"""
    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 设置 DEBUG 模式
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    
    # 创建测试 EBook
    ebook = EBook(id=1, title="测试小说", author="测试作者", language="zh-CN")
    db_session.add(ebook)
    
    # 创建 Profile
    profile = TTSWorkProfile(
        ebook_id=1,
        provider="http",
        language="zh-CN",
        voice="zh-CN-female-1",
        enabled=True
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.flush()  # 确保数据已刷新
    
    # 使用 TestClient 调用 API
    # 注意：TestClient 是同步的，但我们的数据库是异步的
    # 由于测试数据库是内存数据库，数据应该已经提交
    client = TestClient(app)
    response = client.get("/api/dev/tts/work-profile/1")
    
    # 验证
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data is not None, "Profile should not be None"
    assert data["ebook_id"] == 1
    assert data["provider"] == "http"
    assert data["voice"] == "zh-CN-female-1"


@pytest.mark.asyncio
async def test_get_work_profile_returns_null_when_not_exists(db_session, monkeypatch):
    """测试当 Profile 不存在时返回 null"""
    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 设置 DEBUG 模式
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    
    # 创建测试 EBook（没有 Profile）
    ebook = EBook(id=2, title="测试小说2", author="测试作者", language="zh-CN")
    db_session.add(ebook)
    await db_session.commit()
    
    # 使用 TestClient 调用 API
    client = TestClient(app)
    response = client.get("/api/dev/tts/work-profile/2")
    
    # 验证：返回 null
    assert response.status_code == 200
    data = response.json()
    assert data is None


@pytest.mark.asyncio
async def test_upsert_work_profile_create_and_update(db_session, monkeypatch):
    """测试创建和更新 Profile"""
    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 设置 DEBUG 模式
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    
    # 创建测试 EBook
    ebook = EBook(id=3, title="测试小说3", author="测试作者", language="zh-CN")
    db_session.add(ebook)
    await db_session.commit()
    
    client = TestClient(app)
    
    # 创建 Profile
    create_response = client.post(
        "/api/dev/tts/work-profile",
        json={
            "ebook_id": 3,
            "provider": "http",
            "language": "zh-CN",
            "voice": "zh-CN-female-1",
            "speed": 1.2,
            "pitch": 0.5,
            "enabled": True,
            "notes": "测试配置"
        }
    )
    
    assert create_response.status_code == 200
    create_data = create_response.json()
    assert create_data["ebook_id"] == 3
    assert create_data["provider"] == "http"
    assert create_data["voice"] == "zh-CN-female-1"
    assert create_data["speed"] == 1.2
    
    # 更新 Profile
    update_response = client.post(
        "/api/dev/tts/work-profile",
        json={
            "ebook_id": 3,
            "provider": "dummy",
            "voice": "zh-CN-male-1",
            "speed": 1.5,
            "enabled": True
        }
    )
    
    assert update_response.status_code == 200
    update_data = update_response.json()
    assert update_data["ebook_id"] == 3
    assert update_data["provider"] == "dummy"  # 已更新
    assert update_data["voice"] == "zh-CN-male-1"  # 已更新
    assert update_data["speed"] == 1.5  # 已更新


@pytest.mark.asyncio
async def test_delete_work_profile(db_session, monkeypatch):
    """测试删除 Profile"""
    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 设置 DEBUG 模式
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    
    # 创建测试 EBook
    ebook = EBook(id=4, title="测试小说4", author="测试作者", language="zh-CN")
    db_session.add(ebook)
    
    # 创建 Profile
    profile = TTSWorkProfile(
        ebook_id=4,
        provider="http",
        enabled=True
    )
    db_session.add(profile)
    await db_session.commit()
    
    client = TestClient(app)
    
    # 删除 Profile
    delete_response = client.delete("/api/dev/tts/work-profile/4")
    
    assert delete_response.status_code == 200
    data = delete_response.json()
    assert data["success"] is True
    
    # 验证已删除
    get_response = client.get("/api/dev/tts/work-profile/4")
    assert get_response.status_code == 200
    assert get_response.json() is None


@pytest.mark.asyncio
async def test_non_debug_cannot_access_api(db_session, monkeypatch):
    """测试非 DEBUG 模式无法访问 API"""
    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 设置 DEBUG 模式为 False
    monkeypatch.setattr("app.core.config.settings.DEBUG", False)
    
    client = TestClient(app)
    
    # 尝试访问 API
    response = client.get("/api/dev/tts/work-profile/1")
    
    # 验证：返回 403
    assert response.status_code == 403
    assert "Dev only" in response.json()["detail"] or "DEBUG" in response.json()["detail"]

