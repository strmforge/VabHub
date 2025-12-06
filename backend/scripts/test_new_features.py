"""
测试新开发的功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 确保 scripts 目录在 sys.path（支持 CI 环境）
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

import httpx
from loguru import logger

from api_test_config import API_BASE_URL, api_url

# API基础URL
BASE_URL = API_BASE_URL

# 测试数据
TEST_MEDIA_FILE = "/tmp/test_movie.mkv"  # 测试文件路径
TEST_DIRECTORY = "/tmp/test_media"  # 测试目录
TEST_DOUBAN_QUERY = "肖申克的救赎"  # 测试豆瓣搜索


async def test_douban_api():
    """测试豆瓣API"""
    logger.info("=" * 60)
    logger.info("测试豆瓣API")
    logger.info("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 测试搜索电影
            logger.info("1. 测试搜索电影...")
            response = await client.get(
                api_url("/douban/search"),
                params={"query": TEST_DOUBAN_QUERY, "media_type": "movie", "count": 5}
            )
            logger.info(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   响应: {data.get('message', 'N/A')}")
                if data.get('data', {}).get('items'):
                    logger.info(f"   找到 {len(data['data']['items'])} 个结果")
            else:
                logger.error(f"   错误: {response.text}")
            
            # 测试获取TOP250
            logger.info("2. 测试获取TOP250...")
            response = await client.get(
                api_url("/douban/top250"),
                params={"count": 5}
            )
            logger.info(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   响应: {data.get('message', 'N/A')}")
                if data.get('data', {}).get('items'):
                    logger.info(f"   找到 {len(data['data']['items'])} 个结果")
            else:
                logger.error(f"   错误: {response.text}")
            
            # 测试获取热门电影
            logger.info("3. 测试获取热门电影...")
            response = await client.get(
                api_url("/douban/hot/movie"),
                params={"count": 5}
            )
            logger.info(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   响应: {data.get('message', 'N/A')}")
                if data.get('data', {}).get('items'):
                    logger.info(f"   找到 {len(data['data']['items'])} 个结果")
            else:
                logger.error(f"   错误: {response.text}")
        
        except Exception as e:
            logger.error(f"测试豆瓣API失败: {e}")


async def test_media_renamer_api():
    """测试媒体文件管理API"""
    logger.info("=" * 60)
    logger.info("测试媒体文件管理API")
    logger.info("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 测试识别文件（需要实际文件）
            logger.info("1. 测试识别文件...")
            logger.info(f"   注意: 需要实际文件路径: {TEST_MEDIA_FILE}")
            response = await client.post(
                api_url("/media-renamer/identify"),
                params={"file_path": TEST_MEDIA_FILE}
            )
            logger.info(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   响应: {data.get('message', 'N/A')}")
            else:
                logger.warning(f"   警告: {response.status_code} - {response.text}")
        
        except Exception as e:
            logger.error(f"测试媒体文件管理API失败: {e}")


async def test_duplicate_detection_api():
    """测试重复文件检测API"""
    logger.info("=" * 60)
    logger.info("测试重复文件检测API")
    logger.info("=" * 60)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # 测试检测重复文件（需要实际目录）
            logger.info("1. 测试检测重复文件...")
            logger.info(f"   注意: 需要实际目录路径: {TEST_DIRECTORY}")
            response = await client.post(
                api_url("/duplicate-detection/detect"),
                params={
                    "directory": TEST_DIRECTORY,
                    "extensions": [".mp4", ".mkv"],
                    "use_hash": False  # 使用快速检测
                }
            )
            logger.info(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   响应: {data.get('message', 'N/A')}")
                if data.get('data', {}).get('total_groups'):
                    logger.info(f"   找到 {data['data']['total_groups']} 组重复文件")
            else:
                logger.warning(f"   警告: {response.status_code} - {response.text}")
        
        except Exception as e:
            logger.error(f"测试重复文件检测API失败: {e}")


async def test_quality_comparison_api():
    """测试文件质量比较API"""
    logger.info("=" * 60)
    logger.info("测试文件质量比较API")
    logger.info("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 测试分析文件质量（需要实际文件）
            logger.info("1. 测试分析文件质量...")
            logger.info(f"   注意: 需要实际文件路径: {TEST_MEDIA_FILE}")
            response = await client.post(
                api_url("/quality-comparison/analyze"),
                params={"file_path": TEST_MEDIA_FILE}
            )
            logger.info(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   响应: {data.get('message', 'N/A')}")
                if data.get('data'):
                    quality_info = data['data']
                    logger.info(f"   质量评分: {quality_info.get('quality_score', 'N/A')}")
                    logger.info(f"   分辨率: {quality_info.get('resolution', 'N/A')}")
                    logger.info(f"   编码器: {quality_info.get('codec', 'N/A')}")
            else:
                logger.warning(f"   警告: {response.status_code} - {response.text}")
        
        except Exception as e:
            logger.error(f"测试文件质量比较API失败: {e}")


async def test_subtitle_api():
    """测试字幕管理API"""
    logger.info("=" * 60)
    logger.info("测试字幕管理API")
    logger.info("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 测试获取字幕列表
            logger.info("1. 测试获取字幕列表...")
            response = await client.get(
                api_url("/subtitle"),
                params={"page": 1, "page_size": 10}
            )
            logger.info(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"   响应: {data.get('message', 'N/A')}")
                if data.get('data', {}).get('items'):
                    logger.info(f"   找到 {len(data['data']['items'])} 个字幕")
            else:
                logger.warning(f"   警告: {response.status_code} - {response.text}")
        
        except Exception as e:
            logger.error(f"测试字幕管理API失败: {e}")


async def main():
    """主测试函数"""
    logger.info("开始测试新开发的功能...")
    logger.info(f"API基础URL: {BASE_URL}")
    logger.info("")
    
    # 测试各个功能
    await test_douban_api()
    await test_media_renamer_api()
    await test_duplicate_detection_api()
    await test_quality_comparison_api()
    await test_subtitle_api()
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试完成")
    logger.info("=" * 60)
    logger.info("")
    logger.info("注意: 某些测试需要实际的文件或目录路径")
    logger.info("请根据实际情况修改测试数据")


if __name__ == "__main__":
    asyncio.run(main())

