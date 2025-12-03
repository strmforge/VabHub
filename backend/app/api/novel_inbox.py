"""
小说 Inbox 管理 API

提供小说 Inbox 导入日志查看和手动扫描功能
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from loguru import logger

from app.core.database import get_db
from app.core.config import settings
from app.api.auth import oauth2_scheme
from app.core.security import decode_access_token
from app.core.dependencies import get_current_admin_user
from app.models.user import User
from app.models.ebook import EBook
from app.models.novel_inbox_import_log import NovelInboxImportLog, NovelInboxStatus
from app.schemas.novel_inbox import (
    NovelInboxLogListResponse,
    NovelInboxLogItem,
    NovelInboxScanResult,
)
from app.modules.novel.inbox_service import scan_novel_inbox_for_root
from pathlib import Path

router = APIRouter()





@router.get("/dev/novels/inbox/import-logs", response_model=NovelInboxLogListResponse, summary="获取小说 Inbox 导入日志列表")
async def list_novel_inbox_logs(
    status: Optional[str] = Query(None, description="状态筛选：pending/success/skipped/failed"),
    path_substring: Optional[str] = Query(None, description="路径关键字搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=200, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    获取小说 Inbox 导入日志列表
    
    支持分页、状态筛选、路径关键字搜索
    """
    try:
        # 构建查询
        stmt = select(NovelInboxImportLog)
        conditions = []
        
        # 状态筛选
        if status:
            try:
                status_enum = NovelInboxStatus(status)
                conditions.append(NovelInboxImportLog.status == status_enum)
            except ValueError:
                # 无效状态，返回空结果
                return NovelInboxLogListResponse(
                    items=[],
                    total=0,
                    page=page,
                    page_size=page_size,
                    total_pages=0
                )
        
        # 路径关键字搜索
        if path_substring:
            conditions.append(NovelInboxImportLog.original_path.ilike(f"%{path_substring}%"))
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # 获取总数
        count_stmt = select(func.count(NovelInboxImportLog.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()
        
        # 分页
        stmt = stmt.order_by(desc(NovelInboxImportLog.created_at))
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        
        # 执行查询
        result = await db.execute(stmt)
        logs = result.scalars().all()
        
        # 批量查询关联的 EBook 信息
        ebook_ids = [log.ebook_id for log in logs if log.ebook_id is not None]
        ebook_map = {}
        if ebook_ids:
            ebook_stmt = select(EBook).where(EBook.id.in_(ebook_ids))
            ebook_result = await db.execute(ebook_stmt)
            ebooks = ebook_result.scalars().all()
            ebook_map = {ebook.id: ebook for ebook in ebooks}
        
        # 组装响应
        items = []
        for log in logs:
            ebook_title = None
            ebook_author = None
            if log.ebook_id and log.ebook_id in ebook_map:
                ebook = ebook_map[log.ebook_id]
                ebook_title = ebook.title
                ebook_author = ebook.author
            
            items.append(NovelInboxLogItem(
                id=log.id,
                original_path=log.original_path,
                status=log.status.value,
                reason=log.reason,
                error_message=log.error_message,
                ebook_id=log.ebook_id,
                ebook_title=ebook_title,
                ebook_author=ebook_author,
                file_size=log.file_size,
                file_mtime=log.file_mtime,
                created_at=log.created_at,
                updated_at=log.updated_at
            ))
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return NovelInboxLogListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"获取小说 Inbox 导入日志失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )


@router.post("/dev/novels/inbox/scan", response_model=NovelInboxScanResult, summary="手动触发小说 Inbox 扫描")
async def dev_scan_novel_inbox(
    max_files: Optional[int] = Body(None, description="最多扫描文件数"),
    generate_tts: bool = Body(False, description="是否自动创建 TTS Job"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    手动触发小说 Inbox 扫描
    
    从配置的 INBOX_ROOT 目录扫描 TXT/EPUB 文件并导入
    """
    try:
        # 获取 Inbox 根目录（从 settings 获取，不写死）
        inbox_root = Path(settings.INBOX_ROOT)
        
        if not inbox_root.exists():
            logger.warning(f"Inbox 根目录不存在: {inbox_root}")
            return NovelInboxScanResult(
                scanned_files=0,
                imported_count=0,
                skipped_already_imported=0,
                skipped_failed_before=0,
                skipped_unsupported=0,
                tts_jobs_created=0,
                failed_count=0
            )
        
        # 调用扫描服务
        result = await scan_novel_inbox_for_root(
            db=db,
            settings=settings,
            root_dir=inbox_root,
            generate_tts=generate_tts,
            max_files=max_files
        )
        
        # 提交事务
        await db.commit()
        
        return result
        
    except Exception as e:
        await db.rollback()
        logger.error(f"扫描小说 Inbox 失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"扫描失败: {str(e)}"
        )

