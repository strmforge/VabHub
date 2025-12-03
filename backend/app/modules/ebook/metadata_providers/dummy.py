"""
Dummy 元数据提供者

用于测试和示例的本地假数据提供者，不访问外部服务。
"""

import asyncio
from typing import Optional
from loguru import logger

from app.models.ebook import EBook
from . import EBookMetadataUpdate, EBookMetadataProvider


class DummyMetadataProvider:
    """
    Dummy 元数据提供者
    
    基于书名和作者生成模拟的元数据，用于测试和演示。
    不访问外部服务，完全本地运行。
    """
    
    def __init__(self):
        self.name = "dummy"
    
    async def enrich_metadata(self, ebook: EBook) -> Optional[EBookMetadataUpdate]:
        """
        基于现有信息生成模拟元数据
        
        规则：
        - 如果已有 description，不生成
        - 如果已有 publish_year，不生成
        - 如果已有 isbn，不生成
        - 其他字段根据书名/作者生成模拟值
        """
        # 模拟网络延迟
        await asyncio.sleep(0.1)
        
        # 如果没有任何基础信息，无法生成元数据
        if not ebook.title:
            logger.debug("DummyMetadataProvider: 缺少书名，无法生成元数据")
            return None
        
        update = EBookMetadataUpdate(
            provider_name=self.name,
            confidence=0.3,  # 假数据可信度较低
        )
        
        # 生成描述（如果为空）
        if not ebook.description:
            if ebook.author:
                update.description = f"《{ebook.title}》是{ebook.author}创作的一部作品。"
            else:
                update.description = f"《{ebook.title}》是一部优秀的文学作品。"
        
        # 生成出版年份（如果为空，基于书名长度生成一个假年份）
        if not ebook.publish_year:
            # 简单的哈希算法生成一个假年份（2000-2024）
            year_hash = hash(ebook.title) % 25
            update.publish_year = 2000 + year_hash
        
        # 生成 ISBN（如果为空）
        if not ebook.isbn:
            # 生成一个假的 ISBN-13
            isbn_hash = abs(hash(ebook.title + (ebook.author or ""))) % 1000000000000
            update.isbn = f"978{isbn_hash:010d}"
        
        # 生成标签（如果为空）
        if not ebook.tags:
            tags_list = ["文学", "小说"]
            if ebook.author:
                tags_list.append("作者作品")
            if ebook.series:
                tags_list.append("系列作品")
            update.tags = ", ".join(tags_list)
        
        logger.debug(f"DummyMetadataProvider: 为《{ebook.title}》生成了模拟元数据")
        return update

