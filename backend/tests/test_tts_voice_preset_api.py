"""
TTS Voice Preset API 测试
"""

import pytest
from fastapi.testclient import TestClient
from main import app

from app.models.tts_voice_preset import TTSVoicePreset
from app.models.tts_work_profile import TTSWorkProfile
from app.models.ebook import EBook
from app.core.database import Base, engine


@pytest.mark.asyncio
async def test_list_voice_presets(db_session, monkeypatch):
    """测试获取预设列表"""
    from app.core.database import get_db
    
    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 设置 DEBUG 模式 - 同时打补丁到 API 模块
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    monkeypatch.setattr("app.api.tts_voice_presets.settings.DEBUG", True)
    
    # 创建测试预设
    preset1 = TTSVoicePreset(name="预设1", provider="http", language="zh-CN")
    preset2 = TTSVoicePreset(name="预设2", provider="dummy", language="en-US")
    db_session.add_all([preset1, preset2])
    await db_session.commit()
    
    # 覆盖 get_db 依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        client = TestClient(app)
        response = client.get("/api/dev/tts/voice-presets")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert any(p["name"] == "预设1" for p in data)
        assert any(p["name"] == "预设2" for p in data)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_and_update_voice_preset(db_session, monkeypatch):
    """测试创建和更新预设"""
    from app.core.database import get_db
    
    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 设置 DEBUG 模式 - 同时打补丁到 API 模块
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    monkeypatch.setattr("app.api.tts_voice_presets.settings.DEBUG", True)
    
    # 覆盖 get_db 依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        client = TestClient(app)
        
        # 创建预设
        create_response = client.post(
            "/api/dev/tts/voice-presets",
            json={
                "name": "测试预设",
                "provider": "http",
                "language": "zh-CN",
                "voice": "zh-CN-female-1",
                "speed": 1.2,
                "pitch": 0.5,
                "is_default": False,
                "notes": "测试"
            }
        )
        
        assert create_response.status_code == 200
        create_data = create_response.json()
        assert create_data["name"] == "测试预设"
        assert create_data["voice"] == "zh-CN-female-1"
        preset_id = create_data["id"]
        
        # 更新预设
        update_response = client.post(
            "/api/dev/tts/voice-presets",
            json={
                "id": preset_id,
                "name": "测试预设（已更新）",
                "voice": "zh-CN-male-1",
                "speed": 1.5
            }
        )
        
        assert update_response.status_code == 200
        update_data = update_response.json()
        assert update_data["name"] == "测试预设（已更新）"
        assert update_data["voice"] == "zh-CN-male-1"
        assert update_data["speed"] == 1.5
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_voice_preset(db_session, monkeypatch):
    """测试删除预设"""
    from app.core.database import get_db
    
    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 设置 DEBUG 模式
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    monkeypatch.setattr("app.api.tts_voice_presets.settings.DEBUG", True)
    
    # 创建预设
    preset = TTSVoicePreset(name="待删除预设", provider="http")
    db_session.add(preset)
    
    # 创建 EBook 和引用该预设的 Profile
    ebook = EBook(id=1, title="测试", author="作者", language="zh-CN")
    db_session.add(ebook)
    profile = TTSWorkProfile(ebook_id=1, preset_id=None, enabled=True)
    db_session.add(profile)
    await db_session.commit()
    
    # 更新 Profile 引用预设
    profile.preset_id = preset.id
    await db_session.commit()
    
    # 覆盖 get_db 依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        client = TestClient(app)
        
        # 删除预设
        delete_response = client.delete(f"/api/dev/tts/voice-presets/{preset.id}")
        
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data["success"] is True
        
        # 验证预设已删除
        list_response = client.get("/api/dev/tts/voice-presets")
        assert list_response.status_code == 200
        presets = list_response.json()
        assert not any(p["id"] == preset.id for p in presets)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_default_flag_updates_other_presets(db_session, monkeypatch):
    """测试设置默认预设时，其他预设的 is_default 会被设为 False"""
    from app.core.database import get_db
    
    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 设置 DEBUG 模式
    monkeypatch.setattr("app.core.config.settings.DEBUG", True)
    monkeypatch.setattr("app.api.tts_voice_presets.settings.DEBUG", True)
    
    # 覆盖 get_db 依赖
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        client = TestClient(app)
    
        # 创建第一个默认预设
        preset1_response = client.post(
            "/api/dev/tts/voice-presets",
            json={
                "name": "预设1",
                "is_default": True
            }
        )
        assert preset1_response.status_code == 200
        preset1_id = preset1_response.json()["id"]
        
        # 创建第二个默认预设
        preset2_response = client.post(
            "/api/dev/tts/voice-presets",
            json={
                "name": "预设2",
                "is_default": True
            }
        )
        assert preset2_response.status_code == 200
        preset2_id = preset2_response.json()["id"]
        
        # 验证：只有第二个是默认
        list_response = client.get("/api/dev/tts/voice-presets")
        presets = list_response.json()
        preset1 = next(p for p in presets if p["id"] == preset1_id)
        preset2 = next(p for p in presets if p["id"] == preset2_id)
        assert preset1["is_default"] is False
        assert preset2["is_default"] is True
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_dev_guard_for_voice_preset_api(db_session, monkeypatch):
    """测试非 DEBUG 模式无法访问 API"""
    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 设置 DEBUG 模式为 False - 同时打补丁到 API 模块
    monkeypatch.setattr("app.core.config.settings.DEBUG", False)
    monkeypatch.setattr("app.api.tts_voice_presets.settings.DEBUG", False)
    
    client = TestClient(app)
    
    # 尝试访问 API
    response = client.get("/api/dev/tts/voice-presets")
    
    # 验证：返回 403
    assert response.status_code == 403
    assert "Dev only" in response.json()["detail"] or "DEBUG" in response.json()["detail"]

