"""
有声书管理 API
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional
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
from app.models.audiobook import AudiobookFile
from app.models.ebook import EBook
from app.schemas.audiobook import (
    AudiobookFileResponse,
    AudiobookDetailResponse,
    AudiobookStatsResponse
)

router = APIRouter()


@router.get("/", response_model=BaseResponse)
async def list_audiobooks(
    keyword: Optional[str] = Query(None, description="搜索关键词（匹配标题/作者/朗读者）"),
    author: Optional[str] = Query(None, description="作者过滤"),
    narrator: Optional[str] = Query(None, description="朗读者过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取有声书列表
    
    支持分页、关键词搜索、作者和朗读者过滤。
    """
    try:
        # 构建查询
        stmt = select(AudiobookFile).where(AudiobookFile.is_deleted == False)
        
        # 关键词搜索（需要 join EBook）
        if keyword:
            stmt = stmt.join(EBook, AudiobookFile.ebook_id == EBook.id)
            stmt = stmt.where(
                or_(
                    EBook.title.ilike(f"%{keyword}%"),
                    EBook.author.ilike(f"%{keyword}%"),
                    AudiobookFile.narrator.ilike(f"%{keyword}%")
                )
            )
        
        # 作者过滤
        if author:
            if not keyword:  # 如果已有 join，不需要再次 join
                stmt = stmt.join(EBook, AudiobookFile.ebook_id == EBook.id)
            stmt = stmt.where(EBook.author == author)
        
        # 朗读者过滤
        if narrator:
            stmt = stmt.where(AudiobookFile.narrator == narrator)
        
        # 排序：按创建时间降序
        stmt = stmt.order_by(AudiobookFile.created_at.desc())
        
        # 总数查询（需要与主查询保持相同的条件）
        count_stmt = select(func.count(AudiobookFile.id)).where(AudiobookFile.is_deleted == False)
        has_join = False
        
        if keyword:
            count_stmt = count_stmt.join(EBook, AudiobookFile.ebook_id == EBook.id)
            has_join = True
            count_stmt = count_stmt.where(
                or_(
                    EBook.title.ilike(f"%{keyword}%"),
                    EBook.author.ilike(f"%{keyword}%"),
                    AudiobookFile.narrator.ilike(f"%{keyword}%")
                )
            )
        
        if author:
            if not has_join:
                count_stmt = count_stmt.join(EBook, AudiobookFile.ebook_id == EBook.id)
                has_join = True
            count_stmt = count_stmt.where(EBook.author == author)
        
        if narrator:
            count_stmt = count_stmt.where(AudiobookFile.narrator == narrator)
        
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        # 分页
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        
        # 执行查询
        result = await db.execute(stmt)
        audiobook_files = result.scalars().all()
        
        # 转换为响应格式
        items = [AudiobookFileResponse.model_validate(ab) for ab in audiobook_files]
        
        return success_response(
            data=PaginatedResponse(
                items=items,
                total=total,
                page=page,
                page_size=page_size
            ).model_dump(),
            message="获取有声书列表成功"
        )
        
    except Exception as e:
        logger.error(f"获取有声书列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取有声书列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/{audiobook_id}", response_model=BaseResponse)
async def get_audiobook(
    audiobook_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取有声书详情
    
    返回单个 AudiobookFile 及其关联的 EBook 作品信息。
    """
    try:
        stmt = select(AudiobookFile).where(
            AudiobookFile.id == audiobook_id,
            AudiobookFile.is_deleted == False
        )
        result = await db.execute(stmt)
        audiobook_file = result.scalar_one_or_none()
        
        if not audiobook_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message=f"有声书 ID {audiobook_id} 不存在"
                ).model_dump()
            )
        
        # 获取关联的作品信息
        ebook_stmt = select(EBook).where(EBook.id == audiobook_file.ebook_id)
        ebook_result = await db.execute(ebook_stmt)
        ebook = ebook_result.scalar_one_or_none()
        
        # 构建响应
        detail = AudiobookDetailResponse.model_validate(audiobook_file)
        if ebook:
            detail.work = {
                "id": ebook.id,
                "title": ebook.title,
                "original_title": ebook.original_title,
                "author": ebook.author,
                "series": ebook.series,
                "volume_index": ebook.volume_index,
                "publish_year": ebook.publish_year,
                "isbn": ebook.isbn,
                "description": ebook.description,
                "cover_url": ebook.cover_url,
            }
        
        return success_response(
            data=detail.model_dump(),
            message="获取有声书详情成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取有声书详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取有声书详情时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/stats/summary", response_model=BaseResponse)
async def get_audiobook_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    获取有声书统计信息
    
    返回总数、作品数、总大小、总时长等统计信息。
    """
    try:
        # 总数
        total_stmt = select(func.count(AudiobookFile.id)).where(AudiobookFile.is_deleted == False)
        total_result = await db.execute(total_stmt)
        audiobooks_total = total_result.scalar() or 0
        
        # 涉及的作品数（去重）
        works_stmt = select(func.count(func.distinct(AudiobookFile.ebook_id))).where(
            AudiobookFile.is_deleted == False
        )
        works_result = await db.execute(works_stmt)
        works_total = works_result.scalar() or 0
        
        # 总大小
        size_stmt = select(func.sum(AudiobookFile.file_size_mb)).where(
            AudiobookFile.is_deleted == False
        )
        size_result = await db.execute(size_stmt)
        total_size_mb = float(size_result.scalar() or 0)
        
        # 总时长
        duration_stmt = select(func.sum(AudiobookFile.duration_seconds)).where(
            AudiobookFile.is_deleted == False,
            AudiobookFile.duration_seconds.isnot(None)
        )
        duration_result = await db.execute(duration_stmt)
        total_duration_seconds = duration_result.scalar()
        
        stats = AudiobookStatsResponse(
            audiobooks_total=audiobooks_total,
            works_total=works_total,
            total_size_mb=round(total_size_mb, 2),
            total_duration_seconds=total_duration_seconds
        )
        
        return success_response(
            data=stats.model_dump(),
            message="获取有声书统计成功"
        )
        
    except Exception as e:
        logger.error(f"获取有声书统计失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取有声书统计时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/by-ebook/{ebook_id}", response_model=BaseResponse)
async def get_audiobooks_by_ebook(
    ebook_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    根据 EBook ID 获取该作品下的所有有声书文件
    
    用于作品详情页展示该作品的有声书版本。
    """
    try:
        # 验证 EBook 是否存在
        ebook_stmt = select(EBook).where(EBook.id == ebook_id)
        ebook_result = await db.execute(ebook_stmt)
        ebook = ebook_result.scalar_one_or_none()
        
        if not ebook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message=f"作品 ID {ebook_id} 不存在"
                ).model_dump()
            )
        
        # 查询该作品下的所有有声书文件（未删除的）
        stmt = select(AudiobookFile).where(
            AudiobookFile.ebook_id == ebook_id,
            AudiobookFile.is_deleted == False
        ).order_by(AudiobookFile.created_at.desc())
        
        result = await db.execute(stmt)
        audiobook_files = result.scalars().all()
        
        # 转换为响应格式
        items = [AudiobookFileResponse.model_validate(ab) for ab in audiobook_files]
        
        return success_response(
            data={
                "items": items,
                "total": len(items)
            },
            message="获取有声书列表成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"根据作品 ID 获取有声书列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取有声书列表时发生错误: {str(e)}"
            ).model_dump()
        )

