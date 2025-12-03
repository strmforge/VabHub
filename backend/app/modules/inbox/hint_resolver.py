"""
PT 下载任务 hint 解析器

根据文件路径从 DownloadTask 中查找并填充 PT 相关 hint 信息。
"""

from pathlib import Path
from typing import List, Optional
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.models.download import DownloadTask
from .models import InboxItem


async def attach_pt_hints(db: AsyncSession, items: List[InboxItem]) -> List[InboxItem]:
    """
    根据 InboxItem.path 去数据库中尽可能匹配 DownloadTask，
    返回带有 PT hint 的新 InboxItem 列表。
    
    Args:
        db: 数据库会话
        items: 原始 InboxItem 列表
    
    Returns:
        List[InboxItem]: 带有 PT hint 的 InboxItem 列表
    """
    if not items:
        return items
    
    # 批量查询所有 DownloadTask（避免 N+1 查询）
    try:
        stmt = select(DownloadTask)
        result = await db.execute(stmt)
        all_tasks = result.scalars().all()
    except Exception as e:
        logger.warning(f"查询 DownloadTask 失败: {e}")
        return items  # 失败时返回原始列表
    
    # 构建路径到任务的映射
    # 注意：DownloadTask 可能没有直接的 save_path 字段，我们尝试从 extra_metadata 中提取
    path_to_task: dict[Path, DownloadTask] = {}
    
    for task in all_tasks:
        # 尝试从 extra_metadata 中提取路径信息
        if task.extra_metadata:
            save_path = task.extra_metadata.get("save_path") or task.extra_metadata.get("download_path")
            if save_path:
                try:
                    task_path = Path(save_path)
                    # 如果任务路径是目录，匹配该目录下的所有文件
                    if task_path.is_dir() or not task_path.exists():
                        # 存储目录路径，用于后续匹配
                        path_to_task[task_path] = task
                    else:
                        # 存储文件路径
                        path_to_task[task_path] = task
                except Exception as e:
                    logger.debug(f"解析任务路径失败: {save_path}, 错误: {e}")
    
    # 为每个 item 查找匹配的任务
    items_with_hints: List[InboxItem] = []
    
    for item in items:
        matched_task: Optional[DownloadTask] = None
        
        # 策略 1: 精确路径匹配
        if item.path in path_to_task:
            matched_task = path_to_task[item.path]
        else:
            # 策略 2: 父目录匹配（如果任务保存的是目录）
            for task_path, task in path_to_task.items():
                try:
                    if task_path.is_dir() or not task_path.exists():
                        # 检查 item.path 是否在 task_path 目录下
                        try:
                            item.path.relative_to(task_path)
                            matched_task = task
                            break
                        except ValueError:
                            # 不在该目录下，继续
                            continue
                except Exception:
                    continue
        
        # 如果找到匹配的任务，提取 hint 信息
        if matched_task:
            # 从 extra_metadata 中提取分类和标签
            category = None
            tags = None
            site_id = None
            site_name = None
            
            if matched_task.extra_metadata:
                category = matched_task.extra_metadata.get("category") or matched_task.extra_metadata.get("type")
                tags = matched_task.extra_metadata.get("tags") or matched_task.extra_metadata.get("tag_list")
                site_id = matched_task.extra_metadata.get("site_id")
                site_name = matched_task.extra_metadata.get("site_name")
            
            # 如果 extra_metadata 中没有，尝试从 media_type 推断
            if not category and matched_task.media_type and matched_task.media_type != "unknown":
                category = matched_task.media_type
            
            # 创建带 hint 的新 InboxItem
            new_item = InboxItem(
                path=item.path,
                download_task_id=matched_task.id,
                source_site_id=site_id,
                source_site_name=site_name,
                source_category=category,
                source_tags=tags if isinstance(tags, list) else ([tags] if tags else None)
            )
            items_with_hints.append(new_item)
        else:
            # 没有匹配的任务，保持原样
            items_with_hints.append(item)
    
    logger.debug(f"为 {len(items_with_hints)} 个项目附加 PT hint，其中 {sum(1 for item in items_with_hints if item.download_task_id)} 个匹配到下载任务")
    
    return items_with_hints

