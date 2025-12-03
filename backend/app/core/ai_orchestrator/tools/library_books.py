"""
书库统计工具

FUTURE-AI-READING-ASSISTANT-1 P1 实现
获取书库内容统计，用于阅读规划
"""

from typing import Optional
from pydantic import BaseModel, Field
from loguru import logger

from .base import AITool, OrchestratorContext, EmptyInput


class BookTypeStats(BaseModel):
    """书籍类型统计"""
    book_type: str  # novel / manga / audiobook
    total_count: int = 0
    read_count: int = 0     # 已阅读/完成
    reading_count: int = 0  # 阅读中
    unread_count: int = 0   # 未阅读


class SeriesInfo(BaseModel):
    """系列信息"""
    series_name: str
    book_count: int
    read_count: int
    completion_percent: float


class UnreadBook(BaseModel):
    """未阅读书籍"""
    item_id: int
    title: str
    author: Optional[str] = None
    book_type: str
    series: Optional[str] = None
    added_at: Optional[str] = None


class LibraryBooksOutput(BaseModel):
    """书库统计输出"""
    type_stats: list[BookTypeStats] = Field(default_factory=list)
    series_progress: list[SeriesInfo] = Field(default_factory=list)
    unread_books: list[UnreadBook] = Field(default_factory=list)
    total_books: int = 0
    total_unread: int = 0
    summary_text: str = ""


