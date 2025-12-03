"""
为VabHub创建的任务添加VABHUB标签
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
from app.models.download import DownloadTask
from sqlalchemy import select

async def add_vabhub_labels():
    """为VabHub创建的任务添加VABHUB标签"""
    try:
        await init_db()
        
        async with AsyncSessionLocal() as db:
            settings_service = SettingsService(db)
            
            # 获取所有下载任务
            result = await db.execute(select(DownloadTask))
            all_tasks = result.scalars().all()
            
            logger.info(f"数据库中共有 {len(all_tasks)} 个下载任务")
            logger.info("")
            
            # 按下载器分组
            tasks_by_downloader = {}
            for task in all_tasks:
                if task.downloader_hash:
                    if task.downloader not in tasks_by_downloader:
                        tasks_by_downloader[task.downloader] = []
                    tasks_by_downloader[task.downloader].append(task)
            
            logger.info("="*60)
            logger.info("为VabHub任务添加标签")
            logger.info("="*60)
            logger.info("")
            
            for downloader_name, tasks in tasks_by_downloader.items():
                logger.info(f"处理 {downloader_name} 的任务 ({len(tasks)} 个)...")
                
                # 获取下载器配置
                config_prefix = f"{downloader_name.lower()}_"
                host_raw = await settings_service.get_setting(f"{config_prefix}host")
                host = str(host_raw).strip() if host_raw and host_raw != "localhost" else "192.168.51.105"
                
                port_raw = await settings_service.get_setting(f"{config_prefix}port")
                port = int(port_raw) if port_raw else (8080 if downloader_name == "qBittorrent" else 9091)
                
                username_raw = await settings_service.get_setting(f"{config_prefix}username")
                username = str(username_raw).strip() if username_raw else ("admin" if downloader_name == "qBittorrent" else "haishuai")
                
                password_raw = await settings_service.get_setting(f"{config_prefix}password")
                password = str(password_raw).strip() if password_raw else "China1987"
                
                downloader_type = DownloaderType.QBITTORRENT if downloader_name == "qBittorrent" else DownloaderType.TRANSMISSION
                
                # 创建客户端
                client = DownloaderClient(
                    downloader_type,
                    {
                        "host": host,
                        "port": port,
                        "username": username,
                        "password": password
                    }
                )
                
                # 为每个任务添加VABHUB标签
                success_count = 0
                fail_count = 0
                skip_count = 0  # 已有标签的任务数
                
                logger.info(f"  开始处理 {len(tasks)} 个任务...")
                
                for task in tasks:
                    try:
                        if downloader_type == DownloaderType.QBITTORRENT:
                            # qBittorrent使用hash
                            # 获取所有任务以查找对应的任务
                            torrents = await client.get_torrents()
                            torrent_info = None
                            for torrent in torrents:
                                if torrent.get("hash") == task.downloader_hash:
                                    torrent_info = torrent
                                    break
                            
                            if torrent_info:
                                current_tags_str = torrent_info.get("tags", "")
                                current_tags = [tag.strip() for tag in current_tags_str.split(",") if tag.strip()] if current_tags_str else []
                                
                                if "VABHUB" not in current_tags:
                                    # 添加VABHUB标签（hashes参数可以是单个hash字符串）
                                    await client.client.set_torrent_tags(task.downloader_hash, ["VABHUB"])
                                    logger.info(f"  ✓ {task.title[:50]} - 已添加VABHUB标签")
                                    success_count += 1
                                else:
                                    skip_count += 1
                                    if skip_count <= 5:  # 只显示前5个
                                        logger.debug(f"  - {task.title[:50]} - 已有VABHUB标签")
                            else:
                                logger.warning(f"  ✗ {task.title[:50]} - 未找到对应的qBittorrent任务")
                                fail_count += 1
                        else:
                            # Transmission使用ID
                            # 需要先通过hash获取ID
                            torrents = await client.client.get_torrents()
                            torrent_id = None
                            torrent_info = None
                            for torrent in torrents:
                                if torrent.get("hashString") == task.downloader_hash:
                                    torrent_id = torrent.get("id")
                                    torrent_info = torrent
                                    break
                            
                            if torrent_id and torrent_info:
                                # 获取现有标签
                                labels = torrent_info.get("labels", [])
                                if isinstance(labels, str):
                                    current_labels = [label.strip() for label in labels.split(",") if label.strip()]
                                elif isinstance(labels, list):
                                    current_labels = labels
                                else:
                                    current_labels = []
                                
                                if "VABHUB" not in current_labels:
                                    new_labels = current_labels + ["VABHUB"]
                                    await client.client.set_torrent_labels([torrent_id], new_labels)
                                    logger.info(f"  ✓ {task.title[:50]} - 已添加VABHUB标签")
                                    success_count += 1
                                else:
                                    skip_count += 1
                                    if skip_count <= 5:  # 只显示前5个
                                        logger.debug(f"  - {task.title[:50]} - 已有VABHUB标签")
                            else:
                                logger.warning(f"  ✗ {task.title[:50]} - 未找到对应的Transmission任务")
                                fail_count += 1
                    except Exception as e:
                        logger.error(f"  ✗ {task.title[:50]} - 添加标签失败: {e}")
                        fail_count += 1
                
                await client.close()
                
                logger.info("")
                logger.info(f"{downloader_name} 处理完成:")
                logger.info(f"  成功添加: {success_count} 个")
                logger.info(f"  已有标签: {skip_count} 个")
                logger.info(f"  失败: {fail_count} 个")
                logger.info("")
            
            logger.info("="*60)
            logger.info("标签添加完成")
            logger.info("="*60)
            
    except Exception as e:
        logger.error(f"添加标签失败: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(add_vabhub_labels())

