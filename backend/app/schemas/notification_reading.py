"""
阅读通知统一 Payload Schema

定义所有阅读相关通知的统一数据结构，确保前后端渲染一致性。
"""

from datetime import datetime
from typing import Literal, Dict, Any, Optional, List
from pydantic import BaseModel, Field

from app.models.enums.reading_media_type import ReadingMediaType


class ReadingBasePayload(BaseModel):
    """阅读通知基础 Payload"""
    media_type: ReadingMediaType = Field(..., description="媒体类型：NOVEL / AUDIOBOOK / MANGA")
    title: str = Field(..., description="作品标题")
    cover_url: Optional[str] = Field(None, description="封面图片URL")
    route_name: str = Field(..., description="前端路由名称")
    route_params: Dict[str, Any] = Field(..., description="前端路由参数")
    source_label: Optional[str] = Field(None, description="来源标签，如'小说中心' / '有声书中心' / '漫画中心'")


class MangaUpdatedPayload(ReadingBasePayload):
    """漫画更新通知 Payload"""
    notification_type: Literal["MANGA_UPDATED"] = "MANGA_UPDATED"
    series_id: int = Field(..., description="漫画系列ID")
    new_chapters: List[str] = Field(default_factory=list, description="新章节标题列表")
    total_new_count: int = Field(..., description="新增章节数量")
    last_updated_at: Optional[datetime] = Field(None, description="最后更新时间")
    latest_chapter_id: Optional[int] = Field(None, description="最新章节ID")
    # 远程追更支持字段
    is_remote: Optional[bool] = Field(False, description="是否为远程更新")
    source_name: Optional[str] = Field(None, description="源名称，远程模式时显示")


class EbookImportedPayload(ReadingBasePayload):
    """电子书导入完成通知 Payload"""
    notification_type: Literal["READING_EBOOK_IMPORTED"] = "READING_EBOOK_IMPORTED"
    ebook_id: int = Field(..., description="电子书ID")
    imported_at: Optional[datetime] = Field(None, description="导入时间")
    source_type: Optional[str] = Field(None, description="导入来源，如'txt_upload' / 'inbox_import'")


class AudiobookReadyPayload(ReadingBasePayload):
    """有声书就绪通知 Payload"""
    notification_type: Literal["AUDIOBOOK_READY"] = "AUDIOBOOK_READY"
    audiobook_id: int = Field(..., description="有声书ID")
    from_ebook_id: Optional[int] = Field(None, description="来源电子书ID")
    generated_at: Optional[datetime] = Field(None, description="生成完成时间")
    total_chapters: Optional[int] = Field(None, description="总章节数")
    source_type: Optional[str] = Field(None, description="生成来源，如'tts' / 'upload'")


# 类型联合，用于前端类型推断
ReadingNotificationPayload = (
    MangaUpdatedPayload | 
    EbookImportedPayload | 
    AudiobookReadyPayload
)


def create_manga_updated_payload(
    *,
    series_id: int,
    title: str,
    cover_url: Optional[str] = None,
    new_chapters: List[str],
    latest_chapter_id: Optional[int] = None,
    last_updated_at: Optional[datetime] = None,
    # 远程追更支持参数
    is_remote: Optional[bool] = False,
    source_name: Optional[str] = None,
) -> MangaUpdatedPayload:
    """创建漫画更新通知 Payload 的便捷函数"""
    return MangaUpdatedPayload(
        media_type=ReadingMediaType.MANGA,
        title=title,
        cover_url=cover_url,
        route_name="MangaReaderPage",
        route_params={"series_id": series_id, "chapter_id": latest_chapter_id},
        source_label="漫画中心",
        series_id=series_id,
        new_chapters=new_chapters,
        total_new_count=len(new_chapters),
        last_updated_at=last_updated_at,
        latest_chapter_id=latest_chapter_id,
        is_remote=is_remote,
        source_name=source_name,
    )


def create_ebook_imported_payload(
    *,
    ebook_id: int,
    title: str,
    cover_url: Optional[str] = None,
    source_type: Optional[str] = None,
) -> EbookImportedPayload:
    """创建电子书导入通知 Payload 的便捷函数"""
    return EbookImportedPayload(
        media_type=ReadingMediaType.NOVEL,
        title=title,
        cover_url=cover_url,
        route_name="NovelReader",
        route_params={"ebookId": ebook_id},
        source_label="小说中心",
        ebook_id=ebook_id,
        imported_at=datetime.utcnow(),
        source_type=source_type,
    )


def create_audiobook_ready_payload(
    *,
    audiobook_id: int,
    title: str,
    cover_url: Optional[str] = None,
    from_ebook_id: Optional[int] = None,
    total_chapters: Optional[int] = None,
    source_type: Optional[str] = None,
) -> AudiobookReadyPayload:
    """创建有声书就绪通知 Payload 的便捷函数"""
    return AudiobookReadyPayload(
        media_type=ReadingMediaType.AUDIOBOOK,
        title=title,
        cover_url=cover_url,
        route_name="AudiobookCenter",
        route_params={"audiobook_id": audiobook_id},
        source_label="有声书中心",
        audiobook_id=audiobook_id,
        from_ebook_id=from_ebook_id,
        generated_at=datetime.utcnow(),
        total_chapters=total_chapters,
        source_type=source_type,
    )
