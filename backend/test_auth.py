"""
认证系统快速测试脚本
用于验证认证功能是否正常工作
"""

import asyncio
import httpx
from app.core.database import init_db
from app.models.user import User
from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token
from app.core.database import AsyncSessionLocal

from scripts.api_test_config import API_BASE_URL, API_PREFIX as CONFIG_API_PREFIX

PREFIX = CONFIG_API_PREFIX.rstrip("/")
BASE_API_URL = f"{API_BASE_URL}{PREFIX}" if PREFIX else API_BASE_URL


async def test_database():
    """测试数据库连接和初始化"""
    print("=" * 50)
    print("测试1: 数据库初始化")
    print("=" * 50)
    try:
        await init_db()
        print("[OK] 数据库初始化成功")
        return True
    except Exception as e:
        print(f"[FAIL] 数据库初始化失败: {e}")
        return False


async def test_password_hash():
    """测试密码哈希功能"""
    print("\n" + "=" * 50)
    print("测试2: 密码哈希功能")
    print("=" * 50)
    try:
        password = "test123456"
        hashed = get_password_hash(password)
        print(f"[OK] 密码哈希生成成功: {hashed[:20]}...")
        
        is_valid = verify_password(password, hashed)
        if is_valid:
            print("[OK] 密码验证成功")
        else:
            print("[FAIL] 密码验证失败")
            return False
        
        is_invalid = verify_password("wrong_password", hashed)
        if not is_invalid:
            print("[OK] 错误密码验证正确（返回False）")
        else:
            print("[FAIL] 错误密码验证失败（应该返回False）")
            return False
        
        return True
    except Exception as e:
        print(f"[FAIL] 密码哈希测试失败: {e}")
        return False


async def test_jwt():
    """测试JWT功能"""
    print("\n" + "=" * 50)
    print("测试3: JWT功能")
    print("=" * 50)
    try:
        data = {"sub": "testuser", "user_id": 1}
        token = create_access_token(data)
        print(f"[OK] JWT Token生成成功: {token[:30]}...")
        
        payload = decode_access_token(token)
        if payload.get("sub") == "testuser" and payload.get("user_id") == 1:
            print("[OK] JWT Token解码成功")
        else:
            print("[FAIL] JWT Token解码失败")
            return False
        
        return True
    except Exception as e:
        print(f"[FAIL] JWT测试失败: {e}")
        return False


async def test_user_model():
    """测试用户模型"""
    print("\n" + "=" * 50)
    print("测试4: 用户模型")
    print("=" * 50)
    try:
        async with AsyncSessionLocal() as db:
            # 测试创建用户
            hashed_password = get_password_hash("test123456")
            user = User(
                username="testuser",
                email="test@example.com",
                hashed_password=hashed_password,
                full_name="Test User"
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print(f"[OK] 用户创建成功: ID={user.id}, Username={user.username}")
            
            # 测试根据用户名查找
            found_user = await User.get_by_username(db, "testuser")
            if found_user and found_user.username == "testuser":
                print("[OK] 根据用户名查找用户成功")
            else:
                print("[FAIL] 根据用户名查找用户失败")
                return False
            
            # 测试根据邮箱查找
            found_user = await User.get_by_email(db, "test@example.com")
            if found_user and found_user.email == "test@example.com":
                print("[OK] 根据邮箱查找用户成功")
            else:
                print("[FAIL] 根据邮箱查找用户失败")
                return False
            
            # 清理测试数据
            await db.delete(user)
            await db.commit()
            print("[OK] 测试用户已清理")
        
        return True
    except Exception as e:
        print(f"[FAIL] 用户模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_endpoints():
    """测试API端点"""
    print("\n" + "=" * 50)
    print("测试5: API端点（需要后端服务运行）")
    print("=" * 50)
    print("[INFO] 请确保后端服务已启动: python main.py")
    print("[INFO] 如果后端未运行，此测试将跳过")
    
    base_url = BASE_API_URL
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # 测试健康检查
            try:
                response = await client.get("http://localhost:8000/health")
                if response.status_code == 200:
                    print("[OK] 后端服务运行正常")
                else:
                    print(f"[WARN] 后端服务响应异常: {response.status_code}")
                    return False
            except httpx.ConnectError:
                print("[WARN] 无法连接到后端服务，请先启动: python main.py")
                return False
            
            # 测试注册
            register_data = {
                "username": "apitestuser",
                "email": "apitest@example.com",
                "password": "test123456",
                "full_name": "API Test User"
            }
            response = await client.post(f"{base_url}/auth/register", json=register_data)
            if response.status_code == 201:
                print("[OK] 用户注册API测试成功")
                user_data = response.json()
                print(f"   用户ID: {user_data.get('id')}, 用户名: {user_data.get('username')}")
            else:
                print(f"[FAIL] 用户注册API测试失败: {response.status_code}")
                print(f"   响应: {response.text}")
                return False
            
            # 测试登录
            login_data = {
                "username": "apitestuser",
                "password": "test123456"
            }
            response = await client.post(
                f"{base_url}/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                print("[OK] 用户登录API测试成功")
                print(f"   Token: {access_token[:30]}...")
            else:
                print(f"[FAIL] 用户登录API测试失败: {response.status_code}")
                print(f"   响应: {response.text}")
                return False
            
            # 测试获取用户信息
            response = await client.get(
                f"{base_url}/auth/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if response.status_code == 200:
                user_data = response.json()
                print("[OK] 获取用户信息API测试成功")
                print(f"   用户名: {user_data.get('username')}, 邮箱: {user_data.get('email')}")
            else:
                print(f"[FAIL] 获取用户信息API测试失败: {response.status_code}")
                print(f"   响应: {response.text}")
                return False
            
            return True
    except Exception as e:
        print(f"[FAIL] API端点测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("VabHub 认证系统测试")
    print("=" * 50)
    
    results = []
    
    # 测试1: 数据库
    results.append(await test_database())
    
    # 测试2: 密码哈希
    results.append(await test_password_hash())
    
    # 测试3: JWT
    results.append(await test_jwt())
    
    # 测试4: 用户模型
    results.append(await test_user_model())
    
    # 测试5: API端点（可选）
    try:
        results.append(await test_api_endpoints())
    except Exception as e:
        print(f"\n[SKIP] API端点测试跳过: {e}")
        results.append(None)
    
    # 总结
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)
    
    passed = sum(1 for r in results if r is True)
    failed = sum(1 for r in results if r is False)
    skipped = sum(1 for r in results if r is None)
    
    print(f"[PASS] 通过: {passed}")
    print(f"[FAIL] 失败: {failed}")
    print(f"[SKIP] 跳过: {skipped}")
    
    if failed == 0:
        print("\n[SUCCESS] 所有测试通过！认证系统工作正常！")
        return 0
    else:
        print("\n[WARN] 部分测试失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

