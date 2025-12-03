"""
功能测试脚本
测试主要功能模块的实际功能
"""

import asyncio
import httpx
import sys
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from scripts.api_test_config import API_BASE_URL, API_PREFIX, api_url

BASE_URL = API_BASE_URL
TIMEOUT = 30.0

# 测试用户凭证
TEST_USERNAME = "test_user"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "test_password_123"

# 全局变量存储token
auth_token = None


async def test_user_registration():
    """测试用户注册"""
    print("="*60)
    print("测试1: 用户注册")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                api_url("/auth/register"),
                json={
                    "username": TEST_USERNAME,
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD,
                    "full_name": "Test User"
                }
            )
            
            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                print(f"[OK] 用户注册成功: {response.status_code}")
                # 注册后需要登录获取token
                print(f"[INFO] 注册成功，尝试登录获取Token")
                return await test_user_login()
            elif response.status_code == 400:
                data = response.json()
                if "已存在" in str(data.get("message", "")) or "USERNAME_EXISTS" in str(data) or "EMAIL_EXISTS" in str(data):
                    print(f"[INFO] 用户已存在，尝试登录")
                    return await test_user_login()
                else:
                    print(f"[ERROR] 用户注册失败: {response.status_code}")
                    print(f"     Response: {data}")
                    return False
            else:
                print(f"[ERROR] 用户注册失败: {response.status_code}")
                print(f"     Response: {response.text[:200]}")
                return False
    except httpx.ConnectError as e:
        print(f"[ERROR] 无法连接到服务: {e}")
        print(f"     请确保后端服务已启动: python backend/run_server.py")
        return False
    except httpx.ReadTimeout as e:
        print(f"[ERROR] 请求超时: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 用户注册异常: {type(e).__name__}: {e}")
        import traceback
        print(f"     详细错误: {traceback.format_exc()}")
        return False


async def test_user_login():
    """测试用户登录"""
    print("\n" + "="*60)
    print("测试2: 用户登录")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                api_url("/auth/login"),
                data={
                    "username": TEST_USERNAME,
                    "password": TEST_PASSWORD
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"[OK] 用户登录成功: {response.status_code}")
                if "data" in data and "access_token" in data.get("data", {}):
                    global auth_token
                    auth_token = data["data"]["access_token"]
                    print(f"     Token已获取")
                    return True
                else:
                    print(f"[WARNING] 未获取到Token")
                    return False
            else:
                print(f"[ERROR] 用户登录失败: {response.status_code}")
                print(f"     Response: {response.text[:200]}")
                return False
    except httpx.ConnectError as e:
        print(f"[ERROR] 无法连接到服务: {e}")
        print(f"     请确保后端服务已启动: python backend/run_server.py")
        return None
    except httpx.ReadTimeout as e:
        print(f"[ERROR] 请求超时: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] 用户登录异常: {type(e).__name__}: {e}")
        import traceback
        print(f"     详细错误: {traceback.format_exc()}")
        return None


async def test_get_user_info():
    """测试获取用户信息"""
    print("\n" + "="*60)
    print("测试3: 获取用户信息")
    print("="*60)
    
    if not auth_token:
        print("[SKIP] 未获取到Token，跳过测试")
        return False
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            headers = {"Authorization": f"Bearer {auth_token}"}
            response = await client.get(
                api_url("/auth/me"),
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"[OK] 获取用户信息成功: {response.status_code}")
                if "data" in data:
                    user_data = data["data"]
                    print(f"     用户名: {user_data.get('username')}")
                    print(f"     邮箱: {user_data.get('email')}")
                return True
            else:
                print(f"[ERROR] 获取用户信息失败: {response.status_code}")
                print(f"     Response: {response.text[:200]}")
                return False
    except Exception as e:
        print(f"[ERROR] 获取用户信息异常: {e}")
        return False


async def test_create_subscription():
    """测试创建订阅"""
    print("\n" + "="*60)
    print("测试4: 创建订阅")
    print("="*60)
    
    if not auth_token:
        print("[SKIP] 未获取到Token，跳过测试")
        return False
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            headers = {"Authorization": f"Bearer {auth_token}"}
            response = await client.post(
                api_url("/subscriptions/"),
                headers=headers,
                json={
                    "title": "测试订阅",
                    "media_type": "movie",
                    "year": 2024,
                    "quality": "1080p",
                    "auto_download": False
                }
            )
            
            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                print(f"[OK] 创建订阅成功: {response.status_code}")
                if "data" in data:
                    sub_data = data["data"]
                    print(f"     订阅ID: {sub_data.get('id')}")
                    print(f"     标题: {sub_data.get('title')}")
                    return sub_data.get('id')
                return True
            else:
                print(f"[ERROR] 创建订阅失败: {response.status_code}")
                print(f"     Response: {response.text[:200]}")
                return False
    except Exception as e:
        print(f"[ERROR] 创建订阅异常: {e}")
        return False


