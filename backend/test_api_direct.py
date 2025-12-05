"""
直接测试API端点（不依赖完整服务启动）
"""

import asyncio
import httpx
import sys

from scripts.api_test_config import API_BASE_URL, api_url


async def test_api():
    """测试API端点"""
    base_url = API_BASE_URL
    
    print("=" * 60)
    print("VabHub API 端点测试")
    print("=" * 60)
    print()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 测试1: 健康检查
            print("[测试1] 健康检查...")
            try:
                response = await client.get(f"{API_BASE_URL}/health")
                if response.status_code == 200:
                    print(f"  [OK] 后端服务运行正常: {response.json()}")
                else:
                    print(f"  [FAIL] 后端服务响应异常: {response.status_code}")
                    return False
            except httpx.ConnectError:
                print("  [FAIL] 无法连接到后端服务")
                print("  请先启动后端服务: python main.py")
                return False
            
            print()
            
            # 测试2: 注册用户
            print("[测试2] 用户注册...")
            register_data = {
                "username": "apitestuser",
                "email": "apitest@example.com",
                "password": "test123456",
                "full_name": "API Test User"
            }
            response = await client.post(api_url("/auth/register"), json=register_data)
            if response.status_code == 201:
                user_data = response.json()
                print("  [OK] 用户注册成功")
                print(f"    用户ID: {user_data.get('id')}")
                print(f"    用户名: {user_data.get('username')}")
                print(f"    邮箱: {user_data.get('email')}")
            else:
                print(f"  [FAIL] 用户注册失败: {response.status_code}")
                print(f"    响应: {response.text}")
                return False
            
            print()
            
            # 测试3: 登录
            print("[测试3] 用户登录...")
            login_data = {
                "username": "apitestuser",
                "password": "test123456"
            }
            response = await client.post(
                api_url("/auth/login"),
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                print("  [OK] 用户登录成功")
                print(f"    Token: {access_token[:50]}...")
            else:
                print(f"  [FAIL] 用户登录失败: {response.status_code}")
                print(f"    响应: {response.text}")
                return False
            
            print()
            
            # 测试4: 获取用户信息
            print("[测试4] 获取用户信息...")
            response = await client.get(
                api_url("/auth/me"),
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if response.status_code == 200:
                user_data = response.json()
                print("  [OK] 获取用户信息成功")
                print(f"    用户名: {user_data.get('username')}")
                print(f"    邮箱: {user_data.get('email')}")
                print(f"    全名: {user_data.get('full_name')}")
            else:
                print(f"  [FAIL] 获取用户信息失败: {response.status_code}")
                print(f"    响应: {response.text}")
                return False
            
            print()
            
            # 测试5: 无效token测试
            print("[测试5] 无效Token测试...")
            response = await client.get(
                api_url("/auth/me"),
                headers={"Authorization": "Bearer invalid_token_12345"}
            )
            if response.status_code == 401:
                print("  [OK] 无效Token正确拒绝 (401)")
            else:
                print(f"  [WARN] 无效Token测试: {response.status_code}")
            
            print()
            print("=" * 60)
            print("[SUCCESS] 所有API测试通过！")
            print("=" * 60)
            return True
            
    except Exception as e:
        print(f"[ERROR] 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_api())
    sys.exit(0 if success else 1)

