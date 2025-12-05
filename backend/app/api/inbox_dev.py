"""
统一待整理收件箱 Dev API

提供预览和调试统一收件箱分类结果的接口。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from pydantic import BaseModel
from loguru import logger
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.schemas import success_response, error_response
from app.modules.inbox.service import run_inbox_classification
from app.modules.inbox.router import InboxRouter
from app.models.inbox import InboxRunLog

router = APIRouter()


class InboxPreviewItem(BaseModel):
    """收件箱预览项"""
    path: str
    media_type: str
    score: float
    reason: str
    size_bytes: int
    modified_at: str


class InboxPreviewResponse(BaseModel):
    """收件箱预览响应"""
    items: List[InboxPreviewItem]


class InboxRunOnceItem(BaseModel):
    """收件箱处理项"""
    path: str
    media_type: str
    score: float
    reason: str
    size_bytes: int
    modified_at: str
    result: str


class InboxRunOnceResponse(BaseModel):
    """收件箱处理响应"""
    items: List[InboxRunOnceItem]


@router.get("/preview", summary="Dev: 预览统一收件箱分类结果")
async def preview_inbox(
    db: AsyncSession = Depends(get_db)
):
    """
    预览统一收件箱中的文件及其分类结果
    
    此接口只进行扫描和检测，不执行实际的导入操作。
    用于调试和查看系统如何识别文件类型。
    
    Returns:
        InboxPreviewResponse: 包含每个文件的路径、检测到的媒体类型、置信度等信息
    """
    try:
        # 执行分类（不路由）
        results = await run_inbox_classification(db, router=None)
        
        # 转换为响应格式
        items = [
            InboxPreviewItem(
                path=item["path"],
                media_type=item["media_type"],
                score=item["score"],
                reason=item["reason"],
                size_bytes=item["size_bytes"],
                modified_at=item["modified_at"]
            )
            for item in results
        ]
        
        return success_response(
            data={"items": items},
            message=f"扫描完成，发现 {len(items)} 个项目"
        )
        
    except Exception as e:
        logger.error(f"预览收件箱失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"预览失败: {str(e)}"
            ).model_dump()
        )


@router.post("/run-once", summary="Dev: 执行一次统一收件箱处理")
async def run_inbox_once(
    db: AsyncSession = Depends(get_db)
):
    """
    执行一次统一收件箱处理
    
    扫描收件箱、检测媒体类型，并真正调用对应的 Importer 进行导入。
    此接口明确作为 Dev/运维用，不提供给普通用户。
    
    每次执行都会记录运行日志（InboxRunLog），供健康检查使用。
    
    Returns:
        InboxRunOnceResponse: 包含每个文件的处理结果
    """
    started_at = datetime.utcnow()
    run_log: InboxRunLog = None
    
    try:
        # 执行分类和路由
        router = InboxRouter(db=db)
        results = await run_inbox_classification(db, router=router)
        
        # 转换为响应格式
        items = [
            InboxRunOnceItem(
                path=item["path"],
                media_type=item["media_type"],
                score=item["score"],
                reason=item["reason"],
                size_bytes=item["size_bytes"],
                modified_at=item["modified_at"],
                result=item.get("result", "unknown")
            )
            for item in results
        ]
        
        # 统计处理结果
        total_items = len(items)
        handled_count = sum(1 for item in items if item.result.startswith("handled:"))
        skipped_count = sum(1 for item in items if item.result.startswith("skipped:"))
        failed_count = sum(1 for item in items if item.result.startswith("failed:"))
        
        # 计算 status
        if total_items == 0:
            status_str = "empty"
        elif failed_count == 0:
            status_str = "success"
        elif failed_count > 0 and handled_count > 0:
            status_str = "partial"
        else:
            status_str = "failed"
        
        finished_at = datetime.utcnow()
        message = f"处理完成：成功 {handled_count}，跳过 {skipped_count}，失败 {failed_count}"
        
        # 按 media_type 统计（可选，存入 details）
        by_media_type: Dict[str, Dict[str, int]] = {}
        for item in items:
            media_type = item.media_type
            if media_type not in by_media_type:
                by_media_type[media_type] = {"handled": 0, "skipped": 0, "failed": 0}
            
            if item.result.startswith("handled:"):
                by_media_type[media_type]["handled"] += 1
            elif item.result.startswith("skipped:"):
                by_media_type[media_type]["skipped"] += 1
            elif item.result.startswith("failed:"):
                by_media_type[media_type]["failed"] += 1
        
        details = {
            "by_media_type": by_media_type
        } if by_media_type else None
        
        # 创建运行日志记录
        run_log = InboxRunLog(
            started_at=started_at,
            finished_at=finished_at,
            status=status_str,
            total_items=total_items,
            handled_items=handled_count,
            skipped_items=skipped_count,
            failed_items=failed_count,
            message=message,
            details=details
        )
        
        # 写入数据库（如果失败，记录警告但不影响 API 响应）
        try:
            db.add(run_log)
            await db.commit()
            logger.info(f"收件箱运行日志已记录: status={status_str}, total={total_items}, handled={handled_count}, skipped={skipped_count}, failed={failed_count}")
        except Exception as log_error:
            logger.warning(f"写入收件箱运行日志失败: {log_error}", exc_info=True)
            await db.rollback()
            # 继续执行，不影响 API 响应
        
        return success_response(
            data={"items": items},
            message=message
        )
        
    except Exception as e:
        finished_at = datetime.utcnow()
        logger.error(f"执行收件箱处理失败: {e}", exc_info=True)
        
        # 即使处理失败，也尝试记录日志
        try:
            if run_log is None:
                run_log = InboxRunLog(
                    started_at=started_at,
                    finished_at=finished_at,
                    status="failed",
                    total_items=0,
                    handled_items=0,
                    skipped_items=0,
                    failed_items=0,
                    message=f"处理失败: {str(e)}",
                    details=None
                )
            else:
                # 如果 run_log 已创建但未提交，更新状态
                run_log.status = "failed"
                run_log.finished_at = finished_at
                run_log.message = f"处理失败: {str(e)}"
            
            db.add(run_log)
            await db.commit()
        except Exception as log_error:
            logger.warning(f"写入收件箱运行日志失败: {log_error}", exc_info=True)
            await db.rollback()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"处理失败: {str(e)}"
            ).model_dump()
        )

