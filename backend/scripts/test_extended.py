"""
扩展测试脚本
测试更多模块的功能
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import time

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger


class ExtendedTester:
    """扩展测试器"""
    
    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
        self.start_time = time.time()
    
    def log_test(self, module: str, test_name: str, passed: bool, 
                 details: str = "", duration: float = 0.0):
        """记录测试结果"""
        result = {
            "module": module,
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if passed else "❌"
        logger.info(f"{status} [{module}] {test_name} ({duration:.2f}s)")
        if details:
            logger.info(f"   详情: {details}")
    
    async def test_cache_system(self):
        """测试缓存系统"""
        module = "缓存系统"
        start_time = time.time()
        
        try:
            from app.core.cache import get_cache
            
            cache = get_cache()
            assert cache is not None, "应该能获取缓存实例"
            self.log_test(module, "获取缓存实例", True, "", time.time() - start_time)
            
            # 测试缓存操作
            start_time = time.time()
            await cache.set("test_key", "test_value", ttl=60)
            value = await cache.get("test_key")
            assert value == "test_value", "应该能获取缓存值"
            self.log_test(module, "缓存读写", True, "", time.time() - start_time)
            
            # 测试缓存过期
            start_time = time.time()
            await cache.set("test_key_expire", "test_value", ttl=1)
            await asyncio.sleep(1.1)
            value = await cache.get("test_key_expire")
            assert value is None, "缓存应该已过期"
            self.log_test(module, "缓存过期", True, "", time.time() - start_time)
            
            return True
            
        except Exception as e:
            self.log_test(module, "缓存系统测试", False, str(e), time.time() - start_time)
            return False
    
    async def test_database_models(self):
        """测试数据库模型"""
        module = "数据库模型"
        start_time = time.time()
        
        try:
            from app.models import User, Subscription, DownloadTask
            from app.models.strm import STRMFile, STRMConfig
            
            # 验证模型存在
            assert User is not None
            assert Subscription is not None
            assert DownloadTask is not None
            assert STRMFile is not None
            assert STRMConfig is not None
            
            self.log_test(module, "模型导入", True, "所有模型导入成功", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log_test(module, "数据库模型测试", False, str(e), time.time() - start_time)
            return False
    
    async def test_api_schemas(self):
        """测试API响应模型"""
        module = "API响应模型"
        start_time = time.time()
        
        try:
            from app.core.schemas import (
                BaseResponse,
                success_response,
                error_response,
                PaginatedResponse
            )
            
            # 测试成功响应
            response = success_response(data={"test": "value"}, message="测试成功")
            assert response.success is True
            assert response.data is not None
            
            # 测试错误响应
            error = error_response(error_code="TEST_ERROR", error_message="测试错误")
            assert error.success is False
            assert error.error_code == "TEST_ERROR"
            
            self.log_test(module, "响应模型", True, "", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log_test(module, "API响应模型测试", False, str(e), time.time() - start_time)
            return False
    
    async def test_strm_modules(self):
        """测试STRM模块"""
        module = "STRM模块"
        start_time = time.time()
        
        try:
            from app.modules.strm import (
                STRMGenerator,
                STRMConfig,
                STRMSyncManager,
                STRMSyncTaskManager,
                get_sync_task_manager
            )
            
            # 验证模块导入
            assert STRMGenerator is not None
            assert STRMConfig is not None
            assert STRMSyncManager is not None
            assert STRMSyncTaskManager is not None
            assert get_sync_task_manager is not None
            
            self.log_test(module, "STRM模块导入", True, "所有STRM模块导入成功", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log_test(module, "STRM模块测试", False, str(e), time.time() - start_time)
            return False
    
    async def test_notification_system(self):
        """测试通知系统"""
        module = "通知系统"
        start_time = time.time()
        
        try:
            from app.modules.notification.service import NotificationService, NotificationChannelManager
            
            # 验证服务存在
            assert NotificationService is not None
            # 验证NotificationChannelManager存在（可能是占位符类）
            assert NotificationChannelManager is not None
            
            # 检查是否是占位符类（通过检查是否有特定方法）
            is_placeholder = not hasattr(NotificationChannelManager, '__module__') or \
                           'placeholder' in str(NotificationChannelManager).lower()
            
            if is_placeholder:
                self.log_test(
                    module, 
                    "通知系统导入", 
                    True, 
                    "使用占位符类（功能受限，但系统可运行）", 
                    time.time() - start_time
                )
            else:
                self.log_test(module, "通知系统导入", True, "", time.time() - start_time)
            
            return True
            
        except Exception as e:
            self.log_test(module, "通知系统测试", False, str(e), time.time() - start_time)
            return False
    
    async def test_search_system(self):
        """测试搜索系统"""
        module = "搜索系统"
        start_time = time.time()
        
        try:
            from app.modules.search.service import SearchService
            from app.modules.search.engine import SearchEngine
            
            assert SearchService is not None
            assert SearchEngine is not None
            
            self.log_test(module, "搜索系统导入", True, "", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log_test(module, "搜索系统测试", False, str(e), time.time() - start_time)
            return False
    
    async def test_subscription_system(self):
        """测试订阅系统"""
        module = "订阅系统"
        start_time = time.time()
        
        try:
            from app.modules.subscription.service import SubscriptionService
            
            assert SubscriptionService is not None
            
            self.log_test(module, "订阅系统导入", True, "", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log_test(module, "订阅系统测试", False, str(e), time.time() - start_time)
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("=" * 60)
        logger.info("开始扩展测试")
        logger.info("=" * 60)
        
        tests = [
            ("缓存系统", self.test_cache_system),
            ("数据库模型", self.test_database_models),
            ("API响应模型", self.test_api_schemas),
            ("STRM模块", self.test_strm_modules),
            ("通知系统", self.test_notification_system),
            ("搜索系统", self.test_search_system),
            ("订阅系统", self.test_subscription_system),
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results[test_name] = result
            except Exception as e:
                logger.error(f"测试 {test_name} 时出错: {e}", exc_info=True)
                results[test_name] = False
        
        # 生成测试报告
        self.generate_report(results)
        
        return results
    
    def generate_report(self, results: Dict[str, bool]):
        """生成测试报告"""
        total_time = time.time() - self.start_time
        
        logger.info("\n" + "=" * 60)
        logger.info("扩展测试报告")
        logger.info("=" * 60)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        logger.info(f"总测试数: {total}")
        logger.info(f"通过: {passed}")
        logger.info(f"失败: {total - passed}")
        logger.info(f"通过率: {passed/total*100:.1f}%")
        logger.info(f"总耗时: {total_time:.2f}秒")
        
        logger.info("\n详细结果:")
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"  {status}: {test_name}")
        
        logger.info("\n" + "=" * 60)


async def main():
    """主函数"""
    tester = ExtendedTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

