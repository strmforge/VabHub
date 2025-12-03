"""
HR-POLICY-2 性能测试
P6-2: 确保不影响正常操作性能
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

from app.modules.safety.engine import SafetyPolicyEngine
from app.modules.safety.models import SafetyContext, SafetyDecision
from app.modules.hr_case.models import HrCaseStatus


class TestSafetyPolicyPerformance:
    """安全策略性能测试"""
    
    @pytest.fixture
    def safety_engine(self):
        """安全策略引擎实例"""
        return SafetyPolicyEngine()
    
    @pytest.fixture
    def sample_hr_cases(self):
        """示例HR案例数据"""
        return [
            {
                'id': i,
                'site_key': f'test_site_{i}',
                'torrent_id': f'test_{i}',
                'status': HrCaseStatus.ACTIVE,
                'ratio': 0.5 + i * 0.1,
                'upload_hours': 24 + i * 10,
                'created_at': datetime.utcnow() - timedelta(hours=24 + i * 10)
            }
            for i in range(100)
        ]
    
    async def test_single_evaluation_performance(self, safety_engine):
        """测试单个安全策略评估性能"""
        hr_case = {
            'id': 1,
            'site_key': 'test_site',
            'torrent_id': 'test_123',
            'status': HrCaseStatus.ACTIVE,
            'ratio': 1.0,
            'upload_hours': 72,
            'created_at': datetime.utcnow() - timedelta(hours=72)
        }
        
        safety_ctx = SafetyContext(
            action="download",
            site_key="test_site",
            torrent_id="test_123",
            trigger="user_web",
            hr_case=hr_case
        )
        
        # 执行性能测试
        start_time = time.perf_counter()
        decision = await safety_engine.evaluate(safety_ctx)
        end_time = time.perf_counter()
        
        processing_time_ms = (end_time - start_time) * 1000
        
        # 单次评估应在10ms内完成
        assert processing_time_ms < 10, f"单次评估时间 {processing_time_ms:.2f}ms 超过阈值"
        assert decision.decision in ["ALLOW", "DENY", "REQUIRE_CONFIRM"]
        assert decision.processing_time_ms < 10
    
    async def test_concurrent_evaluation_performance(self, safety_engine, sample_hr_cases):
        """测试并发安全策略评估性能"""
        contexts = []
        for i, hr_case in enumerate(sample_hr_cases[:50]):  # 使用50个并发测试
            contexts.append(SafetyContext(
                action="download",
                site_key=hr_case['site_key'],
                torrent_id=hr_case['torrent_id'],
                trigger="user_web",
                hr_case=hr_case
            ))
        
        # 并发执行评估
        start_time = time.perf_counter()
        tasks = [safety_engine.evaluate(ctx) for ctx in contexts]
        decisions = await asyncio.gather(*tasks)
        end_time = time.perf_counter()
        
        total_time_ms = (end_time - start_time) * 1000
        avg_time_ms = total_time_ms / len(contexts)
        
        # 平均并发评估时间应在20ms内完成
        assert avg_time_ms < 20, f"并发平均评估时间 {avg_time_ms:.2f}ms 超过阈值"
        assert len(decisions) == 50
        
        # 验证所有决策都有效
        for decision in decisions:
            assert decision.decision in ["ALLOW", "DENY", "REQUIRE_CONFIRM"]
            assert decision.processing_time_ms < 50
    
    async def test_batch_evaluation_performance(self, safety_engine, sample_hr_cases):
        """测试批量安全策略评估性能"""
        contexts = []
        for i, hr_case in enumerate(sample_hr_cases):
            contexts.append(SafetyContext(
                action="download",
                site_key=hr_case['site_key'],
                torrent_id=hr_case['torrent_id'],
                trigger="user_web",
                hr_case=hr_case
            ))
        
        # 顺序批量执行评估
        start_time = time.perf_counter()
        decisions = []
        for ctx in contexts:
            decision = await safety_engine.evaluate(ctx)
            decisions.append(decision)
        end_time = time.perf_counter()
        
        total_time_ms = (end_time - start_time) * 1000
        avg_time_ms = total_time_ms / len(contexts)
        
        # 批量平均评估时间应在15ms内完成
        assert avg_time_ms < 15, f"批量平均评估时间 {avg_time_ms:.2f}ms 超过阈值"
        assert len(decisions) == 100
    
    async def test_memory_usage_stability(self, safety_engine):
        """测试内存使用稳定性"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行大量评估操作
        for i in range(1000):
            hr_case = {
                'id': i,
                'site_key': f'test_site_{i}',
                'torrent_id': f'test_{i}',
                'status': HrCaseStatus.ACTIVE,
                'ratio': 1.0,
                'upload_hours': 72,
                'created_at': datetime.utcnow() - timedelta(hours=72)
            }
            
            safety_ctx = SafetyContext(
                action="download",
                site_key=hr_case['site_key'],
                torrent_id=hr_case['torrent_id'],
                trigger="user_web",
                hr_case=hr_case
            )
            
            await safety_engine.evaluate(safety_ctx)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # 内存增长应小于50MB
        assert memory_increase < 50, f"内存增长 {memory_increase:.2f}MB 超过阈值"
    
    async def test_database_query_performance(self, safety_engine):
        """测试数据库查询性能"""
        # 模拟数据库查询延迟
        with patch('app.modules.hr_case.repository.get_hr_repository') as mock_repo:
            mock_instance = AsyncMock()
            mock_instance.get_by_site_and_torrent.return_value = {
                'id': 1,
                'status': HrCaseStatus.ACTIVE,
                'ratio': 1.0,
                'upload_hours': 72
            }
            mock_repo.return_value = mock_instance
            
            safety_ctx = SafetyContext(
                action="download",
                site_key="test_site",
                torrent_id="test_123",
                trigger="user_web"
            )
            
            # 测试数据库查询对性能的影响
            start_time = time.perf_counter()
            decision = await safety_engine.evaluate(safety_ctx)
            end_time = time.perf_counter()
            
            processing_time_ms = (end_time - start_time) * 1000
            
            # 即使包含数据库查询，也应在50ms内完成
            assert processing_time_ms < 50, f"包含数据库查询的评估时间 {processing_time_ms:.2f}ms 超过阈值"
    
    async def test_error_handling_performance(self, safety_engine):
        """测试错误处理性能"""
        # 测试各种错误情况下的性能
        error_contexts = [
            SafetyContext(action="invalid_action"),  # 无效操作
            SafetyContext(action="download", site_key=None),  # 缺失站点
            SafetyContext(action="delete", torrent_id=""),  # 空种子ID
        ]
        
        start_time = time.perf_counter()
        for ctx in error_contexts:
            decision = await safety_engine.evaluate(ctx)
            assert decision.decision == "ALLOW"  # 错误时应默认允许
        end_time = time.perf_counter()
        
        total_time_ms = (end_time - start_time) * 1000
        avg_time_ms = total_time_ms / len(error_contexts)
        
        # 错误处理也应在10ms内完成
        assert avg_time_ms < 10, f"错误处理平均时间 {avg_time_ms:.2f}ms 超过阈值"
    
    async def test_configuration_loading_performance(self, safety_engine):
        """测试配置加载性能"""
        # 测试配置加载对性能的影响
        contexts = []
        for i in range(100):
            contexts.append(SafetyContext(
                action="download",
                site_key=f"test_site_{i}",
                torrent_id=f"test_{i}",
                trigger="user_web"
            ))
        
        start_time = time.perf_counter()
        for ctx in contexts:
            decision = await safety_engine.evaluate(ctx)
            assert decision is not None
        end_time = time.perf_counter()
        
        total_time_ms = (end_time - start_time) * 1000
        avg_time_ms = total_time_ms / len(contexts)
        
        # 配置加载不应显著影响性能
        assert avg_time_ms < 20, f"包含配置加载的评估时间 {avg_time_ms:.2f}ms 超过阈值"
    
    async def test_notification_performance_impact(self):
        """测试通知系统对性能的影响"""
        from app.modules.notification.service import NotificationService
        
        mock_db = AsyncMock()
        notification_service = NotificationService(mock_db)
        
        # 模拟通知发送
        with patch.object(notification_service, 'send_notification') as mock_send:
            mock_send.return_value = AsyncMock()
            
            start_time = time.perf_counter()
            
            # 发送多个安全通知
            for i in range(10):
                await notification_service.send_safety_blocked_notification(
                    action="delete",
                    reason="分享率过低",
                    site_key=f"test_site_{i}",
                    torrent_id=f"test_{i}"
                )
            
            end_time = time.perf_counter()
            total_time_ms = (end_time - start_time) * 1000
            avg_time_ms = total_time_ms / 10
            
            # 通知发送平均时间应在100ms内完成
            assert avg_time_ms < 100, f"通知发送平均时间 {avg_time_ms:.2f}ms 超过阈值"


