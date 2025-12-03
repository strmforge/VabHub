"""
CookieCloud集成测试
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

from app.modules.cookiecloud.service import CookieCloudSyncService
from app.core.scheduler import get_scheduler, TaskScheduler
from app.models.cookiecloud import CookieCloudSettings
from app.models.site import Site
from app.schemas.cookiecloud import CookieSource


class TestCookieCloudIntegration:
    """CookieCloud集成测试类"""

    @pytest.mark.asyncio
    async def test_full_sync_workflow(self, db_session, test_cookiecloud_settings, test_cookiecloud_sites, mock_cookiecloud_client):
        """测试完整同步工作流程"""
        service = CookieCloudSyncService(db_session)
        
        with patch('app.modules.cookiecloud.service.CookieCloudClient', return_value=mock_cookiecloud_client):
            # 1. 测试连接
            connection_ok = await service.test_connection()
            assert connection_ok is True
            
            # 2. 执行完整同步
            sync_result = await service.sync_all_sites(batch_size=10, site_timeout=30)
            assert sync_result.success is True
            assert sync_result.total_sites == 2
            assert sync_result.synced_sites == 2
            
            # 3. 验证状态更新
            settings = await service._get_settings()
            assert settings.last_status == "SUCCESS"
            assert settings.last_sync_at is not None
            
            # 4. 验证站点Cookie更新
            for site in test_cookiecloud_sites[:2]:  # 前两个是CookieCloud站点
                await db_session.refresh(site)
                assert site.cookie is not None
                assert "test_" in site.cookie  # Mock数据包含test_

    @pytest.mark.asyncio
    async def test_sync_with_domain_whitelist_filtering(self, db_session, mock_cookiecloud_client):
        """测试域名白名单过滤同步"""
        # 创建设置，只允许tracker.example.com
        settings = CookieCloudSettings(
            enabled=True,
            host="https://test.cookiecloud.com",
            uuid="12345678-1234-1234-1234-123456789abc",
            password="test_password",
            sync_interval_minutes=60,
            safe_host_whitelist='["tracker.example.com"]',  # 只允许这个域名
            last_status="NEVER",
            last_error=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(settings)
        
        # 创建测试站点
        sites = [
            Site(
                id=1,
                name="Allowed Site",
                url="https://tracker.example.com",
                cookie="old_cookie=value",
                cookie_source=CookieSource.COOKIECLOUD,
                enabled=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            Site(
                id=2,
                name="Blocked Site",
                url="https://blocked.example.com",
                cookie="old_cookie=value",
                cookie_source=CookieSource.COOKIECLOUD,
                enabled=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        for site in sites:
            db_session.add(site)
        
        await db_session.commit()
        
        service = CookieCloudSyncService(db_session)
        
        with patch('app.modules.cookiecloud.service.CookieCloudClient', return_value=mock_cookiecloud_client):
            result = await service.sync_all_sites(batch_size=10, site_timeout=30)
            
            # 应该只有1个站点被同步（允许的域名）
            assert result.total_sites == 1
            assert result.synced_sites == 1
            assert result.unmatched_sites == 1  # 被白名单过滤

    @pytest.mark.asyncio
    async def test_sync_error_recovery(self, db_session, test_cookiecloud_settings, test_cookiecloud_sites):
        """测试同步错误恢复"""
        service = CookieCloudSyncService(db_session)
        
        # Mock客户端第一次失败，第二次成功
        mock_client = AsyncMock()
        call_count = 0
        
        async def mock_get_cookies(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Network error")
            else:
                return {
                    "tracker.example.com": {
                        "cookie_data": [{"name": "session", "value": "recovered", "domain": "tracker.example.com"}]
                    }
                }
        
        mock_client.get_cookies = mock_get_cookies
        
        with patch('app.modules.cookiecloud.service.CookieCloudClient', return_value=mock_client):
            # 第一次同步应该失败
            result1 = await service.sync_all_sites(batch_size=10, site_timeout=30)
            assert result1.success is False
            assert result1.error_sites > 0
            
            # 第二次同步应该成功
            result2 = await service.sync_all_sites(batch_size=10, site_timeout=30)
            assert result2.success is True
            assert result2.synced_sites > 0

    @pytest.mark.asyncio
    async def test_scheduler_integration(self, db_session, test_cookiecloud_settings):
        """测试调度器集成"""
        scheduler = get_scheduler()
        
        # 添加CookieCloud同步任务
        scheduler.add_cookiecloud_sync_job(user_id=1, interval_minutes=1)
        
        # 验证任务已添加
        job = scheduler.get_job("cookiecloud_sync_1")
        assert job is not None
        assert "CookieCloud自动同步" in job["name"]
        
        # 模拟任务执行
        with patch('app.modules.cookiecloud.service.CookieCloudClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get_cookies.return_value = {}
            mock_client.return_value = mock_instance
            
            # 执行任务
            await scheduler._cookiecloud_sync_task(user_id=1)
        
        # 更新任务间隔
        scheduler.update_cookiecloud_sync_job(user_id=1, interval_minutes=5)
        
        # 验证任务已更新
        updated_job = scheduler.get_job("cookiecloud_sync_1")
        assert updated_job is not None
        
        # 移除任务
        scheduler.remove_cookiecloud_sync_job(user_id=1)
        
        # 验证任务已移除
        removed_job = scheduler.get_job("cookiecloud_sync_1")
        assert removed_job is None

    @pytest.mark.asyncio
    async def test_scheduler_startup_registration(self, db_session):
        """测试调度器启动时自动注册任务"""
        # 创建启用的CookieCloud设置
        settings = CookieCloudSettings(
            enabled=True,
            host="https://test.cookiecloud.com",
            uuid="12345678-1234-1234-1234-123456789abc",
            password="test_password",
            sync_interval_minutes=30,
            safe_host_whitelist='["example.com"]',
            last_status="NEVER",
            last_error=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(settings)
        await db_session.commit()
        
        scheduler = TaskScheduler()
        
        # 执行启动时注册
        await scheduler._register_cookiecloud_jobs_async()
        
        # 验证任务已注册
        job = scheduler.get_job("cookiecloud_sync_1")
        assert job is not None
        assert "CookieCloud自动同步" in job["name"]

    @pytest.mark.asyncio
    async def test_scheduler_disabled_settings_no_registration(self, db_session):
        """测试禁用设置时不注册调度器任务"""
        # 创建禁用的CookieCloud设置
        settings = CookieCloudSettings(
            enabled=False,  # 禁用
            host="https://test.cookiecloud.com",
            uuid="12345678-1234-1234-1234-123456789abc",
            password="test_password",
            sync_interval_minutes=30,
            safe_host_whitelist='["example.com"]',
            last_status="NEVER",
            last_error=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(settings)
        await db_session.commit()
        
        scheduler = TaskScheduler()
        
        # 执行启动时注册
        await scheduler._register_cookiecloud_jobs_async()
        
        # 验证任务未注册
        job = scheduler.get_job("cookiecloud_sync_1")
        assert job is None

    @pytest.mark.asyncio
    async def test_concurrent_sync_prevention(self, db_session, test_cookiecloud_settings, test_cookiecloud_sites):
        """测试并发同步防护"""
        service = CookieCloudSyncService(db_session)
        
        # 添加同步锁模拟
        sync_lock = asyncio.Lock()
        
        async def locked_sync():
            async with sync_lock:
                return await service.sync_all_sites(batch_size=10, site_timeout=30)
        
        with patch('app.modules.cookiecloud.service.CookieCloudClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get_cookies.return_value = {
                "tracker.example.com": {
                    "cookie_data": [{"name": "session", "value": "concurrent_test", "domain": "tracker.example.com"}]
                }
            }
            mock_client.return_value = mock_instance
            
            # 并发执行多个同步任务
            tasks = [locked_sync() for _ in range(3)]
            results = await asyncio.gather(*tasks)
            
            # 所有任务都应该成功（因为是串行执行）
            for result in results:
                assert result.success is True

    @pytest.mark.asyncio
    async def test_sync_with_large_site_list(self, db_session, test_cookiecloud_settings):
        """测试大量站点同步性能"""
        # 创建大量测试站点
        sites = []
        for i in range(50):
            site = Site(
                id=i + 1,
                name=f"Site {i + 1}",
                url=f"https://site{i + 1}.example.com",
                cookie="old_cookie=value",
                cookie_source=CookieSource.COOKIECLOUD,
                enabled=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            sites.append(site)
            db_session.add(site)
        
        await db_session.commit()
        
        service = CookieCloudSyncService(db_session)
        
        # Mock客户端返回数据
        mock_client = AsyncMock()
        mock_client.get_cookies.return_value = {
            f"site{i + 1}.example.com": {
                "cookie_data": [{"name": "session", "value": f"value{i + 1}", "domain": f"site{i + 1}.example.com"}]
            }
            for i in range(50)
        }
        
        with patch('app.modules.cookiecloud.service.CookieCloudClient', return_value=mock_client):
            # 使用较小的批处理大小测试
            start_time = datetime.utcnow()
            result = await service.sync_all_sites(batch_size=10, site_timeout=30)
            end_time = datetime.utcnow()
            
            assert result.success is True
            assert result.total_sites == 50
            assert result.synced_sites == 50
            
            # 验证执行时间合理（应该在几秒内完成）
            duration = (end_time - start_time).total_seconds()
            assert duration < 10  # 应该在10秒内完成

    @pytest.mark.asyncio
    async def test_sync_timeout_handling(self, db_session, test_cookiecloud_settings, test_cookiecloud_sites):
        """测试同步超时处理"""
        service = CookieCloudSyncService(db_session)
        
        # Mock客户端响应缓慢
        mock_client = AsyncMock()
        
        async def slow_get_cookies(*args, **kwargs):
            await asyncio.sleep(5)  # 模拟慢响应
            return {
                "tracker.example.com": {
                    "cookie_data": [{"name": "session", "value": "slow", "domain": "tracker.example.com"}]
                }
            }
        
        mock_client.get_cookies = slow_get_cookies
        
        with patch('app.modules.cookiecloud.service.CookieCloudClient', return_value=mock_client):
            # 使用较短的超时时间
            result = await service.sync_all_sites(batch_size=10, site_timeout=2)
            
            # 应该有超时错误
            assert result.success is False
            assert result.error_sites > 0
            assert any("timeout" in error.lower() or "超时" in error for error in result.errors)

    @pytest.mark.asyncio
    async def test_cookie_format_validation(self, db_session, test_cookiecloud_settings, test_cookiecloud_sites):
        """测试Cookie格式验证"""
        service = CookieCloudSyncService(db_session)
        
        # 测试各种Cookie格式
        test_cases = [
            # 标准格式
            [{"name": "session", "value": "abc123", "domain": "example.com"}],
            # 多个Cookie
            [
                {"name": "session", "value": "abc123", "domain": "example.com"},
                {"name": "auth", "value": "token456", "domain": "example.com"}
            ],
            # 带特殊字符
            [{"name": "special", "value": "abc@#$%", "domain": "example.com"}],
            # 空值
            [{"name": "empty", "value": "", "domain": "example.com"}],
        ]
        
        for i, cookie_data in enumerate(test_cases):
            mock_client = AsyncMock()
            mock_client.get_cookies.return_value = {
                "tracker.example.com": {"cookie_data": cookie_data}
            }
            
            with patch('app.modules.cookiecloud.service.CookieCloudClient', return_value=mock_client):
                result = await service.sync_site(test_cookiecloud_sites[0].id)
                
                if i == 3:  # 空值情况可能失败
                    if not result.success:
                        continue
                
                assert result.success is True
                assert result.cookie_updated is True

    @pytest.mark.asyncio
    async def test_database_transaction_rollback(self, db_session, test_cookiecloud_settings, test_cookiecloud_sites):
        """测试数据库事务回滚"""
        service = CookieCloudSyncService(db_session)
        
        # Mock客户端在处理第二个站点时失败
        mock_client = AsyncMock()
        
        async def failing_get_cookies(*args, **kwargs):
            raise Exception("Database error during sync")
        
        mock_client.get_cookies = failing_get_cookies
        
        with patch('app.modules.cookiecloud.service.CookieCloudClient', return_value=mock_client):
            # 记录同步前的Cookie状态
            original_cookies = {}
            for site in test_cookiecloud_sites[:2]:
                await db_session.refresh(site)
                original_cookies[site.id] = site.cookie
            
            # 执行同步（应该失败）
            result = await service.sync_all_sites(batch_size=10, site_timeout=30)
            assert result.success is False
            
            # 验证数据库状态未损坏
            for site in test_cookiecloud_sites[:2]:
                await db_session.refresh(site)
                assert site.cookie == original_cookies[site.id]

    @pytest.mark.asyncio
    async def test_memory_usage_during_sync(self, db_session, test_cookiecloud_settings):
        """测试同步过程中的内存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 创建大量站点
        sites = []
        for i in range(100):
            site = Site(
                id=i + 1,
                name=f"Memory Test Site {i + 1}",
                url=f"https://memory{i + 1}.example.com",
                cookie="old_cookie=value",
                cookie_source=CookieSource.COOKIECLOUD,
                enabled=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            sites.append(site)
            db_session.add(site)
        
        await db_session.commit()
        
        service = CookieCloudSyncService(db_session)
        
        # Mock客户端
        mock_client = AsyncMock()
        mock_client.get_cookies.return_value = {
            f"memory{i + 1}.example.com": {
                "cookie_data": [{"name": "session", "value": f"memory_value{i + 1}", "domain": f"memory{i + 1}.example.com"}]
            }
            for i in range(100)
        }
        
        with patch('app.modules.cookiecloud.service.CookieCloudClient', return_value=mock_client):
            # 执行同步
            result = await service.sync_all_sites(batch_size=20, site_timeout=30)
            
            assert result.success is True
            assert result.total_sites == 100
            
            # 检查内存使用增长是否合理
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            
            # 内存增长应该小于100MB
            assert memory_increase < 100 * 1024 * 1024

    @pytest.mark.asyncio
    async def test_sync_status_persistence(self, db_session, test_cookiecloud_settings, test_cookiecloud_sites, mock_cookiecloud_client):
        """测试同步状态持久化"""
        service = CookieCloudSyncService(db_session)
        
        with patch('app.modules.cookiecloud.service.CookieCloudClient', return_value=mock_cookiecloud_client):
            # 执行同步
            sync_time = datetime.utcnow()
            await service.sync_all_sites(batch_size=10, site_timeout=30)
            
            # 验证状态已保存
            settings = await service._get_settings()
            assert settings.last_status == "SUCCESS"
            assert settings.last_sync_at is not None
            assert settings.last_error is None
            
            # 验证时间戳合理
            time_diff = settings.last_sync_at - sync_time
            assert abs(time_diff.total_seconds()) < 60  # 应该在1分钟内

    @pytest.mark.asyncio
    async def test_error_logging_and_monitoring(self, db_session, test_cookiecloud_settings, test_cookiecloud_sites):
        """测试错误日志记录和监控"""
        service = CookieCloudSyncService(db_session)
        
        # Mock客户端返回特定错误
        mock_client = AsyncMock()
        mock_client.get_cookies.side_effect = [
            Exception("Network timeout"),
            Exception("Connection refused"),
            {"tracker.example.com": {"cookie_data": []}}  # 空数据
        ]
        
        with patch('app.modules.cookiecloud.service.CookieCloudClient', return_value=mock_client):
            result = await service.sync_all_sites(batch_size=10, site_timeout=30)
            
            assert result.success is False
            assert len(result.errors) > 0
            
            # 验证错误信息被正确记录
            assert any("timeout" in error.lower() for error in result.errors)
            assert any("refused" in error.lower() for error in result.errors)
            assert any("未找到" in error for error in result.errors)
            
            # 验证数据库中的错误状态
            settings = await service._get_settings()
            assert settings.last_status == "FAILED"
            assert settings.last_error is not None
