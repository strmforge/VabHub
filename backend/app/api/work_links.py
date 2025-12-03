"""
作品关联（Work Link）管理 API

提供手动标记作品关联关系的 CRUD 接口。
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from loguru import logger

from app.core.database import get_db
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)
from app.models.work_link import WorkLink
from app.models.ebook import EBook
from app.schemas.work_link import (
    WorkLinkCreate,
    WorkLinkUpdate,
    WorkLinkResponse
)

router = APIRouter(prefix="/api/admin/work-links", tags=["work-links"])


@router.get("/by-ebook/{ebook_id}", response_model=BaseResponse, summary="获取指定 ebook 的所有关联")
async def get_links_by_ebook(
    ebook_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定 ebook 的所有 WorkLink 记录（包含 include 和 exclude）
    
    Args:
        ebook_id: 电子书作品 ID
        db: 数据库会话
    
    Returns:
        List[WorkLinkResponse]: WorkLink 列表
    """
    try:
        # 验证 ebook 是否存在
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
        
        # 查询所有 WorkLink
        links_stmt = select(WorkLink).where(WorkLink.ebook_id == ebook_id).order_by(WorkLink.created_at.desc())
        links_result = await db.execute(links_stmt)
        links = links_result.scalars().all()
        
        return success_response(
            data=[WorkLinkResponse.model_validate(link) for link in links],
            message="获取作品关联成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取作品关联失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取作品关联时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("", response_model=BaseResponse, summary="创建或更新作品关联")
async def create_or_update_link(
    payload: WorkLinkCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建或更新作品关联
    
    如果已有同 ebook_id/target_type/target_id 记录，则更新 relation；
    否则创建新记录。
    
    Args:
        payload: WorkLinkCreate
        db: 数据库会话
    
    Returns:
        WorkLinkResponse: 创建或更新后的 WorkLink
    """
    try:
        # 验证 ebook 是否存在
        ebook_stmt = select(EBook).where(EBook.id == payload.ebook_id)
        ebook_result = await db.execute(ebook_stmt)
        ebook = ebook_result.scalar_one_or_none()
        
        if not ebook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message=f"作品 ID {payload.ebook_id} 不存在"
                ).model_dump()
            )
        
        # 查找是否已存在
        existing_stmt = select(WorkLink).where(
            and_(
                WorkLink.ebook_id == payload.ebook_id,
                WorkLink.target_type == payload.target_type,
                WorkLink.target_id == payload.target_id
            )
        )
        existing_result = await db.execute(existing_stmt)
        existing_link = existing_result.scalar_one_or_none()
        
        if existing_link:
            # 更新现有记录
            existing_link.relation = payload.relation
            await db.commit()
            await db.refresh(existing_link)
            
            return success_response(
                data=WorkLinkResponse.model_validate(existing_link),
                message="更新作品关联成功"
            )
        else:
            # 创建新记录
            new_link = WorkLink(
                ebook_id=payload.ebook_id,
                target_type=payload.target_type,
                target_id=payload.target_id,
                relation=payload.relation
            )
            db.add(new_link)
            await db.commit()
            await db.refresh(new_link)
            
            return success_response(
                data=WorkLinkResponse.model_validate(new_link),
                message="创建作品关联成功"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"创建或更新作品关联失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"创建或更新作品关联时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/{link_id}", response_model=BaseResponse, summary="删除作品关联")
async def delete_link(
    link_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    删除指定的 WorkLink 记录
    
    Args:
        link_id: WorkLink ID
        db: 数据库会话
    
    Returns:
        成功消息
    """
    try:
        # 查找记录
        link_stmt = select(WorkLink).where(WorkLink.id == link_id)
        link_result = await db.execute(link_stmt)
        link = link_result.scalar_one_or_none()
        
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message=f"关联 ID {link_id} 不存在"
                ).model_dump()
            )
        
        await db.delete(link)
        await db.commit()
        
        return success_response(
            data=None,
            message="删除作品关联成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"删除作品关联失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除作品关联时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/by-target", response_model=BaseResponse, summary="通过组合键删除作品关联")
async def delete_link_by_target(
    ebook_id: int = Query(..., description="电子书作品 ID"),
    target_type: str = Query(..., description="目标类型: video/comic/music"),
    target_id: int = Query(..., description="目标 ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    通过组合键删除 WorkLink 记录
    
    Args:
        ebook_id: 电子书作品 ID
        target_type: 目标类型
        target_id: 目标 ID
        db: 数据库会话
    
    Returns:
        成功消息
    """
    try:
        # 验证 target_type
        if target_type not in ["video", "comic", "music"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="INVALID_PARAMETER",
                    error_message=f"无效的 target_type: {target_type}，必须是 video/comic/music 之一"
                ).model_dump()
            )
        
        # 查找记录
        link_stmt = select(WorkLink).where(
            and_(
                WorkLink.ebook_id == ebook_id,
                WorkLink.target_type == target_type,
                WorkLink.target_id == target_id
            )
        )
        link_result = await db.execute(link_stmt)
        link = link_result.scalar_one_or_none()
        
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message=f"未找到对应的关联记录"
                ).model_dump()
            )
        
        await db.delete(link)
        await db.commit()
        
        return success_response(
            data=None,
            message="删除作品关联成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"删除作品关联失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除作品关联时发生错误: {str(e)}"
            ).model_dump()
        )

