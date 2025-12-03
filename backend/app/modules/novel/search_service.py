"""
小说书内搜索服务

提供在当前 EBook 范围内按关键字搜索的功能
"""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.ebook import EBook
from app.schemas.novel_reader import NovelSearchHit
from app.modules.novel.reader_service import get_chapters_from_ebook, get_chapter_content


async def search_novel(
    *,
    db: AsyncSession,
    ebook_id: int,
    query: str,
    max_hits: int = 50,
    max_hits_per_chapter: int = 5,
) -> List[NovelSearchHit]:
    """
    在指定 EBook 中搜索关键字
    
    Args:
        db: 数据库会话
        ebook_id: 作品 ID
        query: 搜索关键字
        max_hits: 最多返回的命中数（全书合计）
        max_hits_per_chapter: 每章最多返回的命中数
    
    Returns:
        搜索结果列表（按章节顺序）
    """
    try:
        # 查询 EBook
        from sqlalchemy import select
        stmt = select(EBook).where(EBook.id == ebook_id)
        result = await db.execute(stmt)
        ebook = result.scalar_one_or_none()
        
        if not ebook:
            logger.warning(f"EBook {ebook_id} not found")
            return []
        
        # 获取章节列表
        chapters = await get_chapters_from_ebook(ebook)
        if not chapters:
            logger.warning(f"EBook {ebook_id} has no chapters")
            return []
        
        hits: List[NovelSearchHit] = []
        query_lower = query.lower()  # 转换为小写用于匹配（简单处理）
        
        # 遍历每个章节
        for chapter_idx, chapter in enumerate(chapters):
            if len(hits) >= max_hits:
                # 已达到最大命中数，提前终止
                break
            
            # 获取章节内容
            chapter_content = chapter.content or ""
            if not chapter_content:
                continue
            
            # 在章节内容中搜索（简单字面匹配）
            content_lower = chapter_content.lower()
            chapter_hits = []
            search_start = 0
            
            # 查找所有匹配位置
            while len(chapter_hits) < max_hits_per_chapter and len(hits) < max_hits:
                pos = content_lower.find(query_lower, search_start)
                if pos == -1:
                    # 没有更多匹配
                    break
                
                # 构造 snippet（前后各约 40 字）
                snippet_start = max(0, pos - 40)
                snippet_end = min(len(chapter_content), pos + len(query) + 40)
                snippet_text = chapter_content[snippet_start:snippet_end]
                
                # 添加前后省略号（如果截取了内容）
                if snippet_start > 0:
                    snippet_text = "..." + snippet_text
                if snippet_end < len(chapter_content):
                    snippet_text = snippet_text + "..."
                
                chapter_hits.append(NovelSearchHit(
                    chapter_index=chapter_idx,
                    chapter_title=chapter.title,
                    snippet=snippet_text
                ))
                
                # 继续搜索下一个位置（跳过当前匹配，避免重复）
                search_start = pos + len(query)
            
            # 添加到总结果
            hits.extend(chapter_hits)
        
        logger.info(f"搜索完成 (ebook_id={ebook_id}, query='{query}'): 找到 {len(hits)} 个命中")
        return hits
        
    except Exception as e:
        logger.error(f"搜索小说失败 (ebook_id={ebook_id}, query='{query}'): {e}", exc_info=True)
        return []

