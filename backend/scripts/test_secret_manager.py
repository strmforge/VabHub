"""
测试密钥管理功能
测试SecretManager的密钥生成、加载、环境变量覆盖等功能
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.secret_manager import SecretManager, initialize_secrets
from app.core.config import settings


def print_section(title: str):
    """打印测试章节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(test_name: str, passed: bool, details: str = ""):
    """打印测试结果"""
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status}: {test_name}")
    if details:
        print(f"  详情: {details}")


def test_1_secret_generation():
    """测试1: 密钥生成"""
    print_section("测试1: 密钥生成")
    
    # 删除密钥文件（模拟首次安装）
    secrets_file = Path("./data/.vabhub_secrets.json")
    original_secrets = None
    if secrets_file.exists():
        # 保存原始密钥用于后续测试
        with open(secrets_file, 'r', encoding='utf-8') as f:
            original_secrets = json.load(f)
        print(f"备份现有密钥文件: {secrets_file}")
        secrets_file.unlink()
    
    # 创建新的SecretManager实例
    manager = SecretManager()
    
    # 测试生成SECRET_KEY
    secret_key = manager.get_secret_key()
    passed_1 = len(secret_key) > 0 and secret_key != "change-this-to-a-random-secret-key-in-production"
    print_result("SECRET_KEY生成", passed_1, f"长度: {len(secret_key)} 字符")
    
    # 测试生成JWT_SECRET_KEY
    jwt_secret = manager.get_jwt_secret_key()
    passed_2 = len(jwt_secret) > 0 and jwt_secret != "change-this-to-a-random-jwt-secret-key-in-production"
    print_result("JWT_SECRET_KEY生成", passed_2, f"长度: {len(jwt_secret)} 字符")
    
    # 测试生成API_TOKEN
    api_token = manager.get_api_token()
    passed_3 = len(api_token) > 0
    print_result("API_TOKEN生成", passed_3, f"长度: {len(api_token)} 字符")
    
    # 验证密钥文件是否存在
    file_exists = secrets_file.exists()
    print_result("密钥文件创建", file_exists, f"路径: {str(secrets_file.absolute())}")
    
    # 验证密钥文件格式
    if file_exists:
        try:
            with open(secrets_file, 'r', encoding='utf-8') as f:
                secrets_data = json.load(f)
            has_secret_key = "SECRET_KEY" in secrets_data
            has_jwt_secret = "JWT_SECRET_KEY" in secrets_data
            has_api_token = "API_TOKEN" in secrets_data
            print_result("密钥文件格式", has_secret_key and has_jwt_secret and has_api_token, 
                        f"包含: SECRET_KEY={has_secret_key}, JWT_SECRET_KEY={has_jwt_secret}, API_TOKEN={has_api_token}")
            
            # 显示密钥（部分隐藏）
            if has_secret_key:
                print(f"  SECRET_KEY: {secrets_data['SECRET_KEY'][:20]}...")
            if has_jwt_secret:
                print(f"  JWT_SECRET_KEY: {secrets_data['JWT_SECRET_KEY'][:20]}...")
            if has_api_token:
                print(f"  API_TOKEN: {secrets_data['API_TOKEN'][:20]}...")
            
            # 保存生成的密钥到全局变量，供测试2使用
            test_1_secret_generation.generated_secrets = secrets_data
        except Exception as e:
            print_result("密钥文件格式", False, f"解析失败: {e}")
            test_1_secret_generation.generated_secrets = None
    
    # 验证文件权限（Unix系统）
    if file_exists and os.name != 'nt':
        file_stat = os.stat(secrets_file)
        file_mode = oct(file_stat.st_mode)[-3:]
        expected_mode = "600"
        passed_perm = file_mode == expected_mode
        print_result("密钥文件权限", passed_perm, f"当前: {file_mode}, 期望: {expected_mode}")
    
    return passed_1 and passed_2 and passed_3 and file_exists

# 初始化全局变量
test_1_secret_generation.generated_secrets = None


