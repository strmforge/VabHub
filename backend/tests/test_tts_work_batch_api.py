"""
TTS Work Batch API 测试
"""

import pytest
from fastapi.testclient import TestClient
from main import app

from app.models.ebook import EBook
from app.models.tts_work_profile import TTSWorkProfile
from app.models.tts_voice_preset import TTSVoicePreset
from app.core.database import Base, engine


@pytest.mark.asyncio
async def test_preview_filters_by_language_and_author(db_session, monkeypatch):
    """测试预览按语言和作者筛选"""
    from app.core.database import get_db
    
    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 设置 DEBUG 模式 - 同时打补丁到 API 模块
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    monkeypatch.setattr("app.api.tts_work_batch.settings.DEBUG", True)
    
    # 创建测试数据
    ebook1 = EBook(id=1, title="测试书1", author="作者A", language="zh-CN")
    ebook2 = EBook(id=2, title="测试书2", author="作者B", language="en-US")
    ebook3 = EBook(id=3, title="测试书3", author="作者A", language="zh-CN")
    db_session.add_all([ebook1, ebook2, ebook3])
    await db_session.commit()
    
    # 覆盖 get_db 依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        client = TestClient(app)
        
        # 测试按语言筛选
        response = client.post(
            "/api/dev/tts/work-batch/preview",
            json={"language": "zh-CN"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(item["language"] == "zh-CN" for item in data["items"])
        
        # 测试按作者筛选
        response = client.post(
            "/api/dev/tts/work-batch/preview",
            json={"author_substring": "作者A"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all("作者A" in (item["author"] or "") for item in data["items"])
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_preview_includes_profile_and_preset_info(db_session, monkeypatch):
    """测试预览包含 Profile 和 Preset 信息"""
    from app.core.database import get_db
    
    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 设置 DEBUG 模式 - 同时打补丁到 API 模块
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    monkeypatch.setattr("app.api.tts_work_batch.settings.DEBUG", True)
    
    # 创建测试数据
    preset = TTSVoicePreset(name="测试预设", provider="http", language="zh-CN")
    db_session.add(preset)
    await db_session.flush()
    
    ebook = EBook(id=1, title="测试书", author="作者", language="zh-CN")
    db_session.add(ebook)
    await db_session.flush()
    
    profile = TTSWorkProfile(ebook_id=1, preset_id=preset.id, enabled=True)
    db_session.add(profile)
    await db_session.commit()
    
    # 覆盖 get_db 依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        client = TestClient(app)
        response = client.post(
            "/api/dev/tts/work-batch/preview",
            json={}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        
        item = next((item for item in data["items"] if item["ebook_id"] == 1), None)
        assert item is not None
        assert item["has_profile"] is True
        assert item["profile_enabled"] is True
        assert item["profile_preset_id"] == preset.id
        assert item["profile_preset_name"] == "测试预设"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_apply_creates_profiles_for_ebooks_without_profile(db_session, monkeypatch):
    """测试应用为没有 Profile 的作品创建 Profile"""
    from app.core.database import get_db
    
    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 设置 DEBUG 模式 - 同时打补丁到 API 模块
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    monkeypatch.setattr("app.api.tts_work_batch.settings.DEBUG", True)
    
    # 创建测试数据
    preset = TTSVoicePreset(name="测试预设", provider="http")
    db_session.add(preset)
    await db_session.flush()
    
    ebook = EBook(id=1, title="测试书", author="作者", language="zh-CN")
    db_session.add(ebook)
    await db_session.commit()
    
    # 覆盖 get_db 依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        client = TestClient(app)
        
        # 应用预设
        response = client.post(
            "/api/dev/tts/work-batch/apply",
            json={
                "preset_id": preset.id,
                "filter": {},
                "override_existing": False,
                "enable_profile": True,
                "dry_run": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["matched_ebooks"] >= 1
        assert data["created_profiles"] >= 1
        
        # 验证 Profile 确实被创建
        from sqlalchemy import select
        profile_result = await db_session.execute(
            select(TTSWorkProfile)
            .where(TTSWorkProfile.ebook_id == 1)
        )
        profile = profile_result.scalar_one_or_none()
        assert profile is not None
        assert profile.preset_id == preset.id
        assert profile.enabled is True
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_apply_skips_existing_when_override_false(db_session, monkeypatch):
    """测试 override_existing=False 时跳过已有 Profile"""
    from app.core.database import get_db
    
    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 设置 DEBUG 模式 - 同时打补丁到 API 模块
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    monkeypatch.setattr("app.api.tts_work_batch.settings.DEBUG", True)
    
    # 创建测试数据
    preset1 = TTSVoicePreset(name="预设1", provider="http")
    preset2 = TTSVoicePreset(name="预设2", provider="dummy")
    db_session.add_all([preset1, preset2])
    await db_session.flush()
    
    ebook = EBook(id=1, title="测试书", author="作者", language="zh-CN")
    db_session.add(ebook)
    await db_session.flush()
    
    # 已有 Profile，使用 preset1
    profile = TTSWorkProfile(ebook_id=1, preset_id=preset1.id, enabled=True)
    db_session.add(profile)
    await db_session.commit()
    
    # 覆盖 get_db 依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        client = TestClient(app)
        
        # 尝试应用 preset2，但 override_existing=False
        response = client.post(
            "/api/dev/tts/work-batch/apply",
            json={
                "preset_id": preset2.id,
                "filter": {},
                "override_existing": False,
                "enable_profile": True,
                "dry_run": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["skipped_existing_profile"] >= 1
        
        # 验证 Profile 的 preset_id 没有被改变
        await db_session.refresh(profile)
        assert profile.preset_id == preset1.id  # 仍然是 preset1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_apply_updates_existing_when_override_true(db_session, monkeypatch):
    """测试 override_existing=True 时更新已有 Profile"""
    from app.core.database import get_db
    
    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 设置 DEBUG 模式 - 同时打补丁到 API 模块
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    monkeypatch.setattr("app.api.tts_work_batch.settings.DEBUG", True)
    
    # 创建测试数据
    preset1 = TTSVoicePreset(name="预设1", provider="http")
    preset2 = TTSVoicePreset(name="预设2", provider="dummy")
    db_session.add_all([preset1, preset2])
    await db_session.flush()
    
    ebook = EBook(id=1, title="测试书", author="作者", language="zh-CN")
    db_session.add(ebook)
    await db_session.flush()
    
    # 已有 Profile，使用 preset1
    profile = TTSWorkProfile(ebook_id=1, preset_id=preset1.id, enabled=True)
    db_session.add(profile)
    await db_session.commit()
    
    # 覆盖 get_db 依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        client = TestClient(app)
        
        # 应用 preset2，override_existing=True
        response = client.post(
            "/api/dev/tts/work-batch/apply",
            json={
                "preset_id": preset2.id,
                "filter": {},
                "override_existing": True,
                "enable_profile": False,  # 同时测试 enabled 更新
                "dry_run": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["updated_profiles"] >= 1
        
        # 验证 Profile 的 preset_id 和 enabled 被更新
        await db_session.refresh(profile)
        assert profile.preset_id == preset2.id  # 已更新为 preset2
        assert profile.enabled is False  # 已更新为 False
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_dev_guard_blocks_when_debug_false(db_session, monkeypatch):
    """测试非 DEBUG 模式无法访问 API"""
    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 设置 DEBUG 模式为 False - 同时打补丁到 API 模块
    monkeypatch.setattr("app.core.config.settings.DEBUG", False)
    monkeypatch.setattr("app.api.tts_work_batch.settings.DEBUG", False)
    
    client = TestClient(app)
    
    # 尝试访问预览接口
    response = client.post(
        "/api/dev/tts/work-batch/preview",
        json={}
    )
    
    # 验证：返回 403
    assert response.status_code == 403
    assert "DEBUG" in response.json()["detail"] or "Dev only" in response.json()["detail"]
    
    # 尝试访问应用接口
    response = client.post(
        "/api/dev/tts/work-batch/apply",
        json={
            "preset_id": 1,
            "filter": {},
            "override_existing": False,
            "enable_profile": True
        }
    )
    
    # 验证：返回 403
    assert response.status_code == 403

