"""
统一待整理收件箱扫描器

负责扫描 INBOX_ROOT 目录，发现待处理的文件。
"""

from pathlib import Path
from typing import List, Optional
from loguru import logger

from app.core.config import settings
from .models import InboxItem


class InboxScanner:
    """
    待整理收件箱扫描器
    
    从 INBOX_ROOT 目录中扫描待处理的文件。
    """
    
    def __init__(self, inbox_root: Optional[Path] = None, max_items: Optional[int] = None):
        """
        初始化扫描器
        
        Args:
            inbox_root: 收件箱根目录（如果为 None，使用 settings.INBOX_ROOT）
            max_items: 最大扫描项目数（如果为 None，使用 settings.INBOX_SCAN_MAX_ITEMS）
        """
        self.inbox_root = Path(inbox_root) if inbox_root else Path(settings.INBOX_ROOT)
        self.max_items = max_items if max_items is not None else settings.INBOX_SCAN_MAX_ITEMS
    
    def scan_inbox(self) -> List[InboxItem]:
        """
        扫描收件箱目录，返回待处理项目列表
        
        Returns:
            List[InboxItem]: 待处理项目列表
        """
        items: List[InboxItem] = []
        
        # 检查目录是否存在
        if not self.inbox_root.exists():
            logger.warning(f"收件箱目录不存在: {self.inbox_root}，将自动创建")
            try:
                self.inbox_root.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"创建收件箱目录失败: {e}")
                return items
        
        if not self.inbox_root.is_dir():
            logger.error(f"收件箱路径不是目录: {self.inbox_root}")
            return items
        
        # 递归遍历目录（先只处理文件，忽略目录）
        try:
            for file_path in self.inbox_root.rglob("*"):
                # 达到最大项目数限制
                if len(items) >= self.max_items:
                    logger.warning(f"达到最大扫描项目数限制: {self.max_items}，停止扫描")
                    break
                
                # 跳过目录
                if not file_path.is_file():
                    continue
                
                # 跳过隐藏文件（以 . 开头）
                if file_path.name.startswith('.'):
                    continue
                
                # 跳过已处理标记（例如以 .imported 结尾的文件）
                if file_path.name.endswith('.imported'):
                    continue
                
                # 跳过临时文件
                if file_path.suffix.lower() in {'.tmp', '.temp', '.part'}:
                    continue
                
                items.append(InboxItem(path=file_path))
            
            logger.info(f"扫描收件箱完成，发现 {len(items)} 个待处理项目")
            
        except Exception as e:
            logger.error(f"扫描收件箱失败: {e}", exc_info=True)
        
        return items

