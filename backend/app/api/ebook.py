"""
电子书管理 API
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from loguru import logger

from app.core.database import get_db
from app.core.schemas import (
    BaseResponse,
    PaginatedResponse,
    NotFoundResponse,
    success_response,
    error_response
)
from app.models.ebook import EBook, EBookFile

router = APIRouter()


class EBookFileResponse(BaseModel):
    """电子书文件响应"""
    id: int
    ebook_id: int
    file_path: str
    file_size_bytes: Optional[int] = None
    file_size_mb: Optional[float] = None
    format: str
    source_site_id: Optional[str] = None
    source_torrent_id: Optional[str] = None
    download_task_id: Optional[int] = None
    is_deleted: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class EBookResponse(BaseModel):
    """
    电子书响应
    
    注意：此响应返回的是"作品"（work），而不是单个文件。
    一个 EBook 可以包含多个 EBookFile（不同格式、不同来源）。
    """
    id: int
    title: str
    original_title: Optional[str] = None
    author: Optional[str] = None
    series: Optional[str] = None
    volume_index: Optional[str] = None
    language: Optional[str] = None
    publish_year: Optional[int] = None
    isbn: Optional[str] = None
    tags: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    files: List[EBookFileResponse] = []
    
    class Config:
        from_attributes = True


class EBookStatsResponse(BaseModel):
    """电子书统计响应"""
    total_books: int
    total_files: int
    total_authors: int
    total_series: int
    total_size_mb: float


@router.get("/", response_model=BaseResponse)
async def list_ebooks(
    keyword: Optional[str] = Query(None, description="搜索关键词（匹配标题/作者）"),
    author: Optional[str] = Query(None, description="作者过滤"),
    series: Optional[str] = Query(None, description="系列名过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取电子书列表（支持分页和筛选）
    """
    try:
        # 构建查询
        stmt = select(EBook)
        conditions = []
        
        if keyword:
            keyword_pattern = f"%{keyword}%"
            conditions.append(
                or_(
                    EBook.title.ilike(keyword_pattern),
                    EBook.author.ilike(keyword_pattern),
                    EBook.original_title.ilike(keyword_pattern)
                )
            )
        
        if author:
            conditions.append(EBook.author.ilike(f"%{author}%"))
        
        if series:
            conditions.append(EBook.series.ilike(f"%{series}%"))
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # 获取总数
        count_stmt = select(func.count(EBook.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()
        
        # 分页
        stmt = stmt.order_by(EBook.updated_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        
        # 执行查询
        result = await db.execute(stmt)
        ebooks = result.scalars().all()
        
        # 加载关联的文件
        ebook_list = []
        for ebook in ebooks:
            # 查询该电子书的所有文件（未删除的）
            files_stmt = select(EBookFile).where(
                EBookFile.ebook_id == ebook.id,
                EBookFile.is_deleted == False
            ).order_by(EBookFile.created_at.desc())
            files_result = await db.execute(files_stmt)
            files = files_result.scalars().all()
            
            ebook_dict = {
                "id": ebook.id,
                "title": ebook.title,
                "original_title": ebook.original_title,
                "author": ebook.author,
                "series": ebook.series,
                "volume_index": ebook.volume_index,
                "language": ebook.language,
                "publish_year": ebook.publish_year,
                "isbn": ebook.isbn,
                "tags": ebook.tags,
                "description": ebook.description,
                "cover_url": ebook.cover_url,
                "created_at": ebook.created_at,
                "updated_at": ebook.updated_at,
                "files": [EBookFileResponse.model_validate(f) for f in files],
            }
            ebook_list.append(ebook_dict)
        
        total_pages = (total + page_size - 1) // page_size
        
        return success_response(
            data={
                "items": ebook_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            },
            message="获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取电子书列表失败: {e}", exc_info=True)
        return error_response(message=f"获取失败: {str(e)}")


@router.get("/{ebook_id}", response_model=BaseResponse)
async def get_ebook(
    ebook_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取电子书详情
    """
    try:
        stmt = select(EBook).where(EBook.id == ebook_id)
        result = await db.execute(stmt)
        ebook = result.scalar_one_or_none()
        
        if not ebook:
            return NotFoundResponse(message="电子书不存在")
        
        # 查询所有文件（包括已删除的）
        files_stmt = select(EBookFile).where(
            EBookFile.ebook_id == ebook.id
        ).order_by(EBookFile.created_at.desc())
        files_result = await db.execute(files_stmt)
        files = files_result.scalars().all()
        
        ebook_dict = {
            "id": ebook.id,
            "title": ebook.title,
            "original_title": ebook.original_title,
            "author": ebook.author,
            "series": ebook.series,
            "volume_index": ebook.volume_index,
            "language": ebook.language,
            "publish_year": ebook.publish_year,
            "isbn": ebook.isbn,
            "tags": ebook.tags,
            "description": ebook.description,
            "cover_url": ebook.cover_url,
            "created_at": ebook.created_at,
            "updated_at": ebook.updated_at,
            "files": [EBookFileResponse.model_validate(f) for f in files],
        }
        
        return success_response(data=ebook_dict, message="获取成功")
        
    except Exception as e:
        logger.error(f"获取电子书详情失败: {e}", exc_info=True)
        return error_response(message=f"获取失败: {str(e)}")


@router.get("/stats/summary", response_model=BaseResponse)
async def get_ebook_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    获取电子书统计信息
    """
    try:
        # 统计电子书数量
        books_stmt = select(func.count(EBook.id))
        books_result = await db.execute(books_stmt)
        total_books = books_result.scalar() or 0
        
        # 统计文件数量（未删除的）
        files_stmt = select(func.count(EBookFile.id)).where(EBookFile.is_deleted == False)
        files_result = await db.execute(files_stmt)
        total_files = files_result.scalar() or 0
        
        # 统计作者数量
        authors_stmt = select(func.count(func.distinct(EBook.author))).where(EBook.author.isnot(None))
        authors_result = await db.execute(authors_stmt)
        total_authors = authors_result.scalar() or 0
        
        # 统计系列数量
        series_stmt = select(func.count(func.distinct(EBook.series))).where(EBook.series.isnot(None))
        series_result = await db.execute(series_stmt)
        total_series = series_result.scalar() or 0
        
        # 统计总大小（MB）
        size_stmt = select(func.sum(EBookFile.file_size_mb)).where(EBookFile.is_deleted == False)
        size_result = await db.execute(size_stmt)
        total_size_mb = size_result.scalar() or 0.0
        
        stats = {
            "total_books": total_books,
            "total_files": total_files,
            "total_authors": total_authors,
            "total_series": total_series,
            "total_size_mb": round(total_size_mb, 2),
        }
        
        return success_response(data=stats, message="获取成功")
        
    except Exception as e:
        logger.error(f"获取电子书统计失败: {e}", exc_info=True)
        return error_response(message=f"获取失败: {str(e)}")

