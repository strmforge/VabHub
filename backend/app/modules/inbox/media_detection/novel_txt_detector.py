"""
小说 TXT 文件检测器

针对 .txt 文件进行进一步判断，识别是否为小说。
"""

import re
from pathlib import Path
from typing import Optional
from loguru import logger

from app.modules.inbox.models import InboxItem
from .base import MediaTypeDetector, MediaTypeGuess


class NovelTxtDetector:
    """
    小说 TXT 文件检测器
    
    通过文件大小和内容特征判断是否为小说。
    """
    
    name = "novel_txt"
    
    # 合理的小说文件大小范围（字节）
    MIN_SIZE = 50 * 1024  # 50KB
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    
    # 章节标记模式
    CHAPTER_PATTERNS = [
        r'第[零一二三四五六七八九十百千万\d]+[章节回]',  # 第1章、第一章、第一回
        r'Chapter\s+\d+',  # Chapter 1
        r'CHAPTER\s+\d+',  # CHAPTER 1
        r'第\s*\d+\s*章',  # 第 1 章（带空格）
        r'第\s*[零一二三四五六七八九十百千万]+\s*章',  # 第 一 章
    ]
    
    def guess(self, item: InboxItem) -> Optional[MediaTypeGuess]:
        """
        判断 TXT 文件是否为小说
        
        Args:
            item: 待检测的项目
        
        Returns:
            Optional[MediaTypeGuess]: 如果是小说，返回猜测结果；否则返回 None
        """
        path = item.path
        
        # 只处理 .txt 文件
        if path.suffix.lower() != ".txt":
            return None
        
        try:
            # 检查文件大小
            file_size = path.stat().st_size
            
            if file_size < self.MIN_SIZE:
                # 文件太小，不太可能是小说
                return None
            
            if file_size > self.MAX_SIZE:
                # 文件太大，可能是其他类型的文本文件
                return None
            
            # 读取文件开头的一小段内容（控制 IO 成本）
            sample_size = min(8192, file_size)  # 最多读取 8KB
            
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                sample = f.read(sample_size)
            
            # 检查中文字符比例
            chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', sample))
            total_chars = len([c for c in sample if c.isprintable()])
            
            if total_chars == 0:
                return None
            
            chinese_ratio = chinese_chars / total_chars if total_chars > 0 else 0
            
            # 检查是否包含章节标记
            has_chapter_marker = False
            for pattern in self.CHAPTER_PATTERNS:
                if re.search(pattern, sample, re.IGNORECASE):
                    has_chapter_marker = True
                    break
            
            # 判断逻辑
            score = 0.5  # 基础分数
            
            # 中文字符比例高，加分
            if chinese_ratio > 0.3:
                score += 0.2
            
            # 有章节标记，加分
            if has_chapter_marker:
                score += 0.2
            
            # 如果满足条件，返回小说类型
            if score >= 0.7:
                reason_parts = []
                if chinese_ratio > 0.3:
                    reason_parts.append(f"chinese_ratio={chinese_ratio:.2f}")
                if has_chapter_marker:
                    reason_parts.append("chapter_pattern")
                reason = f"extension=txt + {' + '.join(reason_parts)} => novel_txt ({score:.2f})"
                
                return MediaTypeGuess(
                    media_type="novel_txt",
                    score=min(score, 0.9),  # 最高 0.9
                    reason=reason
                )
            
            # 不满足条件，返回 None（让其他检测器处理）
            return None
            
        except UnicodeDecodeError:
            # 编码错误，尝试 GBK
            try:
                with open(path, 'r', encoding='gbk', errors='ignore') as f:
                    sample = f.read(min(8192, file_size))
                
                # 同样的判断逻辑
                chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', sample))
                total_chars = len([c for c in sample if c.isprintable()])
                chinese_ratio = chinese_chars / total_chars if total_chars > 0 else 0
                
                has_chapter_marker = any(
                    re.search(pattern, sample, re.IGNORECASE)
                    for pattern in self.CHAPTER_PATTERNS
                )
                
                score = 0.5
                if chinese_ratio > 0.3:
                    score += 0.2
                if has_chapter_marker:
                    score += 0.2
                
                if score >= 0.7:
                    return MediaTypeGuess(
                        media_type="novel_txt",
                        score=min(score, 0.9),
                        reason=f"extension=txt + gbk_encoding + content_check => novel_txt ({score:.2f})"
                    )
            except Exception as e:
                logger.debug(f"读取文件失败（GBK 也失败）: {path}, 错误: {e}")
        
        except Exception as e:
            logger.warning(f"检测小说 TXT 文件失败: {path}, 错误: {e}")
        
        return None

