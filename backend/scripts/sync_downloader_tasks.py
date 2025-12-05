"""
从下载器同步任务到数据库
从qBittorrent和Transmission获取现有任务，同步到数据库并获取hash
"""

import asyncio
import sys
from pathlib import Path
from loguru import logger
from datetime import datetime

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import AsyncSessionLocal, init_db
from app.core.downloaders import DownloaderClient, DownloaderType
from app.constants.media_types import MEDIA_TYPE_UNKNOWN
from app.modules.settings.service import SettingsService
from app.models.download import DownloadTask
from sqlalchemy import select

BASE_URL = "http://localhost:8001/api"
TIMEOUT = 30.0


async def sync_qbittorrent_tasks(db):
    """从qBittorrent同步任务"""
    try:
        settings_service = SettingsService(db)
        
        # 获取qBittorrent配置
        # 先尝试从设置获取，如果失败则使用默认值
        host_raw = await settings_service.get_setting("qbittorrent_host")
        logger.info(f"qBittorrent host 原始值: {repr(host_raw)} (类型: {type(host_raw)})")
        
        # 处理配置值（可能是JSON字符串、普通字符串或None）
        if host_raw is None:
            host = "192.168.51.105"  # 使用已知的正确IP
        elif isinstance(host_raw, str):
            # 如果是JSON字符串（带引号），需要解析
            if host_raw.startswith('"') and host_raw.endswith('"'):
                import json
                try:
                    host = json.loads(host_raw)
                except:
                    host = host_raw.strip()
            else:
                host = host_raw.strip()
            if not host:
                host = "192.168.51.105"
        else:
            host = str(host_raw).strip() if host_raw else "192.168.51.105"
        
        port_raw = await settings_service.get_setting("qbittorrent_port")
        if port_raw is None:
            port = 8080
        elif isinstance(port_raw, str):
            try:
                port = int(port_raw)
            except:
                port = 8080
        elif isinstance(port_raw, int):
            port = port_raw
        else:
            port = 8080
            
        username_raw = await settings_service.get_setting("qbittorrent_username")
        username = str(username_raw).strip() if username_raw else "admin"
        password_raw = await settings_service.get_setting("qbittorrent_password")
        password = str(password_raw).strip() if password_raw else "China1987"  # 使用已知的正确密码
        logger.info(f"qBittorrent 用户名: {username}, 密码: {'已设置' if password else '未设置'}")
        
        logger.info(f"连接qBittorrent: {host}:{port}")
        logger.info(f"  用户名: {username or '未设置'}")
        logger.info(f"  密码: {'已设置' if password else '未设置'}")
        
        # 创建客户端
        client = DownloaderClient(
            DownloaderType.QBITTORRENT,
            {
                "host": host,
                "port": int(port) if isinstance(port, str) else port,
                "username": username,
                "password": password
            }
        )
        
        # 确保已登录
        try:
            if hasattr(client.client, 'sid') and not client.client.sid:
                logger.info("qBittorrent未登录，尝试登录...")
                login_success = await client.client.login()
                if login_success:
                    logger.success("qBittorrent登录成功")
                else:
                    logger.error("qBittorrent登录失败")
        except Exception as e:
            logger.warning(f"qBittorrent登录检查失败: {e}")
        
        # 获取所有任务
        try:
            torrents = await client.get_torrents()
            logger.info(f"从qBittorrent获取到 {len(torrents)} 个任务")
            if len(torrents) == 0:
                logger.warning("qBittorrent返回0个任务")
                # 尝试直接调用API验证
                try:
                    if hasattr(client.client, 'session'):
                        test_response = await client.client.session.get(
                            f"{client.client.base_url}/api/v2/torrents/info"
                        )
                        if test_response.status_code == 200:
                            test_torrents = test_response.json()
                            logger.info(f"直接API调用获取到 {len(test_torrents)} 个任务")
                            if len(test_torrents) > 0:
                                logger.info(f"示例任务: {test_torrents[0].get('name', '未知')[:50]}")
                        else:
                            logger.warning(f"直接API调用失败: HTTP {test_response.status_code}, {test_response.text[:100]}")
                except Exception as api_e:
                    logger.warning(f"直接API调用异常: {api_e}")
        except Exception as e:
            logger.error(f"获取qBittorrent任务列表失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            torrents = []
        
        synced_count = 0
        updated_count = 0
        
        for torrent in torrents:
            torrent_hash = torrent.get("hash")
            torrent_name = torrent.get("name", "未知")
            torrent_size = torrent.get("size", 0) / (1024 ** 3)  # 转换为GB
            torrent_state = torrent.get("state", "unknown")
            
            # 映射状态
            status_map = {
                "downloading": "downloading",
                "pausedDL": "paused",
                "queuedDL": "downloading",
                "uploading": "completed",
                "pausedUP": "paused",
                "queuedUP": "completed",
                "stalledDL": "downloading",
                "stalledUP": "completed",
                "checkingDL": "downloading",
                "checkingUP": "completed",
                "missingFiles": "failed",
                "error": "failed"
            }
            status = status_map.get(torrent_state, "downloading")
            
            # 计算进度
            progress = torrent.get("progress", 0) / 100.0  # qBittorrent返回0-100
            downloaded = torrent_size * progress
            
            # 查找数据库中是否已存在（通过hash）
            result = await db.execute(
                select(DownloadTask).where(DownloadTask.downloader_hash == torrent_hash)
            )
            existing_task = result.scalar_one_or_none()
            
            if existing_task:
                # 更新现有任务
                existing_task.title = torrent_name
                existing_task.status = status
                existing_task.progress = progress * 100
                existing_task.size_gb = torrent_size
                existing_task.downloaded_gb = downloaded
                existing_task.downloader = "qBittorrent"
                existing_task.downloader_hash = torrent_hash
                existing_task.updated_at = datetime.utcnow()
                updated_count += 1
                logger.info(f"  更新任务: {torrent_name} (Hash: {torrent_hash[:16]}...)")
            else:
                # 创建新任务
                import uuid
                new_task = DownloadTask(
                    task_id=str(uuid.uuid4()),
                    title=torrent_name,
                    status=status,
                    progress=progress * 100,
                    size_gb=torrent_size,
                    downloaded_gb=downloaded,
                    downloader="qBittorrent",
                    downloader_hash=torrent_hash,
                    media_type=MEDIA_TYPE_UNKNOWN,
                )
                db.add(new_task)
                synced_count += 1
                logger.info(f"  同步任务: {torrent_name} (Hash: {torrent_hash[:16]}...)")
        
        await db.commit()
        await client.close()
        
        logger.success(f"qBittorrent同步完成: 新增 {synced_count} 个，更新 {updated_count} 个")
        return synced_count + updated_count
        
    except Exception as e:
        logger.error(f"同步qBittorrent任务失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 0


async def sync_transmission_tasks(db):
    """从Transmission同步任务"""
    try:
        settings_service = SettingsService(db)
        
        # 获取Transmission配置
        host_raw = await settings_service.get_setting("transmission_host")
        logger.info(f"Transmission host 原始值: {repr(host_raw)} (类型: {type(host_raw)})")
        
        # 处理配置值（可能是JSON字符串、普通字符串或None）
        if host_raw is None:
            host = "192.168.51.105"  # 使用已知的正确IP
        elif isinstance(host_raw, str):
            # 如果是JSON字符串（带引号），需要解析
            if host_raw.startswith('"') and host_raw.endswith('"'):
                import json
                try:
                    host = json.loads(host_raw)
                except:
                    host = host_raw.strip()
            else:
                host = host_raw.strip()
            if not host:
                host = "192.168.51.105"
        else:
            host = str(host_raw).strip() if host_raw else "192.168.51.105"
        
        port_raw = await settings_service.get_setting("transmission_port")
        if port_raw is None:
            port = 9091
        elif isinstance(port_raw, str):
            try:
                port = int(port_raw)
            except:
                port = 9091
        elif isinstance(port_raw, int):
            port = port_raw
        else:
            port = 9091
            
        username_raw = await settings_service.get_setting("transmission_username")
        username = str(username_raw).strip() if username_raw else "haishuai"  # 使用已知的正确用户名
        password_raw = await settings_service.get_setting("transmission_password")
        password = str(password_raw).strip() if password_raw else "China1987"  # 使用已知的正确密码
        logger.info(f"Transmission 用户名: {username or '未设置'}, 密码: {'已设置' if password else '未设置'}")
        
        logger.info(f"连接Transmission: {host}:{port}")
        logger.info(f"  用户名: {username or '未设置'}")
        logger.info(f"  密码: {'已设置' if password else '未设置'}")
        
        # 创建客户端
        client = DownloaderClient(
            DownloaderType.TRANSMISSION,
            {
                "host": host,
                "port": int(port) if isinstance(port, str) else port,
                "username": username,
                "password": password
            }
        )
        
        # 获取所有任务
        try:
            torrents = await client.get_torrents()
            logger.info(f"从Transmission获取到 {len(torrents)} 个任务")
            if len(torrents) == 0:
                logger.warning("Transmission返回0个任务，可能原因：")
                logger.warning("  1. 下载器中确实没有任务")
                logger.warning("  2. 连接失败（检查网络和配置）")
                logger.warning("  3. 权限不足")
        except Exception as e:
            logger.error(f"获取Transmission任务列表失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            torrents = []
        
        synced_count = 0
        updated_count = 0
        
        for torrent in torrents:
            torrent_hash = torrent.get("hashString")
            torrent_name = torrent.get("name", "未知")
            torrent_size = torrent.get("totalSize", 0) / (1024 ** 3)  # 转换为GB
            torrent_status = torrent.get("status", 0)
            
            # 获取标签信息
            labels = torrent.get("labels", [])
            if isinstance(labels, str):
                labels = [label.strip() for label in labels.split(",") if label.strip()]
            elif not isinstance(labels, list):
                labels = []
            
            # 映射状态（Transmission状态码）
            # 0 = stopped, 1 = check wait, 2 = check, 3 = download wait, 4 = downloading, 5 = seed wait, 6 = seeding
            status_map = {
                0: "paused",
                1: "downloading",
                2: "downloading",
                3: "downloading",
                4: "downloading",
                5: "completed",
                6: "completed"
            }
            status = status_map.get(torrent_status, "downloading")
            
            # 计算进度
            progress = torrent.get("percentDone", 0) * 100  # Transmission返回0-1
            downloaded = torrent_size * (progress / 100)
            
            # 查找数据库中是否已存在（通过hash）
            result = await db.execute(
                select(DownloadTask).where(DownloadTask.downloader_hash == torrent_hash)
            )
            existing_task = result.scalar_one_or_none()
            
            if existing_task:
                # 更新现有任务
                existing_task.title = torrent_name
                existing_task.status = status
                existing_task.progress = progress
                existing_task.size_gb = torrent_size
                existing_task.downloaded_gb = downloaded
                existing_task.downloader = "Transmission"
                existing_task.downloader_hash = torrent_hash
                existing_task.updated_at = datetime.utcnow()
                updated_count += 1
                labels_str = ", ".join(labels) if labels else "无标签"
                logger.info(f"  更新任务: {torrent_name} (Hash: {torrent_hash[:16]}..., 标签: {labels_str})")
            else:
                # 创建新任务
                import uuid
                new_task = DownloadTask(
                    task_id=str(uuid.uuid4()),
                    title=torrent_name,
                    status=status,
                    progress=progress,
                    size_gb=torrent_size,
                    downloaded_gb=downloaded,
                    downloader="Transmission",
                    downloader_hash=torrent_hash,
                    media_type=MEDIA_TYPE_UNKNOWN,
                )
                db.add(new_task)
                synced_count += 1
                logger.info(f"  同步任务: {torrent_name} (Hash: {torrent_hash[:16]}...)")
        
        await db.commit()
        await client.close()
        
        logger.success(f"Transmission同步完成: 新增 {synced_count} 个，更新 {updated_count} 个")
        return synced_count + updated_count
        
    except Exception as e:
        logger.error(f"同步Transmission任务失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 0


async def main():
    """主函数"""
    logger.info("="*60)
    logger.info("从下载器同步任务到数据库")
    logger.info("="*60)
    logger.info("")
    
    # 初始化数据库
    await init_db()
    
    # 创建数据库会话
    async with AsyncSessionLocal() as db:
        try:
            # 同步qBittorrent任务
            logger.info("1. 同步qBittorrent任务...")
            logger.info("-" * 60)
            qb_count = await sync_qbittorrent_tasks(db)
            
            logger.info("")
            # 同步Transmission任务
            logger.info("2. 同步Transmission任务...")
            logger.info("-" * 60)
            tr_count = await sync_transmission_tasks(db)
            
            logger.info("")
            logger.info("="*60)
            logger.info("同步完成")
            logger.info("="*60)
            logger.info(f"qBittorrent: {qb_count} 个任务")
            logger.info(f"Transmission: {tr_count} 个任务")
            logger.info(f"总计: {qb_count + tr_count} 个任务")
            
            # 查找有hash的任务
            logger.info("")
            logger.info("查找有hash的任务...")
            result = await db.execute(
                select(DownloadTask).where(DownloadTask.downloader_hash.isnot(None))
            )
            tasks_with_hash = result.scalars().all()
            
            if tasks_with_hash:
                logger.info(f"找到 {len(tasks_with_hash)} 个有hash的任务:")
                task_ids = []
                for i, task in enumerate(tasks_with_hash[:10], 1):  # 只显示前10个
                    logger.info(f"  {i}. {task.title}")
                    logger.info(f"     ID: {task.task_id}")
                    logger.info(f"     Hash: {task.downloader_hash[:40]}...")
                    logger.info(f"     状态: {task.status}")
                    logger.info("")
                    task_ids.append(task.task_id)
                
                # 保存到文件
                if task_ids:
                    output_file = Path(__file__).parent / "test_task_ids.txt"
                    with open(output_file, "w", encoding="utf-8") as f:
                        for task_id in task_ids:
                            f.write(f"{task_id}\n")
                    logger.info(f"任务ID已保存到: {output_file}")
                    logger.info("")
                    logger.info("现在可以运行功能测试:")
                    logger.info("python VabHub/backend/scripts/test_download_features.py")
            else:
                logger.warning("未找到有hash的任务")
                
        except Exception as e:
            logger.error(f"同步任务失败: {e}")
            import traceback
            logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())