class GetLibraryBooksTool(AITool):
    """
    书库统计工具
    
    获取书库内容统计和未阅读书籍
    """
    
    name = "get_library_books"
    description = (
        "获取用户书库的统计信息。"
        "包括各类书籍数量、系列阅读进度、未阅读书籍列表。"
        "用于分析待读书单和制定阅读计划。"
    )
    input_model = EmptyInput
    output_model = LibraryBooksOutput
    
    async def run(
        self,
        params: EmptyInput,
        context: OrchestratorContext,
    ) -> LibraryBooksOutput:
        """获取书库统计"""
        try:
            type_stats = await self._get_type_stats(context)
            series_progress = await self._get_series_progress(context)
            unread_books = await self._get_unread_books(context)
            
            # 汇总
            total_books = sum(s.total_count for s in type_stats)
            total_unread = sum(s.unread_count for s in type_stats)
            
            # 生成摘要
            if total_books == 0:
                summary_text = "书库为空，可以添加一些书籍开始阅读。"
            else:
                parts = [f"书库共 {total_books} 本"]
                
                if total_unread > 0:
                    parts.append(f"待阅读 {total_unread} 本")
                
                # 统计各类型
                for stat in type_stats:
                    if stat.total_count > 0:
                        type_name = {
                            "novel": "小说",
                            "manga": "漫画",
                            "audiobook": "有声书",
                        }.get(stat.book_type, stat.book_type)
                        parts.append(f"{type_name} {stat.total_count} 本")
                
                summary_text = "；".join(parts) + "。"
            
            return LibraryBooksOutput(
                type_stats=type_stats,
                series_progress=series_progress[:10],  # 限制返回数量
                unread_books=unread_books[:20],
                total_books=total_books,
                total_unread=total_unread,
                summary_text=summary_text,
            )
            
        except Exception as e:
            logger.error(f"[library_books] 获取书库统计失败: {e}")
            return LibraryBooksOutput(
                summary_text=f"获取书库统计时发生错误: {str(e)[:100]}"
            )
    
    async def _get_type_stats(self, context: OrchestratorContext) -> list[BookTypeStats]:
        """获取类型统计"""
        stats: list[BookTypeStats] = []
        
        try:
            from sqlalchemy import select, func
            from app.models.ebook import EBook
            from app.models.user_novel_reading_progress import UserNovelReadingProgress
            from app.models.user_audiobook_progress import UserAudiobookProgress
            from app.models.manga_series_local import MangaSeriesLocal
            from app.models.manga_reading_progress import MangaReadingProgress
            
            # 小说统计
            total_novels = await context.db.execute(select(func.count()).select_from(EBook))
            total_novel_count = total_novels.scalar() or 0
            
            # 已读/阅读中小说
            read_novels = await context.db.execute(
                select(func.count()).select_from(UserNovelReadingProgress)
                .where(UserNovelReadingProgress.user_id == context.user_id)
                .where(UserNovelReadingProgress.is_finished == True)
            )
            read_novel_count = read_novels.scalar() or 0
            
            reading_novels = await context.db.execute(
                select(func.count()).select_from(UserNovelReadingProgress)
                .where(UserNovelReadingProgress.user_id == context.user_id)
                .where(UserNovelReadingProgress.is_finished == False)
            )
            reading_novel_count = reading_novels.scalar() or 0
            
            stats.append(BookTypeStats(
                book_type="novel",
                total_count=total_novel_count,
                read_count=read_novel_count,
                reading_count=reading_novel_count,
                unread_count=max(0, total_novel_count - read_novel_count - reading_novel_count),
            ))
            
            # 漫画统计
            total_manga = await context.db.execute(select(func.count()).select_from(MangaSeriesLocal))
            total_manga_count = total_manga.scalar() or 0
            
            read_manga = await context.db.execute(
                select(func.count()).select_from(MangaReadingProgress)
                .where(MangaReadingProgress.user_id == context.user_id)
                .where(MangaReadingProgress.is_finished == True)
            )
            read_manga_count = read_manga.scalar() or 0
            
            reading_manga = await context.db.execute(
                select(func.count()).select_from(MangaReadingProgress)
                .where(MangaReadingProgress.user_id == context.user_id)
                .where(MangaReadingProgress.is_finished == False)
            )
            reading_manga_count = reading_manga.scalar() or 0
            
            stats.append(BookTypeStats(
                book_type="manga",
                total_count=total_manga_count,
                read_count=read_manga_count,
                reading_count=reading_manga_count,
                unread_count=max(0, total_manga_count - read_manga_count - reading_manga_count),
            ))
            
        except Exception as e:
            logger.warning(f"[library_books] 获取类型统计失败: {e}")
        
        return stats
    
    async def _get_series_progress(self, context: OrchestratorContext) -> list[SeriesInfo]:
        """获取系列进度"""
        series_list: list[SeriesInfo] = []
        
        try:
            from sqlalchemy import select, func
            from app.models.ebook import EBook
            from app.models.user_novel_reading_progress import UserNovelReadingProgress
            
            # 按系列分组统计
            series_query = (
                select(
                    EBook.series,
                    func.count(EBook.id).label("total"),
                )
                .where(EBook.series.isnot(None))
                .group_by(EBook.series)
                .having(func.count(EBook.id) > 1)  # 至少 2 本才算系列
                .order_by(func.count(EBook.id).desc())
                .limit(15)
            )
            
            result = await context.db.execute(series_query)
            for row in result.fetchall():
                series_name = row[0]
                total_count = row[1]
                
                # 查询该系列已读数量
                read_query = (
                    select(func.count())
                    .select_from(UserNovelReadingProgress)
                    .join(EBook, UserNovelReadingProgress.ebook_id == EBook.id)
                    .where(EBook.series == series_name)
                    .where(UserNovelReadingProgress.user_id == context.user_id)
                    .where(UserNovelReadingProgress.is_finished == True)
                )
                read_result = await context.db.execute(read_query)
                read_count = read_result.scalar() or 0
                
                completion_percent = round(read_count / total_count * 100, 1) if total_count > 0 else 0
                
                series_list.append(SeriesInfo(
                    series_name=series_name,
                    book_count=total_count,
                    read_count=read_count,
                    completion_percent=completion_percent,
                ))
            
        except Exception as e:
            logger.warning(f"[library_books] 获取系列进度失败: {e}")
        
        return sorted(series_list, key=lambda x: -x.book_count)
    
    async def _get_unread_books(self, context: OrchestratorContext) -> list[UnreadBook]:
        """获取未阅读书籍"""
        unread: list[UnreadBook] = []
        
        try:
            from sqlalchemy import select
            from app.models.ebook import EBook
            from app.models.user_novel_reading_progress import UserNovelReadingProgress
            
            # 找出没有阅读进度的书籍
            subquery = (
                select(UserNovelReadingProgress.ebook_id)
                .where(UserNovelReadingProgress.user_id == context.user_id)
            )
            
            unread_query = (
                select(EBook)
                .where(EBook.id.notin_(subquery))
                .order_by(EBook.created_at.desc())
                .limit(30)
            )
            
            result = await context.db.execute(unread_query)
            for ebook in result.scalars().all():
                unread.append(UnreadBook(
                    item_id=ebook.id,
                    title=ebook.title,
                    author=ebook.author,
                    book_type="novel",
                    series=ebook.series,
                    added_at=ebook.created_at.isoformat() if ebook.created_at else None,
                ))
            
        except Exception as e:
            logger.warning(f"[library_books] 获取未阅读书籍失败: {e}")
        
        return unread