def test_2_secret_loading():
    """测试2: 密钥加载"""
    print_section("测试2: 密钥加载")
    
    # 使用测试1生成的密钥
    if test_1_secret_generation.generated_secrets is None:
        # 如果测试1没有保存，尝试从文件读取
        secrets_file = Path("./data/.vabhub_secrets.json")
        if not secrets_file.exists():
            print("[WARNING] 密钥文件不存在，请先运行测试1")
            return False
        with open(secrets_file, 'r', encoding='utf-8') as f:
            original_secrets = json.load(f)
    else:
        original_secrets = test_1_secret_generation.generated_secrets
    
    # 创建新的SecretManager实例（模拟重启）
    manager = SecretManager()
    
    # 测试加载SECRET_KEY
    loaded_secret_key = manager.get_secret_key()
    passed_1 = loaded_secret_key == original_secrets.get("SECRET_KEY")
    print_result("SECRET_KEY加载", passed_1, 
                f"原始: {original_secrets.get('SECRET_KEY', '')[:20]}..., "
                f"加载: {loaded_secret_key[:20]}...")
    
    # 测试加载JWT_SECRET_KEY
    loaded_jwt_secret = manager.get_jwt_secret_key()
    passed_2 = loaded_jwt_secret == original_secrets.get("JWT_SECRET_KEY")
    print_result("JWT_SECRET_KEY加载", passed_2,
                f"原始: {original_secrets.get('JWT_SECRET_KEY', '')[:20]}..., "
                f"加载: {loaded_jwt_secret[:20]}...")
    
    # 测试加载API_TOKEN
    loaded_api_token = manager.get_api_token()
    passed_3 = loaded_api_token == original_secrets.get("API_TOKEN")
    print_result("API_TOKEN加载", passed_3,
                f"原始: {original_secrets.get('API_TOKEN', '')[:20]}..., "
                f"加载: {loaded_api_token[:20]}...")
    
    return passed_1 and passed_2 and passed_3


def test_3_env_override():
    """测试3: 环境变量覆盖"""
    print_section("测试3: 环境变量覆盖")
    
    # 保存原始环境变量
    original_secret_key = os.environ.get("SECRET_KEY")
    original_jwt_secret = os.environ.get("JWT_SECRET_KEY")
    original_api_token = os.environ.get("API_TOKEN")
    
    try:
        # 设置测试环境变量
        test_secret_key = "test-secret-key-from-env-12345"
        test_jwt_secret = "test-jwt-secret-from-env-67890"
        test_api_token = "test-api-token-from-env-abcde"
        
        os.environ["SECRET_KEY"] = test_secret_key
        os.environ["JWT_SECRET_KEY"] = test_jwt_secret
        os.environ["API_TOKEN"] = test_api_token
        
        # 创建新的SecretManager实例
        manager = SecretManager()
        
        # 测试环境变量覆盖SECRET_KEY
        loaded_secret_key = manager.get_secret("SECRET_KEY")
        passed_1 = loaded_secret_key == test_secret_key
        print_result("SECRET_KEY环境变量覆盖", passed_1,
                    f"期望: {test_secret_key}, 实际: {loaded_secret_key}")
        
        # 测试环境变量覆盖JWT_SECRET_KEY
        loaded_jwt_secret = manager.get_secret("JWT_SECRET_KEY")
        passed_2 = loaded_jwt_secret == test_jwt_secret
        print_result("JWT_SECRET_KEY环境变量覆盖", passed_2,
                    f"期望: {test_jwt_secret}, 实际: {loaded_jwt_secret}")
        
        # 测试环境变量覆盖API_TOKEN
        loaded_api_token = manager.get_secret("API_TOKEN")
        passed_3 = loaded_api_token == test_api_token
        print_result("API_TOKEN环境变量覆盖", passed_3,
                    f"期望: {test_api_token}, 实际: {loaded_api_token}")
        
        return passed_1 and passed_2 and passed_3
        
    finally:
        # 恢复原始环境变量
        if original_secret_key is not None:
            os.environ["SECRET_KEY"] = original_secret_key
        elif "SECRET_KEY" in os.environ:
            del os.environ["SECRET_KEY"]
        
        if original_jwt_secret is not None:
            os.environ["JWT_SECRET_KEY"] = original_jwt_secret
        elif "JWT_SECRET_KEY" in os.environ:
            del os.environ["JWT_SECRET_KEY"]
        
        if original_api_token is not None:
            os.environ["API_TOKEN"] = original_api_token
        elif "API_TOKEN" in os.environ:
            del os.environ["API_TOKEN"]


