"""
SafetyPolicyEngine 基础单元测试
覆盖关键决策场景和边界情况
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.safety.engine import SafetyPolicyEngine, get_safety_policy_engine
from app.modules.safety.models import (
    SafetyContext,
    SafetyDecision,
    GlobalSafetySettings,
    SiteSafetySettings,
    SubscriptionSafetySettings,
    SafetyDecisionReason,
)
from app.modules.hr_case.models import HrCase


class TestSafetyPolicyEngine:
    """SafetyPolicyEngine 基础测试"""
    
    @pytest.fixture
    def engine(self):
        """创建引擎实例"""
        return SafetyPolicyEngine()
    
    @pytest.fixture
    def mock_hr_repo(self):
        """模拟HR仓库"""
        repo = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_settings_service(self):
        """模拟设置服务"""
        service = AsyncMock()
        return service
    
    @pytest.fixture
    def active_hr_case(self):
        """创建活跃HR案件"""
        return HrCase(
            id=1,
            site_id=1,
            site_key="test_site",
            torrent_id="test_torrent_123",
            status="ACTIVE",
            life_status="ALIVE",
            requirement_hours=72.0,
            seeded_hours=24.0,
            deadline=datetime.utcnow() + timedelta(days=3),
            entered_at=datetime.utcnow() - timedelta(days=1),
            first_seen_at=datetime.utcnow() - timedelta(days=1),
            last_seen_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def safe_hr_case(self):
        """创建安全HR案件"""
        return HrCase(
            id=2,
            site_id=1,
            site_key="test_site",
            torrent_id="test_torrent_456",
            status="SAFE",
            life_status="ALIVE",
            requirement_hours=72.0,
            seeded_hours=80.0,
            deadline=datetime.utcnow() - timedelta(days=1),
            entered_at=datetime.utcnow() - timedelta(days=5),
            first_seen_at=datetime.utcnow() - timedelta(days=5),
            last_seen_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def global_settings(self):
        """创建全局设置"""
        return GlobalSafetySettings(
            mode="BALANCED",
            min_keep_hours=24.0,
            min_ratio_for_delete=0.8,
            prefer_copy_on_move_for_hr=True,
            enable_hr_protection=True,
            auto_approve_hours=2.0
        )
    
    @pytest.fixture
    def site_settings_normal(self):
        """创建普通站点设置"""
        return SiteSafetySettings(
            site_key="normal_site",
            hr_sensitivity="normal",
            min_keep_ratio=0.8,
            min_keep_time_hours=48.0
        )
    
    @pytest.fixture
    def site_settings_sensitive(self):
        """创建敏感站点设置"""
        return SiteSafetySettings(
            site_key="sensitive_site",
            hr_sensitivity="highly_sensitive",
            min_keep_ratio=1.0,
            min_keep_time_hours=72.0
        )
    
    @pytest.fixture
    def subscription_settings_no_hr(self):
        """创建不允许HR的订阅设置"""
        return SubscriptionSafetySettings(
            allow_hr=False,
            allow_h3h5=False,
            strict_free_only=False,
            enable_hr_warning=True,
            enable_hr_confirmation=True
        )
    
    @pytest.mark.asyncio
    async def test_download_hr_active_denied(self, engine, active_hr_case, global_settings):
        """测试下载活跃HR种子被拒绝"""
        ctx = SafetyContext(
            action="download",
            site_key="test_site",
            torrent_id="test_torrent_123",
            trigger="user_web",
            hr_case=active_hr_case
        )
        
        with patch.object(engine._settings_service, 'get_global', return_value=global_settings), \
             patch.object(engine._settings_service, 'get_site', return_value=None), \
             patch.object(engine._settings_service, 'get_subscription', return_value=None), \
             patch('app.modules.safety.engine.settings') as mock_settings:
            
            mock_settings.SAFETY_ENGINE_ENABLED = True
            
            decision = await engine.evaluate(ctx)
            
            assert decision.decision == "DENY"
            assert decision.reason_code == SafetyDecisionReason.HR_ACTIVE_DOWNLOAD
            assert "HR期" in decision.message
            assert decision.hr_status_snapshot is not None
            assert decision.hr_status_snapshot["status"] == "ACTIVE"
    
    @pytest.mark.asyncio
    async def test_download_hr_safe_allowed(self, engine, safe_hr_case, global_settings):
        """测试下载安全HR种子被允许"""
        ctx = SafetyContext(
            action="download",
            site_key="test_site",
            torrent_id="test_torrent_456",
            trigger="user_web",
            hr_case=safe_hr_case
        )
        
        with patch.object(engine._settings_service, 'get_global', return_value=global_settings), \
             patch.object(engine._settings_service, 'get_site', return_value=None), \
             patch.object(engine._settings_service, 'get_subscription', return_value=None), \
             patch('app.modules.safety.engine.settings') as mock_settings:
            
            mock_settings.SAFETY_ENGINE_ENABLED = True
            
            decision = await engine.evaluate(ctx)
            
            assert decision.decision == "ALLOW"
            assert decision.reason_code == SafetyDecisionReason.SAFE
            assert "允许下载" in decision.message
    
    @pytest.mark.asyncio
    async def test_download_subscription_no_hr_require_confirm(self, engine, safe_hr_case, 
                                                               global_settings, subscription_settings_no_hr):
        """测试订阅不允许HR时需要确认（使用安全HR种子）"""
        ctx = SafetyContext(
            action="download",
            site_key="test_site",
            torrent_id="test_torrent_456",
            trigger="user_web",
            subscription_id=123,
            hr_case=safe_hr_case
        )
        
        with patch.object(engine._settings_service, 'get_global', return_value=global_settings), \
             patch.object(engine._settings_service, 'get_site', return_value=None), \
             patch.object(engine._settings_service, 'get_subscription', return_value=subscription_settings_no_hr), \
             patch('app.modules.safety.engine.settings') as mock_settings:
            
            mock_settings.SAFETY_ENGINE_ENABLED = True
            
            decision = await engine.evaluate(ctx)
            
            assert decision.decision == "REQUIRE_CONFIRM"
            assert decision.reason_code == SafetyDecisionReason.SUBSCRIPTION_NO_HR
            assert "订阅设置不允许HR种子" in decision.message
            assert decision.requires_user_action is True
            assert decision.auto_approve_after is not None
    
    @pytest.mark.asyncio
    async def test_download_site_highly_sensitive_require_confirm(self, engine, safe_hr_case,
                                                                   global_settings, site_settings_sensitive):
        """测试高敏感站点需要确认（使用安全HR种子）"""
        ctx = SafetyContext(
            action="download",
            site_key="sensitive_site",
            torrent_id="test_torrent_456",
            trigger="user_web",
            hr_case=safe_hr_case
        )
        
        with patch.object(engine._settings_service, 'get_global', return_value=global_settings), \
             patch.object(engine._settings_service, 'get_site', return_value=site_settings_sensitive), \
             patch.object(engine._settings_service, 'get_subscription', return_value=None), \
             patch('app.modules.safety.engine.settings') as mock_settings:
            
            mock_settings.SAFETY_ENGINE_ENABLED = True
            
            decision = await engine.evaluate(ctx)
            
            assert decision.decision == "REQUIRE_CONFIRM"
            assert decision.reason_code == SafetyDecisionReason.SITE_HIGHLY_SENSITIVE
            assert "高敏感站点" in decision.message
            assert decision.requires_user_action is True
    
    @pytest.mark.asyncio
    async def test_delete_hr_active_denied(self, engine, active_hr_case, global_settings):
        """测试删除活跃HR种子被拒绝"""
        ctx = SafetyContext(
            action="delete",
            site_key="test_site",
            torrent_id="test_torrent_123",
            trigger="user_web",
            hr_case=active_hr_case
        )
        
        with patch.object(engine._settings_service, 'get_global', return_value=global_settings), \
             patch.object(engine._settings_service, 'get_site', return_value=None), \
             patch.object(engine._settings_service, 'get_subscription', return_value=None), \
             patch('app.modules.safety.engine.settings') as mock_settings:
            
            mock_settings.SAFETY_ENGINE_ENABLED = True
            
            decision = await engine.evaluate(ctx)
            
            assert decision.decision == "DENY"
            assert decision.reason_code == SafetyDecisionReason.HR_ACTIVE_DELETE
            assert "HR期" in decision.message
            assert decision.hr_status_snapshot is not None
    
    @pytest.mark.asyncio
    async def test_delete_low_ratio_require_confirm(self, engine, global_settings):
        """测试低分享率删除需要确认"""
        low_ratio_case = HrCase(
            id=3,
            site_id=1,
            site_key="test_site",
            torrent_id="test_torrent_789",
            status="SAFE",
            life_status="ALIVE",
            current_ratio=0.5,
            requirement_hours=72.0,
            seeded_hours=80.0
        )
        
        ctx = SafetyContext(
            action="delete",
            site_key="test_site",
            torrent_id="test_torrent_789",
            trigger="user_web",
            hr_case=low_ratio_case
        )
        
        with patch.object(engine._settings_service, 'get_global', return_value=global_settings), \
             patch.object(engine._settings_service, 'get_site', return_value=None), \
             patch.object(engine._settings_service, 'get_subscription', return_value=None), \
             patch('app.modules.safety.engine.settings') as mock_settings:
            
            mock_settings.SAFETY_ENGINE_ENABLED = True
            
            decision = await engine.evaluate(ctx)
            
            assert decision.decision == "REQUIRE_CONFIRM"
            assert decision.reason_code == SafetyDecisionReason.LOW_RATIO_WARNING
            assert "分享率" in decision.message
            assert "0.50" in decision.message
            assert decision.requires_user_action is True
    
    @pytest.mark.asyncio
    async def test_move_hr_active_suggest_copy(self, engine, active_hr_case, global_settings):
        """测试HR期内移动建议复制"""
        ctx = SafetyContext(
            action="move",
            site_key="test_site",
            torrent_id="test_torrent_123",
            path_from="/downloads/torrent_123",
            path_to="/media/movies/torrent_123",
            changes_seeding_path=True,
            trigger="user_web",
            hr_case=active_hr_case
        )
        
        with patch.object(engine._settings_service, 'get_global', return_value=global_settings), \
             patch.object(engine._settings_service, 'get_site', return_value=None), \
             patch.object(engine._settings_service, 'get_subscription', return_value=None), \
             patch('app.modules.safety.engine.settings') as mock_settings:
            
            mock_settings.SAFETY_ENGINE_ENABLED = True
            
            decision = await engine.evaluate(ctx)
            
            assert decision.decision == "REQUIRE_CONFIRM"
            assert decision.reason_code == SafetyDecisionReason.HR_MOVE_SUGGEST_COPY
            assert "复制" in decision.message
            assert decision.suggested_alternative is not None
            assert decision.suggested_alternative == "复制文件到目标位置"
    
    @pytest.mark.asyncio
    async def test_move_hr_safe_allowed(self, engine, safe_hr_case, global_settings):
        """测试HR完成后移动允许"""
        ctx = SafetyContext(
            action="move",
            site_key="test_site",
            torrent_id="test_torrent_456",
            path_from="/downloads/torrent_456",
            path_to="/media/movies/torrent_456",
            changes_seeding_path=True,
            trigger="user_web",
            hr_case=safe_hr_case
        )
        
        with patch.object(engine._settings_service, 'get_global', return_value=global_settings), \
             patch.object(engine._settings_service, 'get_site', return_value=None), \
             patch.object(engine._settings_service, 'get_subscription', return_value=None), \
             patch('app.modules.safety.engine.settings') as mock_settings:
            
            mock_settings.SAFETY_ENGINE_ENABLED = True
            
            decision = await engine.evaluate(ctx)
            
            assert decision.decision == "ALLOW"
            assert decision.reason_code == SafetyDecisionReason.HR_SAFE
            assert "HR已完成" in decision.message
    
    @pytest.mark.asyncio
    async def test_cleanup_hr_active_denied(self, engine, active_hr_case, global_settings):
        """测试自动清理遇到HR种子被拒绝"""
        ctx = SafetyContext(
            action="upload_cleanup",
            site_key="test_site",
            torrent_id="test_torrent_123",
            trigger="system_runner",
            hr_case=active_hr_case
        )
        
        with patch.object(engine._settings_service, 'get_global', return_value=global_settings), \
             patch.object(engine._settings_service, 'get_site', return_value=None), \
             patch.object(engine._settings_service, 'get_subscription', return_value=None), \
             patch('app.modules.safety.engine.settings') as mock_settings:
            
            mock_settings.SAFETY_ENGINE_ENABLED = True
            
            decision = await engine.evaluate(ctx)
            
            assert decision.decision == "DENY"
            assert decision.reason_code == SafetyDecisionReason.HR_ACTIVE_CLEANUP
            assert "自动清理" in decision.message
            assert decision.hr_status_snapshot is not None
    
    @pytest.mark.asyncio
    async def test_feature_disabled_allow_all(self, engine):
        """测试功能禁用时允许所有操作"""
        ctx = SafetyContext(
            action="download",
            site_key="test_site",
            torrent_id="test_torrent_123",
            trigger="user_web"
        )
        
        with patch('app.modules.safety.engine.settings') as mock_settings:
            mock_settings.SAFETY_ENGINE_ENABLED = False
            
            decision = await engine.evaluate(ctx)
            
            assert decision.decision == "ALLOW"
            assert decision.reason_code == SafetyDecisionReason.SETTINGS_DISABLED
            assert "功能已禁用" in decision.message
    
    @pytest.mark.asyncio
    async def test_unknown_action_allowed(self, engine, global_settings):
        """测试未知操作类型被允许（使用generate_strm作为测试）"""
        ctx = SafetyContext(
            action="generate_strm",
            site_key="test_site",
            torrent_id="test_torrent_123",
            trigger="user_web"
        )
        
        with patch.object(engine._settings_service, 'get_global', return_value=global_settings), \
             patch.object(engine._settings_service, 'get_site', return_value=None), \
             patch.object(engine._settings_service, 'get_subscription', return_value=None), \
             patch('app.modules.safety.engine.settings') as mock_settings:
            
            mock_settings.SAFETY_ENGINE_ENABLED = True
            
            decision = await engine.evaluate(ctx)
            
            assert decision.decision == "ALLOW"
            assert decision.reason_code == SafetyDecisionReason.SAFE
            assert "STRM文件" in decision.message
    
    @pytest.mark.asyncio
    async def test_error_handling_allow_with_low_confidence(self, engine):
        """测试错误处理时允许操作但降低置信度"""
        ctx = SafetyContext(
            action="download",
            site_key="test_site",
            torrent_id="test_torrent_123",
            trigger="user_web"
        )
        
        with patch.object(engine._settings_service, 'get_global', side_effect=Exception("测试异常")), \
             patch('app.modules.safety.engine.settings') as mock_settings:
            
            mock_settings.SAFETY_ENGINE_ENABLED = True
            
            decision = await engine.evaluate(ctx)
            
            assert decision.decision == "ALLOW"
            assert decision.reason_code == SafetyDecisionReason.ERROR_OCCURRED
            assert decision.confidence == 0.5
            assert "评估失败" in decision.message
            assert decision.processing_time_ms is not None
    
    @pytest.mark.asyncio
    async def test_generate_strm_allowed(self, engine, active_hr_case, global_settings):
        """测试生成STRM文件总是允许"""
        ctx = SafetyContext(
            action="generate_strm",
            site_key="test_site",
            torrent_id="test_torrent_123",
            trigger="system_runner",
            hr_case=active_hr_case
        )
        
        with patch.object(engine._settings_service, 'get_global', return_value=global_settings), \
             patch.object(engine._settings_service, 'get_site', return_value=None), \
             patch.object(engine._settings_service, 'get_subscription', return_value=None), \
             patch('app.modules.safety.engine.settings') as mock_settings:
            
            mock_settings.SAFETY_ENGINE_ENABLED = True
            
            decision = await engine.evaluate(ctx)
            
            assert decision.decision == "ALLOW"
            assert decision.reason_code == SafetyDecisionReason.SAFE
            assert "STRM文件" in decision.message
            assert decision.hr_status_snapshot is not None
    
    @pytest.mark.asyncio
    async def test_batch_evaluate(self, engine, global_settings):
        """测试批量评估"""
        contexts = [
            SafetyContext(action="download", site_key="site1", torrent_id="torrent1", trigger="user_web"),
            SafetyContext(action="delete", site_key="site2", torrent_id="torrent2", trigger="user_web"),
            SafetyContext(action="move", site_key="site3", torrent_id="torrent3", trigger="user_web")
        ]
        
        with patch.object(engine._settings_service, 'get_global', return_value=global_settings), \
             patch.object(engine._settings_service, 'get_site', return_value=None), \
             patch.object(engine._settings_service, 'get_subscription', return_value=None), \
             patch('app.modules.safety.engine.settings') as mock_settings:
            
            mock_settings.SAFETY_ENGINE_ENABLED = True
            
            decisions = await engine.batch_evaluate(contexts)
            
            assert len(decisions) == 3
            for decision in decisions:
                assert decision.decision == "ALLOW"
                assert decision.processing_time_ms is not None
    
    def test_get_safety_policy_engine_singleton(self):
        """测试单例模式"""
        engine1 = get_safety_policy_engine()
        engine2 = get_safety_policy_engine()
        assert engine1 is engine2
    
    def test_effective_min_ratio_priority(self, engine, global_settings, site_settings_sensitive):
        """测试最低分享率优先级"""
        # 站点设置应该覆盖全局设置
        effective_ratio = engine._get_effective_min_ratio(global_settings, site_settings_sensitive)
        assert effective_ratio == 1.0  # 站点设置
        
        # 全局设置作为默认值
        effective_ratio = engine._get_effective_min_ratio(global_settings, None)
        assert effective_ratio == 0.8  # 全局设置
    
    def test_effective_min_hours_priority(self, engine, global_settings, site_settings_sensitive):
        """测试最低保种时间优先级"""
        # 站点设置应该覆盖全局设置
        effective_hours = engine._get_effective_min_hours(global_settings, site_settings_sensitive)
        assert effective_hours == 72.0  # 站点设置
        
        # 全局设置作为默认值
        effective_hours = engine._get_effective_min_hours(global_settings, None)
        assert effective_hours == 24.0  # 全局设置


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
