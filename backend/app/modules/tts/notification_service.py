"""
TTS 通知服务

负责在 TTS Job 完成时创建用户通知
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.user_notification import UserNotification
from app.models.tts_job import TTSJob
from app.models.ebook import EBook
from app.models.enums.notification_type import NotificationType
from app.models.enums.reading_media_type import ReadingMediaType


async def create_tts_job_notification(
    db: AsyncSession,
    *,
    job: TTSJob,
    ebook: Optional[EBook],
    status: str,
    summary: Optional[dict] = None,
) -> UserNotification:
    """
    为 TTS Job 创建用户通知
    
    Args:
        db: 数据库会话
        job: TTS Job 对象
        ebook: EBook 对象（可选）
        status: Job 状态（"success" | "partial" | "failed"）
        summary: 可选的摘要信息（包含 generated_chapters, total_chapters 等）
    
    Returns:
        UserNotification: 创建的通知对象
    """
    # 根据状态确定通知类型和严重程度
    if status == "success":
        notification_type = NotificationType.TTS_JOB_COMPLETED
        severity = "success"
    elif status == "partial":
        notification_type = NotificationType.TTS_JOB_COMPLETED  # 部分完成也使用完成类型
        severity = "warning"
    elif status == "failed":
        notification_type = NotificationType.TTS_JOB_FAILED
        severity = "error"
    else:
        # 未知状态，使用 info
        notification_type = NotificationType.TTS_JOB_COMPLETED
        severity = "info"
    
    # 构建标题
    ebook_title = ebook.title if ebook else "某作品"
    if status == "success":
        title = f"《{ebook_title}》TTS 有声书生成成功"
    elif status == "partial":
        title = f"《{ebook_title}》TTS 有声书部分生成完成"
    elif status == "failed":
        title = f"《{ebook_title}》TTS 有声书生成失败"
    else:
        title = f"《{ebook_title}》TTS 任务状态更新"
    
    # 构建消息
    message_parts = []
    
    if status == "success":
        if summary and summary.get("generated_chapters"):
            generated = summary["generated_chapters"]
            total = summary.get("total_chapters", generated)
            message_parts.append(f"本次共生成 {generated} 章有声书")
            if total and total > generated:
                message_parts.append(f"（共 {total} 章）")
        else:
            message_parts.append("TTS 有声书生成完成")
        message_parts.append("可在作品详情页收听")
    
    elif status == "partial":
        if summary:
            generated = summary.get("generated_chapters", 0)
            total = summary.get("total_chapters", 0)
            if total > 0:
                message_parts.append(f"已生成 {generated}/{total} 章")
            else:
                message_parts.append(f"已生成 {generated} 章")
        else:
            message_parts.append("已生成部分章节")
        message_parts.append("后续可继续执行任务完成剩余章节")
    
    elif status == "failed":
        if job.last_error:
            message_parts.append(f"TTS 任务执行失败：{job.last_error}")
        else:
            message_parts.append("TTS 任务执行失败")
        message_parts.append("请稍后重试或联系管理员")
    
    else:
        message_parts.append("TTS 任务状态已更新")
    
    message = "，".join(message_parts) if message_parts else "TTS 任务已完成"
    
    # 创建通知
    notification = UserNotification(
        type=notification_type,
        ebook_id=job.ebook_id,
        tts_job_id=job.id,
        title=title,
        message=message,
        severity=severity,
        is_read=False,
        # 设置用户ID（从job.created_by或默认值）
        user_id=job.created_by if job.created_by else 1,  # 使用任务创建者或默认管理员
        # 设置媒体类型和路由payload
        media_type=ReadingMediaType.AUDIOBOOK,
        payload={
            "route_name": "AudiobookDetail",
            "route_params": {"audiobook_id": job.ebook_id},
            "job_id": job.id,
            "ebook_id": job.ebook_id
        }
    )
    
    db.add(notification)
    await db.flush()
    
    logger.info(f"Created notification {notification.id} for TTS job {job.id} (status: {status})")
    
    # 如果TTS任务成功完成，额外创建AUDIOBOOK_READY通知
    if status == "success":
        try:
            from app.services.notification_service import notify_audiobook_ready_for_user
            from app.schemas.notification_reading import create_audiobook_ready_payload
            
            # 获取有声书标题
            ebook_title = ebook.title if ebook else "某作品"
            
            # 创建标准化的 AUDIOBOOK_READY payload
            audiobook_payload = create_audiobook_ready_payload(
                audiobook_id=job.ebook_id,
                title=ebook_title,
                cover_url=ebook.cover_url if ebook else None,
                from_ebook_id=job.ebook_id,
                total_chapters=summary.get("total_chapters") if summary else None,
                source_type="tts",
            )
            
            # 创建AUDIOBOOK_READY通知
            audiobook_notification = await notify_audiobook_ready_for_user(
                session=db,
                user_id=job.created_by if job.created_by else 1,
                payload=audiobook_payload.dict(),
            )
            
            logger.info(f"Created AUDIOBOOK_READY notification {audiobook_notification.id} for audiobook {job.ebook_id}")
            
        except Exception as audiobook_notify_err:
            logger.warning(f"Failed to create AUDIOBOOK_READY notification for TTS job {job.id}: {audiobook_notify_err}", exc_info=True)
            # 不影响主流程，继续执行
    
    return notification

