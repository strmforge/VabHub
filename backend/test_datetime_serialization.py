"""
测试datetime序列化问题
"""

import asyncio
import json
from datetime import datetime
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder

# 模拟UserResponse
class TestUserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str = None
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True

async def test_serialization():
    print("测试datetime序列化...")
    
    # 创建测试数据
    user_data = TestUserResponse(
        id=1,
        username="test_user",
        email="test@example.com",
        full_name="Test User",
        is_active=True,
        is_superuser=False,
        created_at=datetime.now()
    )
    
    # 方法1: 直接dict()
    try:
        result1 = user_data.model_dump()
        print("方法1 (model_dump()):", result1)
        json_str1 = json.dumps(result1, default=str)
        print("JSON序列化成功:", json_str1[:100] + "...")
    except Exception as e:
        print("方法1失败:", e)
    
    # 方法2: model_dump(mode='json')
    try:
        result2 = user_data.model_dump(mode='json')
        print("方法2 (mode='json'):", result2)
        json_str2 = json.dumps(result2)
        print("JSON序列化成功:", json_str2[:100] + "...")
    except Exception as e:
        print("方法2失败:", e)
    
    # 方法3: jsonable_encoder
    try:
        result3 = jsonable_encoder(user_data)
        print("方法3 (jsonable_encoder):", result3)
        json_str3 = json.dumps(result3)
        print("JSON序列化成功:", json_str3[:100] + "...")
    except Exception as e:
        print("方法3失败:", e)
    
    # 方法4: 手动处理datetime
    try:
        result4 = {
            "id": user_data.id,
            "username": user_data.username,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "is_active": user_data.is_active,
            "is_superuser": user_data.is_superuser,
            "created_at": user_data.created_at.isoformat()
        }
        print("方法4 (手动处理):", result4)
        json_str4 = json.dumps(result4)
        print("JSON序列化成功:", json_str4[:100] + "...")
    except Exception as e:
        print("方法4失败:", e)

if __name__ == "__main__":
    asyncio.run(test_serialization())