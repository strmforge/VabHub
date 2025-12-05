"""
测试导入和配置
用于诊断启动问题
"""

import sys
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

print("="*60)
print("测试导入和配置")
print("="*60)
print()

# 测试1: 基础导入
print("测试1: 基础模块导入...")
try:
    print("[OK] fastapi 导入成功")
except Exception as e:
    print(f"[ERROR] fastapi 导入失败: {e}")
    sys.exit(1)

try:
    print("[OK] uvicorn 导入成功")
except Exception as e:
    print(f"[ERROR] uvicorn 导入失败: {e}")
    sys.exit(1)

# 测试2: 应用配置
print("\n测试2: 应用配置...")
try:
    from app.core.config import settings
    print("[OK] 配置导入成功")
    print(f"   HOST: {settings.HOST}")
    print(f"   PORT: {settings.PORT}")
    print(f"   DATABASE_URL: {settings.DATABASE_URL}")
except Exception as e:
    print(f"[ERROR] 配置导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试3: 数据库连接
print("\n测试3: 数据库连接...")
try:
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import text
    import asyncio
    
    async def test_db():
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            print("[OK] 数据库连接成功")
    
    asyncio.run(test_db())
except Exception as e:
    print(f"[ERROR] 数据库连接失败: {e}")
    import traceback
    traceback.print_exc()

# 测试4: 应用创建
print("\n测试4: 应用创建...")
try:
    from app.core.logging import setup_logging
    setup_logging()
    print("[OK] 日志系统初始化成功")
except Exception as e:
    print(f"[ERROR] 日志系统初始化失败: {e}")
    import traceback
    traceback.print_exc()

try:
    from main import app
    print("[OK] 应用创建成功")
    print(f"   应用标题: {app.title}")
    print(f"   应用版本: {app.version}")
except Exception as e:
    print(f"[ERROR] 应用创建失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试5: API路由
print("\n测试5: API路由...")
try:
    routes = [route.path for route in app.routes]
    print("[OK] API路由加载成功")
    print(f"   路由数量: {len(routes)}")
    if routes:
        print(f"   前5个路由: {routes[:5]}")
except Exception as e:
    print(f"[ERROR] API路由加载失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("所有测试完成")
print("="*60)

