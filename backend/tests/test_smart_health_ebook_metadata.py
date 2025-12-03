"""
测试智能健康检查 API 中的电子书元数据增强状态
"""

import pytest
from fastapi.testclient import TestClient
from app.core.config import settings
from main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


def test_smart_health_ebook_metadata_default_config(client):
    """测试默认配置（enabled=False）"""
    response = client.get("/api/smart/health")
    
    assert response.status_code == 200
    data = response.json()
    
    # 验证响应结构
    assert "features" in data
    assert "ebook_metadata" in data["features"]
    
    ebook_metadata = data["features"]["ebook_metadata"]
    
    # 验证默认配置
    assert ebook_metadata["enabled"] is False
    assert ebook_metadata["status"] == "disabled"
    assert "providers" in ebook_metadata
    assert "timeout_seconds" in ebook_metadata
    assert ebook_metadata["timeout_seconds"] == settings.SMART_EBOOK_METADATA_TIMEOUT
    assert ebook_metadata["last_success_at"] is None
    assert ebook_metadata["last_error"] is None


def test_smart_health_ebook_metadata_enabled_with_providers(monkeypatch, client):
    """测试启用元数据增强并指定 providers"""
    # 临时修改配置
    monkeypatch.setattr(settings, "SMART_EBOOK_METADATA_ENABLED", True)
    monkeypatch.setattr(settings, "SMART_EBOOK_METADATA_PROVIDERS", "dummy,openlibrary")
    monkeypatch.setattr(settings, "SMART_EBOOK_METADATA_TIMEOUT", 3)
    
    # 需要重新导入以获取新的服务实例
    # 但为了简化测试，我们直接检查配置值
    response = client.get("/api/smart/health")
    
    assert response.status_code == 200
    data = response.json()
    
    ebook_metadata = data["features"]["ebook_metadata"]
    
    # 验证配置
    assert ebook_metadata["enabled"] is True
    assert ebook_metadata["status"] in ["ok", "degraded"]  # 取决于 providers 是否成功加载
    assert "dummy" in ebook_metadata["providers"]
    assert "openlibrary" in ebook_metadata["providers"]
    assert ebook_metadata["timeout_seconds"] == 3


def test_smart_health_ebook_metadata_enabled_empty_providers(monkeypatch, client):
    """测试 enabled=True 但 providers 为空的情况"""
    # 临时修改配置
    monkeypatch.setattr(settings, "SMART_EBOOK_METADATA_ENABLED", True)
    monkeypatch.setattr(settings, "SMART_EBOOK_METADATA_PROVIDERS", "")
    
    response = client.get("/api/smart/health")
    
    assert response.status_code == 200
    data = response.json()
    
    ebook_metadata = data["features"]["ebook_metadata"]
    
    # 验证状态为 degraded
    assert ebook_metadata["enabled"] is True
    assert ebook_metadata["status"] == "degraded"
    assert ebook_metadata["providers"] == []
    
    # 整体状态应该为 False（因为配置不完整）
    assert data["ok"] is False


def test_smart_health_ebook_metadata_enabled_single_provider(monkeypatch, client):
    """测试启用单个 provider"""
    # 临时修改配置
    monkeypatch.setattr(settings, "SMART_EBOOK_METADATA_ENABLED", True)
    monkeypatch.setattr(settings, "SMART_EBOOK_METADATA_PROVIDERS", "dummy")
    
    response = client.get("/api/smart/health")
    
    assert response.status_code == 200
    data = response.json()
    
    ebook_metadata = data["features"]["ebook_metadata"]
    
    # 验证配置
    assert ebook_metadata["enabled"] is True
    assert ebook_metadata["status"] in ["ok", "degraded"]  # 取决于 provider 是否成功加载
    assert ebook_metadata["providers"] == ["dummy"]


def test_smart_health_ebook_metadata_structure(client):
    """测试响应结构完整性"""
    response = client.get("/api/smart/health")
    
    assert response.status_code == 200
    data = response.json()
    
    # 验证整体结构
    assert "ok" in data
    assert "features" in data
    
    # 验证 ebook_metadata 结构
    ebook_metadata = data["features"]["ebook_metadata"]
    
    required_fields = [
        "enabled",
        "status",
        "providers",
        "timeout_seconds",
        "last_success_at",
        "last_error"
    ]
    
    for field in required_fields:
        assert field in ebook_metadata, f"缺少字段: {field}"
    
    # 验证 status 的有效值
    assert ebook_metadata["status"] in ["disabled", "ok", "degraded"]
    
    # 验证 providers 是列表
    assert isinstance(ebook_metadata["providers"], list)
    
    # 验证 timeout_seconds 是整数
    assert isinstance(ebook_metadata["timeout_seconds"], int)
    assert ebook_metadata["timeout_seconds"] > 0

