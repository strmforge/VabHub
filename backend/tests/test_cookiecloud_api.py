"""
CookieCloud API端点测试
"""
import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from datetime import datetime

from main import app
from app.core.database import get_db
from app.models.user import User
from app.models.cookiecloud import CookieCloudSettings


class TestCookieCloudAPI:
    """CookieCloud API测试类"""

    @pytest.fixture
    def mock_current_user(self):
        """Mock当前用户"""
        user = User(
            id=1,
            username="test_user",
            email="test@example.com",
            is_active=True
        )
        return user

    @pytest.fixture
    async def override_dependencies(self, db_session, mock_current_user):
        """覆盖依赖项"""
        async def override_get_db():
            yield db_session
        
        async def override_get_current_user():
            return mock_current_user
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Import get_current_user dependency
        from app.api.auth import get_current_user
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        yield
        
        app.dependency_overrides.clear()

    def test_get_settings_success(self, override_dependencies, test_cookiecloud_settings):
        """测试获取设置成功"""
        client = TestClient(app)
        response = client.get("/api/cookiecloud/settings")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["enabled"] is True
        assert data["data"]["host"] == "https://test.cookiecloud.com"
        assert data["data"]["uuid"] == "12345678-1234-1234-1234-123456789abc"
        assert data["data"]["password"] == "***"  # 密码应该被脱敏

    def test_get_settings_not_found(self, override_dependencies):
        """测试获取设置不存在"""
        client = TestClient(app)
        response = client.get("/api/cookiecloud/settings")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] is None

    def test_update_settings_success(self, override_dependencies, test_cookiecloud_settings):
        """测试更新设置成功"""
        client = TestClient(app)
        update_data = {
            "enabled": True,
            "host": "https://updated.cookiecloud.com",
            "uuid": "87654321-4321-4321-4321-cba987654321",
            "password": "new_password",
            "sync_interval_minutes": 30,
            "safe_host_whitelist": ["new.example.com"]
        }
        
        with patch('app.core.scheduler.get_scheduler') as mock_scheduler:
            mock_scheduler_instance = AsyncMock()
            mock_scheduler.return_value = mock_scheduler_instance
            
            response = client.put("/api/cookiecloud/settings", json=update_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["host"] == "https://updated.cookiecloud.com"
            assert data["data"]["sync_interval_minutes"] == 30
            
            # 验证调度器被调用
            mock_scheduler_instance.update_cookiecloud_sync_job.assert_called_once()

    def test_update_settings_with_masked_password(self, override_dependencies, test_cookiecloud_settings):
        """测试使用脱敏密码更新设置"""
        client = TestClient(app)
        update_data = {
            "enabled": True,
            "sync_interval_minutes": 45,
            "password": "***"  # 脱敏密码，应该保持原密码不变
        }
        
        with patch('app.core.scheduler.get_scheduler') as mock_scheduler:
            mock_scheduler_instance = AsyncMock()
            mock_scheduler.return_value = mock_scheduler_instance
            
            response = client.put("/api/cookiecloud/settings", json=update_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["sync_interval_minutes"] == 45

    def test_update_settings_create_new(self, override_dependencies):
        """测试创建新设置"""
        client = TestClient(app)
        create_data = {
            "enabled": True,
            "host": "https://new.cookiecloud.com",
            "uuid": "new-uuid-here",
            "password": "new_password",
            "sync_interval_minutes": 60,
            "safe_host_whitelist": ["example.com"]
        }
        
        with patch('app.core.scheduler.get_scheduler') as mock_scheduler:
            mock_scheduler_instance = AsyncMock()
            mock_scheduler.return_value = mock_scheduler_instance
            
            response = client.put("/api/cookiecloud/settings", json=create_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["host"] == "https://new.cookiecloud.com"
            
            # 验证调度器被调用
            mock_scheduler_instance.update_cookiecloud_sync_job.assert_called_once()

    def test_update_settings_disable_scheduler(self, override_dependencies, test_cookiecloud_settings):
        """测试禁用设置时移除调度器任务"""
        client = TestClient(app)
        update_data = {
            "enabled": False,
            "sync_interval_minutes": 60
        }
        
        with patch('app.core.scheduler.get_scheduler') as mock_scheduler:
            mock_scheduler_instance = AsyncMock()
            mock_scheduler.return_value = mock_scheduler_instance
            
            response = client.put("/api/cookiecloud/settings", json=update_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["enabled"] is False
            
            # 验证调度器任务被移除
            mock_scheduler_instance.remove_cookiecloud_sync_job.assert_called_once()

    def test_trigger_sync_success(self, override_dependencies, test_cookiecloud_settings, test_cookiecloud_sites):
        """测试触发同步成功"""
        client = TestClient(app)
        
        with patch('app.modules.cookiecloud.service.check_rate_limit', return_value=True):
            with patch('app.modules.cookiecloud.service.CookieCloudSyncService') as mock_service:
                mock_instance = AsyncMock()
                mock_service.return_value = mock_instance
                mock_instance._get_settings.return_value = test_cookiecloud_settings
                
                response = client.post("/api/cookiecloud/sync")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "同步任务已启动" in data["message"]

    def test_trigger_sync_rate_limited(self, override_dependencies, test_cookiecloud_settings):
        """测试触发同步被速率限制"""
        client = TestClient(app)
        
        with patch('app.modules.cookiecloud.service.check_rate_limit', return_value=False):
            response = client.post("/api/cookiecloud/sync")
            
            assert response.status_code == 429
            data = response.json()
            assert "过于频繁" in data["detail"]

    def test_trigger_sync_not_enabled(self, override_dependencies):
        """测试触发同步未启用"""
        client = TestClient(app)
        
        with patch('app.modules.cookiecloud.service.check_rate_limit', return_value=True):
            response = client.post("/api/cookiecloud/sync")
            
            assert response.status_code == 400
            data = response.json()
            assert "未启用" in data["detail"]

    def test_trigger_sync_immediate_success(self, override_dependencies, test_cookiecloud_settings, test_cookiecloud_sites):
        """测试立即同步成功"""
        client = TestClient(app)
        
        mock_result = AsyncMock()
        mock_result.success = True
        mock_result.total_sites = 2
        mock_result.synced_sites = 2
        mock_result.unmatched_sites = 0
        mock_result.error_sites = 0
        mock_result.errors = []
        
        with patch('app.modules.cookiecloud.service.CookieCloudSyncService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            mock_instance.sync_all_sites.return_value = mock_result
            
            response = client.post("/api/cookiecloud/sync-immediate")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["success"] is True
            assert data["data"]["total_sites"] == 2

    def test_trigger_site_sync_success(self, override_dependencies, test_cookiecloud_settings, test_cookiecloud_sites):
        """测试单站点同步成功"""
        client = TestClient(app)
        site = test_cookiecloud_sites[0]
        
        mock_result = AsyncMock()
        mock_result.success = True
        mock_result.site_id = site.id
        mock_result.site_name = site.name
        mock_result.cookie_updated = True
        mock_result.error_message = None
        
        with patch('app.modules.cookiecloud.service.CookieCloudSyncService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            mock_instance.sync_site.return_value = mock_result
            
            response = client.post(f"/api/cookiecloud/sync-site/{site.id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["site_id"] == site.id
            assert data["data"]["success"] is True

    def test_trigger_site_sync_not_found(self, override_dependencies, test_cookiecloud_settings):
        """测试单站点同步不存在"""
        client = TestClient(app)
        
        response = client.post("/api/cookiecloud/sync-site/999")
        
        assert response.status_code == 404
        data = response.json()
        assert "不存在" in data["detail"]

    def test_test_connection_success(self, override_dependencies, test_cookiecloud_settings):
        """测试连接成功"""
        client = TestClient(app)
        
        with patch('app.modules.cookiecloud.service.CookieCloudSyncService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            mock_instance.test_connection.return_value = True
            
            response = client.post("/api/cookiecloud/test-connection")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["success"] is True
            assert data["data"]["message"] == "连接成功"

    def test_test_connection_failure(self, override_dependencies, test_cookiecloud_settings):
        """测试连接失败"""
        client = TestClient(app)
        
        with patch('app.modules.cookiecloud.service.CookieCloudSyncService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            mock_instance.test_connection.return_value = False
            
            response = client.post("/api/cookiecloud/test-connection")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["success"] is False
            assert data["data"]["message"] == "连接失败"

    def test_test_connection_no_settings(self, override_dependencies):
        """测试连接无设置"""
        client = TestClient(app)
        
        response = client.post("/api/cookiecloud/test-connection")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["success"] is False
        assert "连接测试异常" in data["data"]["message"]

    def test_get_status_success(self, override_dependencies, test_cookiecloud_settings, test_cookiecloud_sites):
        """测试获取状态成功"""
        client = TestClient(app)
        
        response = client.get("/api/cookiecloud/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["enabled"] is True
        assert data["data"]["configured"] is True
        assert data["data"]["total_sites"] == 4  # 总站点数
        assert data["data"]["cookiecloud_sites"] == 2  # CookieCloud站点数
        assert data["data"]["sync_interval_minutes"] == 60

    def test_get_status_no_settings(self, override_dependencies):
        """测试获取状态无设置"""
        client = TestClient(app)
        
        response = client.get("/api/cookiecloud/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["enabled"] is False
        assert data["data"]["configured"] is False
        assert data["data"]["total_sites"] == 0

    @pytest.mark.asyncio
    async def test_get_sync_history_success(self, override_dependencies, test_cookiecloud_settings, db_session):
        """测试获取同步历史成功"""
        client = TestClient(app)
        
        # 设置一些历史数据
        test_cookiecloud_settings.last_sync_at = datetime.utcnow()
        test_cookiecloud_settings.last_status = "SUCCESS"
        test_cookiecloud_settings.last_error = None
        await db_session.commit()
        
        response = client.get("/api/cookiecloud/sync-history?page=1&size=10")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert "page" in data["data"]
        assert "size" in data["data"]

    def test_get_sync_history_pagination(self, override_dependencies, test_cookiecloud_settings):
        """测试同步历史分页"""
        client = TestClient(app)
        
        response = client.get("/api/cookiecloud/sync-history?page=2&size=5")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["page"] == 2
        assert data["data"]["size"] == 5

    def test_unauthorized_access(self):
        """测试未授权访问"""
        client = TestClient(app)
        
        # 不覆盖依赖项，应该返回401
        response = client.get("/api/cookiecloud/settings")
        
        assert response.status_code == 401

    def test_invalid_json_request(self, override_dependencies):
        """测试无效JSON请求"""
        client = TestClient(app)
        
        response = client.put(
            "/api/cookiecloud/settings",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422

    def test_invalid_sync_interval(self, override_dependencies, test_cookiecloud_settings):
        """测试无效同步间隔"""
        client = TestClient(app)
        update_data = {
            "enabled": True,
            "sync_interval_minutes": 1  # 小于最小值5
        }
        
        response = client.put("/api/cookiecloud/settings", json=update_data)
        
        # 应该有验证错误
        assert response.status_code in [400, 422]

    def test_empty_host_url(self, override_dependencies, test_cookiecloud_settings):
        """测试空主机地址"""
        client = TestClient(app)
        update_data = {
            "enabled": True,
            "host": "",
            "uuid": "test-uuid",
            "password": "test-password"
        }
        
        response = client.put("/api/cookiecloud/settings", json=update_data)
        
        # 应该有验证错误
        assert response.status_code in [400, 422]

    def test_scheduler_error_handling(self, override_dependencies, test_cookiecloud_settings):
        """测试调度器错误处理"""
        client = TestClient(app)
        update_data = {
            "enabled": True,
            "sync_interval_minutes": 60
        }
        
        with patch('app.core.scheduler.get_scheduler') as mock_scheduler:
            mock_scheduler.side_effect = Exception("Scheduler error")
            
            response = client.put("/api/cookiecloud/settings", json=update_data)
            
            # 即使调度器出错，设置更新仍应成功
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
