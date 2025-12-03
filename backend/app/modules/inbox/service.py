"""
统一待整理收件箱服务

提供高层接口，整合扫描、检测、路由的完整流程。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from .scanner import InboxScanner
from .models import InboxItem
from .hint_resolver import attach_pt_hints
from .media_detection.service import get_default_detection_service, MediaTypeDetectionService
from .router import InboxRouter


async def run_inbox_classification(
    db: AsyncSession,
    detection_service: Optional[MediaTypeDetectionService] = None,
    router: Optional[InboxRouter] = None,
    scanner: Optional[InboxScanner] = None
) -> List[Dict[str, Any]]:
    """
    执行统一收件箱分类流程
    
    1. 扫描 INBOX_ROOT，得到 InboxItem 列表
    2. 对每个 InboxItem 调用 detection_service.detect()
    3. 再调用 InboxRouter.route()（如果 router 不为 None）
    4. 返回结果列表
    
    Args:
        db: 数据库会话
        detection_service: 检测服务（如果为 None，使用默认服务）
        router: 路由器（如果为 None，只检测不路由）
        scanner: 扫描器（如果为 None，使用默认扫描器）
    
    Returns:
        List[Dict[str, Any]]: 结果列表，每项包含：
            - path: str
            - media_type: str
            - score: float
            - reason: str
            - size_bytes: int
            - modified_at: str (ISO 格式)
            - result: str (如果执行了路由，包含处理结果)
    """
    # 初始化组件
    if scanner is None:
        scanner = InboxScanner()
    
    if detection_service is None:
        detection_service = get_default_detection_service()
    
    if router is None:
        router = InboxRouter(db=db)
    
    results: List[Dict[str, Any]] = []
    
    # 步骤 1: 扫描收件箱
    logger.info("开始扫描统一收件箱...")
    items = scanner.scan_inbox()
    logger.info(f"扫描完成，发现 {len(items)} 个待处理项目")
    
    # 步骤 1.5: 为 items 附加 PT hint（从 DownloadTask 中查找）
    items = await attach_pt_hints(db, items)
    
    # 步骤 2 & 3: 对每个项目进行检测和路由
    for item in items:
        try:
            # 获取文件信息
            stat = item.path.stat()
            size_bytes = stat.st_size
            modified_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
            
            # 检测媒体类型
            guess = detection_service.detect(item)
            
            # 构建结果字典
            result_dict: Dict[str, Any] = {
                "path": str(item.path),
                "media_type": guess.media_type,
                "score": guess.score,
                "reason": guess.reason,
                "size_bytes": size_bytes,
                "modified_at": modified_at
            }
            
            # 如果提供了 router，执行路由
            if router:
                route_result = await router.route(item, guess)
                result_dict["result"] = route_result
            
            results.append(result_dict)
            
        except Exception as e:
            logger.error(f"处理项目失败: {item.path}, 错误: {e}", exc_info=True)
            # 即使失败，也记录一个结果
            results.append({
                "path": str(item.path),
                "media_type": "unknown",
                "score": 0.0,
                "reason": f"error:{str(e)}",
                "size_bytes": 0,
                "modified_at": datetime.now().isoformat(),
                "result": f"error:{str(e)}" if router else None
            })
    
    logger.info(f"统一收件箱分类完成，处理了 {len(results)} 个项目")
    
    return results

