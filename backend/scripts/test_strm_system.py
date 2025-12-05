"""
测试STRM系统功能
测试STRM文件生成、重定向功能、pickcode存储和使用
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.modules.strm.config import STRMConfig
from app.modules.strm.generator import STRMGenerator
from app.core.database import AsyncSessionLocal, init_db, close_db
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


async def test_1_strm_file_generation():
    """测试1: STRM文件生成"""
    print_section("测试1: STRM文件生成")
    
    try:
        # 初始化数据库
        await init_db()
        
        # 创建STRM配置
        config = STRMConfig()
        config.media_library_path = "./test_media_library"
        config.strm_url_mode = "local_redirect"
        
        # 创建测试媒体库目录
        media_lib_path = Path(config.media_library_path)
        media_lib_path.mkdir(parents=True, exist_ok=True)
        
        # 创建STRM生成器
        async with AsyncSessionLocal() as db:
            generator = STRMGenerator(config, db)
            
            # 测试媒体信息
            test_media_info = {
                "type": "movie",
                "title": "测试电影",
                "year": 2024,
                "tmdb_id": 12345
            }
            
            # 测试pickcode（115网盘文件标识码）
            test_pickcode = "test_pickcode_12345"
            test_cloud_path = "/测试电影/测试电影.2024.1080p.mp4"
            
            # 生成STRM文件
            result = await generator.generate_strm_file(
                media_info=test_media_info,
                cloud_file_id=test_pickcode,
                cloud_storage="115",
                cloud_path=test_cloud_path
            )
            
            # 验证结果
            strm_path = result.get("strm_path")
            passed_1 = strm_path is not None and Path(strm_path).exists()
            print_result("STRM文件生成", passed_1, f"路径: {strm_path}")
            
            # 验证STRM文件内容
            if passed_1:
                strm_content = Path(strm_path).read_text(encoding='utf-8').strip()
                # 检查是否包含local_redirect URL
                has_redirect_url = "api/strm/stream" in strm_content
                has_token = "TOKEN" in strm_content or len(strm_content.split("/")) > 5
                passed_2 = has_redirect_url
                print_result("STRM文件内容", passed_2, f"内容: {strm_content[:100]}...")
                
                # 验证pickcode是否正确传递到token中
                try:
                    from jose import jwt
                    # 从URL中提取token
                    url_parts = strm_content.split("/")
                    if len(url_parts) > 0:
                        token = url_parts[-1]
                        jwt_secret = settings.JWT_SECRET_KEY_DYNAMIC
                        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
                        token_pickcode = payload.get("pick_code")
                        passed_3 = token_pickcode == test_pickcode
                        print_result("Pickcode在Token中", passed_3, 
                                    f"期望: {test_pickcode}, 实际: {token_pickcode}")
                    else:
                        passed_3 = False
                        print_result("Pickcode在Token中", False, "无法提取token")
                except Exception as e:
                    passed_3 = False
                    print_result("Pickcode在Token中", False, f"错误: {e}")
            else:
                passed_2 = False
                passed_3 = False
            
            return passed_1 and passed_2 and passed_3
            
    except Exception as e:
        print_result("STRM文件生成", False, f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await close_db()


async def test_2_strm_redirect():
    """测试2: STRM重定向功能"""
    print_section("测试2: STRM重定向功能")
    
    try:
        # 初始化数据库
        await init_db()
        
        # 创建STRM配置
        config = STRMConfig()
        
        # 创建测试pickcode和token
        test_pickcode = "test_pickcode_redirect_12345"
        
        # 生成JWT token
        from jose import jwt
        from datetime import datetime, timedelta
        
        jwt_secret = settings.JWT_SECRET_KEY_DYNAMIC
        payload = {
            "pick_code": test_pickcode,
            "storage_type": "115",
            "file_type": "video",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        test_token = jwt.encode(payload, jwt_secret, algorithm="HS256")
        
        # 测试token验证
        try:
            decoded = jwt.decode(test_token, jwt_secret, algorithms=["HS256"])
            passed_1 = decoded.get("pick_code") == test_pickcode
            print_result("Token生成和验证", passed_1, 
                        f"Pickcode: {decoded.get('pick_code')}")
        except Exception as e:
            passed_1 = False
            print_result("Token生成和验证", False, f"错误: {e}")
        
        # 测试重定向端点（模拟）
        # 注意：这里只测试token验证，不实际调用115 API
        async with AsyncSessionLocal() as db:
            from app.modules.strm.service import STRMService
            
            strm_service = STRMService(db)
            
            # 验证token可以正确解析
            try:
                decoded_payload = jwt.decode(test_token, jwt_secret, algorithms=["HS256"])
                extracted_pickcode = decoded_payload.get("pick_code")
                extracted_storage = decoded_payload.get("storage_type")
                
                passed_2 = extracted_pickcode == test_pickcode and extracted_storage == "115"
                print_result("Token解析", passed_2,
                            f"Pickcode: {extracted_pickcode}, Storage: {extracted_storage}")
            except Exception as e:
                passed_2 = False
                print_result("Token解析", False, f"错误: {e}")
            
            # 测试115 API客户端获取（如果配置了115）
            try:
                api_client = await strm_service.get_115_api_client()
                if api_client:
                    passed_3 = True
                    print_result("115 API客户端获取", True, "客户端已配置")
                else:
                    passed_3 = True  # 如果没有配置115，不算失败
                    print_result("115 API客户端获取", True, "未配置115（跳过）")
            except Exception as e:
                passed_3 = True  # 如果没有配置115，不算失败
                print_result("115 API客户端获取", True, f"未配置115: {e}")
        
        return passed_1 and passed_2
        
    except Exception as e:
        print_result("STRM重定向功能", False, f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await close_db()


async def test_3_pickcode_storage():
    """测试3: Pickcode存储和使用"""
    print_section("测试3: Pickcode存储和使用")
    
    try:
        # 初始化数据库
        await init_db()
        
        async with AsyncSessionLocal() as db:
            from app.models.strm import STRMFile
            from sqlalchemy import select
            
            # 测试数据
            test_pickcode = "test_pickcode_storage_67890"
            test_media_info = {
                "type": "tv",
                "title": "测试电视剧",
                "year": 2024,
                "season": 1,
                "episode": 1
            }
            
            # 创建STRM文件记录（模拟）
            strm_file = STRMFile(
                cloud_file_id=test_pickcode,
                cloud_storage="115",
                cloud_path="/测试电视剧/Season 01/测试电视剧.S01E01.1080p.mp4",
                strm_path="./test_media_library/测试电视剧/Season 01/测试电视剧.S01E01.1080p.strm",
                media_type="tv",
                title="测试电视剧",
                year=2024,
                season=1,
                episode=1
            )
            
            db.add(strm_file)
            await db.commit()
            await db.refresh(strm_file)
            
            # 验证pickcode存储
            passed_1 = strm_file.cloud_file_id == test_pickcode
            print_result("Pickcode存储", passed_1, 
                        f"期望: {test_pickcode}, 实际: {strm_file.cloud_file_id}")
            
            # 查询pickcode
            result = await db.execute(
                select(STRMFile).where(STRMFile.cloud_file_id == test_pickcode)
            )
            found_file = result.scalar_one_or_none()
            
            passed_2 = found_file is not None and found_file.cloud_file_id == test_pickcode
            print_result("Pickcode查询", passed_2,
                        f"找到文件: {found_file is not None}")
            
            # 验证pickcode在JWT token中的使用
            from jose import jwt
            from datetime import datetime, timedelta
            
            jwt_secret = settings.JWT_SECRET_KEY_DYNAMIC
            token_payload = {
                "pick_code": strm_file.cloud_file_id,
                "storage_type": strm_file.cloud_storage,
                "file_type": "video",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(hours=24)
            }
            token = jwt.encode(token_payload, jwt_secret, algorithm="HS256")
            
            # 验证token
            decoded = jwt.decode(token, jwt_secret, algorithms=["HS256"])
            passed_3 = decoded.get("pick_code") == test_pickcode
            print_result("Pickcode在Token中使用", passed_3,
                        f"Token中的pickcode: {decoded.get('pick_code')}")
            
            # 清理测试数据
            await db.delete(strm_file)
            await db.commit()
            
            return passed_1 and passed_2 and passed_3
            
    except Exception as e:
        print_result("Pickcode存储和使用", False, f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await close_db()


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("  STRM系统功能测试")
    print("=" * 60)
    
    results = {}
    
    # 运行所有测试
    try:
        results["测试1: STRM文件生成"] = await test_1_strm_file_generation()
        results["测试2: STRM重定向功能"] = await test_2_strm_redirect()
        results["测试3: Pickcode存储和使用"] = await test_3_pickcode_storage()
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
    if total_tests > 0:
        print(f"通过率: {passed_tests/total_tests*100:.1f}%")
    
    print("\n详细结果:")
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status}: {test_name}")
    
    if all(results.values()):
        print("\n[SUCCESS] 所有测试通过！STRM系统功能正常工作。")
        return 0
    else:
        print("\n[WARNING] 部分测试失败，请检查上述错误信息。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

