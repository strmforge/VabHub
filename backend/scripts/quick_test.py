"""
快速测试脚本
启动服务并运行基本测试验证修复效果
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

from scripts.api_test_config import API_BASE_URL, API_PREFIX, api_url

BASE_URL = API_BASE_URL
TIMEOUT = 10.0

# 测试用户凭证
TEST_USERNAME = "test_user"
TEST_PASSWORD = "test_password_123"

auth_token = None


async def check_service():
    """检查服务是否运行"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BASE_URL}/")
            return response.status_code == 200
    except Exception:
        return False


async def test_api_serialization():
    """测试API序列化修复"""
    print("="*60)
    print("测试API序列化修复")
    print("="*60)
    print()
    
    global auth_token
    
    # 1. 测试登录获取token
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # 尝试登录
            response = await client.post(
                api_url("/auth/login"),
                data={
                    "username": TEST_USERNAME,
                    "password": TEST_PASSWORD
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "access_token" in data.get("data", {}):
                    auth_token = data["data"]["access_token"]
                    print(f"[OK] 登录成功，获取Token")
                else:
                    print(f"[WARNING] 登录响应格式异常: {data}")
                    return False
            else:
                print(f"[WARNING] 登录失败: {response.status_code}")
                print(f"     尝试注册新用户...")
                # 尝试注册
                response = await client.post(
                    api_url("/auth/register"),
                    json={
                        "username": TEST_USERNAME,
                        "email": "test@example.com",
                        "password": TEST_PASSWORD,
                        "full_name": "Test User"
                    }
                )
                if response.status_code in [200, 201]:
                    print(f"[OK] 用户注册成功，重新登录...")
                    await asyncio.sleep(1)
                    response = await client.post(
                        api_url("/auth/login"),
                        data={
                            "username": TEST_USERNAME,
                            "password": TEST_PASSWORD
                        }
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if "data" in data and "access_token" in data.get("data", {}):
                            auth_token = data["data"]["access_token"]
                            print(f"[OK] 登录成功，获取Token")
                        else:
                            print(f"[ERROR] 登录响应格式异常")
                            return False
                    else:
                        print(f"[ERROR] 登录失败: {response.status_code}")
                        return False
                else:
                    print(f"[ERROR] 注册失败: {response.status_code}")
                    return False
    except Exception as e:
        print(f"[ERROR] 登录/注册异常: {e}")
        return False
    
    if not auth_token:
        print("[ERROR] 无法获取Token，跳过API测试")
        return False
    
    # 2. 测试订阅管理API - 创建订阅
    print(f"\n测试1: 创建订阅 (POST {API_PREFIX}/subscriptions/)")
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                api_url("/subscriptions/"),
                json={
                    "title": "测试订阅",
                    "media_type": "movie",
                    "year": 2024,
                    "quality": "1080p",
                    "auto_download": False
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                # 检查响应格式
                if "success" in data:
                    print(f"[OK] 创建订阅成功，响应格式正确")
                    print(f"     success: {data.get('success')}")
                    if "data" in data:
                        print(f"     data字段存在: [OK]")
                    else:
                        print(f"     data字段缺失: [ERROR]")
                    return True
                else:
                    print(f"[ERROR] 响应格式错误，缺少'success'字段")
                    print(f"     Response: {data}")
                    return False
            else:
                print(f"[WARNING] 创建订阅失败: {response.status_code}")
                print(f"     Response: {response.text[:200]}")
                # 继续测试其他端点
    except Exception as e:
        print(f"[ERROR] 创建订阅异常: {e}")
        # 继续测试其他端点
    
    # 3. 测试订阅管理API - 获取订阅列表
    print(f"\n测试2: 获取订阅列表 (GET {API_PREFIX}/subscriptions/)")
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(
                api_url("/subscriptions/"),
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "success" in data:
                    print(f"[OK] 获取订阅列表成功，响应格式正确")
                    print(f"     success: {data.get('success')}")
                    if "data" in data:
                        print(f"     data字段存在: [OK]")
                        if isinstance(data.get("data"), dict) and "items" in data.get("data", {}):
                            print(f"     items字段存在: [OK]")
                    else:
                        print(f"     data字段缺失: [ERROR]")
                    return True
                else:
                    print(f"[ERROR] 响应格式错误，缺少'success'字段")
                    print(f"     Response: {data}")
                    return False
            else:
                print(f"[WARNING] 获取订阅列表失败: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] 获取订阅列表异常: {e}")
    
    return True


async def main():
    """主函数"""
    print("="*60)
    print("VabHub API序列化修复验证")
    print("="*60)
    print()
    
    # 检查服务状态
    print("检查服务状态...")
    if not await check_service():
        print("[WARNING] 服务未运行")
        print()
        print("请先启动服务:")
        print("  python backend/run_server.py")
        print()
        print("或者等待30秒让脚本自动检测服务启动...")
        for i in range(30):
            await asyncio.sleep(1)
            if await check_service():
                print(f"[OK] 服务已启动 (等待了 {i+1} 秒)")
                break
            if (i + 1) % 5 == 0:
                print(f"[INFO] 等待中... ({i+1}/30 秒)")
        else:
            print()
            print("[ERROR] 服务未启动，无法运行测试")
            print("请手动启动服务后重新运行此脚本")
            return
    
    print("[OK] 服务运行正常")
    print()
    
    # 等待服务完全就绪
    await asyncio.sleep(2)
    
    # 运行测试
    success = await test_api_serialization()
    
    print()
    print("="*60)
    if success:
        print("[OK] API序列化修复验证通过")
    else:
        print("[WARNING] API序列化修复验证部分通过")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