async def test_get_subscriptions():
    """测试获取订阅列表"""
    print("\n" + "="*60)
    print("测试5: 获取订阅列表")
    print("="*60)
    
    if not auth_token:
        print("[SKIP] 未获取到Token，跳过测试")
        return False
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            headers = {"Authorization": f"Bearer {auth_token}"}
            response = await client.get(
                api_url("/subscriptions/?page=1&page_size=10"),
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"[OK] 获取订阅列表成功: {response.status_code}")
                if "data" in data:
                    items = data["data"].get("items", [])
                    print(f"     订阅数量: {len(items)}")
                    print(f"     总数量: {data['data'].get('total', 0)}")
                return True
            else:
                print(f"[ERROR] 获取订阅列表失败: {response.status_code}")
                print(f"     Response: {response.text[:200]}")
                return False
    except Exception as e:
        print(f"[ERROR] 获取订阅列表异常: {e}")
        return False


async def test_get_dashboard():
    """测试获取仪表盘数据"""
    print("\n" + "="*60)
    print("测试6: 获取仪表盘数据")
    print("="*60)
    
    if not auth_token:
        print("[SKIP] 未获取到Token，跳过测试")
        return False
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            headers = {"Authorization": f"Bearer {auth_token}"}
            response = await client.get(
                api_url("/dashboard/"),
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"[OK] 获取仪表盘数据成功: {response.status_code}")
                if "data" in data:
                    dashboard_data = data["data"]
                    print(f"     统计数据: {list(dashboard_data.keys())}")
                return True
            else:
                print(f"[ERROR] 获取仪表盘数据失败: {response.status_code}")
                print(f"     Response: {response.text[:200]}")
                return False
    except Exception as e:
        print(f"[ERROR] 获取仪表盘数据异常: {e}")
        return False


async def test_get_settings():
    """测试获取设置"""
    print("\n" + "="*60)
    print("测试7: 获取设置")
    print("="*60)
    
    if not auth_token:
        print("[SKIP] 未获取到Token，跳过测试")
        return False
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            headers = {"Authorization": f"Bearer {auth_token}"}
            response = await client.get(
                api_url("/settings/"),
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"[OK] 获取设置成功: {response.status_code}")
                if "data" in data:
                    settings = data["data"]
                    if isinstance(settings, list):
                        print(f"     设置数量: {len(settings)}")
                    elif isinstance(settings, dict):
                        print(f"     设置键: {list(settings.keys())[:5]}")
                return True
            else:
                print(f"[ERROR] 获取设置失败: {response.status_code}")
                print(f"     Response: {response.text[:200]}")
                return False
    except Exception as e:
        print(f"[ERROR] 获取设置异常: {e}")
        return False


async def main():
    """主测试函数"""
    print("="*60)
    print("VabHub 功能测试")
    print("="*60)
    print()
    print(f"测试服务器: {BASE_URL}")
    print(f"测试用户: {TEST_USERNAME}")
    print()
    
    results = []
    
    # 测试1: 用户注册
    result = await test_user_registration()
    results.append(("用户注册", result))
    await asyncio.sleep(1)
    
    # 测试2: 用户登录（如果注册失败或需要重新登录）
    if not result or not auth_token:
        result = await test_user_login()
        results.append(("用户登录", result))
        await asyncio.sleep(1)
    
    # 测试3: 获取用户信息
    if auth_token:
        result = await test_get_user_info()
        results.append(("获取用户信息", result))
        await asyncio.sleep(1)
    
    # 测试4: 创建订阅
    if auth_token:
        result = await test_create_subscription()
        results.append(("创建订阅", result))
        await asyncio.sleep(1)
    
    # 测试5: 获取订阅列表
    if auth_token:
        result = await test_get_subscriptions()
        results.append(("获取订阅列表", result))
        await asyncio.sleep(1)
    
    # 测试6: 获取仪表盘数据
    if auth_token:
        result = await test_get_dashboard()
        results.append(("获取仪表盘数据", result))
        await asyncio.sleep(1)
    
    # 测试7: 获取设置
    if auth_token:
        result = await test_get_settings()
        results.append(("获取设置", result))
        await asyncio.sleep(1)
    
    # 统计结果
    print("\n" + "="*60)
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


if __name__ == "__main__":
    asyncio.run(main())