class TestSystemPerformanceRegression:
    """系统性能回归测试"""
    
    async def test_download_service_performance_with_safety(self):
        """测试下载服务集成安全策略后的性能"""
        from app.modules.decision.service import DecisionService
        from app.modules.decision.models import DecisionCandidate, DecisionContext
        
        decision_service = DecisionService()
        
        candidate = DecisionCandidate(
            title="Test Movie",
            media_type="movie",
            site_key="test_site",
            torrent_id="test_123"
        )
        
        context = DecisionContext(
            subscription=None,
            debug_enabled=False
        )
        
        start_time = time.perf_counter()
        result = await decision_service.decide_download(candidate, context)
        end_time = time.perf_counter()
        
        processing_time_ms = (end_time - start_time) * 1000
        
        # 下载决策应在100ms内完成（包含安全检查）
        assert processing_time_ms < 100, f"下载决策时间 {processing_time_ms:.2f}ms 超过阈值"
        assert result is not None
    
    async def test_file_operation_performance_with_safety(self):
        """测试文件操作集成安全策略后的性能"""
        from app.modules.file_operation.transfer_service import TransferService
        from unittest.mock import AsyncMock
        
        mock_db = AsyncMock()
        transfer_service = TransferService(mock_db)
        
        # 模拟文件传输操作
        with patch.object(transfer_service, '_get_operation_mode') as mock_mode:
            mock_mode.return_value = None  # 跳过实际文件操作
            
            start_time = time.perf_counter()
            
            result = await transfer_service.transfer_file(
                source_path="/test/source",
                target_path="/test/target",
                directory_config=None,
                media_info={"site_key": "test_site", "torrent_id": "test_123"}
            )
            
            end_time = time.perf_counter()
            processing_time_ms = (end_time - start_time) * 1000
            
            # 文件传输安全检查应在50ms内完成
            assert processing_time_ms < 50, f"文件传输安全检查时间 {processing_time_ms:.2f}ms 超过阈值"
    
    def test_api_response_time_with_safety_checks(self):
        """测试API响应时间包含安全检查"""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        with patch('app.api.download.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            
            with patch('app.modules.download.service.DownloadService') as mock_service:
                mock_instance = AsyncMock()
                mock_instance.get_download_by_id.return_value = None
                mock_instance.delete_download.return_value = False
                mock_service.return_value = mock_instance
                
                start_time = time.perf_counter()
                response = client.delete("/api/download/nonexistent_task")
                end_time = time.perf_counter()
                
                processing_time_ms = (end_time - start_time) * 1000
                
                # API响应时间应在200ms内完成
                assert processing_time_ms < 200, f"API响应时间 {processing_time_ms:.2f}ms 超过阈值"
                assert response.status_code in [200, 404]
