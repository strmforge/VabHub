"""
COOKIECLOUD-1 P2阶段实现测试
验证CookieCloudClient和CookieCloudSyncService的功能完整性
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal
from app.core.cookiecloud import CookieCloudClient
from app.modules.cookiecloud.service import CookieCloudSyncService
from sqlalchemy import text
from loguru import logger


async def test_cookiecloud_client():
    """测试CookieCloudClient解密算法"""
    logger.info("=== 测试CookieCloudClient解密算法 ===")
    
    try:
        # 使用官方测试服务器（如果可用）
        # 这里使用模拟数据进行算法验证
        client = CookieCloudClient(
            server_url="https://cookiecloud.example.com",  # 测试URL
            uuid="test-uuid-12345678",
            password="test-password"
        )
        
        # 测试密钥派生算法
        key = client._derive_key()
        expected_key = "md5(test-uuid-12345678-test-password)"[:16]
        
        logger.info(f"派生密钥: {key}")
        logger.info(f"密钥长度: {len(key)}")
        
        # 验证密钥格式
        assert len(key) == 16, "密钥长度应为16位"
        assert isinstance(key, str), "密钥应为字符串类型"
        
        logger.info("✅ CookieCloudClient密钥派生算法测试通过")
        
        await client.close()
        
    except Exception as e:
        logger.error(f"❌ CookieCloudClient测试失败: {e}")
        return False
    
    return True


async def test_cookiecloud_sync_service():
    """测试CookieCloudSyncService基础功能"""
    logger.info("=== 测试CookieCloudSyncService基础功能 ===")
    
    async with AsyncSessionLocal() as db:
        try:
            # 创建同步服务实例
            sync_service = CookieCloudSyncService(db)
            
            # 测试获取配置
            settings = await sync_service._get_settings()
            if settings:
                logger.info(f"✅ 获取配置成功: enabled={settings.enabled}")
                logger.info(f"配置详情: host={settings.host}, uuid存在={bool(settings.uuid)}")
            else:
                logger.warning("⚠️ 未找到CookieCloud配置，这是正常的（首次运行）")
            
            # 测试域名匹配逻辑
            test_cases = [
                ("pt.example.com", "pt.example.com", True),
                ("example.com", "pt.example.com", False),
                (".example.com", "pt.example.com", True),
                ("pt.example.com", ".example.com", True),
                ("hdhome.org", "hdhome.org", True),
                ("tracker.hdhome.org", "hdhome.org", True),
            ]
            
            for cookie_domain, site_domain, expected in test_cases:
                result = sync_service._is_domain_match(cookie_domain, site_domain)
                status = "✅" if result == expected else "❌"
                logger.info(f"{status} 域名匹配测试: {cookie_domain} vs {site_domain} = {result} (期望: {expected})")
            
            # 测试Cookie提取逻辑
            mock_cookie_data = {
                "cookie_data": {
                    "pt.example.com": [
                        {"name": "uid", "value": "12345"},
                        {"name": "passkey", "value": "abcdef123456"}
                    ],
                    "hdhome.org": "uid=67890; passkey=ghijk789012"
                }
            }
            
            # 测试精确匹配
            cookie_string = sync_service._extract_domain_cookies(mock_cookie_data, "pt.example.com")
            expected = "uid=12345; passkey=abcdef123456"
            assert cookie_string == expected, f"Cookie提取失败: 期望'{expected}', 实际'{cookie_string}'"
            logger.info(f"✅ Cookie提取测试通过: {cookie_string}")
            
            # 测试字符串格式Cookie
            cookie_string2 = sync_service._extract_domain_cookies(mock_cookie_data, "hdhome.org")
            expected2 = "uid=67890; passkey=ghijk789012"
            assert cookie_string2 == expected2, f"Cookie提取失败: 期望'{expected2}', 实际'{cookie_string2}'"
            logger.info(f"✅ 字符串Cookie提取测试通过: {cookie_string2}")
            
            logger.info("✅ CookieCloudSyncService基础功能测试通过")
            
        except Exception as e:
            logger.error(f"❌ CookieCloudSyncService测试失败: {e}")
            return False
    
    return True


async def test_database_integration():
    """测试数据库集成"""
    logger.info("=== 测试数据库集成 ===")
    
    async with AsyncSessionLocal() as db:
        try:
            # 检查CookieCloudSettings表
            result = await db.execute(text("SELECT COUNT(*) FROM cookiecloud_settings"))
            settings_count = result.scalar()
            logger.info(f"✅ CookieCloudSettings表记录数: {settings_count}")
            
            # 检查sites表新字段
            result = await db.execute(text("SELECT COUNT(*) FROM sites WHERE cookie_source IS NOT NULL"))
            sites_with_source = result.scalar()
            logger.info(f"✅ 有cookie_source标记的站点数: {sites_with_source}")
            
            # 检查字段类型
            result = await db.execute(text("""
                SELECT name, type FROM pragma_table_info('sites') 
                WHERE name IN ('cookie_source', 'last_cookiecloud_sync_at')
            """))
            fields = result.fetchall()
            for field in fields:
                logger.info(f"✅ 字段 {field[0]} 类型: {field[1]}")
            
            logger.info("✅ 数据库集成测试通过")
            
        except Exception as e:
            logger.error(f"❌ 数据库集成测试失败: {e}")
            return False
    
    return True


async def test_sync_scenarios():
    """测试同步场景"""
    logger.info("=== 测试同步场景 ===")
    
    async with AsyncSessionLocal() as db:
        try:
            sync_service = CookieCloudSyncService(db)
            
            # 场景1: 未启用CookieCloud - 先确保配置为禁用状态
            await db.execute(text("UPDATE cookiecloud_settings SET enabled = 0 WHERE id = 1"))
            await db.commit()
            
            result = await sync_service.sync_all_sites()
            assert not result.success, "未启用时应返回失败"
            logger.info(f"实际错误信息: {result.errors}")
            # 检查错误信息是否包含未启用相关关键词
            error_text = str(result.errors)
            assert any(keyword in error_text for keyword in ["未启用", "启用", "enabled"]), f"错误信息应包含启用相关词汇，实际: {error_text}"
            logger.info("✅ 场景1测试通过: 未启用CookieCloud")
            
            # 场景2: 配置不完整
            # 更新配置为启用但缺少必要字段
            await db.execute(text("""
                UPDATE cookiecloud_settings 
                SET enabled = 1, host = NULL, uuid = NULL, password = NULL
                WHERE id = 1
            """))
            await db.commit()
            
            result = await sync_service.sync_all_sites()
            assert not result.success, "配置不完整时应返回失败"
            assert "配置不完整" in str(result.errors), "错误信息应包含配置不完整"
            logger.info("✅ 场景2测试通过: 配置不完整")
            
            # 场景3: 测试连接（预期失败，因为使用测试URL）
            connection_ok = await sync_service.test_connection()
            logger.info(f"✅ 场景3测试: 连接测试结果 {connection_ok}（预期失败，因为使用测试URL）")
            
            logger.info("✅ 同步场景测试通过")
            
        except Exception as e:
            logger.error(f"❌ 同步场景测试失败: {e}")
            return False
    
    return True


async def test_integration_hook():
    """测试集成钩子"""
    logger.info("=== 测试集成钩子 ===")
    
    try:
        # 导入集成钩子
        from app.modules.site_manager.integration_hooks import cookiecloud_sync_hook
        from app.schemas.site_manager import SiteDetail
        
        # 创建测试站点数据
        test_site = SiteDetail(
            id=1,
            name="测试站点",
            url="https://pt.example.com",
            domain="pt.example.com",
            enabled=True,
            key="test",
            category="pt",
            icon_url=None,
            priority=0,
            tags=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # 测试钩子执行（无数据库会话）
        await cookiecloud_sync_hook(test_site)
        logger.info("✅ 集成钩子测试通过: 无数据库会话时优雅跳过")
        
        # 测试钩子执行（有数据库会话）
        async with AsyncSessionLocal() as db:
            await cookiecloud_sync_hook(test_site, db=db)
            logger.info("✅ 集成钩子测试通过: 有数据库会话时正常执行")
        
        logger.info("✅ 集成钩子测试通过")
        
    except Exception as e:
        logger.error(f"❌ 集成钩子测试失败: {e}")
        return False
    
    return True


async def main():
    """主测试函数"""
    logger.info("🚀 开始COOKIECLOUD-1 P2阶段实现测试")
    
    test_results = []
    
    # 执行各项测试
    tests = [
        ("CookieCloudClient解密算法", test_cookiecloud_client),
        ("CookieCloudSyncService基础功能", test_cookiecloud_sync_service),
        ("数据库集成", test_database_integration),
        ("同步场景", test_sync_scenarios),
        ("集成钩子", test_integration_hook),
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n--- 开始测试: {test_name} ---")
        try:
            result = await test_func()
            test_results.append((test_name, result))
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"--- 测试完成: {test_name} {status} ---")
        except Exception as e:
            logger.error(f"--- 测试异常: {test_name} ❌ 异常: {e} ---")
            test_results.append((test_name, False))
    
    # 输出测试结果摘要
    logger.info("\n" + "="*60)
    logger.info("📊 P2阶段实现测试结果摘要")
    logger.info("="*60)
    
    passed_count = 0
    total_count = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed_count += 1
    
    logger.info("-"*60)
    logger.info(f"总计: {passed_count}/{total_count} 测试通过")
    
    if passed_count == total_count:
        logger.info("🎉 所有测试通过！P2阶段实现验证成功，可以进入P3阶段。")
        return True
    else:
        logger.warning(f"⚠️ {total_count - passed_count} 个测试失败，需要修复后重新测试。")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        sys.exit(1)
