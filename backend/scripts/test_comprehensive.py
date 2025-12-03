"""
综合测试脚本
整合功能测试、API端点测试、集成测试和性能测试
"""

import asyncio
import sys
from pathlib import Path
import subprocess
import time

# 添加backend目录到路径
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

BASE_URL = "http://localhost:8000"


async def run_test_script(script_name: str, description: str):
    """运行测试脚本"""
    print("="*60)
    print(f"运行测试: {description}")
    print("="*60)
    print()
    
    script_path = Path(__file__).parent / script_name
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(backend_dir.parent)
        )
        
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"[ERROR] 测试超时: {script_name}")
        return False
    except Exception as e:
        print(f"[ERROR] 运行测试失败: {e}")
        return False


async def check_service():
    """检查服务状态"""
    import httpx
    
    print("检查服务状态...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BASE_URL}/")
            if response.status_code == 200:
                print("[OK] 服务运行正常")
                return True
            else:
                print(f"[WARNING] 服务响应异常: {response.status_code}")
                return False
    except Exception as e:
        print(f"[ERROR] 无法连接到服务: {e}")
        print("请确保服务已启动: python backend/run_server.py")
        return False


async def main():
    """主测试函数"""
    print("="*60)
    print("VabHub 综合测试")
    print("="*60)
    print()
    print(f"测试服务器: {BASE_URL}")
    print()
    
    # 检查服务状态
    if not await check_service():
        print("\n[ERROR] 服务未运行，请先启动服务")
        print("启动命令: python backend/run_server.py")
        return
    
    print()
    print("等待服务完全启动...")
    await asyncio.sleep(5)
    
    results = {}
    
    # 测试1: 基础功能测试
    print("\n" + "="*60)
    print("阶段1: 基础功能测试")
    print("="*60)
    result = await run_test_script("test_simple.py", "基础功能测试")
    results["basic"] = result
    await asyncio.sleep(2)
    
    # 测试2: 功能测试
    print("\n" + "="*60)
    print("阶段2: 功能测试")
    print("="*60)
    result = await run_test_script("test_functional.py", "功能测试")
    results["functional"] = result
    await asyncio.sleep(2)
    
    # 测试3: API端点测试
    print("\n" + "="*60)
    print("阶段3: API端点测试")
    print("="*60)
    result = await run_test_script("test_api_endpoints.py", "API端点测试")
    results["api_endpoints"] = result
    await asyncio.sleep(2)
    
    # 测试4: 集成测试
    print("\n" + "="*60)
    print("阶段4: 集成测试")
    print("="*60)
    result = await run_test_script("test_integration.py", "集成测试")
    results["integration"] = result
    await asyncio.sleep(2)
    
    # 测试5: 性能测试
    print("\n" + "="*60)
    print("阶段5: 性能测试")
    print("="*60)
    result = await run_test_script("test_performance.py", "性能测试")
    results["performance"] = result
    
    # 汇总结果
    print("\n" + "="*60)
    print("综合测试结果汇总")
    print("="*60)
    print()
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print(f"总计: {total} 个测试阶段")
    print(f"通过: {passed} 个")
    print(f"失败: {total - passed} 个")
    print(f"通过率: {passed/total*100:.1f}%")
    print()
    
    print("各阶段结果:")
    for stage, result in results.items():
        status = "通过" if result else "失败"
        print(f"  - {stage}: {status}")
    
    print()
    print("="*60)
    print("综合测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

