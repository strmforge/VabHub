"""
电子书构建器

将 StandardChapter 列表构建为 EPUB 文件的构建器。
"""

from pathlib import Path
from typing import Iterable
from loguru import logger

from .models import NovelMetadata, StandardChapter


class EpubBuilder:
    """
    将 StandardChapter 列表构建为 EPUB 文件的构建器。
    
    目前可以只提供接口，具体实现留到未来任务。
    """
    
    def build_epub(
        self,
        output_dir: Path,
        metadata: NovelMetadata,
        chapters: Iterable[StandardChapter]
    ) -> Path:
        """
        根据元数据和章节列表，在 output_dir 中生成 EPUB 文件，并返回路径。
        
        Args:
            output_dir: 输出目录
            metadata: 小说元数据
            chapters: 章节列表（可迭代对象）
        
        Returns:
            Path: 生成的 EPUB 文件路径
        
        Raises:
            NotImplementedError: 当前版本尚未实现真正的 EPUB 构建逻辑
        """
        # TODO: 实现真正的 EPUB 构建逻辑
        # 可以使用 ebooklib、pypandoc 等库来生成 EPUB
        
        logger.warning("EpubBuilder.build_epub 尚未实现，返回占位文件路径")
        
        # 当前实现：生成一个简单的 TXT 占位文件
        # 未来可以替换为真正的 EPUB 生成逻辑
        output_file = output_dir / f"{metadata.title}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入元数据
            f.write(f"标题: {metadata.title}\n")
            if metadata.author:
                f.write(f"作者: {metadata.author}\n")
            if metadata.description:
                f.write(f"简介: {metadata.description}\n")
            f.write("\n" + "=" * 50 + "\n\n")
            
            # 写入章节内容
            for chapter in chapters:
                f.write(f"\n第 {chapter.index} 章: {chapter.title}\n")
                f.write("-" * 50 + "\n")
                f.write(chapter.content)
                f.write("\n\n")
        
        logger.info(f"已生成占位文件: {output_file}")
        return output_file

