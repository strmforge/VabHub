"""
创建真实测试下载任务
在实际环境中创建一些测试任务，然后使用真实的任务ID进行测试
"""

import asyncio
import httpx
import sys
from pathlib import Path
from loguru import logger

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

BASE_URL = "http://localhost:8001/api"
TIMEOUT = 30.0

# 测试用的磁力链接（公开的小文件，用于测试）
TEST_MAGNETS = [
    {
        "title": "测试任务1 - Ubuntu ISO",
        "magnet_link": "magnet:?xt=urn:btih:1234567890abcdef1234567890abcdef12345678&dn=ubuntu-20.04.iso",
        "size_gb": 2.5,
        "downloader": "qBittorrent"
    },
    {
        "title": "测试任务2 - Debian ISO",
        "magnet_link": "magnet:?xt=urn:btih:abcdef1234567890abcdef1234567890abcdef12&dn=debian-11.iso",
        "size_gb": 3.0,
        "downloader": "qBittorrent"
    },
    {
        "title": "测试任务3 - Fedora ISO",
        "magnet_link": "magnet:?xt=urn:btih:fedcba0987654321fedcba0987654321fedcba09&dn=fedora-35.iso",
        "size_gb": 1.8,
        "downloader": "Transmission"
    }
]


async def create_test_download(magnet_info: dict) -> str:
    """创建测试下载任务"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            response = await client.post(
                f"{BASE_URL}/downloads/",
                json={
                    "title": magnet_info["title"],
                    "magnet_link": magnet_info["magnet_link"],
                    "size_gb": magnet_info["size_gb"],
                    "downloader": magnet_info["downloader"]
                }
            )
            
            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                if data.get("success"):
                    task_id = data.get("data", {}).get("id") or data.get("data", {}).get("task_id")
                    if task_id:
                        logger.success(f"✓ 创建任务成功: {magnet_info['title']} (ID: {task_id})")
                        return task_id
                    else:
                        logger.warning(f"✗ 创建任务成功但未返回ID: {magnet_info['title']}")
                        logger.debug(f"响应数据: {data}")
                else:
                    logger.warning(f"✗ 创建任务失败: {magnet_info['title']} - {data.get('error_message', '未知错误')}")
            else:
                logger.warning(f"✗ 创建任务失败: {magnet_info['title']} - HTTP {response.status_code}")
                logger.debug(f"响应: {response.text}")
    except Exception as e:
        logger.error(f"✗ 创建任务异常: {magnet_info['title']} - {e}")
    
    return None


async def list_downloads() -> list:
    """获取下载列表"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            response = await client.get(f"{BASE_URL}/downloads/")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    downloads = data.get("data", {}).get("items", []) or data.get("data", [])
                    if isinstance(downloads, list):
                        return downloads
                    else:
                        logger.warning("下载列表格式错误")
                else:
                    logger.warning(f"获取下载列表失败: {data.get('error_message', '未知错误')}")
            else:
                logger.warning(f"获取下载列表失败: HTTP {response.status_code}")
    except Exception as e:
        logger.error(f"获取下载列表异常: {e}")
    
    return []


async def main():
    """主函数"""
    logger.info("="*60)
    logger.info("创建真实测试下载任务")
    logger.info("="*60)
    
    # 检查后端服务
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            # 尝试多个可能的健康检查端点
            health_urls = [
                "http://localhost:8001/health",
                "http://127.0.0.1:8001/health",
                f"{BASE_URL.replace('/api', '')}/health"
            ]
            
            connected = False
            for url in health_urls:
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        connected = True
                        break
                except:
                    continue
            
            if not connected:
                logger.error("后端服务未运行或不可用")
                logger.info("请先启动后端服务: cd VabHub/backend && python main.py")
                return
    except Exception as e:
        logger.error(f"无法连接到后端服务: {e}")
        logger.info("请先启动后端服务: cd VabHub/backend && python main.py")
        return
    
    logger.info("后端服务连接正常\n")
    
    # 获取现有下载任务
    logger.info("获取现有下载任务...")
    existing_downloads = await list_downloads()
    logger.info(f"找到 {len(existing_downloads)} 个现有任务\n")
    
    # 创建测试任务
    logger.info("创建测试下载任务...")
    created_task_ids = []
    
    for magnet_info in TEST_MAGNETS:
        task_id = await create_test_download(magnet_info)
        if task_id:
            created_task_ids.append(task_id)
        await asyncio.sleep(1)  # 避免请求过快
    
    logger.info(f"\n成功创建 {len(created_task_ids)} 个测试任务")
    
    if created_task_ids:
        logger.info("\n创建的任务ID:")
        for i, task_id in enumerate(created_task_ids, 1):
            logger.info(f"  {i}. {task_id}")
        
        # 保存到文件
        output_file = Path(__file__).parent / "test_task_ids.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            for task_id in created_task_ids:
                f.write(f"{task_id}\n")
        logger.info(f"\n任务ID已保存到: {output_file}")
        logger.info("\n提示：")
        logger.info("1. 这些任务ID可以用于测试脚本")
        logger.info("2. 测试完成后可以删除这些任务")
        logger.info("3. 如果任务创建失败，请检查下载器配置和连接")
    else:
        logger.warning("\n未创建任何测试任务")
        logger.info("\n可能的原因：")
        logger.info("1. 下载器服务未运行")
        logger.info("2. 下载器配置不正确")
        logger.info("3. 磁力链接无效")
        logger.info("4. 网络连接问题")


if __name__ == "__main__":
    asyncio.run(main())

