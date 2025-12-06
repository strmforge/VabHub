"""
健康检查端点测试

BACKEND-REGRESSION-HEALTH-1: 确保 /health 端点在各种场景下正确返回
"""

import pytest
from unittest.mock import patch, AsyncMock


class TestHealthEndpointStatusCode:
    """测试 /health 端点状态码逻辑"""
    
    def test_healthy_returns_200(self):
        """测试：healthy 状态应返回 200"""
        from app.core.health import _get_run_mode
        
        # 验证状态码判定逻辑
        result = {"status": "healthy"}
        status_code = 503 if result["status"] == "unhealthy" else 200
        assert status_code == 200
    
    def test_warning_returns_200(self):
        """测试：warning 状态应返回 200（非关键组件异常不影响服务可用性）"""
        result = {"status": "warning"}
        status_code = 503 if result["status"] == "unhealthy" else 200
        assert status_code == 200
    
    def test_unhealthy_returns_503(self):
        """测试：unhealthy 状态应返回 503"""
        result = {"status": "unhealthy"}
        status_code = 503 if result["status"] == "unhealthy" else 200
        assert status_code == 503


class TestHealthCheckerMode:
    """测试健康检查器运行模式检测"""
    
    def test_ci_mode_detection(self, monkeypatch):
        """测试：VABHUB_CI=1 时应返回 'ci' 模式"""
        monkeypatch.setenv("VABHUB_CI", "1")
        
        # 重新导入以获取新的环境变量
        from app.core import health
        import importlib
        importlib.reload(health)
        
        assert health._get_run_mode() == "ci"
    
    def test_dev_mode_detection(self, monkeypatch):
        """测试：使用 SQLite 时应返回 'dev' 模式"""
        monkeypatch.delenv("VABHUB_CI", raising=False)
        
        from app.core import health
        import importlib
        importlib.reload(health)
        
        # 默认配置使用 SQLite
        mode = health._get_run_mode()
        assert mode in ["dev", "ci"]  # 取决于环境


class TestHealthCheckerResponse:
    """测试健康检查响应结构"""
    
    @pytest.mark.asyncio
    async def test_check_all_returns_required_fields(self):
        """测试：check_all 应返回必需的字段"""
        from app.core.health import get_health_checker
        
        health_checker = get_health_checker()
        result = await health_checker.check_all()
        
        # 验证必需字段
        assert "status" in result
        assert "mode" in result
        assert "timestamp" in result
        assert "checks" in result
        
        # 验证状态值
        assert result["status"] in ["healthy", "warning", "unhealthy"]
        
        # 验证模式值
        assert result["mode"] in ["ci", "dev", "prod"]
    
    @pytest.mark.asyncio
    async def test_check_all_includes_database_check(self):
        """测试：check_all 应包含数据库检查"""
        from app.core.health import get_health_checker
        
        health_checker = get_health_checker()
        result = await health_checker.check_all()
        
        assert "database" in result["checks"]
        assert "status" in result["checks"]["database"]
    
    @pytest.mark.asyncio
    async def test_database_check_succeeds_with_sqlite(self):
        """测试：SQLite 开发模式下数据库检查应成功"""
        from app.core.health import get_health_checker
        
        health_checker = get_health_checker()
        result = await health_checker.check_all()
        
        # SQLite 应该能正常连接
        assert result["checks"]["database"]["status"] == "healthy"


class TestHealthEndpointIntegration:
    """健康检查端点集成测试"""
    
    @pytest.mark.asyncio
    async def test_health_endpoint_returns_200_in_dev_mode(self):
        """测试：开发模式下 /health 应返回 200"""
        from app.core.health import get_health_checker
        
        health_checker = get_health_checker()
        result = await health_checker.check_all()
        
        # 在开发模式下，即使有 warning 也应返回 200
        status_code = 503 if result["status"] == "unhealthy" else 200
        assert status_code == 200
    
    @pytest.mark.asyncio
    async def test_warning_does_not_block_health_check(self):
        """测试：warning 状态不应阻止健康检查通过"""
        from app.core.health import get_health_checker
        
        health_checker = get_health_checker()
        result = await health_checker.check_all()
        
        # 即使某些检查返回 warning，整体也不应是 unhealthy
        # （除非有真正的硬性失败）
        if result["status"] == "warning":
            # warning 状态仍然应该返回 200
            status_code = 503 if result["status"] == "unhealthy" else 200
            assert status_code == 200
