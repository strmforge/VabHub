"""
测试 TTS Storage API
"""

import pytest
from pathlib import Path
from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient

from main import app
from app.core.config import settings
from app.core.database import get_db


@pytest.fixture(autouse=True)
def override_get_db_dependency(db_session):
    """覆盖 get_db 依赖"""
    async def _override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def temp_storage_root(monkeypatch):
    """创建临时存储目录并设置配置"""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        monkeypatch.setattr(settings, "SMART_TTS_OUTPUT_ROOT", str(root))
        monkeypatch.setattr(settings, "DEBUG", True)
        yield root


def test_overview_returns_structure_correctly(temp_storage_root):
    """测试 overview 返回结构正确"""
    # 创建测试文件
    playground_dir = temp_storage_root / "playground"
    playground_dir.mkdir(parents=True)
    (playground_dir / "test.mp3").write_bytes(b"test")
    
    client = TestClient(app)
    response = client.get("/api/dev/tts/storage/overview")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "root" in data
    assert "total_files" in data
    assert "total_size_bytes" in data
    assert "by_category" in data
    assert data["total_files"] >= 1


def test_preview_returns_matched_count_and_sample(temp_storage_root):
    """测试 preview 返回匹配数量和示例"""
    # 创建旧文件
    old_file = temp_storage_root / "old.mp3"
    old_file.write_bytes(b"old data")
    now = datetime.now(timezone.utc)
    old_mtime = now - timedelta(days=10)
    import os
    os.utime(old_file, (old_mtime.timestamp(), old_mtime.timestamp()))
    
    client = TestClient(app)
    response = client.post(
        "/api/dev/tts/storage/preview",
        json={
            "scope": "all",
            "min_age_days": 7,
            "max_files": 100
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "root" in data
    assert "total_matched_files" in data
    assert "total_freed_bytes" in data
    assert "sample" in data
    assert data["total_matched_files"] >= 1


def test_cleanup_dry_run_does_not_delete_files(temp_storage_root):
    """测试 cleanup dry_run 不删除文件"""
    # 创建测试文件
    test_file = temp_storage_root / "test.mp3"
    test_file.write_bytes(b"test")
    
    client = TestClient(app)
    response = client.post(
        "/api/dev/tts/storage/cleanup",
        json={
            "scope": "all",
            "min_age_days": 0,
            "max_files": 100,
            "dry_run": True
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["dry_run"] is True
    # 文件应该还在
    assert test_file.exists()


def test_cleanup_deletes_files_after_execution(temp_storage_root):
    """测试 cleanup 执行后文件数量减少"""
    # 创建测试文件
    file1 = temp_storage_root / "file1.mp3"
    file2 = temp_storage_root / "file2.mp3"
    
    file1.write_bytes(b"data1")
    file2.write_bytes(b"data2")
    
    # 先获取概览
    client = TestClient(app)
    overview_before = client.get("/api/dev/tts/storage/overview").json()
    
    # 执行清理
    response = client.post(
        "/api/dev/tts/storage/cleanup",
        json={
            "scope": "all",
            "min_age_days": 0,
            "max_files": 100,
            "dry_run": False
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["dry_run"] is False
    assert data["deleted_files"] >= 1
    
    # 再次获取概览，文件数应该减少
    overview_after = client.get("/api/dev/tts/storage/overview").json()
    assert overview_after["total_files"] < overview_before["total_files"]


def test_storage_api_requires_debug_mode(monkeypatch):
    """测试存储 API 需要 Debug 模式"""
    monkeypatch.setattr(settings, "DEBUG", False)
    
    client = TestClient(app)
    response = client.get("/api/dev/tts/storage/overview")
    
    assert response.status_code == 403
    assert "Dev-only" in response.json()["detail"]

