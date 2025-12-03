"""
漫画作品解析器

负责查找或创建 Comic 作品记录，确保同一作品不会重复创建。
"""

import re
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from loguru import logger

from app.models.comic import Comic


class ComicWorkResolver:
    """
    漫画作品解析器
    
    用于查找已存在的漫画作品，避免重复创建。
    """
    
    @staticmethod
    def _normalize_string(s: Optional[str]) -> Optional[str]:
        """规范化字符串（去除空格、转小写）"""
        if not s:
            return None
        return s.strip().lower()
    
    @staticmethod
    def _normalize_volume_index(volume_index: Optional[int]) -> Optional[int]:
        """规范化卷号"""
        return volume_index
    
    async def find_existing_work(
        self,
        db: AsyncSession,
        title: str,
        author: Optional[str] = None,
        series: Optional[str] = None,
        volume_index: Optional[int] = None
    ) -> Optional[Comic]:
        """
        查找已存在的漫画作品
        
        Args:
            db: 数据库会话
            title: 作品标题
            author: 作者（可选）
            series: 系列名（可选）
            volume_index: 卷号（可选）
        
        Returns:
            如果找到已存在的作品，返回 Comic 对象；否则返回 None
        """
        if not title:
            return None
        
        # 规范化输入
        normalized_title = self._normalize_string(title)
        normalized_author = self._normalize_string(author)
        normalized_series = self._normalize_string(series)
        normalized_volume = self._normalize_volume_index(volume_index)
        
        # 构建查询条件
        conditions = []
        
        # 标题必须匹配
        conditions.append(
            or_(
                Comic.title.ilike(f"%{normalized_title}%"),
                Comic.original_title.ilike(f"%{normalized_title}%")
            )
        )
        
        # 如果有作者，尝试匹配作者
        if normalized_author:
            conditions.append(
                or_(
                    Comic.author.ilike(f"%{normalized_author}%"),
                    Comic.illustrator.ilike(f"%{normalized_author}%")
                )
            )
        
        # 如果有系列，尝试匹配系列
        if normalized_series:
            conditions.append(Comic.series.ilike(f"%{normalized_series}%"))
        
        # 如果有卷号，尝试匹配卷号
        if normalized_volume is not None:
            conditions.append(Comic.volume_index == normalized_volume)
        
        # 执行查询
        stmt = select(Comic).where(and_(*conditions))
        result = await db.execute(stmt)
        existing_comic = result.scalar_one_or_none()
        
        if existing_comic:
            logger.debug(f"找到已存在的漫画作品: {existing_comic.id} - {existing_comic.title}")
        
        return existing_comic

