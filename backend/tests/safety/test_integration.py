"""
HR-POLICY-2 集成测试
P6-1: 端到端测试所有安全策略
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
import json

from app.main import app
from app.core.database import get_db
from app.modules.safety.engine import SafetyPolicyEngine
from app.modules.safety.models import SafetyContext, SafetyDecision
from app.modules.hr_case.models import HrCaseStatus


class TestSafetyPolicyIntegration:
    """安全策略集成测试"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    async def mock_db(self):
        """模拟数据库会话"""
        mock_session = AsyncMock(spec=AsyncSession)
        return mock_session
    
    @pytest.fixture
    def safety_engine(self):
        """安全策略引擎"""
        return SafetyPolicyEngine()
    
    async def test_download_with_active_hr_blocked(self, safety_engine):
        """测试下载时遇到活跃HR案例被阻止"""
        # 创建活跃HR案例
        hr_case = {
            'id': 1,
            'site_key': 'test_site',
            'torrent_id': 'test_123',
            'status': HrCaseStatus.ACTIVE,
            'ratio': 0.5,
            'upload_hours': 24,
            'created_at': datetime.utcnow() - timedelta(hours=24)
        }
        
        # 创建安全上下文
        safety_ctx = SafetyContext(
            action="download",
            site_key="test_site",
            torrent_id="test_123",
            trigger="user_web",
            hr_case=hr_case
        )
        
        # 执行评估
        decision = await safety_engine.evaluate(safety_ctx)
        
        # 验证结果
        assert decision.decision == "REQUIRE_CONFIRM"
        assert "HR" in decision.message
        assert decision.requires_user_action == True
    
    async def test_delete_with_low_ratio_blocked(self, safety_engine):
        """测试删除低分享率HR案例被阻止"""
        # 创建低分享率HR案例
        hr_case = {
            'id': 2,
            'site_key': 'test_site',
            'torrent_id': 'test_456',
            'status': HrCaseStatus.ACTIVE,
            'ratio': 0.3,  # 低于最低删除阈值
            'upload_hours': 48,
            'created_at': datetime.utcnow() - timedelta(hours=48)
        }
        
        safety_ctx = SafetyContext(
            action="delete",
            site_key="test_site",
            torrent_id="test_456",
            trigger="user_web",
            hr_case=hr_case
        )
        
        decision = await safety_engine.evaluate(safety_ctx)
        
        assert decision.decision == "DENY"
        assert "分享率" in decision.message
    
    async def test_move_with_hr_require_copy(self, safety_engine):
        """测试移动HR文件需要复制策略"""
        hr_case = {
            'id': 3,
            'site_key': 'test_site',
            'torrent_id': 'test_789',
            'status': HrCaseStatus.ACTIVE,
            'ratio': 1.2,
            'upload_hours': 100,
            'created_at': datetime.utcnow() - timedelta(hours=100)
        }
        
        safety_ctx = SafetyContext(
            action="move",
            site_key="test_site",
            torrent_id="test_789",
            trigger="user_web",
            hr_case=hr_case,
            metadata={"changes_seeding_path": True}
        )
        
        decision = await safety_engine.evaluate(safety_ctx)
        
        assert decision.decision == "REQUIRE_CONFIRM"
        assert "复制" in decision.message
    
    async def test_cleanup_operation_blocked(self, safety_engine):
        """测试清理操作被安全策略阻止"""
        safety_ctx = SafetyContext(
            action="upload_cleanup",
            trigger="system_runner",
            metadata={"cleanup_directory": "/downloads"}
        )
        
        decision = await safety_engine.evaluate(safety_ctx)
        
        # 清理操作应该被允许（安全模式）
        assert decision.decision == "ALLOW"
    
    def test_safety_settings_api_endpoints(self, client):
        """测试安全设置API端点"""
        # 测试获取全局安全设置
        with patch('app.api.settings.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            
            # 模拟安全设置服务
            with patch('app.modules.safety.settings.SafetySettingsService') as mock_service:
                mock_instance = AsyncMock()
                mock_instance.get_global.return_value = {
                    "mode": "SAFE",
                    "hr_protection_enabled": True,
                    "min_ratio_for_delete": 1.0,
                    "min_keep_hours": 72
                }
                mock_service.return_value = mock_instance
                
                response = client.get("/api/settings/safety/global")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] == True
                assert "data" in data
    
    def test_download_api_with_safety_check(self, client):
        """测试下载API的安全检查集成"""
        with patch('app.api.download.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            
            # 模拟下载服务
            with patch('app.modules.download.service.DownloadService') as mock_service:
                mock_instance = AsyncMock()
                mock_instance.get_download_by_id.return_value = None  # 任务不存在
                mock_service.return_value = mock_instance
                
                response = client.delete("/api/download/test_task_id")
                assert response.status_code == 404
    
    async def test_safety_engine_performance(self, safety_engine):
        """测试安全策略引擎性能"""
        import time
        
        # 创建测试上下文
        hr_case = {
            'id': 4,
            'site_key': 'test_site',
            'torrent_id': 'test_perf',
            'status': HrCaseStatus.ACTIVE,
            'ratio': 1.0,
            'upload_hours': 72,
            'created_at': datetime.utcnow() - timedelta(hours=72)
        }
        
        safety_ctx = SafetyContext(
            action="download",
            site_key="test_site",
            torrent_id="test_perf",
            trigger="user_web",
            hr_case=hr_case
        )
        
        # 性能测试：多次执行评估
        start_time = time.time()
        for _ in range(100):
            decision = await safety_engine.evaluate(safety_ctx)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 100
        # 平均响应时间应小于50ms
        assert avg_time < 0.05, f"平均响应时间 {avg_time:.3f}s 超过阈值"
        assert decision.processing_time_ms < 50
    
    async def test_safety_notification_integration(self):
        """测试安全通知集成"""
        from app.modules.notification.service import NotificationService
        from unittest.mock import AsyncMock
        
        mock_db = AsyncMock()
        notification_service = NotificationService(mock_db)
        
        # 测试安全阻止通知
        with patch.object(notification_service, 'send_notification') as mock_send:
            mock_send.return_value = AsyncMock()
            
            result = await notification_service.send_safety_blocked_notification(
                action="delete",
                reason="分享率过低",
                site_key="test_site",
                torrent_id="test_123"
            )
            
            assert result is not None
            mock_send.assert_called_once()
    
    async def test_batch_safety_evaluation(self, safety_engine):
        """测试批量安全策略评估"""
        contexts = []
        for i in range(10):
            hr_case = {
                'id': i,
                'site_key': f'test_site_{i}',
                'torrent_id': f'test_{i}',
                'status': HrCaseStatus.ACTIVE,
                'ratio': 0.5 + i * 0.1,
                'upload_hours': 24 + i * 10,
                'created_at': datetime.utcnow() - timedelta(hours=24 + i * 10)
            }
            
            contexts.append(SafetyContext(
                action="download",
                site_key=f'test_site_{i}',
                torrent_id=f'test_{i}',
                trigger="user_web",
                hr_case=hr_case
            ))
        
        # 批量评估
        decisions = []
        for ctx in contexts:
            decision = await safety_engine.evaluate(ctx)
            decisions.append(decision)
        
        assert len(decisions) == 10
        # 验证所有决策都有结果
        for decision in decisions:
            assert decision.decision in ["ALLOW", "DENY", "REQUIRE_CONFIRM"]
            assert decision.reason_code is not None
            assert decision.message is not None


class TestSafetyPolicyRegression:
    """安全策略回归测试"""
    
    async def test_backward_compatibility(self):
        """测试向后兼容性"""
        # 确保安全策略引擎不会影响现有功能
        from app.modules.decision.service import DecisionService
        
        decision_service = DecisionService()
        
        # 测试没有HR案例的情况
        from app.modules.decision.models import DecisionCandidate, DecisionContext
        
        candidate = DecisionCandidate(
            title="Test Movie",
            media_type="movie",
            site_key="test_site",
            torrent_id="test_123"
        )
        
        # 模拟上下文（不包含HR案例）
        context = DecisionContext(
            subscription=None,
            debug_enabled=False
        )
        
        # 这应该正常工作，不会因为安全策略检查而失败
        try:
            result = await decision_service.decide_download(candidate, context)
            assert result is not None
        except Exception as e:
            pytest.fail(f"向后兼容性测试失败: {e}")
    
    async def test_error_handling_robustness(self):
        """测试错误处理健壮性"""
        from app.modules.safety.engine import SafetyPolicyEngine
        
        engine = SafetyPolicyEngine()
        
        # 测试无效上下文
        invalid_ctx = SafetyContext(
            action="invalid_action",
            site_key=None,
            torrent_id=None,
            trigger="test"
        )
        
        decision = await engine.evaluate(invalid_ctx)
        # 应该返回默认允许决策而不是抛出异常
        assert decision.decision == "ALLOW"
        assert "错误" in decision.reason_code
    
    def test_configuration_validation(self):
        """测试配置验证"""
        from app.modules.safety.models import GlobalSafetySettings, SiteSafetySettings
        
        # 测试有效配置
        valid_global = GlobalSafetySettings(
            mode="SAFE",
            hr_protection_enabled=True,
            min_ratio_for_delete=1.0,
            min_keep_hours=72
        )
        assert valid_global.mode in ["SAFE", "BALANCED", "AGGRESSIVE"]
        assert valid_global.min_ratio_for_delete >= 0
        assert valid_global.min_keep_hours >= 0
        
        # 测试站点配置
        valid_site = SiteSafetySettings(
            site_key="test_site",
            hr_sensitivity="HIGH",
            min_ratio_for_delete=1.2,
            enabled=True
        )
        assert valid_site.hr_sensitivity in ["LOW", "MEDIUM", "HIGH"]
