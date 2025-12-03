"""
媒体库快照工具

FUTURE-AI-CLEANUP-ADVISOR-1 P1 实现
获取媒体库统计和清理候选，用于清理建议
"""

from typing import Optional
from pydantic import BaseModel, Field
from loguru import logger

from .base import AITool, OrchestratorContext, EmptyInput


class MediaTypeStats(BaseModel):
    """媒体类型统计"""
    media_type: str
    count: int = 0
    total_size_gb: float = 0.0


class QualityStats(BaseModel):
    """质量分布统计"""
    quality: str  # 4K / 1080p / 720p / other
    count: int = 0
    total_size_gb: float = 0.0


class DuplicateMedia(BaseModel):
    """重复媒体"""
    media_id: int
    title: str
    versions: int  # 版本数
    total_size_gb: float
    qualities: list[str]  # 各版本质量
    savable_gb: float  # 如果保留最高质量可节省的空间


class HRActiveItem(BaseModel):
    """活跃保种项"""
    task_id: int
    title: str
    site_name: str
    size_gb: float
    current_ratio: float
    required_ratio: float
    seed_hours: float
    required_hours: float
    risk_score: float


class CleanupCandidate(BaseModel):
    """清理候选"""
    target_type: str  # media_file / download_task
    target_id: int
    title: str
    size_gb: float
    reason: str  # low_quality / duplicate / completed_seeding / old_download
    risk_level: str  # safe / caution / risky
    hr_status: Optional[str] = None  # active / completed / none


class LibrarySnapshotOutput(BaseModel):
    """媒体库快照输出"""
    media_stats: list[MediaTypeStats] = Field(default_factory=list)
    quality_stats: list[QualityStats] = Field(default_factory=list)
    duplicates: list[DuplicateMedia] = Field(default_factory=list)
    hr_active_items: list[HRActiveItem] = Field(default_factory=list)
    cleanup_candidates: list[CleanupCandidate] = Field(default_factory=list)
    total_media_count: int = 0
    total_size_gb: float = 0.0
    potential_savable_gb: float = 0.0
    summary_text: str = ""


