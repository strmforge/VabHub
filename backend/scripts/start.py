"""
VabHub 启动脚本
提供完整的启动前检查和启动功能
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
backend_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.cache import get_cache
from loguru import logger
from sqlalchemy import text


async def check_database():
    """检查数据库连接"""
    logger.info("检查数据库连接...")
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            logger.info("✅ 数据库连接正常")
            return True
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        logger.error("请检查:")
        logger.error("1. 数据库服务是否运行")
        logger.error("2. DATABASE_URL配置是否正确")
        if settings.DATABASE_URL.startswith("postgresql"):
            logger.error("   PostgreSQL: postgresql://用户名:密码@主机:端口/数据库名")
            logger.error("   示例: postgresql://vabhub:vabhub@localhost:5432/vabhub")
        else:
            logger.error("   SQLite: sqlite:///./vabhub.db")
        return False


async def check_redis():
    """检查Redis连接（可选）"""
    logger.info("检查Redis连接...")
    try:
        cache = get_cache()
        # 检查是否有Redis后端
        has_redis = any(
            'Redis' in str(type(backend).__name__) 
            for backend in cache.backends
        )
        if has_redis:
            # 测试Redis连接
            test_key = "startup_check"
            await cache.set(test_key, "test", ttl=10)
            value = await cache.get(test_key)
            if value == "test":
                await cache.delete(test_key)
                logger.info("✅ Redis连接正常")
                return True
            else:
                logger.warning("⚠️ Redis连接异常，将仅使用内存缓存")
                return False
        else:
            logger.info("ℹ️ Redis未配置，将仅使用内存缓存")
            return True
    except Exception as e:
        logger.warning(f"⚠️ Redis连接失败: {e}")
        logger.warning("将仅使用内存缓存")
        return True  # Redis是可选的，不阻断启动


async def check_environment():
    """检查环境配置"""
    logger.info("检查环境配置...")
    
    issues = []
    
    # 检查关键配置
    # 检查密钥（使用动态获取的值）
    secret_key = settings.SECRET_KEY_DYNAMIC
    jwt_secret_key = settings.JWT_SECRET_KEY_DYNAMIC
    
    if secret_key == "change-this-to-a-random-secret-key-in-production":
        issues.append("⚠️ SECRET_KEY使用默认值，生产环境请修改")
    
    if jwt_secret_key == "change-this-to-a-random-jwt-secret-key-in-production":
        issues.append("⚠️ JWT_SECRET_KEY使用默认值，生产环境请修改")
    
    # 检查API_TOKEN是否已生成
    api_token = settings.API_TOKEN_DYNAMIC
    if not api_token:
        issues.append("⚠️ API_TOKEN未生成，STRM功能可能无法正常工作")
    
    # 检查数据库URL
    if settings.DATABASE_URL.startswith("postgresql"):
        logger.info("✅ 使用PostgreSQL数据库")
    else:
        logger.info("ℹ️ 使用SQLite数据库（开发模式）")
    
    # 检查TMDB API Key（可选）
    if not settings.TMDB_API_KEY:
        issues.append("ℹ️ TMDB_API_KEY未配置，媒体搜索功能可能受限")
    
    if issues:
        for issue in issues:
            logger.warning(issue)
    else:
        logger.info("✅ 环境配置检查通过")
    
    return True


async def check_database_tables():
    """检查数据库表"""
    logger.info("检查数据库表...")
    try:
        # 使用异步方式检查表
        async with AsyncSessionLocal() as session:
            # 尝试查询一个关键表来验证表是否存在
            # 如果表不存在，查询会失败
            required_tables = [
                'users',
                'subscriptions',
                'download_tasks',
                'sites',
                'system_settings'
            ]
            
            missing_tables = []
            for table_name in required_tables:
                try:
                    # 尝试查询表（使用原始SQL）
                    result = await session.execute(
                        text(f"SELECT 1 FROM {table_name} LIMIT 1")
                    )
                    result.scalar()  # 触发查询执行
                except Exception:
                    # 如果查询失败，说明表不存在
                    missing_tables.append(table_name)
            
            if missing_tables:
                logger.error(f"❌ 缺少数据库表: {', '.join(missing_tables)}")
                logger.error("请运行: python backend/scripts/init_db.py")
                return False
            else:
                logger.info("✅ 数据库表检查通过")
                return True
    except Exception as e:
        # 如果数据库连接失败，这里会捕获
        logger.error(f"❌ 数据库表检查失败: {e}")
        logger.warning("如果这是首次运行，请先运行: python backend/scripts/init_db.py")
        return False


async def pre_start_checks():
    """启动前检查"""
    logger.info("="*50)
    logger.info("VabHub 启动前检查")
    logger.info("="*50)
    
    checks = [
        ("环境配置", check_environment),
        ("数据库连接", check_database),
        ("数据库表", check_database_tables),
        ("Redis连接", check_redis),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = await check_func()
        except Exception as e:
            logger.error(f"检查 {name} 时出错: {e}")
            results[name] = False
        logger.info("")
    
    # 汇总结果
    logger.info("="*50)
    logger.info("检查结果汇总")
    logger.info("="*50)
    
    all_passed = True
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{name}: {status}")
        if not result and name in ["数据库连接", "数据库表"]:
            all_passed = False
    
    logger.info("="*50)
    
    if not all_passed:
        logger.error("启动前检查失败，请解决上述问题后重试")
        return False
    else:
        logger.info("✅ 所有检查通过，可以启动应用")
        return True


def start_server():
    """启动服务器"""
    import uvicorn
    
    logger.info("="*50)
    logger.info("启动 VabHub 服务器")
    logger.info("="*50)
    logger.info(f"主机: {settings.HOST}")
    logger.info(f"端口: {settings.PORT}")
    logger.info(f"调试模式: {settings.DEBUG}")
    logger.info(f"API文档: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info("="*50)
    
    # 切换到backend目录
    backend_dir = Path(__file__).parent.parent
    original_dir = os.getcwd()
    try:
        os.chdir(backend_dir)
        uvicorn.run(
            "main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            workers=1 if settings.DEBUG else settings.WORKERS,
            log_level=settings.LOG_LEVEL.lower()
        )
    finally:
        os.chdir(original_dir)


async def main():
    """主函数"""
    # 执行启动前检查
    if not await pre_start_checks():
        sys.exit(1)
    
    # 启动服务器
    start_server()


if __name__ == "__main__":
    # 如果是直接运行，执行检查后启动
    if len(sys.argv) > 1 and sys.argv[1] == "--skip-checks":
        # 跳过检查直接启动
        start_server()
    else:
        # 执行检查后启动
        asyncio.run(main())

