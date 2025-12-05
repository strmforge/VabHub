"""
功能测试脚本
测试已实现的功能是否正常工作
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal, init_db
from app.modules.media_server.service import MediaServerService
from app.modules.scheduler.monitor import SchedulerMonitor
from loguru import logger


async def test_media_server():
    """测试媒体服务器功能"""
    logger.info("=" * 60)
    logger.info("测试媒体服务器功能")
    logger.info("=" * 60)
    
    try:
        async with AsyncSessionLocal() as session:
            service = MediaServerService(session)
            
            # 测试1: 创建媒体服务器
            logger.info("\n[测试1] 创建媒体服务器...")
            server = await service.create_media_server(
                name="测试Jellyfin服务器",
                server_type="jellyfin",
                url="http://localhost:8096",
                api_key="test_api_key",
                user_id="test_user_id",
                enabled=False
            )
            await session.commit()
            logger.info(f"✅ 创建成功: ID={server.id}, Name={server.name}")
            server_id = server.id
            
            # 测试2: 获取服务器列表
            logger.info("\n[测试2] 获取服务器列表...")
            servers = await service.list_media_servers()
            logger.info(f"✅ 获取成功: 共 {len(servers)} 个服务器")
            
            # 测试3: 获取服务器详情
            logger.info("\n[测试3] 获取服务器详情...")
            server = await service.get_media_server(server_id)
            if server:
                logger.info(f"✅ 获取成功: {server.name}")
            else:
                logger.error("❌ 获取失败")
            
            # 测试4: 更新服务器
            logger.info("\n[测试4] 更新服务器...")
            server = await service.update_media_server(
                server_id,
                name="测试Jellyfin服务器（已更新）"
            )
            await session.commit()
            if server:
                logger.info(f"✅ 更新成功: {server.name}")
            
            # 测试5: 删除服务器
            logger.info("\n[测试5] 删除服务器...")
            success = await service.delete_media_server(server_id)
            await session.commit()
            if success:
                logger.info("✅ 删除成功")
            
            logger.info("\n✅ 媒体服务器功能测试完成")
            return True
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_scheduler_monitor():
    """测试调度器监控功能"""
    logger.info("\n" + "=" * 60)
    logger.info("测试调度器监控功能")
    logger.info("=" * 60)
    
    try:
        async with AsyncSessionLocal() as session:
            monitor = SchedulerMonitor(session)
            
            # 测试1: 同步任务
            logger.info("\n[测试1] 同步任务到数据库...")
            await monitor.sync_tasks()
            await session.commit()
            logger.info("✅ 同步成功")
            
            # 测试2: 获取任务列表
            logger.info("\n[测试2] 获取任务列表...")
            tasks = await monitor.get_tasks()
            logger.info(f"✅ 获取成功: 共 {len(tasks)} 个任务")
            for task in tasks[:5]:
                logger.info(f"   - {task.name} ({task.job_id}): {task.status}")
            
            # 测试3: 获取统计信息
            logger.info("\n[测试3] 获取统计信息...")
            stats = await monitor.get_overall_statistics()
            logger.info("✅ 获取成功:")
            logger.info(f"   总任务数: {stats.get('total_tasks', 0)}")
            logger.info(f"   启用任务数: {stats.get('enabled_tasks', 0)}")
            logger.info(f"   总体成功率: {stats.get('overall_success_rate', 0):.2f}%")
            
            logger.info("\n✅ 调度器监控功能测试完成")
            return True
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    logger.info("开始功能测试...")
    logger.info("")
    
    # 初始化数据库
    try:
        await init_db()
        logger.info("✅ 数据库初始化成功")
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        return
    
    # 测试媒体服务器
    media_server_ok = await test_media_server()
    
    # 测试调度器监控
    scheduler_ok = await test_scheduler_monitor()
    
    # 总结
    logger.info("\n" + "=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)
    logger.info(f"媒体服务器功能: {'✅ 通过' if media_server_ok else '❌ 失败'}")
    logger.info(f"调度器监控功能: {'✅ 通过' if scheduler_ok else '❌ 失败'}")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

