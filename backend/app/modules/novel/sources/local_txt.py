"""
本地 TXT 文件小说来源适配器

Demo 用途：从本地 TXT 文件中读取小说内容并拆分为章节。
注意：这是 Demo 实现，不是面向任意网站/文件的通用实现。
"""

import re
from pathlib import Path
from typing import Iterable, List, Optional
from loguru import logger

from app.modules.novel.source_base import NovelSourceAdapter
from app.modules.novel.models import StandardChapter, NovelMetadata


class LocalTxtNovelSourceAdapter(NovelSourceAdapter):
    """
    本地 TXT 文件小说来源适配器
    
    从本地 TXT 文件中读取小说内容，并尝试拆分为章节。
    这是一个 Demo 实现，主要用于验证小说到电子书的流程。
    """
    
    def __init__(
        self,
        file_path: Path,
        metadata: NovelMetadata,
        encoding: str = "utf-8"
    ):
        """
        初始化适配器。
        
        Args:
            file_path: TXT 文件路径
            metadata: 小说元数据
            encoding: 文件编码（默认 UTF-8）
        """
        self.file_path = file_path
        self._metadata = metadata
        self.encoding = encoding
    
    def get_metadata(self) -> NovelMetadata:
        """获取小说元数据"""
        return self._metadata
    
    def iter_chapters(self) -> Iterable[StandardChapter]:
        """
        从 TXT 文件中生成章节流。
        
        章节拆分策略：
        1. 如果文本中存在类似 "第1章" / "第X章" 的模式，用正则分割章节
        2. 否则，把整个文件作为一个章节
        
        Yields:
            StandardChapter: 标准化的章节数据
        """
        if not self.file_path.exists():
            logger.warning(f"文件不存在: {self.file_path}")
            return
        
        try:
            # 读取文件内容
            content = self.file_path.read_text(encoding=self.encoding)
            
            if not content.strip():
                logger.warning(f"文件内容为空: {self.file_path}")
                return
            
            # 尝试按章节分割
            # 匹配模式：第X章、第X回、Chapter X 等
            chapter_patterns = [
                r'第[零一二三四五六七八九十百千万\d]+[章节回]',  # 第1章、第一章、第一回
                r'Chapter\s+\d+',  # Chapter 1
                r'CHAPTER\s+\d+',  # CHAPTER 1
                r'第\s*\d+\s*章',  # 第 1 章（带空格）
            ]
            
            # 尝试找到第一个匹配的模式
            matched_pattern = None
            for pattern in chapter_patterns:
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                if matches:
                    matched_pattern = pattern
                    logger.debug(f"使用章节模式: {pattern}, 找到 {len(matches)} 个章节")
                    break
            
            if matched_pattern:
                # 按章节分割
                chapters = self._split_by_pattern(content, matched_pattern)
                for idx, (title, chapter_content) in enumerate(chapters, start=1):
                    yield StandardChapter(
                        index=idx,
                        title=title.strip() or f"第{idx}章",
                        content=chapter_content.strip()
                    )
            else:
                # 没有找到章节标记，将整个文件作为一个章节
                logger.debug(f"未找到章节标记，将整个文件作为一个章节: {self.file_path}")
                yield StandardChapter(
                    index=1,
                    title=self._metadata.title or "正文",
                    content=content.strip()
                )
                
        except UnicodeDecodeError as e:
            logger.error(f"文件编码错误: {self.file_path}, 错误: {e}")
            # 尝试其他编码
            try:
                content = self.file_path.read_text(encoding="gbk")
                yield StandardChapter(
                    index=1,
                    title=self._metadata.title or "正文",
                    content=content.strip()
                )
            except Exception as e2:
                logger.error(f"尝试 GBK 编码也失败: {e2}")
        except Exception as e:
            logger.error(f"读取文件失败: {self.file_path}, 错误: {e}", exc_info=True)
    
    def _split_by_pattern(self, content: str, pattern: str) -> List[tuple]:
        """
        根据正则模式分割章节。
        
        Args:
            content: 文件内容
            pattern: 章节标题的正则模式
        
        Returns:
            List[tuple]: [(章节标题, 章节内容), ...]
        """
        chapters: List[tuple] = []
        
        # 找到所有章节标题的位置
        matches = list(re.finditer(pattern, content, re.IGNORECASE))
        
        if not matches:
            return [(self._metadata.title or "正文", content)]
        
        # 去重：如果同一位置有多个匹配（如"第1章"和"第一章"），只保留第一个
        # 按位置排序，并过滤掉重叠的匹配
        unique_matches = []
        for match in matches:
            start = match.start()
            # 检查是否与已有匹配重叠（允许小范围重叠，比如同一行的不同格式）
            is_duplicate = False
            for existing in unique_matches:
                if abs(existing.start() - start) < 10:  # 10个字符内的重叠认为是重复
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_matches.append(match)
        
        # 按位置排序
        unique_matches.sort(key=lambda m: m.start())
        
        # 分割章节
        for i, match in enumerate(unique_matches):
            chapter_title = match.group(0)
            start_pos = match.start()
            
            # 确定章节内容的结束位置
            if i + 1 < len(unique_matches):
                end_pos = unique_matches[i + 1].start()
            else:
                end_pos = len(content)
            
            # 提取章节内容（从标题后开始，到下一章标题前）
            chapter_content = content[start_pos:end_pos]
            
            # 移除章节标题行（如果内容以标题开头）
            if chapter_content.startswith(chapter_title):
                chapter_content = chapter_content[len(chapter_title):].lstrip('\n\r')
            
            chapters.append((chapter_title, chapter_content))
        
        return chapters

