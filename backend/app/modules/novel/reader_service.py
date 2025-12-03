"""
小说阅读器服务

提供章节列表和章节内容读取功能
"""
from pathlib import Path
from typing import List, Optional
from loguru import logger

from app.models.ebook import EBook
from app.modules.novel.models import StandardChapter
from app.modules.novel.sources.local_txt import LocalTxtNovelSourceAdapter


async def get_chapters_from_ebook(ebook: EBook) -> List[StandardChapter]:
    """
    从 EBook 获取章节列表
    
    优先从源 TXT 文件读取章节信息
    """
    try:
        # 从 extra_metadata 获取源文件路径
        if not ebook.extra_metadata:
            logger.warning(f"EBook {ebook.id} 没有 extra_metadata")
            return []
        
        novel_source = ebook.extra_metadata.get("novel_source")
        if not novel_source:
            logger.warning(f"EBook {ebook.id} 没有 novel_source 信息")
            return []
        
        source_type = novel_source.get("type")
        if source_type != "local_txt":
            logger.warning(f"EBook {ebook.id} 的源类型不是 local_txt: {source_type}")
            return []
        
        # 获取归档的 TXT 文件路径
        archived_path = novel_source.get("archived_txt_path")
        if not archived_path:
            logger.warning(f"EBook {ebook.id} 没有 archived_txt_path")
            return []
        
        txt_path = Path(archived_path)
        if not txt_path.exists():
            logger.warning(f"源文件不存在: {txt_path}")
            return []
        
        # 使用 LocalTxtNovelSourceAdapter 解析章节
        # 构造简单的 metadata（适配器需要）
        from app.modules.novel.models import NovelMetadata
        metadata = NovelMetadata(
            title=ebook.title or "未知",
            author=ebook.author
        )
        adapter = LocalTxtNovelSourceAdapter(txt_path, metadata)
        chapters = list(adapter.iter_chapters())
        
        logger.debug(f"从 {txt_path} 读取到 {len(chapters)} 个章节")
        return chapters
        
    except Exception as e:
        logger.error(f"获取章节列表失败 (ebook_id={ebook.id}): {e}", exc_info=True)
        return []


async def get_chapter_content(ebook: EBook, chapter_index: int) -> Optional[StandardChapter]:
    """
    获取指定章节的内容
    
    Args:
        ebook: EBook 对象
        chapter_index: 章节索引（从 0 开始）
    
    Returns:
        StandardChapter 对象，如果不存在则返回 None
    """
    try:
        chapters = await get_chapters_from_ebook(ebook)
        
        if chapter_index < 0 or chapter_index >= len(chapters):
            logger.warning(f"章节索引超出范围: {chapter_index}, 总章节数: {len(chapters)}")
            return None
        
        return chapters[chapter_index]
        
    except Exception as e:
        logger.error(f"获取章节内容失败 (ebook_id={ebook.id}, chapter_index={chapter_index}): {e}", exc_info=True)
        return None

