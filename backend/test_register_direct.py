"""
直接测试用户注册API
"""

import asyncio
import httpx
import json

API_BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

async def test_register():
    """测试用户注册"""
    url = f"{API_BASE_URL}{API_PREFIX}/auth/register"
    data = {
        "username": "direct_test_user",
        "email": "direct_test@example.com", 
        "password": "test123456"
    }
    
    print(f"测试注册URL: {url}")
    print(f"测试数据: {data}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=data)
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            print(f"响应内容: {response.text}")
            
            # 尝试解析JSON
            try:
                resp_json = response.json()
                print(f"解析后的JSON: {json.dumps(resp_json, indent=2, ensure_ascii=False)}")
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
                
        except Exception as e:
            print(f"请求失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_register())