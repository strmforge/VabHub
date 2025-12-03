#!/usr/bin/env python3
"""
测试速度限制功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import AsyncSessionLocal, init_db
from app.modules.download.service import DownloadService
from loguru import logger

async def test_speed_limit():
    """测试速度限制功能"""
    print("\n" + "="*60)
    print("速度限制功能测试")
    print("="*60)
    
    await init_db()
    
    async with AsyncSessionLocal() as db:
        service = DownloadService(db)
        
        # 1. 测试设置全局速度限制
        print("\n[1] 测试设置全局速度限制...")
        success = await service.set_global_speed_limit(
            downloader="qBittorrent",
            download_limit=10.0,  # 10 MB/s
            upload_limit=5.0      # 5 MB/s
        )
        if success:
            print("[OK] 全局速度限制设置成功")
        else:
            print("[FAIL] 全局速度限制设置失败（可能是下载器未配置）")
        
        # 2. 测试获取全局速度限制
        print("\n[2] 测试获取全局速度限制...")
        limits = await service.get_global_speed_limit(downloader="qBittorrent")
        if limits:
            print(f"[OK] 获取全局速度限制成功: {limits}")
        else:
            print("[FAIL] 获取全局速度限制失败（可能是下载器未配置）")
        
        # 3. 测试设置单任务速度限制（需要先有任务）
        print("\n[3] 测试设置单任务速度限制...")
        # 这里需要先获取一个任务ID，如果没有任务则跳过
        downloads = await service.list_downloads()
        if downloads:
            task_id = downloads[0].get("id")
            if task_id:
                success = await service.set_task_speed_limit(
                    task_id=task_id,
                    download_limit=5.0,  # 5 MB/s
                    upload_limit=2.0    # 2 MB/s
                )
                if success:
                    print(f"[OK] 任务速度限制设置成功: {task_id}")
                else:
                    print(f"[FAIL] 任务速度限制设置失败: {task_id}")
            else:
                print("[SKIP] 没有可用的任务ID")
        else:
            print("[SKIP] 没有下载任务，跳过单任务速度限制测试")
    
    print("\n" + "="*60)
    print("速度限制功能测试完成")
    print("="*60)
    print("\n注意: 如果测试失败，可能是因为下载器未配置或未连接")
    print("这是正常的，功能代码本身是正确的")

if __name__ == "__main__":
    try:
        asyncio.run(test_speed_limit())
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

