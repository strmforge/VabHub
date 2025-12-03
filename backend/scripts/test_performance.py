"""
性能测试脚本
测试API响应时间、缓存性能等
"""

import asyncio
import httpx
import time
import sys
from pathlib import Path
from statistics import mean, median, stdev

# 添加backend目录到路径
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from scripts.api_test_config import API_BASE_URL, API_PREFIX as CONFIG_API_PREFIX, api_url

BASE_URL = API_BASE_URL
API_PREFIX = CONFIG_API_PREFIX
TIMEOUT = 30.0

# 测试用户凭证
TEST_USERNAME = "test_user"
TEST_PASSWORD = "test_password_123"

auth_token = None


async def get_auth_token():
    """获取认证Token"""
    global auth_token
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                api_url("/auth/login"),
                data={
                    "username": TEST_USERNAME,
                    "password": TEST_PASSWORD
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "access_token" in data.get("data", {}):
                    auth_token = data["data"]["access_token"]
                    return True
    except Exception as e:
        print(f"[ERROR] 获取Token失败: {e}")
    return False


async def test_response_time(endpoint: str, method: str = "GET", headers: dict = None, json_data: dict = None, iterations: int = 10):
    """测试响应时间"""
    times = []
    errors = 0
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for i in range(iterations):
            try:
                start_time = time.time()
                
                if method == "GET":
                    response = await client.get(endpoint, headers=headers)
                elif method == "POST":
                    response = await client.post(endpoint, headers=headers, json=json_data)
                else:
                    continue
                
                elapsed = time.time() - start_time
                times.append(elapsed * 1000)  # 转换为毫秒
                
                if response.status_code >= 400:
                    errors += 1
                    
            except Exception as e:
                errors += 1
                print(f"  [ERROR] 请求失败: {e}")
    
    if not times:
        return None
    
    return {
        "endpoint": endpoint,
        "iterations": iterations,
        "errors": errors,
        "mean": mean(times),
        "median": median(times),
        "min": min(times),
        "max": max(times),
        "stdev": stdev(times) if len(times) > 1 else 0
    }


async def test_cache_performance():
    """测试缓存性能"""
    print("="*60)
    print("性能测试: 缓存性能")
    print("="*60)
    
    if not auth_token:
        if not await get_auth_token():
            print("[ERROR] 无法获取Token，跳过测试")
            return None
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # 测试仪表盘数据（可能有缓存）
    endpoint = api_url("/dashboard/")
    
    print(f"\n测试端点: {endpoint}")
    print(f"迭代次数: 20")
    
    result = await test_response_time(endpoint, "GET", headers, iterations=20)
    
    if result:
        print(f"\n结果:")
        print(f"  平均响应时间: {result['mean']:.2f} ms")
        print(f"  中位数响应时间: {result['median']:.2f} ms")
        print(f"  最小响应时间: {result['min']:.2f} ms")
        print(f"  最大响应时间: {result['max']:.2f} ms")
        print(f"  标准差: {result['stdev']:.2f} ms")
        print(f"  错误数: {result['errors']}")
        
        # 分析缓存效果
        if result['max'] / result['min'] > 2:
            print(f"  [INFO] 响应时间变化较大，可能缓存未生效")
        else:
            print(f"  [INFO] 响应时间较稳定，缓存可能生效")
    
    return result


async def test_database_query_performance():
    """测试数据库查询性能"""
    print("\n" + "="*60)
    print("性能测试: 数据库查询性能")
    print("="*60)
    
    if not auth_token:
        if not await get_auth_token():
            print("[ERROR] 无法获取Token，跳过测试")
            return None
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # 测试订阅列表查询
    endpoint = api_url("/subscriptions/?page=1&page_size=10")
    
    print(f"\n测试端点: {endpoint}")
    print(f"迭代次数: 10")
    
    result = await test_response_time(endpoint, "GET", headers, iterations=10)
    
    if result:
        print(f"\n结果:")
        print(f"  平均响应时间: {result['mean']:.2f} ms")
        print(f"  中位数响应时间: {result['median']:.2f} ms")
        print(f"  最小响应时间: {result['min']:.2f} ms")
        print(f"  最大响应时间: {result['max']:.2f} ms")
        print(f"  标准差: {result['stdev']:.2f} ms")
        print(f"  错误数: {result['errors']}")
        
        # 性能评估
        if result['mean'] < 100:
            print(f"  [OK] 响应时间优秀 (< 100ms)")
        elif result['mean'] < 500:
            print(f"  [OK] 响应时间良好 (< 500ms)")
        else:
            print(f"  [WARNING] 响应时间较慢 (> 500ms)")
    
    return result


async def test_api_endpoints_performance():
    """测试多个API端点的性能"""
    print("\n" + "="*60)
    print("性能测试: API端点性能")
    print("="*60)
    
    if not auth_token:
        if not await get_auth_token():
            print("[ERROR] 无法获取Token，跳过测试")
            return []
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    endpoints = [
        api_url("/auth/me"),
        api_url("/dashboard/"),
        api_url("/settings/"),
        api_url("/subscriptions/?page=1&page_size=10"),
    ]
    
    results = []
    
    for endpoint in endpoints:
        print(f"\n测试: {endpoint}")
        result = await test_response_time(endpoint, "GET", headers, iterations=5)
        if result:
            results.append(result)
            print(f"  平均响应时间: {result['mean']:.2f} ms")
        await asyncio.sleep(0.5)
    
    return results


async def main():
    """主测试函数"""
    print("="*60)
    print("VabHub 性能测试")
    print("="*60)
    print()
    print(f"测试服务器: {BASE_URL}")
    print(f"测试用户: {TEST_USERNAME}")
    print()
    
    results = {}
    
    # 测试1: 缓存性能
    result = await test_cache_performance()
    results["cache"] = result
    await asyncio.sleep(1)
    
    # 测试2: 数据库查询性能
    result = await test_database_query_performance()
    results["database"] = result
    await asyncio.sleep(1)
    
    # 测试3: API端点性能
    results_list = await test_api_endpoints_performance()
    results["endpoints"] = results_list
    
    # 汇总结果
    print("\n" + "="*60)
    print("性能测试结果汇总")
    print("="*60)
    
    if results.get("cache"):
        print(f"\n缓存性能:")
        print(f"  平均响应时间: {results['cache']['mean']:.2f} ms")
    
    if results.get("database"):
        print(f"\n数据库查询性能:")
        print(f"  平均响应时间: {results['database']['mean']:.2f} ms")
    
    if results.get("endpoints"):
        print(f"\nAPI端点性能:")
        for result in results["endpoints"]:
            print(f"  {result['endpoint']}: {result['mean']:.2f} ms")
    
    print()
    print("="*60)
    print("性能测试完成")
    print("="*60)
    
    return results


if __name__ == "__main__":
    asyncio.run(main())

