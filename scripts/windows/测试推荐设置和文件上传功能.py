#!/usr/bin/env python3
"""
测试推荐设置和文件上传功能
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加后端路径
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

import httpx
from loguru import logger

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

# 测试用户ID
TEST_USER_ID = 1


async def test_recommendation_settings():
    """测试推荐设置功能"""
    logger.info("=" * 60)
    logger.info("测试推荐设置功能")
    logger.info("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 获取默认设置
        logger.info("\n1. 获取默认推荐设置...")
        try:
            response = await client.get(f"{BASE_URL}/recommendations/{TEST_USER_ID}/settings")
            if response.status_code == 200:
                settings = response.json()
                logger.info(f"✅ 获取设置成功:")
                logger.info(f"   用户ID: {settings.get('user_id')}")
                logger.info(f"   算法: {settings.get('settings', {}).get('algorithm')}")
                logger.info(f"   数量: {settings.get('settings', {}).get('limit')}")
            else:
                logger.error(f"❌ 获取设置失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ 获取设置异常: {e}")
            return False
        
        # 2. 更新设置
        logger.info("\n2. 更新推荐设置...")
        try:
            new_settings = {
                "algorithm": "hybrid",
                "limit": 30,
                "preferences": {
                    "includeMovies": True,
                    "includeTVShows": True,
                    "includeAnime": False
                },
                "weights": {
                    "collaborative": 60,
                    "content": 25,
                    "popularity": 15
                }
            }
            response = await client.post(
                f"{BASE_URL}/recommendations/{TEST_USER_ID}/settings",
                json=new_settings
            )
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ 更新设置成功:")
                logger.info(f"   算法: {result.get('settings', {}).get('algorithm')}")
                logger.info(f"   数量: {result.get('settings', {}).get('limit')}")
                logger.info(f"   偏好: {result.get('settings', {}).get('preferences')}")
            else:
                logger.error(f"❌ 更新设置失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ 更新设置异常: {e}")
            return False
        
        # 3. 验证设置已保存
        logger.info("\n3. 验证设置已保存...")
        try:
            response = await client.get(f"{BASE_URL}/recommendations/{TEST_USER_ID}/settings")
            if response.status_code == 200:
                settings = response.json()
                if settings.get('settings', {}).get('algorithm') == 'hybrid':
                    logger.info("✅ 设置验证成功")
                else:
                    logger.warning("⚠️  设置验证失败: 算法不匹配")
            else:
                logger.error(f"❌ 验证设置失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ 验证设置异常: {e}")
            return False
        
        # 4. 获取推荐（应该使用新设置）
        logger.info("\n4. 获取推荐（使用新设置）...")
        try:
            response = await client.get(
                f"{BASE_URL}/recommendations/{TEST_USER_ID}",
                params={"limit": 10, "algorithm": "hybrid"}
            )
            if response.status_code == 200:
                recommendations = response.json()
                logger.info(f"✅ 获取推荐成功: {len(recommendations)} 条推荐")
                if recommendations:
                    logger.info("   前3条推荐:")
                    for i, rec in enumerate(recommendations[:3], 1):
                        logger.info(f"   {i}. {rec.get('media_id')} - 分数: {rec.get('score'):.2f} - 理由: {rec.get('reason')}")
            else:
                logger.error(f"❌ 获取推荐失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ 获取推荐异常: {e}")
            return False
    
    return True


async def test_file_upload():
    """测试文件上传功能"""
    logger.info("\n" + "=" * 60)
    logger.info("测试文件上传功能")
    logger.info("=" * 60)
    
    # 创建测试文件
    test_file_path = Path(__file__).parent / "backend" / "tmp" / "test_upload.txt"
    test_file_path.parent.mkdir(parents=True, exist_ok=True)
    test_file_path.write_text("这是一个测试文件，用于测试文件上传功能。\nTest file for upload testing.")
    
    logger.info(f"\n1. 准备测试文件: {test_file_path}")
    logger.info(f"   文件大小: {test_file_path.stat().st_size} bytes")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 2. 上传文件
        logger.info("\n2. 上传文件...")
        try:
            with open(test_file_path, "rb") as f:
                files = {"file": ("test_upload.txt", f, "text/plain")}
                response = await client.post(
                    f"{BASE_URL}/media-identification/upload",
                    files=files
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ 上传文件成功:")
                logger.info(f"   文件名: {result.get('file_name')}")
                logger.info(f"   文件路径: {result.get('file_path')}")
                logger.info(f"   文件大小: {result.get('file_size')} bytes")
                logger.info(f"   识别成功: {result.get('success')}")
                if result.get('success'):
                    logger.info(f"   标题: {result.get('title')}")
                    logger.info(f"   类型: {result.get('type')}")
                    logger.info(f"   置信度: {result.get('confidence', 0):.2f}")
            else:
                logger.error(f"❌ 上传文件失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ 上传文件异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True


async def test_batch_upload():
    """测试批量文件上传功能"""
    logger.info("\n" + "=" * 60)
    logger.info("测试批量文件上传功能")
    logger.info("=" * 60)
    
    # 创建测试文件
    upload_dir = Path(__file__).parent / "backend" / "tmp"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    test_files = []
    for i in range(3):
        test_file = upload_dir / f"test_batch_{i+1}.txt"
        test_file.write_text(f"这是第 {i+1} 个测试文件。\nTest file {i+1} for batch upload testing.")
        test_files.append(test_file)
    
    logger.info(f"\n1. 准备 {len(test_files)} 个测试文件")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        # 2. 批量上传文件
        logger.info("\n2. 批量上传文件...")
        try:
            files = []
            for test_file in test_files:
                files.append(("files", (test_file.name, open(test_file, "rb"), "text/plain")))
            
            response = await client.post(
                f"{BASE_URL}/media-identification/upload/batch",
                files=files
            )
            
            # 关闭文件
            for _, (_, file_obj, _) in files:
                file_obj.close()
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ 批量上传成功:")
                logger.info(f"   总文件数: {result.get('total')}")
                logger.info(f"   结果数: {len(result.get('results', []))}")
                
                for i, res in enumerate(result.get('results', [])[:3], 1):
                    logger.info(f"   文件 {i}: {res.get('file_name')} - 成功: {res.get('success')}")
            else:
                logger.error(f"❌ 批量上传失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ 批量上传异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True


async def main():
    """主测试函数"""
    logger.info("开始测试推荐设置和文件上传功能")
    logger.info("=" * 60)
    
    results = {}
    
    # 测试推荐设置
    try:
        results['recommendation_settings'] = await test_recommendation_settings()
    except Exception as e:
        logger.error(f"推荐设置测试异常: {e}")
        results['recommendation_settings'] = False
    
    # 测试文件上传
    try:
        results['file_upload'] = await test_file_upload()
    except Exception as e:
        logger.error(f"文件上传测试异常: {e}")
        results['file_upload'] = False
    
    # 测试批量上传
    try:
        results['batch_upload'] = await test_batch_upload()
    except Exception as e:
        logger.error(f"批量上传测试异常: {e}")
        results['batch_upload'] = False
    
    # 输出测试结果
    logger.info("\n" + "=" * 60)
    logger.info("测试结果总结")
    logger.info("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    logger.info(f"\n总体结果: {'✅ 全部通过' if all_passed else '❌ 部分失败'}")
    
    return all_passed


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