def test_4_uniqueness():
    """测试4: 密钥唯一性"""
    print_section("测试4: 密钥唯一性")
    
    # 创建两个不同的SecretManager实例（模拟两个安装）
    temp_dir_1 = Path("./data/test_instance_1")
    temp_dir_2 = Path("./data/test_instance_2")
    
    temp_dir_1.mkdir(parents=True, exist_ok=True)
    temp_dir_2.mkdir(parents=True, exist_ok=True)
    
    try:
        # 实例1
        manager_1 = SecretManager(config_file=temp_dir_1 / ".vabhub_secrets.json")
        secret_key_1 = manager_1.get_secret_key()
        jwt_secret_1 = manager_1.get_jwt_secret_key()
        api_token_1 = manager_1.get_api_token()
        
        # 实例2
        manager_2 = SecretManager(config_file=temp_dir_2 / ".vabhub_secrets.json")
        secret_key_2 = manager_2.get_secret_key()
        jwt_secret_2 = manager_2.get_jwt_secret_key()
        api_token_2 = manager_2.get_api_token()
        
        # 验证唯一性
        passed_1 = secret_key_1 != secret_key_2
        print_result("SECRET_KEY唯一性", passed_1,
                    f"实例1: {secret_key_1[:20]}..., 实例2: {secret_key_2[:20]}...")
        
        passed_2 = jwt_secret_1 != jwt_secret_2
        print_result("JWT_SECRET_KEY唯一性", passed_2,
                    f"实例1: {jwt_secret_1[:20]}..., 实例2: {jwt_secret_2[:20]}...")
        
        passed_3 = api_token_1 != api_token_2
        print_result("API_TOKEN唯一性", passed_3,
                    f"实例1: {api_token_1[:20]}..., 实例2: {api_token_2[:20]}...")
        
        return passed_1 and passed_2 and passed_3
        
    finally:
        # 清理测试文件
        if (temp_dir_1 / ".vabhub_secrets.json").exists():
            (temp_dir_1 / ".vabhub_secrets.json").unlink()
        if temp_dir_1.exists():
            temp_dir_1.rmdir()
        
        if (temp_dir_2 / ".vabhub_secrets.json").exists():
            (temp_dir_2 / ".vabhub_secrets.json").unlink()
        if temp_dir_2.exists():
            temp_dir_2.rmdir()


def test_5_strm_integration():
    """测试5: STRM集成"""
    print_section("测试5: STRM集成")
    
    try:
        # 初始化密钥
        initialize_secrets()
        
        # 测试动态密钥获取
        secret_key_dynamic = settings.SECRET_KEY_DYNAMIC
        jwt_secret_dynamic = settings.JWT_SECRET_KEY_DYNAMIC
        api_token_dynamic = settings.API_TOKEN_DYNAMIC
        
        passed_1 = len(secret_key_dynamic) > 0 and secret_key_dynamic != "change-this-to-a-random-secret-key-in-production"
        print_result("SECRET_KEY_DYNAMIC获取", passed_1, f"长度: {len(secret_key_dynamic)} 字符")
        
        passed_2 = len(jwt_secret_dynamic) > 0 and jwt_secret_dynamic != "change-this-to-a-random-jwt-secret-key-in-production"
        print_result("JWT_SECRET_KEY_DYNAMIC获取", passed_2, f"长度: {len(jwt_secret_dynamic)} 字符")
        
        passed_3 = len(api_token_dynamic) > 0
        print_result("API_TOKEN_DYNAMIC获取", passed_3, f"长度: {len(api_token_dynamic)} 字符")
        
        # 测试JWT token生成（模拟STRM使用）
        try:
            from jose import jwt
            from datetime import datetime, timedelta
            
            payload = {
                "pick_code": "test_pickcode_12345",
                "storage_type": "115",
                "file_type": "video",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(hours=24)
            }
            
            token = jwt.encode(payload, jwt_secret_dynamic, algorithm="HS256")
            decoded = jwt.decode(token, jwt_secret_dynamic, algorithms=["HS256"])
            
            passed_4 = decoded.get("pick_code") == "test_pickcode_12345"
            print_result("JWT Token生成和验证", passed_4, "Token生成和验证成功")
            
        except Exception as e:
            print_result("JWT Token生成和验证", False, f"错误: {e}")
            passed_4 = False
        
        return passed_1 and passed_2 and passed_3 and passed_4
        
    except Exception as e:
        print_result("STRM集成测试", False, f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("  密钥管理功能测试")
    print("=" * 60)
    
    results = {}
    
    # 运行所有测试
    try:
        results["测试1: 密钥生成"] = test_1_secret_generation()
        results["测试2: 密钥加载"] = test_2_secret_loading()
        results["测试3: 环境变量覆盖"] = test_3_env_override()
        results["测试4: 密钥唯一性"] = test_4_uniqueness()
        results["测试5: STRM集成"] = test_5_strm_integration()
    except Exception as e:
        print(f"\n[ERROR] 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    # 打印测试总结
    print_section("测试总结")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    failed_tests = total_tests - passed_tests
    
    print(f"总测试数: {total_tests}")
    print(f"通过: {passed_tests} [PASS]")
    print(f"失败: {failed_tests} [FAIL]")
    print(f"通过率: {passed_tests/total_tests*100:.1f}%")
    
    print("\n详细结果:")
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status}: {test_name}")
    
    if all(results.values()):
        print("\n[SUCCESS] 所有测试通过！密钥管理功能正常工作。")
        return 0
    else:
        print("\n[WARNING] 部分测试失败，请检查上述错误信息。")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

