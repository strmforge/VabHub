"""
健康检查脚本
检查系统各个组件的健康状态
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
backend_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.core.health import get_health_checker
from loguru import logger


async def main():
    """主函数"""
    logger.info("="*50)
    logger.info("VabHub 健康检查")
    logger.info("="*50)
    
    health_checker = get_health_checker()
    
    # 执行所有检查
    result = await health_checker.check_all()
    
    # 显示结果
    logger.info(f"整体状态: {result['status']}")
    logger.info(f"检查项数量: {len(result['checks'])}")
    logger.info("")
    
    for check_name, check_result in result['checks'].items():
        status = check_result.get('status', 'unknown')
        message = check_result.get('message', '')
        
        if status == 'healthy':
            logger.info(f"✅ {check_name}: {message}")
        elif status == 'warning':
            logger.warning(f"⚠️ {check_name}: {message}")
        else:
            logger.error(f"❌ {check_name}: {message}")
    
    logger.info("="*50)
    
    # 返回退出码
    if result['status'] == 'healthy':
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

