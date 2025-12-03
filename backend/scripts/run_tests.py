"""
自动化测试执行脚本
检查服务状态，然后运行所有测试
"""

import asyncio
import httpx
import sys
import subprocess
import time
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

BASE_URL = "http://localhost:8000"
TIMEOUT = 5.0


async def check_service_running():
    """检查服务是否运行"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{BASE_URL}/")
            return response.status_code == 200
    except Exception:
        return False


async def wait_for_service(max_wait=30):
    """等待服务启动"""
    print("等待服务启动...")
    for i in range(max_wait):
        if await check_service_running():
            print(f"[OK] 服务已启动 (等待了 {i+1} 秒)")
            return True
        await asyncio.sleep(1)
        if (i + 1) % 5 == 0:
            print(f"[INFO] 等待中... ({i+1}/{max_wait} 秒)")
    return False


def run_test_script(script_name, description):
    """运行测试脚本"""
    print("\n" + "="*60)
    print(f"运行测试: {description}")
    print("="*60)
    print()
    
    script_path = backend_dir / "scripts" / script_name
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=False,
            text=True,
            cwd=str(backend_dir.parent)
        )
        return result.returncode == 0
    except Exception as e:
        print(f"[ERROR] 运行测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("="*60)
    print("VabHub 自动化测试执行")
    print("="*60)
    print()
    
    # 检查服务状态
    print("检查服务状态...")
    if not await check_service_running():
        print("[WARNING] 服务未运行")
        print()
        print("请先启动服务:")
        print("  方法1: python backend/run_server.py")
        print("  方法2: 在另一个终端运行启动命令")
        print()
        print("或者等待30秒让脚本自动检测服务启动...")
        
        if not await wait_for_service():
            print()
            print("[ERROR] 服务未启动，无法运行测试")
            print("请手动启动服务后重新运行此脚本")
            return
    
    print()
    print("[OK] 服务运行正常，开始执行测试...")
    print()
    
    # 等待服务完全就绪
    await asyncio.sleep(2)
    
    results = {}
    
    # 测试1: 基础功能测试
    results["basic"] = run_test_script("test_simple.py", "基础功能测试")
    await asyncio.sleep(1)
    
    # 测试2: 功能模块测试
    results["functional"] = run_test_script("test_functional.py", "功能模块测试")
    await asyncio.sleep(1)
    
    # 测试3: API端点测试
    results["api_endpoints"] = run_test_script("test_api_endpoints.py", "API端点测试")
    await asyncio.sleep(1)
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    print()
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print(f"总计: {total} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {total - passed} 个")
    print(f"通过率: {passed/total*100:.1f}%")
    print()
    
    print("各测试结果:")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  - {test_name}: {status}")
    
    print()
    print("="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

