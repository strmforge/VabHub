"""
集成测试脚本
测试多个功能模块的集成
"""

import asyncio
import httpx
import sys
from pathlib import Path

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

# 全局变量
auth_token = None
subscription_id = None
download_id = None


async def test_auth_flow():
    """测试认证流程"""
    print("="*60)
    print("集成测试1: 认证流程")
    print("="*60)
    
    global auth_token
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # 登录
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
                    print("[OK] 登录成功，Token已获取")
                    return True
                else:
                    print("[ERROR] 未获取到Token")
                    return False
            else:
                print(f"[ERROR] 登录失败: {response.status_code}")
                return False
    except Exception as e:
        print(f"[ERROR] 认证流程异常: {e}")
        return False


async def test_subscription_workflow():
    """测试订阅工作流"""
    print("\n" + "="*60)
    print("集成测试2: 订阅工作流")
    print("="*60)
    
    global auth_token, subscription_id
    
    if not auth_token:
        print("[SKIP] 未获取到Token，跳过测试")
        return False
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            headers = {"Authorization": f"Bearer {auth_token}"}
            
            # 1. 创建订阅
            print("  1. 创建订阅...")
            response = await client.post(
                api_url("/subscriptions/"),
                headers=headers,
                json={
                    "title": "集成测试订阅",
                    "media_type": "movie",
                    "year": 2024,
                    "quality": "1080p",
                    "auto_download": False
                }
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                if "data" in data and "id" in data["data"]:
                    subscription_id = data["data"]["id"]
                    print(f"     [OK] 订阅创建成功，ID: {subscription_id}")
                else:
                    print("     [ERROR] 未获取到订阅ID")
                    return False
            else:
                print(f"     [ERROR] 创建订阅失败: {response.status_code}")
                print(f"     Response: {response.text[:200]}")
                return False
            
            # 2. 获取订阅列表
            print("  2. 获取订阅列表...")
            response = await client.get(
                api_url("/subscriptions/?page=1&page_size=10"),
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "items" in data["data"]:
                    items = data["data"]["items"]
                    print(f"     [OK] 获取订阅列表成功，数量: {len(items)}")
                else:
                    print("     [ERROR] 订阅列表数据格式错误")
                    return False
            else:
                print(f"     [ERROR] 获取订阅列表失败: {response.status_code}")
                return False
            
            # 3. 获取订阅详情
            if subscription_id:
                print(f"  3. 获取订阅详情 (ID: {subscription_id})...")
                response = await client.get(
                    api_url(f"/subscriptions/{subscription_id}"),
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "data" in data:
                        print("     [OK] 获取订阅详情成功")
                    else:
                        print("     [ERROR] 订阅详情数据格式错误")
                        return False
                else:
                    print(f"     [ERROR] 获取订阅详情失败: {response.status_code}")
                    return False
            
            return True
            
    except Exception as e:
        print(f"[ERROR] 订阅工作流异常: {e}")
        return False


async def test_dashboard_integration():
    """测试仪表盘集成"""
    print("\n" + "="*60)
    print("集成测试3: 仪表盘集成")
    print("="*60)
    
    if not auth_token:
        print("[SKIP] 未获取到Token，跳过测试")
        return False
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            headers = {"Authorization": f"Bearer {auth_token}"}
            
            # 获取仪表盘数据
            response = await client.get(
                api_url("/dashboard/"),
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    dashboard_data = data["data"]
                    print("[OK] 获取仪表盘数据成功")
                    print(f"     数据键: {list(dashboard_data.keys())[:5]}")
                    return True
                else:
                    print("[ERROR] 仪表盘数据格式错误")
                    return False
            else:
                print(f"[ERROR] 获取仪表盘数据失败: {response.status_code}")
                print(f"     Response: {response.text[:200]}")
                return False
    except Exception as e:
        print(f"[ERROR] 仪表盘集成异常: {e}")
        return False


async def test_settings_integration():
    """测试设置集成"""
    print("\n" + "="*60)
    print("集成测试4: 设置集成")
    print("="*60)
    
    if not auth_token:
        print("[SKIP] 未获取到Token，跳过测试")
        return False
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            headers = {"Authorization": f"Bearer {auth_token}"}
            
            # 获取设置
            response = await client.get(
                api_url("/settings/"),
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    settings = data["data"]
                    if isinstance(settings, list):
                        print(f"[OK] 获取设置成功，数量: {len(settings)}")
                    elif isinstance(settings, dict):
                        print(f"[OK] 获取设置成功，键: {list(settings.keys())[:5]}")
                    return True
                else:
                    print("[ERROR] 设置数据格式错误")
                    return False
            else:
                print(f"[ERROR] 获取设置失败: {response.status_code}")
                print(f"     Response: {response.text[:200]}")
                return False
    except Exception as e:
        print(f"[ERROR] 设置集成异常: {e}")
        return False


async def test_search_integration():
    """测试搜索集成"""
    print("\n" + "="*60)
    print("集成测试5: 搜索集成")
    print("="*60)
    
    if not auth_token:
        print("[SKIP] 未获取到Token，跳过测试")
        return False
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            headers = {"Authorization": f"Bearer {auth_token}"}
            
            # 搜索
            response = await client.get(
                api_url("/search/?query=test&page=1&page_size=10"),
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    print("[OK] 搜索成功")
                    return True
                else:
                    print("[ERROR] 搜索数据格式错误")
                    return False
            else:
                print(f"[ERROR] 搜索失败: {response.status_code}")
                return False
    except Exception as e:
        print(f"[ERROR] 搜索集成异常: {e}")
        return False


async def main():
    """主测试函数"""
    print("="*60)
    print("VabHub 集成测试")
    print("="*60)
    print()
    print(f"测试服务器: {BASE_URL}")
    print(f"测试用户: {TEST_USERNAME}")
    print()
    
    results = []
    
    # 测试1: 认证流程
    result = await test_auth_flow()
    results.append(("认证流程", result))
    await asyncio.sleep(1)
    
    # 测试2: 订阅工作流
    if auth_token:
        result = await test_subscription_workflow()
        results.append(("订阅工作流", result))
        await asyncio.sleep(1)
    
    # 测试3: 仪表盘集成
    if auth_token:
        result = await test_dashboard_integration()
        results.append(("仪表盘集成", result))
        await asyncio.sleep(1)
    
    # 测试4: 设置集成
    if auth_token:
        result = await test_settings_integration()
        results.append(("设置集成", result))
        await asyncio.sleep(1)
    
    # 测试5: 搜索集成
    if auth_token:
        result = await test_search_integration()
        results.append(("搜索集成", result))
        await asyncio.sleep(1)
    
    # 统计结果
    print("\n" + "="*60)
    print("集成测试结果汇总")
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
    print("集成测试完成")
    print("="*60)
    
    return passed, total


if __name__ == "__main__":
    asyncio.run(main())

