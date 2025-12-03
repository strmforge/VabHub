"""
测试用户注册
"""

import asyncio
import httpx
import json
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from scripts.api_test_config import API_BASE_URL, api_url

async def test_register():
    """测试用户注册"""
    BASE_URL = API_BASE_URL
    
    # 测试新用户注册
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("测试1: 注册新用户")
        response = await client.post(
            api_url("/auth/register"),
            json={
                "username": "test_user_new",
                "email": "test_new@example.com",
                "password": "test_password_123",
                "full_name": "Test User New"
            }
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        print()
        
        # 测试重复注册（应该返回400错误）
        print("测试2: 重复注册（应该失败）")
        response2 = await client.post(
            api_url("/auth/register"),
            json={
                "username": "test_user_new",
                "email": "test_new2@example.com",
                "password": "test_password_123",
                "full_name": "Test User New"
            }
        )
        
        print(f"状态码: {response2.status_code}")
        print(f"响应: {json.dumps(response2.json(), indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    asyncio.run(test_register())

