"""
电子书作品解析器

负责识别和匹配电子书作品，确保同一作品只对应一个 EBook 记录。
"""

import re
from typing import Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from loguru import logger

from app.models.ebook import EBook


class EBookWorkResolver:
    """
    电子书作品解析器
    
    用于判断新导入的电子书是否与已有作品重复，并找到对应的 EBook 记录。
    匹配策略保守，宁可少合并，避免不同书被错当成同一本。
    """
    
    @staticmethod
    def normalize_isbn(isbn: Optional[str]) -> Optional[str]:
        """
        规范化 ISBN
        
        移除连字符、空格等，只保留数字和字母。
        
        Args:
            isbn: 原始 ISBN 字符串
        
        Returns:
            规范化后的 ISBN，如果输入为空则返回 None
        """
        if not isbn:
            return None
        
        # 移除所有非字母数字字符
        normalized = re.sub(r'[^0-9A-Za-z]', '', str(isbn))
        
        # 如果规范化后为空，返回 None
        if not normalized:
            return None
        
        return normalized
    
    @staticmethod
    def normalize_title(title: str) -> str:
        """
        规范化书名
        
        规则：
        - 去除前后空格
        - 转为小写
        - 移除常见的后缀标记，如 [精校]、[EPUB]、[完整版] 等
        
        Args:
            title: 原始书名
        
        Returns:
            规范化后的书名
        """
        if not title:
            return ""
        
        # 去除前后空格
        normalized = title.strip()
        
        # 移除常见的后缀标记（用正则匹配方括号、圆括号内的内容）
        # 例如："三体 [精校版]" -> "三体"
        # 例如："三体 (完整版)" -> "三体"
        # 例如："Title [Enhanced]" -> "Title"
        # 注意：只移除常见的标记，保留可能有意义的括号内容（如副标题）
        common_suffixes = [
            r'\s*\[精校[^\]]*\]',
            r'\s*\[EPUB[^\]]*\]',
            r'\s*\[完整版[^\]]*\]',
            r'\s*\[校对[^\]]*\]',
            r'\s*\(精校[^\)]*\)',
            r'\s*\(EPUB[^\)]*\)',
            r'\s*\(完整版[^\)]*\)',
            r'\s*\[Enhanced[^\]]*\]',
            r'\s*\[enhanced[^\]]*\]',
            r'\s*\[ENHANCED[^\]]*\]',
        ]
        
        for pattern in common_suffixes:
            normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
        
        # 转为小写（用于匹配）
        # 注意：这里只做规范化用于匹配，实际存储时保留原始大小写
        normalized = normalized.lower().strip()
        
        return normalized
    
    @staticmethod
    def normalize_author(author: Optional[str]) -> Optional[str]:
        """
        规范化作者名
        
        规则：
        - 去除前后空格
        - 转为小写
        - 移除常见的后缀标记，如（作者版）、[著] 等
        
        Args:
            author: 原始作者名
        
        Returns:
            规范化后的作者名，如果输入为空则返回 None
        """
        if not author:
            return None
        
        # 去除前后空格
        normalized = author.strip()
        
        # 移除常见的后缀标记（支持中文括号）
        common_suffixes = [
            r'\s*\(作者版[^\)]*\)',
            r'\s*（作者版[^）]*）',  # 中文括号
            r'\s*\[著[^\]]*\]',
            r'\s*\[作者[^\]]*\]',
        ]
        
        for pattern in common_suffixes:
            normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
        
        # 转为小写（用于匹配）
        normalized = normalized.lower().strip()
        
        if not normalized:
            return None
        
        return normalized
    
    @staticmethod
    def normalize_volume_index(volume_index: Optional[Union[int, str]]) -> Optional[str]:
        """
        规范化卷号
        
        将卷号统一为字符串格式，便于比较。
        
        Args:
            volume_index: 卷号（可能是整数或字符串）
        
        Returns:
            规范化后的卷号字符串，如果输入为空则返回 None
        """
        if volume_index is None:
            return None
        
        # 转为字符串并去除空格
        normalized = str(volume_index).strip()
        
        if not normalized:
            return None
        
        return normalized
    
    async def find_existing_work(
        self,
        db: AsyncSession,
        *,
        isbn: Optional[str] = None,
        title: str,
        author: Optional[str] = None,
        series: Optional[str] = None,
        volume_index: Optional[Union[int, str]] = None
    ) -> Optional[EBook]:
        """
        查找已存在的作品
        
        匹配策略（按优先级）：
        1. 如果有 ISBN，优先使用 ISBN 匹配（最可靠）
        2. 如果没有 ISBN 或未命中，使用规范化后的 (title, author, series, volume_index) 组合匹配
        3. 如果 series/volume_index 信息完整，使用更严格的匹配
        
        Args:
            db: 数据库会话
            isbn: ISBN 号码（可选）
            title: 书名（必需）
            author: 作者名（可选）
            series: 系列名（可选）
            volume_index: 卷号（可选）
        
        Returns:
            找到的 EBook 对象，如果未找到则返回 None
        """
        if not title:
            logger.warning("EBookWorkResolver: title 为空，无法匹配作品")
            return None
        
        # 规范化输入
        normalized_isbn = self.normalize_isbn(isbn) if isbn else None
        normalized_title = self.normalize_title(title)
        normalized_author = self.normalize_author(author)
        normalized_series = series.strip() if series else None
        normalized_volume_index = self.normalize_volume_index(volume_index)
        
        # 策略 1: 如果有 ISBN，优先使用 ISBN 匹配
        if normalized_isbn:
            try:
                stmt = select(EBook).where(EBook.isbn == normalized_isbn)
                result = await db.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    logger.debug(f"通过 ISBN {normalized_isbn} 找到已存在的作品: {existing.id} - {existing.title}")
                    return existing
            except Exception as e:
                logger.warning(f"通过 ISBN 匹配作品时出错: {e}")
        
        # 策略 2: 使用规范化后的 (title, author, series, volume_index) 组合匹配
        # 构建查询条件
        conditions = []
        
        # title 必须匹配（使用规范化后的值）
        # 注意：由于规范化涉及大小写转换，我们需要在 Python 侧进行规范化比较
        # 或者使用数据库的 LOWER 函数（如果数据库支持）
        # 这里先查询所有可能的候选，然后在 Python 侧进行规范化比较
        
        # 先按 title 的原始值查询（近似匹配）
        # 由于规范化可能改变大小写，我们先查询所有可能的候选
        stmt = select(EBook)
        
        # 如果 author 存在，加入 author 条件
        if normalized_author:
            # 同样，author 也需要规范化比较
            # 先按原始值查询近似匹配
            pass
        
        # 执行查询，获取候选列表
        # 由于规范化涉及大小写转换和移除后缀，我们需要查询所有可能的候选，然后在 Python 侧比较
        # 策略：
        # 1. 先用 series/volume_index 精确过滤（如果提供）- 这些字段通常比较准确
        # 2. 对于 title/author，如果 series/volume 已提供，可以放宽查询条件
        # 3. 在 Python 侧进行规范化后的精确比较
        
        stmt = select(EBook)
        
        # 如果 series 存在，先用 series 精确过滤
        if normalized_series:
            stmt = stmt.where(EBook.series == normalized_series)
        
        # 如果 volume_index 存在，先用 volume_index 精确过滤
        if normalized_volume_index:
            stmt = stmt.where(EBook.volume_index == normalized_volume_index)
        
        # 对于 title，提取核心部分（去掉常见后缀）进行查询
        # 策略：先用 series/volume 精确过滤（如果提供），然后用 title 核心部分模糊查询
        # 最后在 Python 侧进行规范化后的精确比较
        if normalized_title:
            # 提取 title 的核心部分（去掉常见后缀）
            import re
            title_core = title
            # 移除常见后缀
            for pattern in [r'\s*\[精校[^\]]*\]', r'\s*\[EPUB[^\]]*\]', r'\s*\[完整版[^\]]*\]', 
                           r'\s*\[校对[^\]]*\]', r'\s*\(精校[^\)]*\)', r'\s*\(EPUB[^\)]*\)', r'\s*\(完整版[^\)]*\)',
                           r'\s*\[Enhanced[^\]]*\]', r'\s*\[enhanced[^\]]*\]']:
                title_core = re.sub(pattern, '', title_core, flags=re.IGNORECASE)
            title_core = title_core.strip()
            if title_core:
                # 使用核心部分进行模糊查询（不区分大小写）
                stmt = stmt.where(EBook.title.ilike(f"%{title_core}%"))
        
        # 如果 author 存在，加入 author 条件（精确匹配）
        if normalized_author and author:
            stmt = stmt.where(EBook.author == author)
        
        try:
            result = await db.execute(stmt)
            candidates = result.scalars().all()
            
            # 在 Python 侧进行规范化比较
            for candidate in candidates:
                # 规范化候选记录的字段
                candidate_title_norm = self.normalize_title(candidate.title or "")
                candidate_author_norm = self.normalize_author(candidate.author)
                candidate_series_norm = candidate.series.strip() if candidate.series else None
                candidate_volume_index_norm = self.normalize_volume_index(candidate.volume_index)
                
                # 比较规范化后的值
                title_match = candidate_title_norm == normalized_title
                author_match = (
                    (normalized_author is None and candidate_author_norm is None) or
                    (normalized_author is not None and candidate_author_norm is not None and
                     candidate_author_norm == normalized_author)
                )
                series_match = (
                    (normalized_series is None and candidate_series_norm is None) or
                    (normalized_series is not None and candidate_series_norm is not None and
                     candidate_series_norm == normalized_series)
                )
                volume_index_match = (
                    (normalized_volume_index is None and candidate_volume_index_norm is None) or
                    (normalized_volume_index is not None and candidate_volume_index_norm is not None and
                     candidate_volume_index_norm == normalized_volume_index)
                )
                
                # 匹配规则（保守策略）：
                # - title 必须匹配
                # - 如果提供了 author，必须匹配
                # - 如果提供了 series，必须匹配
                # - 如果提供了 volume_index，必须匹配
                if title_match:
                    # 如果提供了 author，必须匹配
                    if normalized_author is not None:
                        if not author_match:
                            continue
                    
                    # 如果提供了 series，必须匹配
                    if normalized_series is not None:
                        if not series_match:
                            continue
                    
                    # 如果提供了 volume_index，必须匹配
                    if normalized_volume_index is not None:
                        if not volume_index_match:
                            continue
                    
                    # 所有条件都满足，认为是同一作品
                    logger.debug(
                        f"通过规范化匹配找到已存在的作品: {candidate.id} - {candidate.title} "
                        f"(title={title_match}, author={author_match}, series={series_match}, volume={volume_index_match})"
                    )
                    return candidate
            
            # 没有找到匹配的作品
            logger.debug(f"未找到匹配的作品: title={title}, author={author}, series={series}, volume_index={volume_index}")
            return None
            
        except Exception as e:
            logger.warning(f"匹配作品时出错: {e}")
            return None

