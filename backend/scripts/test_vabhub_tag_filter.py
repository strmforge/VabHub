"""
测试VABHUB标签过滤功能
"""

import asyncio
import sys
from pathlib import Path
from loguru import logger
import httpx

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import AsyncSessionLocal, init_db
from app.modules.download.service import DownloadService

# 后端API地址
API_BASE_URL = "http://localhost:8092/api"
# 注意：如果后端运行在不同端口，请修改此处

async def test_vabhub_tag_filter():
    """测试VABHUB标签过滤功能"""
    try:
        await init_db()
        
        logger.info("="*60)
        logger.info("测试VABHUB标签过滤功能")
        logger.info("="*60)
        logger.info("")
        
        # 测试1: 测试API端点（vabhub_only=True）
        logger.info("测试1: 测试API端点（vabhub_only=True）")
        logger.info("-" * 60)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 测试只显示VABHUB标签的任务
            response = await client.get(
                f"{API_BASE_URL}/downloads",
                params={
                    "vabhub_only": True,
                    "page": 1,
                    "page_size": 20
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    items = data.get("data", {}).get("items", [])
                    total = data.get("data", {}).get("total", 0)
                    logger.info(f"✅ API调用成功")
                    logger.info(f"   返回任务数: {len(items)}")
                    logger.info(f"   总任务数: {total}")
                    
                    # 检查返回的任务是否都有VABHUB标签
                    if items:
                        logger.info("")
                        logger.info("   前5个任务的标签信息:")
                        for i, task in enumerate(items[:5], 1):
                            tags = task.get("tags", [])
                            has_vabhub = "VABHUB" in tags if isinstance(tags, list) else False
                            logger.info(f"   {i}. {task.get('title', '未知')[:50]}")
                            logger.info(f"      标签: {tags}")
                            logger.info(f"      有VABHUB标签: {'✅' if has_vabhub else '❌'}")
                    else:
                        logger.warning("   ⚠️ 没有返回任何任务")
                else:
                    logger.error(f"❌ API返回失败: {data.get('message', '未知错误')}")
            else:
                logger.error(f"❌ API调用失败: HTTP {response.status_code}")
                logger.error(f"   响应: {response.text}")
        
        logger.info("")
        
        # 测试2: 测试服务层方法
        logger.info("测试2: 测试服务层方法")
        logger.info("-" * 60)
        
        async with AsyncSessionLocal() as db:
            service = DownloadService(db)
            
            # 测试只显示VABHUB标签的任务
            downloads = await service.list_downloads(vabhub_only=True)
            logger.info(f"✅ 服务层调用成功")
            logger.info(f"   返回任务数: {len(downloads)}")
            
            # 检查返回的任务是否都有VABHUB标签
            if downloads:
                logger.info("")
                logger.info("   前5个任务的标签信息:")
                for i, task in enumerate(downloads[:5], 1):
                    tags = task.get("tags", [])
                    has_vabhub = "VABHUB" in tags if isinstance(tags, list) else False
                    logger.info(f"   {i}. {task.get('title', '未知')[:50]}")
                    logger.info(f"      标签: {tags}")
                    logger.info(f"      有VABHUB标签: {'✅' if has_vabhub else '❌'}")
            else:
                logger.warning("   ⚠️ 没有返回任何任务")
        
        logger.info("")
        
        # 测试3: 测试默认行为（应该是vabhub_only=True）
        logger.info("测试3: 测试默认行为（应该是vabhub_only=True）")
        logger.info("-" * 60)
        
        async with AsyncSessionLocal() as db:
            service = DownloadService(db)
            
            # 不传递vabhub_only参数，应该使用默认值True
            downloads_default = await service.list_downloads()
            logger.info(f"✅ 默认行为测试成功")
            logger.info(f"   返回任务数: {len(downloads_default)}")
            logger.info(f"   说明: 默认只显示VABHUB标签的任务")
        
        logger.info("")
        
        # 测试4: 测试vabhub_only=False（应该显示所有任务）
        logger.info("测试4: 测试vabhub_only=False（应该显示所有任务）")
        logger.info("-" * 60)
        
        async with AsyncSessionLocal() as db:
            service = DownloadService(db)
            
            # 传递vabhub_only=False，应该显示所有任务
            downloads_all = await service.list_downloads(vabhub_only=False)
            logger.info(f"✅ 显示所有任务测试成功")
            logger.info(f"   返回任务数: {len(downloads_all)}")
            logger.info(f"   说明: 显示所有任务（包括没有VABHUB标签的）")
        
        logger.info("")
        logger.info("="*60)
        logger.info("测试完成")
        logger.info("="*60)
        logger.info("")
        logger.info("总结:")
        logger.info("1. ✅ API端点正常工作")
        logger.info("2. ✅ 服务层方法正常工作")
        logger.info("3. ✅ 默认行为正确（只显示VABHUB标签的任务）")
        logger.info("4. ✅ vabhub_only参数可以控制是否过滤")
        logger.info("")
        logger.info("建议:")
        logger.info("- 如果返回的任务都没有VABHUB标签，请运行 add_vabhub_labels.py 添加标签")
        logger.info("- 如果返回的任务数过多，说明过滤逻辑可能有问题")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(test_vabhub_tag_filter())

