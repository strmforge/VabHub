"""
检查服务状态脚本
检查后端服务是否正常运行
"""

import asyncio
import sys
import httpx
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

from loguru import logger

# 配置日志（修复Windows编码问题）
import io
import sys

# 设置标准输出编码为UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except:
        # 如果reconfigure不可用，使用TextIOWrapper
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logger.remove()
logger.add(
    sys.stdout, 
    format="{time:HH:mm:ss} | {level: <8} | {message}", 
    level="INFO"
)


async def check_service():
    """检查服务状态"""
    base_url = "http://localhost:8000"
    
    logger.info("=" * 60)
    logger.info("检查后端服务状态")
    logger.info("=" * 60)
    logger.info("")
    
    # 检查健康检查端点
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                logger.info("[OK] 后端服务运行正常")
                logger.info(f"响应: {response.json()}")
                return True
            else:
                logger.error(f"[ERROR] 健康检查失败: {response.status_code}")
                logger.error(f"响应: {response.text}")
                return False
    except httpx.ConnectError:
        logger.error("[ERROR] 无法连接到后端服务")
        logger.error("请确保后端服务已启动")
        logger.error("启动命令: python backend/scripts/start.py")
        return False
    except httpx.ReadTimeout:
        logger.warning("[WARNING] 服务响应超时，可能正在启动中...")
        logger.warning("请稍候再试，或检查服务日志")
        return False
    except Exception as e:
        logger.error(f"[ERROR] 检查服务状态失败: {e}")
        return False


async def check_api_docs():
    """检查API文档"""
    base_url = "http://localhost:8000"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{base_url}/docs")
            if response.status_code == 200:
                logger.info("[OK] API文档可访问")
                return True
            else:
                logger.error(f"[ERROR] API文档不可访问: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"[ERROR] 检查API文档失败: {e}")
        return False


async def main():
    """主函数"""
    logger.info("")
    logger.info("开始检查服务状态...")
    logger.info("")
    
    # 检查服务
    service_ok = await check_service()
    logger.info("")
    
    # 检查API文档
    if service_ok:
        await check_api_docs()
    
    logger.info("")
    logger.info("=" * 60)
    
    if service_ok:
        logger.info("[OK] 服务状态正常，可以开始测试")
        return 0
    else:
        logger.error("[ERROR] 服务未运行或无法访问，请先启动服务")
        logger.error("启动命令: python backend/scripts/start.py")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