class GetLibrarySnapshotTool(AITool):
    """
    媒体库快照工具
    
    获取媒体库统计和清理候选项
    """
    
    name = "get_library_snapshot"
    description = (
        "获取媒体库的统计快照和清理候选项。"
        "包括媒体类型分布、质量分布、重复媒体、活跃保种任务和清理候选。"
        "用于分析媒体库结构和识别可清理的内容。"
    )
    input_model = EmptyInput
    output_model = LibrarySnapshotOutput
    
    async def run(
        self,
        params: EmptyInput,
        context: OrchestratorContext,
    ) -> LibrarySnapshotOutput:
        """获取媒体库快照"""
        try:
            # 获取各类统计
            media_stats = await self._get_media_stats(context)
            quality_stats = await self._get_quality_stats(context)
            duplicates = await self._get_duplicates(context)
            hr_items = await self._get_hr_active_items(context)
            candidates = await self._get_cleanup_candidates(context, hr_items)
            
            # 汇总
            total_count = sum(s.count for s in media_stats)
            total_size = sum(s.total_size_gb for s in media_stats)
            potential_save = sum(d.savable_gb for d in duplicates)
            potential_save += sum(c.size_gb for c in candidates if c.risk_level == "safe")
            
            # 生成摘要
            if not media_stats:
                summary_text = "媒体库为空或无法获取统计信息。"
            else:
                summary_text = f"媒体库共 {total_count} 项，占用 {total_size:.1f} GB。"
                
                if duplicates:
                    summary_text += f" 发现 {len(duplicates)} 组重复媒体。"
                
                if candidates:
                    safe_count = sum(1 for c in candidates if c.risk_level == "safe")
                    summary_text += f" 有 {safe_count} 项安全可清理候选。"
                
                if hr_items:
                    summary_text += f" {len(hr_items)} 个活跃保种任务需要继续做种。"
                
                if potential_save > 0:
                    summary_text += f" 预计可释放 {potential_save:.1f} GB。"
            
            return LibrarySnapshotOutput(
                media_stats=media_stats,
                quality_stats=quality_stats,
                duplicates=duplicates[:10],  # 限制返回数量
                hr_active_items=hr_items[:20],
                cleanup_candidates=candidates[:30],
                total_media_count=total_count,
                total_size_gb=round(total_size, 2),
                potential_savable_gb=round(potential_save, 2),
                summary_text=summary_text,
            )
            
        except Exception as e:
            logger.error(f"[library_snapshot] 获取媒体库快照失败: {e}")
            return LibrarySnapshotOutput(
                summary_text=f"获取媒体库快照时发生错误: {str(e)[:100]}"
            )
    
    async def _get_media_stats(self, context: OrchestratorContext) -> list[MediaTypeStats]:
        """获取媒体类型统计"""
        stats: list[MediaTypeStats] = []
        
        try:
            from sqlalchemy import select, func
            from app.models.media import Media, MediaFile
            
            # 按媒体类型分组统计
            query = (
                select(
                    Media.media_type,
                    func.count(Media.id).label("count"),
                )
                .group_by(Media.media_type)
            )
            
            result = await context.db.execute(query)
            for row in result.fetchall():
                media_type = row[0] or "unknown"
                count = row[1] or 0
                
                # 获取该类型的总大小
                size_query = (
                    select(func.sum(MediaFile.file_size_gb))
                    .join(Media, Media.id == MediaFile.media_id)
                    .where(Media.media_type == media_type)
                )
                size_result = await context.db.execute(size_query)
                total_size = size_result.scalar() or 0.0
                
                stats.append(MediaTypeStats(
                    media_type=media_type,
                    count=count,
                    total_size_gb=round(total_size, 2),
                ))
            
        except ImportError:
            logger.warning("[library_snapshot] Media 模型不可用")
        except Exception as e:
            logger.warning(f"[library_snapshot] 获取媒体统计失败: {e}")
        
        return sorted(stats, key=lambda x: -x.total_size_gb)
    
    async def _get_quality_stats(self, context: OrchestratorContext) -> list[QualityStats]:
        """获取质量分布统计"""
        stats: list[QualityStats] = []
        
        try:
            from sqlalchemy import select, func
            from app.models.media import MediaFile
            
            query = (
                select(
                    MediaFile.quality,
                    func.count(MediaFile.id).label("count"),
                    func.sum(MediaFile.file_size_gb).label("total_size"),
                )
                .group_by(MediaFile.quality)
            )
            
            result = await context.db.execute(query)
            for row in result.fetchall():
                quality = row[0] or "unknown"
                count = row[1] or 0
                total_size = row[2] or 0.0
                
                stats.append(QualityStats(
                    quality=quality,
                    count=count,
                    total_size_gb=round(total_size, 2),
                ))
            
        except Exception as e:
            logger.warning(f"[library_snapshot] 获取质量统计失败: {e}")
        
        return sorted(stats, key=lambda x: -x.total_size_gb)
    
    async def _get_duplicates(self, context: OrchestratorContext) -> list[DuplicateMedia]:
        """获取重复媒体"""
        duplicates: list[DuplicateMedia] = []
        
        try:
            from sqlalchemy import select, func
            from app.models.media import Media, MediaFile
            
            # 找出有多个文件的媒体
            subquery = (
                select(
                    MediaFile.media_id,
                    func.count(MediaFile.id).label("file_count"),
                )
                .group_by(MediaFile.media_id)
                .having(func.count(MediaFile.id) > 1)
                .subquery()
            )
            
            query = (
                select(Media, subquery.c.file_count)
                .join(subquery, Media.id == subquery.c.media_id)
                .limit(20)
            )
            
            result = await context.db.execute(query)
            for row in result.fetchall():
                media = row[0]
                file_count = row[1]
                
                # 获取该媒体的所有文件
                files_query = select(MediaFile).where(MediaFile.media_id == media.id)
                files_result = await context.db.execute(files_query)
                files = files_result.scalars().all()
                
                qualities = [f.quality or "unknown" for f in files]
                total_size = sum(f.file_size_gb or 0 for f in files)
                
                # 计算可节省空间（保留最大文件）
                sizes = [f.file_size_gb or 0 for f in files]
                max_size = max(sizes) if sizes else 0
                savable = total_size - max_size
                
                duplicates.append(DuplicateMedia(
                    media_id=media.id,
                    title=media.title,
                    versions=file_count,
                    total_size_gb=round(total_size, 2),
                    qualities=qualities,
                    savable_gb=round(savable, 2),
                ))
            
        except Exception as e:
            logger.warning(f"[library_snapshot] 获取重复媒体失败: {e}")
        
        return sorted(duplicates, key=lambda x: -x.savable_gb)
    
    async def _get_hr_active_items(self, context: OrchestratorContext) -> list[HRActiveItem]:
        """获取活跃保种任务"""
        items: list[HRActiveItem] = []
        
        try:
            from sqlalchemy import select
            from app.models.hnr import HNRTask
            
            query = (
                select(HNRTask)
                .where(HNRTask.status == "monitoring")
                .order_by(HNRTask.risk_score.desc())
                .limit(30)
            )
            
            result = await context.db.execute(query)
            for task in result.scalars().all():
                items.append(HRActiveItem(
                    task_id=task.id,
                    title=task.title[:100] if task.title else "未知",
                    site_name=task.site_name or "未知站点",
                    size_gb=round(task.downloaded_gb or 0, 2),
                    current_ratio=round(task.current_ratio or 0, 2),
                    required_ratio=round(task.required_ratio or 1.0, 2),
                    seed_hours=round(task.seed_time_hours or 0, 1),
                    required_hours=round(task.required_seed_time_hours or 0, 1),
                    risk_score=round(task.risk_score or 0, 2),
                ))
            
        except Exception as e:
            logger.warning(f"[library_snapshot] 获取保种任务失败: {e}")
        
        return items
    
    async def _get_cleanup_candidates(
        self,
        context: OrchestratorContext,
        hr_items: list[HRActiveItem],
    ) -> list[CleanupCandidate]:
        """获取清理候选"""
        candidates: list[CleanupCandidate] = []
        
        # HR 活跃任务的下载 ID 集合
        hr_active_ids = set()
        
        try:
            from sqlalchemy import select
            from app.models.download import DownloadTask
            from app.models.hnr import HNRTask
            
            # 获取 HR 活跃任务关联的下载 ID
            hr_query = select(HNRTask.download_task_id).where(HNRTask.status == "monitoring")
            hr_result = await context.db.execute(hr_query)
            hr_active_ids = set(r[0] for r in hr_result.fetchall() if r[0])
            
            # 获取已完成且较大的下载任务作为候选
            query = (
                select(DownloadTask)
                .where(DownloadTask.status == "completed")
                .order_by(DownloadTask.size_gb.desc())
                .limit(50)
            )
            
            result = await context.db.execute(query)
            for task in result.scalars().all():
                # 判断风险级别
                if task.id in hr_active_ids:
                    risk_level = "risky"
                    hr_status = "active"
                    reason = "已完成下载，仍在保种中"
                else:
                    # 检查是否有完成的 HNR 任务
                    hnr_check = await context.db.execute(
                        select(HNRTask)
                        .where(HNRTask.download_task_id == task.id)
                        .where(HNRTask.status == "completed")
                    )
                    completed_hnr = hnr_check.scalar_one_or_none()
                    
                    if completed_hnr:
                        risk_level = "safe"
                        hr_status = "completed"
                        reason = "保种任务已完成，可安全清理"
                    else:
                        risk_level = "caution"
                        hr_status = "none"
                        reason = "已完成下载，无保种记录"
                
                candidates.append(CleanupCandidate(
                    target_type="download_task",
                    target_id=task.id,
                    title=task.title[:100] if task.title else "未知",
                    size_gb=round(task.size_gb or 0, 2),
                    reason=reason,
                    risk_level=risk_level,
                    hr_status=hr_status,
                ))
            
        except Exception as e:
            logger.warning(f"[library_snapshot] 获取清理候选失败: {e}")
        
        # 按风险级别排序：safe < caution < risky
        risk_order = {"safe": 0, "caution": 1, "risky": 2}
        return sorted(candidates, key=lambda x: (risk_order.get(x.risk_level, 1), -x.size_gb))
