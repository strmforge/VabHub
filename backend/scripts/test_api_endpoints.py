"""
测试API端点
用于验证各个API端点是否正常工作
"""

import asyncio
import httpx
import sys
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from scripts.api_test_config import API_BASE_URL, api_url

BASE_URL = API_BASE_URL
TIMEOUT = 30.0


async def test_endpoint(name: str, method: str, url: str, expected_status: int = 200, **kwargs):
    """测试单个端点"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            if method.upper() == "GET":
                response = await client.get(url, **kwargs)
            elif method.upper() == "POST":
                response = await client.post(url, **kwargs)
            elif method.upper() == "PUT":
                response = await client.put(url, **kwargs)
            elif method.upper() == "DELETE":
                response = await client.delete(url, **kwargs)
            else:
                print(f"[ERROR] {name}: 不支持的HTTP方法 {method}")
                return False
            
            if response.status_code == expected_status:
                print(f"[OK] {name}: {response.status_code}")
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        # 检查统一响应格式
                        if "success" in data:
                            print(f"     Success: {data.get('success')}")
                        if "data" in data:
                            print(f"     Data type: {type(data.get('data'))}")
                        if "message" in data:
                            print(f"     Message: {data.get('message')}")
                except:
                    pass
                return True
            else:
                print(f"[ERROR] {name}: {response.status_code} (期望: {expected_status})")
                try:
                    error_data = response.json()
                    print(f"     Error: {error_data}")
                except:
                    print(f"     Response: {response.text[:200]}")
                return False
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        return False


async def main():
    """主测试函数"""
    print("="*60)
    print("API端点测试")
    print("="*60)
    print()
    
    tests = [
        # 基础端点
        ("根端点", "GET", f"{BASE_URL}/"),
        ("API文档", "GET", f"{BASE_URL}/docs"),
        ("健康检查", "GET", f"{BASE_URL}/health", 503),  # 503是预期的（Redis未运行）
        
        # 认证API（需要认证的端点会返回401，这是正常的）
        ("用户注册", "POST", api_url("/auth/register"), 422),  # 422是预期的（缺少参数）
        ("用户登录", "POST", api_url("/auth/login"), 422),  # 422是预期的（缺少参数）
        
        # 订阅管理API
        ("订阅列表", "GET", api_url("/subscriptions?page=1&page_size=10"), 401),  # 401是预期的（需要认证）
        
        # 下载管理API
        ("下载列表", "GET", api_url("/downloads?page=1&page_size=10"), 401),  # 401是预期的（需要认证）
        
        # 搜索系统API
        ("搜索", "GET", api_url("/search?query=test&page=1&page_size=10"), 401),  # 401是预期的（需要认证）
        
        # 站点管理API
        ("站点列表", "GET", api_url("/sites?page=1&page_size=10"), 401),  # 401是预期的（需要认证）
        
        # 工作流API
        ("工作流列表", "GET", api_url("/workflows?page=1&page_size=10"), 401),  # 401是预期的（需要认证）
        
        # 通知API
        ("通知列表", "GET", api_url("/notifications?page=1&page_size=10"), 401),  # 401是预期的（需要认证）
        
        # 仪表盘API
        ("仪表盘", "GET", api_url("/dashboard"), 401),  # 401是预期的（需要认证）
        
        # 设置API
        ("设置列表", "GET", api_url("/settings"), 401),  # 401是预期的（需要认证）
        
        # 云存储API
        ("云存储列表", "GET", api_url("/cloud-storage?page=1&page_size=10"), 401),  # 401是预期的（需要认证）
        
        # 音乐API
        ("音乐订阅列表", "GET", api_url("/music/subscriptions?page=1&page_size=10"), 401),  # 401是预期的（需要认证）
        
        # 日历API
        ("日历", "GET", api_url("/calendar"), 401),  # 401是预期的（需要认证）
        
        # HNR检测API
        ("HNR检测列表", "GET", api_url("/hnr/detections?page=1&page_size=10"), 401),  # 401是预期的（需要认证）
        
        # 推荐API
        ("推荐", "GET", api_url("/recommendation/popular"), 401),  # 401是预期的（需要认证）
        
        # 媒体识别API
        ("媒体识别历史", "GET", api_url("/media/identification/history?page=1&page_size=10"), 401),  # 401是预期的（需要认证）
    ]
    
    results = []
    for name, method, url, *expected_status in tests:
        expected = expected_status[0] if expected_status else 200
        result = await test_endpoint(name, method, url, expected)
        results.append((name, result))
        await asyncio.sleep(0.5)  # 避免请求过快
    
    # 统计结果
    print()
    print("="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    total = len(results)
    
    print(f"总计: {total} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    print(f"通过率: {passed/total*100:.1f}%")
    print()
    
    if failed > 0:
        print("失败的测试:")
        for name, result in results:
            if not result:
                print(f"  - {name}")
    
    print()
    print("="*60)
    print("测试完成")
    print("="*60)
    
    # 说明
    print()
    print("说明:")
    print("- 401状态码是预期的（需要认证）")
    print("- 422状态码是预期的（缺少参数）")
    print("- 503状态码是预期的（Redis未运行，但不影响服务）")
    print("- 如果看到200状态码，说明端点正常工作")


if __name__ == "__main__":
    asyncio.run(main())

