"""
后端基础功能测试脚本
测试数据库连接、Redis连接、健康检查等基础功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

# 确保 scripts 目录在 sys.path（支持 CI 环境）
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

import httpx
from loguru import logger

from api_test_config import API_BASE_URL, api_url

# 配置日志
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>", level="INFO")

BASE_URL = API_BASE_URL


async def test_health_check():
    """测试健康检查端点"""
    logger.info("=" * 60)
    logger.info("测试健康检查端点")
    logger.info("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_URL}/health")
            
            if response.status_code == 200:
                logger.info("✅ 健康检查通过")
                logger.info(f"响应内容: {response.json()}")
                return True
            else:
                logger.error(f"❌ 健康检查失败: {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                return False
    except Exception as e:
        logger.error(f"❌ 健康检查失败: {e}")
        return False


async def test_api_docs():
    """测试API文档端点"""
    logger.info("=" * 60)
    logger.info("测试API文档端点")
    logger.info("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_URL}/docs")
            
            if response.status_code == 200:
                logger.info("✅ API文档可访问")
                return True
            else:
                logger.error(f"❌ API文档不可访问: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"❌ API文档测试失败: {e}")
        return False


async def test_root_endpoint():
    """测试根端点"""
    logger.info("=" * 60)
    logger.info("测试根端点")
    logger.info("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_URL}/")
            
            if response.status_code == 200:
                logger.info("✅ 根端点可访问")
                logger.info(f"响应内容: {response.json()}")
                return True
            else:
                logger.error(f"❌ 根端点不可访问: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"❌ 根端点测试失败: {e}")
        return False


async def test_database_health():
    """测试数据库健康检查"""
    logger.info("=" * 60)
    logger.info("测试数据库健康检查")
    logger.info("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_URL}/health/database")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    logger.info("✅ 数据库连接正常")
                    logger.info(f"响应内容: {data}")
                    return True
                else:
                    logger.warning(f"⚠️ 数据库状态: {data.get('status')}")
                    logger.warning(f"响应内容: {data}")
                    return False
            else:
                logger.error(f"❌ 数据库健康检查失败: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"❌ 数据库健康检查失败: {e}")
        return False


async def test_redis_health():
    """测试Redis健康检查"""
    logger.info("=" * 60)
    logger.info("测试Redis健康检查")
    logger.info("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_URL}/health/redis")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    logger.info("✅ Redis连接正常")
                    logger.info(f"响应内容: {data}")
                    return True
                else:
                    logger.warning(f"⚠️ Redis状态: {data.get('status')}")
                    logger.warning(f"响应内容: {data}")
                    return False
            else:
                logger.error(f"❌ Redis健康检查失败: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"❌ Redis健康检查失败: {e}")
        return False


async def test_unified_response_format():
    """测试统一响应格式"""
    logger.info("=" * 60)
    logger.info("测试统一响应格式")
    logger.info("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 测试一个简单的API端点
            response = await client.get(api_url("/subscriptions?page=1&page_size=10"))
            
            if response.status_code == 200:
                data = response.json()
                # 检查是否是统一响应格式
                if "success" in data and "data" in data and "timestamp" in data:
                    logger.info("✅ 统一响应格式正确")
                    logger.info(f"响应格式: success={data.get('success')}, message={data.get('message')}")
                    return True
                else:
                    logger.error("❌ 响应格式不正确")
                    logger.error(f"响应内容: {data}")
                    return False
            else:
                logger.error(f"❌ API请求失败: {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                return False
    except Exception as e:
        logger.error(f"❌ 统一响应格式测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("开始后端基础功能测试")
    logger.info("=" * 60)
    logger.info("")
    logger.info(f"注意: 请确保后端服务已启动 ({BASE_URL})")
    logger.info("")
    
    results = []
    
    # 测试健康检查
    results.append(("健康检查", await test_health_check()))
    logger.info("")
    
    # 测试API文档
    results.append(("API文档", await test_api_docs()))
    logger.info("")
    
    # 测试根端点
    results.append(("根端点", await test_root_endpoint()))
    logger.info("")
    
    # 测试数据库健康检查
    results.append(("数据库健康检查", await test_database_health()))
    logger.info("")
    
    # 测试Redis健康检查
    results.append(("Redis健康检查", await test_redis_health()))
    logger.info("")
    
    # 测试统一响应格式
    results.append(("统一响应格式", await test_unified_response_format()))
    logger.info("")
    
    # 输出测试结果
    logger.info("=" * 60)
    logger.info("测试结果汇总")
    logger.info("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        if result:
            logger.info(f"✅ {test_name}: 通过")
            passed += 1
        else:
            logger.error(f"❌ {test_name}: 失败")
            failed += 1
    
    logger.info("")
    logger.info(f"总计: {len(results)} 个测试")
    logger.info(f"通过: {passed} 个")
    logger.info(f"失败: {failed} 个")
    logger.info(f"通过率: {passed / len(results) * 100:.1f}%")
    logger.info("")
    
    if failed == 0:
        logger.info("🎉 所有测试通过！")
        return 0
    else:
        logger.error("❌ 部分测试失败，请检查后端服务")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

