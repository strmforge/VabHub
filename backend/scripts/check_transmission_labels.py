"""
检查Transmission任务的标签信息
"""

import asyncio
import sys
from pathlib import Path
from loguru import logger

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import AsyncSessionLocal, init_db
from app.core.downloaders import DownloaderClient, DownloaderType
from app.modules.settings.service import SettingsService

async def check_transmission_labels():
    """检查Transmission任务的标签"""
    try:
        await init_db()
        
        async with AsyncSessionLocal() as db:
            settings_service = SettingsService(db)
            
            # 获取Transmission配置
            host_raw = await settings_service.get_setting("transmission_host")
            host = str(host_raw).strip() if host_raw and host_raw != "localhost" else "192.168.51.105"
            
            port_raw = await settings_service.get_setting("transmission_port")
            port = int(port_raw) if port_raw else 9091
            
            username_raw = await settings_service.get_setting("transmission_username")
            username = str(username_raw).strip() if username_raw else "haishuai"
            
            password_raw = await settings_service.get_setting("transmission_password")
            password = str(password_raw).strip() if password_raw else "China1987"
            
            logger.info(f"连接Transmission: {host}:{port}")
            logger.info(f"  用户名: {username}")
            logger.info(f"  密码: {'已设置' if password else '未设置'}")
            logger.info("")
            
            # 创建客户端
            client = DownloaderClient(
                DownloaderType.TRANSMISSION,
                {
                    "host": host,
                    "port": port,
                    "username": username,
                    "password": password
                }
            )
            
            # 获取所有任务
            torrents = await client.get_torrents()
            logger.info(f"从Transmission获取到 {len(torrents)} 个任务")
            logger.info("")
            
            # 统计标签信息
            tasks_with_labels = 0
            tasks_without_labels = 0
            all_labels = set()
            
            logger.info("="*60)
            logger.info("任务标签信息")
            logger.info("="*60)
            logger.info("")
            
            # 查找fedora-35.iso任务
            fedora_task = None
            for torrent in torrents:
                if "fedora-35.iso" in torrent.get("name", ""):
                    fedora_task = torrent
                    break
            
            if fedora_task:
                logger.info("="*60)
                logger.info("fedora-35.iso 任务详情")
                logger.info("="*60)
                labels = fedora_task.get("labels", [])
                if isinstance(labels, str):
                    labels = [label.strip() for label in labels.split(",") if label.strip()]
                elif not isinstance(labels, list):
                    labels = []
                logger.info(f"任务名称: {fedora_task.get('name', '未知')}")
                logger.info(f"Hash: {fedora_task.get('hashString', '未知')}")
                logger.info(f"标签: {', '.join(labels) if labels else '无标签'}")
                logger.info(f"状态: {fedora_task.get('status', '未知')}")
                logger.info("")
            
            for i, torrent in enumerate(torrents[:20], 1):  # 只显示前20个
                torrent_name = torrent.get("name", "未知")
                torrent_hash = torrent.get("hashString", "")
                labels = torrent.get("labels", [])
                
                if isinstance(labels, str):
                    labels = [label.strip() for label in labels.split(",") if label.strip()]
                elif not isinstance(labels, list):
                    labels = []
                
                if labels:
                    tasks_with_labels += 1
                    all_labels.update(labels)
                    labels_str = ", ".join(labels)
                    logger.info(f"{i}. {torrent_name[:60]}")
                    logger.info(f"   标签: {labels_str}")
                else:
                    tasks_without_labels += 1
                    logger.info(f"{i}. {torrent_name[:60]}")
                    logger.info(f"   标签: 无标签")
                logger.info("")
            
            logger.info("="*60)
            logger.info("标签统计")
            logger.info("="*60)
            logger.info(f"有标签的任务: {tasks_with_labels}")
            logger.info(f"无标签的任务: {tasks_without_labels}")
            logger.info(f"总任务数: {len(torrents)}")
            logger.info("")
            
            if all_labels:
                logger.info(f"所有标签: {', '.join(sorted(all_labels))}")
            else:
                logger.warning("所有任务都没有标签")
                logger.info("")
                logger.info("建议:")
                logger.info("1. 在Transmission Web Control中手动为任务添加标签")
                logger.info("2. 或者使用VabHub创建任务时自动添加'VABHUB'标签")
            
            await client.close()
            
    except Exception as e:
        logger.error(f"检查Transmission标签失败: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(check_transmission_labels())

