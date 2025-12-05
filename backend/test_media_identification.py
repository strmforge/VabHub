#!/usr/bin/env python3
"""
测试媒体识别系统API
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import init_db, close_db
from app.modules.media_identification.service import MediaIdentificationService


async def test_media_identification_service():
    """测试媒体识别服务"""
    print("=" * 60)
    print("测试媒体识别服务")
    print("=" * 60)
    
    # 初始化数据库
    await init_db()
    
    try:
        # 获取数据库会话
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            service = MediaIdentificationService(db)
            
            # 测试1: 识别单个文件
            print("\n1. 测试识别单个文件...")
            test_files = [
                "The.Matrix.1999.1080p.BluRay.x264.mkv",
                "Breaking.Bad.S01E01.1080p.BluRay.x264.mkv",
                "Game.of.Thrones.S01E01.720p.HDTV.x264.mkv"
            ]
            
            for file_path in test_files:
                try:
                    result = await service.identify_media(file_path)
                    if result.get("success"):
                        print(f"[OK] 识别成功: {file_path}")
                        print(f"   标题: {result.get('title')}")
                        print(f"   年份: {result.get('year')}")
                        print(f"   类型: {result.get('type')}")
                        print(f"   置信度: {result.get('confidence', 0):.2f}")
                        if result.get('season'):
                            print(f"   季数: {result.get('season')}")
                        if result.get('episode'):
                            print(f"   集数: {result.get('episode')}")
                    else:
                        print(f"[FAIL] 识别失败: {file_path} - {result.get('error', '未知错误')}")
                except Exception as e:
                    print(f"[FAIL] 识别异常: {file_path} - {e}")
                    import traceback
                    traceback.print_exc()
            
            # 测试2: 批量识别
            print("\n2. 测试批量识别...")
            try:
                results = await service.batch_identify(test_files)
                print(f"[OK] 批量识别成功: {len(results)} 个文件")
                for result in results:
                    if result.get("success"):
                        print(f"   [OK] {result.get('file_path')}: {result.get('title')}")
                    else:
                        print(f"   [FAIL] {result.get('file_path')}: {result.get('error', '未知错误')}")
            except Exception as e:
                print(f"[FAIL] 批量识别失败: {e}")
                import traceback
                traceback.print_exc()
    
    finally:
        await close_db()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_media_identification_service())

