"""
CookieCloud同步服务单元测试
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from sqlalchemy import select

from app.modules.cookiecloud.service import CookieCloudSyncService
from app.models.cookiecloud import CookieCloudSettings
from app.models.site import Site
from app.schemas.cookiecloud import (
    CookieCloudSyncResult,
    CookieCloudSiteSyncResult,
    CookieCloudTestResult
)


class TestCookieCloudSyncService:
    """CookieCloud同步服务测试类"""

    @pytest.mark.asyncio
    async def test_get_settings_success(self, db_session, test_cookiecloud_settings):
        """测试获取设置成功"""
        service = CookieCloudSyncService(db_session)
        settings = await service._get_settings()
        
        assert settings is not None
        assert settings.enabled is True
        assert settings.host == "https://test.cookiecloud.com"
        assert settings.uuid == "12345678-1234-1234-1234-123456789abc"
        assert settings.password == "test_password"

    @pytest.mark.asyncio
    async def test_get_settings_not_found(self, db_session):
        """测试获取设置不存在"""
        service = CookieCloudSyncService(db_session)
        settings = await service._get_settings()
        
        assert settings is None

    @pytest.mark.asyncio
    async def test_test_connection_success(self, db_session, test_cookiecloud_settings, mock_cookiecloud_client):
        """测试连接成功"""
        service = CookieCloudSyncService(db_session)
        
        with patch('app.modules.cookiecloud.service.CookieCloudClient', return_value=mock_cookiecloud_client):
            result = await service.test_connection()
            
            assert result is True

    @pytest.mark.asyncio
    async def test_test_connection_no_settings(self, db_session):
        """测试连接无设置"""
        service = CookieCloudSyncService(db_session)
        
        result = await service.test_connection()
        
        assert result is False

    @pytest.mark.asyncio
    async def test_test_connection_client_error(self, db_session, test_cookiecloud_settings):
        """测试连接客户端错误"""
        service = CookieCloudSyncService(db_session)
        mock_client = AsyncMock()
        mock_client.get_cookies.side_effect = Exception("Connection failed")
        
        with patch('app.modules.cookiecloud.service.CookieCloudClient', return_value=mock_client):
            result = await service.test_connection()
            
            assert result is False

    @pytest.mark.asyncio
    async def test_sync_site_success(self, db_session, test_cookiecloud_settings, test_cookiecloud_sites, mock_cookiecloud_client):
        """测试单站点同步成功"""
        service = CookieCloudSyncService(db_session)
        site = test_cookiecloud_sites[0]  # CookieCloud Site 1
        
        with patch('app.modules.cookiecloud.service.CookieCloudClient', return_value=mock_cookiecloud_client):
            result = await service.sync_site(site.id)
            
            assert result.success is True
            assert result.site_id == site.id
            assert result.site_name == site.name
            assert result.cookie_updated is True
            assert result.error_message is None

    @pytest.mark.asyncio
    async def test_sync_site_not_found(self, db_session, test_cookiecloud_settings):
        """测试同步站点不存在"""
        service = CookieCloudSyncService(db_session)
        
        result = await service.sync_site(999)
        
        assert result.success is False
        assert result.error_message == "站点不存在"

    @pytest.mark.asyncio
    async def test_sync_site_disabled(self, db_session, test_cookiecloud_settings, test_cookiecloud_sites):
        """测试同步已禁用站点"""
        service = CookieCloudSyncService(db_session)
        disabled_site = test_cookiecloud_sites[3]  # Disabled Site
        
        result = await service.sync_site(disabled_site.id)
        
        assert result.success is False
        assert "已禁用" in result.error_message

    @pytest.mark.asyncio
    async def test_sync_site_not_cookiecloud_source(self, db_session, test_cookiecloud_settings, test_cookiecloud_sites):
        """测试同步非CookieCloud源站点"""
        service = CookieCloudSyncService(db_session)
        manual_site = test_cookiecloud_sites[2]  # Manual Site
        
        result = await service.sync_site(manual_site.id)
        
        assert result.success is False
        assert "不是CookieCloud源" in result.error_message

    @pytest.mark.asyncio
    async def test_sync_site_domain_not_in_whitelist(self, db_session, test_cookiecloud_settings, test_cookiecloud_sites, mock_cookiecloud_client):
        """测试同步域名不在白名单中"""
        service = CookieCloudSyncService(db_session)
        
        # 修改设置的白名单，排除测试域名
        test_cookiecloud_settings.safe_host_whitelist = '["other.example.com"]'
        await db_session.commit()
        
        site = test_cookiecloud_sites[0]  # CookieCloud Site 1
        
        with patch('app.modules.cookiecloud.service.CookieCloudClient', return_value=mock_cookiecloud_client):
            result = await service.sync_site(site.id)
            
            assert result.success is False
            assert "不在安全域名白名单中" in result.error_message

    @pytest.mark.asyncio
    async def test_sync_site_no_cookie_data(self, db_session, test_cookiecloud_settings, test_cookiecloud_sites):
        """测试同步无Cookie数据"""
        service = CookieCloudSyncService(db_session)
        site = test_cookiecloud_sites[0]
        
        # Mock客户端返回空数据
        mock_client = AsyncMock()
        mock_client.get_cookies.return_value = {}
        
        with patch('app.modules.cookiecloud.service.CookieCloudClient', return_value=mock_client):
            result = await service.sync_site(site.id)
            
            assert result.success is False
            assert "未找到Cookie数据" in result.error_message

    @pytest.mark.asyncio
    async def test_sync_all_sites_success(self, db_session, test_cookiecloud_settings, test_cookiecloud_sites, mock_cookiecloud_client):
        """测试批量同步所有站点成功"""
        service = CookieCloudSyncService(db_session)
        
        with patch('app.modules.cookiecloud.service.CookieCloudClient', return_value=mock_cookiecloud_client):
            result = await service.sync_all_sites(batch_size=10, site_timeout=30)
            
            assert result.success is True
            assert result.total_sites == 2  # 只有2个启用的CookieCloud站点
            assert result.synced_sites == 2
            assert result.unmatched_sites == 0
            assert result.error_sites == 0
            assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_sync_all_sites_partial_failure(self, db_session, test_cookiecloud_settings, test_cookiecloud_sites):
        """测试批量同步部分失败"""
        service = CookieCloudSyncService(db_session)
        
        # Mock客户端部分失败
        mock_client = AsyncMock()
        mock_client.get_cookies.side_effect = [
            {"tracker.example.com": {"cookie_data": [{"name": "test", "value": "value"}]}},
            Exception("Network error")
        ]
        
        with patch('app.modules.cookiecloud.service.CookieCloudClient', return_value=mock_client):
            result = await service.sync_all_sites(batch_size=10, site_timeout=30)
            
            assert result.success is False  # 有错误，整体返回失败
            assert result.total_sites == 2
            assert result.synced_sites == 1
            assert result.error_sites == 1
            assert len(result.errors) == 1

    @pytest.mark.asyncio
    async def test_sync_all_sites_no_settings(self, db_session, test_cookiecloud_sites):
        """测试批量同步无设置"""
        service = CookieCloudSyncService(db_session)
        
        result = await service.sync_all_sites(batch_size=10, site_timeout=30)
        
        assert result.success is False
        assert "未配置" in result.errors[0]

    @pytest.mark.asyncio
    async def test_sync_all_sites_disabled(self, db_session, test_cookiecloud_settings, test_cookiecloud_sites):
        """测试批量同步已禁用"""
        # 禁用CookieCloud设置
        test_cookiecloud_settings.enabled = False
        await db_session.commit()
        
        service = CookieCloudSyncService(db_session)
        
        result = await service.sync_all_sites(batch_size=10, site_timeout=30)
        
        assert result.success is False
        assert "已禁用" in result.errors[0]

    @pytest.mark.asyncio
    async def test_update_sync_status_success(self, db_session, test_cookiecloud_settings):
        """测试更新同步状态成功"""
        service = CookieCloudSyncService(db_session)
        
        await service._update_sync_status(
            status="SUCCESS",
            error=None,
            sync_at=datetime.utcnow()
        )
        
        # 刷新设置
        await db_session.refresh(test_cookiecloud_settings)
        
        assert test_cookiecloud_settings.last_status == "SUCCESS"
        assert test_cookiecloud_settings.last_error is None
        assert test_cookiecloud_settings.last_sync_at is not None

    @pytest.mark.asyncio
    async def test_update_sync_status_with_error(self, db_session, test_cookiecloud_settings):
        """测试更新同步状态带错误"""
        service = CookieCloudSyncService(db_session)
        error_msg = "Test error message"
        
        await service._update_sync_status(
            status="FAILED",
            error=error_msg,
            sync_at=datetime.utcnow()
        )
        
        # 刷新设置
        await db_session.refresh(test_cookiecloud_settings)
        
        assert test_cookiecloud_settings.last_status == "FAILED"
        assert test_cookiecloud_settings.last_error == error_msg

    @pytest.mark.asyncio
    async def test_format_cookie_string(self, db_session):
        """测试Cookie字符串格式化"""
        service = CookieCloudSyncService(db_session)
        
        cookie_data = [
            {"name": "session", "value": "abc123", "domain": "example.com"},
            {"name": "auth", "value": "token456", "domain": "example.com"},
            {"name": "pref", "value": "dark", "domain": "example.com"}
        ]
        
        cookie_string = service._format_cookie_string(cookie_data)
        
        assert "session=abc123" in cookie_string
        assert "auth=token456" in cookie_string
        assert "pref=dark" in cookie_string
        # 检查格式：name=value; name=value; name=value
        assert cookie_string.count(";") == 2

    @pytest.mark.asyncio
    async def test_is_domain_in_whitelist_exact_match(self, db_session, test_cookiecloud_settings):
        """测试域名白名单精确匹配"""
        service = CookieCloudSyncService(db_session)
        
        result = service._is_domain_in_whitelist("tracker.example.com")
        assert result is True

    @pytest.mark.asyncio
    async def test_is_domain_in_whitelist_wildcard_match(self, db_session):
        """测试域名白名单通配符匹配"""
        # 创建带通配符的设置
        settings = CookieCloudSettings(
            enabled=True,
            host="https://test.cookiecloud.com",
            uuid="12345678-1234-1234-1234-123456789abc",
            password="test_password",
            sync_interval_minutes=60,
            safe_host_whitelist='["*.example.com"]',
            last_status="NEVER",
            last_error=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(settings)
        await db_session.commit()
        
        service = CookieCloudSyncService(db_session)
        
        result = service._is_domain_in_whitelist("tracker.example.com")
        assert result is True
        
        result = service._is_domain_in_whitelist("pt.example.com")
        assert result is True
        
        result = service._is_domain_in_whitelist("other.com")
        assert result is False

    @pytest.mark.asyncio
    async def test_is_domain_in_whitelist_empty_list(self, db_session, test_cookiecloud_settings):
        """测试空白名单域名检查"""
        # 设置空白名单
        test_cookiecloud_settings.safe_host_whitelist = "[]"
        await db_session.commit()
        
        service = CookieCloudSyncService(db_session)
        
        result = service._is_domain_in_whitelist("any.domain.com")
        assert result is False

    @pytest.mark.asyncio
    async def test_extract_domain_from_url(self, db_session):
        """测试从URL提取域名"""
        service = CookieCloudSyncService(db_session)
        
        # 测试各种URL格式
        test_cases = [
            ("https://tracker.example.com", "tracker.example.com"),
            ("http://pt.example.org", "pt.example.org"),
            ("https://sub.domain.example.com/path", "sub.domain.example.com"),
            ("https://example.com:8080", "example.com"),
        ]
        
        for url, expected_domain in test_cases:
            domain = service._extract_domain_from_url(url)
            assert domain == expected_domain

    @pytest.mark.asyncio
    async def test_extract_domain_from_url_invalid(self, db_session):
        """测试无效URL域名提取"""
        service = CookieCloudSyncService(db_session)
        
        # 测试无效URL
        invalid_urls = [
            "not-a-url",
            "ftp://invalid.protocol.com",
            "",
            None
        ]
        
        for invalid_url in invalid_urls:
            if invalid_url is None:
                with pytest.raises(AttributeError):
                    service._extract_domain_from_url(invalid_url)
            else:
                domain = service._extract_domain_from_url(invalid_url)
                # 无效URL应该返回空字符串或抛出异常
                assert domain == "" or domain is None
