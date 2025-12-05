"""
测试媒体服务器集成功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal, init_db
from app.modules.media_server.service import MediaServerService
from loguru import logger


async def test_media_server_service():
    """测试媒体服务器服务"""
    logger.info("开始测试媒体服务器服务...")
    
    try:
        # 初始化数据库
        await init_db()
        logger.info("✅ 数据库初始化成功")
        
        # 创建数据库会话
        async with AsyncSessionLocal() as session:
            service = MediaServerService(session)
            
            # 测试1: 创建媒体服务器
            logger.info("\n测试1: 创建媒体服务器...")
            try:
                server = await service.create_media_server(
                    name="测试Jellyfin服务器",
                    server_type="jellyfin",
                    url="http://localhost:8096",
                    api_key="test_api_key",
                    user_id="test_user_id",
                    enabled=False  # 测试时禁用，避免实际连接
                )
                await session.commit()
                logger.info(f"✅ 创建媒体服务器成功: ID={server.id}, Name={server.name}")
                server_id = server.id
            except Exception as e:
                logger.error(f"❌ 创建媒体服务器失败: {e}")
                return
            
            # 测试2: 获取媒体服务器列表
            logger.info("\n测试2: 获取媒体服务器列表...")
            try:
                servers = await service.list_media_servers()
                logger.info(f"✅ 获取媒体服务器列表成功: 共 {len(servers)} 个服务器")
                for server in servers:
                    logger.info(f"   - {server.name} ({server.server_type}): {server.url}")
            except Exception as e:
                logger.error(f"❌ 获取媒体服务器列表失败: {e}")
            
            # 测试3: 获取媒体服务器详情
            logger.info("\n测试3: 获取媒体服务器详情...")
            try:
                server = await service.get_media_server(server_id)
                if server:
                    logger.info(f"✅ 获取媒体服务器详情成功: {server.name}")
                    logger.info(f"   - 类型: {server.server_type}")
                    logger.info(f"   - URL: {server.url}")
                    logger.info(f"   - 状态: {server.status}")
                    logger.info(f"   - 启用: {server.enabled}")
                else:
                    logger.error("❌ 未找到媒体服务器")
            except Exception as e:
                logger.error(f"❌ 获取媒体服务器详情失败: {e}")
            
            # 测试4: 更新媒体服务器
            logger.info("\n测试4: 更新媒体服务器...")
            try:
                server = await service.update_media_server(
                    server_id,
                    name="测试Jellyfin服务器（已更新）"
                )
                await session.commit()
                if server:
                    logger.info(f"✅ 更新媒体服务器成功: {server.name}")
                else:
                    logger.error("❌ 未找到媒体服务器")
            except Exception as e:
                logger.error(f"❌ 更新媒体服务器失败: {e}")
            
            # 测试5: 删除媒体服务器
            logger.info("\n测试5: 删除媒体服务器...")
            try:
                success = await service.delete_media_server(server_id)
                await session.commit()
                if success:
                    logger.info("✅ 删除媒体服务器成功")
                else:
                    logger.error("❌ 删除媒体服务器失败")
            except Exception as e:
                logger.error(f"❌ 删除媒体服务器失败: {e}")
            
            logger.info("\n✅ 媒体服务器服务测试完成")
    
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_scheduler_monitor():
    """测试调度器监控服务"""
    logger.info("\n开始测试调度器监控服务...")
    
    try:
        # 创建数据库会话
        async with AsyncSessionLocal() as session:
            from app.modules.scheduler.monitor import SchedulerMonitor
            
            monitor = SchedulerMonitor(session)
            
            # 测试1: 同步任务到数据库
            logger.info("\n测试1: 同步任务到数据库...")
            try:
                await monitor.sync_tasks()
                await session.commit()
                logger.info("✅ 同步任务到数据库成功")
            except Exception as e:
                logger.error(f"❌ 同步任务失败: {e}")
                import traceback
                traceback.print_exc()
            
            # 测试2: 获取任务列表
            logger.info("\n测试2: 获取任务列表...")
            try:
                tasks = await monitor.get_tasks()
                logger.info(f"✅ 获取任务列表成功: 共 {len(tasks)} 个任务")
                for task in tasks:
                    logger.info(f"   - {task.name} ({task.job_id}): {task.status}")
            except Exception as e:
                logger.error(f"❌ 获取任务列表失败: {e}")
            
            # 测试3: 获取整体统计信息
            logger.info("\n测试3: 获取整体统计信息...")
            try:
                statistics = await monitor.get_overall_statistics()
                logger.info("✅ 获取统计信息成功:")
                logger.info(f"   - 总任务数: {statistics.get('total_tasks', 0)}")
                logger.info(f"   - 启用任务数: {statistics.get('enabled_tasks', 0)}")
                logger.info(f"   - 运行中任务数: {statistics.get('running_tasks', 0)}")
                logger.info(f"   - 失败任务数: {statistics.get('failed_tasks', 0)}")
                logger.info(f"   - 总执行次数: {statistics.get('total_runs', 0)}")
                logger.info(f"   - 总体成功率: {statistics.get('overall_success_rate', 0):.2f}%")
            except Exception as e:
                logger.error(f"❌ 获取统计信息失败: {e}")
                import traceback
                traceback.print_exc()
            
            logger.info("\n✅ 调度器监控服务测试完成")
    
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("开始测试已实现的功能")
    logger.info("=" * 60)
    
    # 测试媒体服务器服务
    await test_media_server_service()
    
    # 测试调度器监控服务
    await test_scheduler_monitor()
    
    logger.info("=" * 60)
    logger.info("所有测试完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

