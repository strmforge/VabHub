"""
测试Transmission标签设置和获取
"""

import asyncio
import sys
from pathlib import Path
from loguru import logger

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.downloaders import DownloaderClient, DownloaderType
from app.modules.settings.service import SettingsService
from app.core.database import AsyncSessionLocal, init_db

async def test_transmission_labels():
    """测试Transmission标签功能"""
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
            
            logger.info("="*60)
            logger.info("测试Transmission标签功能")
            logger.info("="*60)
            logger.info(f"连接信息: {host}:{port}")
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
            
            # 获取前5个任务
            logger.info("获取前5个任务...")
            torrents = await client.client.get_torrents()
            
            if not torrents:
                logger.warning("未找到任何任务")
                return
            
            logger.info(f"找到 {len(torrents)} 个任务，检查前5个...")
            logger.info("")
            
            # 检查前5个任务的标签
            for i, torrent in enumerate(torrents[:5], 1):
                torrent_id = torrent.get("id")
                name = torrent.get("name", "未知")
                labels = torrent.get("labels", [])
                
                logger.info(f"任务 {i}: {name[:60]}")
                logger.info(f"  ID: {torrent_id}")
                logger.info(f"  Hash: {torrent.get('hashString', '未知')}")
                
                # 处理标签格式
                if isinstance(labels, list):
                    labels_list = labels
                elif isinstance(labels, str):
                    labels_list = [label.strip() for label in labels.split(",") if label.strip()]
                else:
                    labels_list = []
                
                logger.info(f"  当前标签: {labels_list if labels_list else '无标签'}")
                logger.info(f"  标签类型: {type(labels)}")
                logger.info(f"  标签原始值: {repr(labels)}")
                
                # 尝试设置标签
                if "VABHUB" not in labels_list:
                    logger.info(f"  尝试添加VABHUB标签...")
                    result = await client.client.set_torrent_labels([torrent_id], labels_list + ["VABHUB"])
                    if result:
                        logger.info(f"  ✓ 标签设置成功")
                        # 重新获取任务信息验证
                        updated_torrents = await client.client.get_torrents(ids=[torrent_id])
                        if updated_torrents:
                            updated_labels = updated_torrents[0].get("labels", [])
                            logger.info(f"  更新后标签: {updated_labels}")
                    else:
                        logger.error(f"  ✗ 标签设置失败")
                else:
                    logger.info(f"  ✓ 已有VABHUB标签")
                
                logger.info("")
            
            # 检查Transmission版本信息
            logger.info("="*60)
            logger.info("检查Transmission版本和API支持")
            logger.info("="*60)
            
            # 尝试获取会话信息
            session_info = await client.client._request("session-get", {})
            if session_info:
                version = session_info.get("version", "未知")
                rpc_version = session_info.get("rpc-version", "未知")
                logger.info(f"Transmission版本: {version}")
                logger.info(f"RPC版本: {rpc_version}")
                
                # 检查是否支持labels字段
                logger.info("")
                logger.info("检查API字段支持...")
                # 尝试获取一个任务的完整信息，看看有哪些字段
                if torrents:
                    test_torrent_id = torrents[0].get("id")
                    # 请求所有可用字段
                    all_fields_result = await client.client._request("torrent-get", {
                        "ids": [test_torrent_id],
                        "fields": ["id", "name", "labels"]
                    })
                    if all_fields_result:
                        logger.info(f"API返回的字段: {list(all_fields_result.get('torrents', [{}])[0].keys())}")
            
            await client.close()
            
            logger.info("")
            logger.info("="*60)
            logger.info("测试完成")
            logger.info("="*60)
            
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(test_transmission_labels())

