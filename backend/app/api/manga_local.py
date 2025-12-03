"""
本地漫画库 API
"""
from typing import Optional, List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path as PathParam, Body
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from loguru import logger

from app.core.database import get_db
from app.core.schemas import BaseResponse, success_response, PaginatedResponse
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.manga_series_local import MangaSeriesLocal
from app.models.manga_chapter_local import MangaChapterLocal, MangaChapterStatus
from app.models.manga_source import MangaSource
from app.schemas.manga_local import (
    MangaSeriesLocalRead,
    MangaChapterLocalRead,
    LocalMangaPageRead,
)
from app.schemas.manga_import import MangaImportOptions
from app.schemas.manga_download_job import MangaDownloadJobRead, MangaDownloadJobList, MangaDownloadJobSummary
from app.services.manga_import_service import (
    import_series_from_remote,
    download_chapter,
    bulk_download_pending_chapters,
)
from app.services.manga_download_job_service import MangaDownloadJobService
from app.services.manga_remote_sync_service import sync_remote_series_once, SeriesSyncResult

router = APIRouter(prefix="/api/manga/local", tags=["本地漫画库"])

# 漫画存储根路径
MANGA_ROOT = getattr(settings, 'COMIC_LIBRARY_ROOT', './data/library/comics')


def _get_cover_url(series: MangaSeriesLocal) -> Optional[str]:
    """获取封面 URL"""
    if series.cover_path:
        # cover_path 已经是相对路径，直接拼接
        return f"/media/{series.cover_path}"
    return None


def _get_page_url(chapter: MangaChapterLocal, page_index: int) -> str:
    """获取页面 URL（支持新旧路径格式的向后兼容）"""
    if chapter.file_path:
        try:
            # 检测路径格式并构建章节目录路径
            if chapter.file_path.startswith("data/") or "series_" in chapter.file_path:
                # 旧格式：data/library/comics/series_{id}/chapter_{id}
                # 直接使用旧路径，媒体服务从./data开始服务
                chapter_dir = Path(MANGA_ROOT).parent.parent / chapter.file_path
            else:
                # 新格式：series-slug/chapter-number - title
                # 需要添加library/comics前缀以匹配媒体服务路径
                new_path = f"library/comics/{chapter.file_path}"
                chapter_dir = Path(MANGA_ROOT).parent.parent / new_path
                
            if chapter_dir.exists():
                # 查找对应索引的文件
                files = sorted(chapter_dir.glob("*.*"))
                if 0 < page_index <= len(files):
                    file_path = files[page_index - 1]
                    # 计算相对于./data的相对路径（媒体服务根目录）
                    media_root = Path(MANGA_ROOT).parent.parent
                    relative_path = file_path.relative_to(media_root)
                    return f"/media/{relative_path.as_posix()}"
        except Exception as e:
            logger.error(f"Failed to get page URL for chapter {chapter.id}: {e}")
    return ""


@router.get("/series", response_model=BaseResponse, summary="列出本地漫画系列")
async def list_local_series(
    keyword: Optional[str] = Query(None, description="关键字（按标题模糊匹配）"),
    source_id: Optional[int] = Query(None, description="源 ID 过滤"),
    favorite: Optional[bool] = Query(None, description="是否收藏"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    列出本地漫画系列
    
    支持关键字搜索、源过滤、收藏筛选
    """
    try:
        # 构建查询条件
        conditions = []
        
        if keyword:
            conditions.append(
                or_(
                    MangaSeriesLocal.title.ilike(f"%{keyword}%"),
                )
            )
        
        if source_id:
            conditions.append(MangaSeriesLocal.source_id == source_id)
        
        if favorite is not None:
            conditions.append(MangaSeriesLocal.is_favorite == favorite)
        
        # 总数查询
        count_query = select(func.count()).select_from(MangaSeriesLocal)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        # 分页查询
        query = select(MangaSeriesLocal)
        if conditions:
            query = query.where(and_(*conditions))
        
        offset = (page - 1) * page_size
        query = query.order_by(MangaSeriesLocal.id.desc()).offset(offset).limit(page_size)
        
        result = await db.execute(query)
        series_list = result.scalars().all()
        
        # 转换为响应格式
        items = []
        for series in series_list:
            series_dict = MangaSeriesLocalRead.model_validate(series).model_dump()
            series_dict['cover_url'] = _get_cover_url(series)
            items.append(series_dict)
        
        paginated_response = PaginatedResponse.create(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )
        
        return success_response(
            data=paginated_response.model_dump(),
            message="获取本地漫画系列列表成功"
        )
        
    except Exception as e:
        logger.error(f"获取本地漫画系列列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取列表失败: {str(e)}"
        )


@router.get("/series/{series_id}", response_model=BaseResponse, summary="获取本地漫画系列详情")
async def get_local_series_detail(
    series_id: int = PathParam(..., description="系列 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取本地漫画系列详情和章节列表
    """
    try:
        # 获取系列
        stmt = select(MangaSeriesLocal).where(MangaSeriesLocal.id == series_id)
        result = await db.execute(stmt)
        series = result.scalar_one_or_none()
        
        if not series:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"系列不存在 (ID: {series_id})"
            )
        
        # 获取章节列表
        stmt = select(MangaChapterLocal).where(
            MangaChapterLocal.series_id == series_id
        ).order_by(
            MangaChapterLocal.volume.asc().nulls_last(),
            MangaChapterLocal.number.asc().nulls_last()
        )
        result = await db.execute(stmt)
        chapters = result.scalars().all()
        
        series_dict = MangaSeriesLocalRead.model_validate(series).model_dump()
        series_dict['cover_url'] = _get_cover_url(series)
        
        return success_response(
            data={
                "series": series_dict,
                "chapters": [MangaChapterLocalRead.model_validate(ch).model_dump() for ch in chapters]
            },
            message="获取详情成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取本地漫画系列详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取详情失败: {str(e)}"
        )


@router.post("/import", response_model=BaseResponse, summary="导入远程系列到本地")
async def import_series(
    source_id: int = Body(..., description="源 ID"),
    remote_series_id: str = Body(..., description="远程系列 ID"),
    mode: str = Body("ALL", description="导入模式：ALL/LATEST_N/SELECTED"),
    latest_n: Optional[int] = Body(None, description="当 mode=LATEST_N 时，导入最近 N 话"),
    chapter_ids: Optional[List[str]] = Body(None, description="当 mode=SELECTED 时，指定章节 ID 列表"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    从远程源导入漫画系列到本地
    
    创建本地记录和 PENDING 状态的章节
    """
    try:
        options = MangaImportOptions(
            mode=mode,
            latest_n=latest_n,
            chapter_ids=chapter_ids
        )
        
        local_series = await import_series_from_remote(
            session=db,
            source_id=source_id,
            remote_series_id=remote_series_id,
            options=options
        )
        
        # 获取章节列表
        stmt = select(MangaChapterLocal).where(
            MangaChapterLocal.series_id == local_series.id
        ).order_by(
            MangaChapterLocal.number.asc().nulls_last()
        )
        result = await db.execute(stmt)
        chapters = result.scalars().all()
        
        series_dict = MangaSeriesLocalRead.model_validate(local_series).model_dump()
        series_dict['cover_url'] = _get_cover_url(local_series)
        
        return success_response(
            data={
                "series": series_dict,
                "chapters": [MangaChapterLocalRead.model_validate(ch).model_dump() for ch in chapters]
            },
            message="导入成功"
        )
        
    except Exception as e:
        logger.error(f"导入远程系列失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}"
        )


@router.post(
    "/series/{series_id}/sync_remote",
    response_model=BaseResponse,
    summary="手动同步指定本地系列的远程章节",
)
async def sync_single_series_remote(
    series_id: int = PathParam(..., description="系列 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """手动触发单个本地系列的远程章节同步。

    - 仅同步远程章节到 MangaChapterLocal
    - 不处理用户追更状态和通知
    """
    try:
        stmt = select(MangaSeriesLocal).where(MangaSeriesLocal.id == series_id)
        result = await db.execute(stmt)
        series = result.scalar_one_or_none()

        if not series:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"系列不存在 (ID: {series_id})",
            )

        sync_result: SeriesSyncResult = await sync_remote_series_once(db, series=series)

        if sync_result.had_error:
            await db.rollback()
        else:
            await db.commit()

        return success_response(
            data={
                "series_id": sync_result.series_id,
                "source_id": sync_result.source_id,
                "remote_series_id": sync_result.remote_series_id,
                "new_chapters_count": sync_result.new_chapters_count,
                "had_error": sync_result.had_error,
                "error_message": sync_result.error_message,
            },
            message="同步完成" if not sync_result.had_error else "同步失败",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"手动同步系列 {series_id} 远程章节失败: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"同步失败: {str(e)}",
        )


@router.get("/chapters/{chapter_id}/pages", response_model=BaseResponse, summary="获取章节页面列表")
async def get_chapter_pages(
    chapter_id: int = PathParam(..., description="章节 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取章节页面列表
    
    返回所有页面的访问 URL
    """
    try:
        stmt = select(MangaChapterLocal).where(MangaChapterLocal.id == chapter_id)
        result = await db.execute(stmt)
        chapter = result.scalar_one_or_none()
        
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"章节不存在 (ID: {chapter_id})"
            )
        
        if chapter.status != MangaChapterStatus.READY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="章节尚未下载完成"
            )
        
        if not chapter.file_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="章节文件路径不存在"
            )
        
        # 枚举章节目录下的所有图片文件
        # 检测路径格式并构建章节目录路径（支持新旧格式的向后兼容）
        if chapter.file_path.startswith("data/") or "series_" in chapter.file_path:
            # 旧格式：data/library/comics/series_{id}/chapter_{id}
            # 直接使用旧路径，媒体服务从./data开始服务
            chapter_dir = Path(MANGA_ROOT).parent.parent / chapter.file_path
            media_root = Path(MANGA_ROOT).parent.parent
        else:
            # 新格式：series-slug/chapter-number - title
            # 需要添加library/comics前缀以匹配媒体服务路径
            new_path = f"library/comics/{chapter.file_path}"
            chapter_dir = Path(MANGA_ROOT).parent.parent / new_path
            media_root = Path(MANGA_ROOT).parent.parent
            
        if not chapter_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="章节文件目录不存在"
            )
        
        # 获取所有图片文件并按文件名排序
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
        image_files = sorted([
            f for f in chapter_dir.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ], key=lambda x: x.name)
        
        pages = []
        for idx, image_file in enumerate(image_files, start=1):
            relative_path = image_file.relative_to(media_root)
            pages.append(LocalMangaPageRead(
                index=idx,
                image_url=f"/media/{relative_path.as_posix()}"
            ))
        
        return success_response(
            data=[p.model_dump() for p in pages],
            message="获取页面列表成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取章节页面列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取页面列表失败: {str(e)}"
        )


@router.get("/chapters/{chapter_id}/pages/{page_index}", summary="获取章节页面图片")
async def get_chapter_page_image(
    chapter_id: int = PathParam(..., description="章节 ID"),
    page_index: int = PathParam(..., ge=1, description="页面索引（从1开始）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取章节页面的图片文件
    
    直接返回图片文件流，支持浏览器直接显示
    """
    try:
        # 获取章节信息
        stmt = select(MangaChapterLocal).where(MangaChapterLocal.id == chapter_id)
        result = await db.execute(stmt)
        chapter = result.scalar_one_or_none()
        
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"章节不存在 (ID: {chapter_id})"
            )
        
        if chapter.status != MangaChapterStatus.READY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"章节未准备就绪 (状态: {chapter.status})"
            )
        
        # 获取页面URL
        page_url = _get_page_url(chapter, page_index)
        if not page_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"页面不存在 (索引: {page_index})"
            )
        
        # 构建完整的文件路径
        if chapter.file_path:
            # 检测路径格式并构建章节目录路径（支持新旧格式的向后兼容）
            if chapter.file_path.startswith("data/") or "series_" in chapter.file_path:
                # 旧格式：data/library/comics/series_{id}/chapter_{id}
                # 直接使用旧路径，媒体服务从./data开始服务
                chapter_dir = Path(MANGA_ROOT).parent.parent / chapter.file_path
            else:
                # 新格式：series-slug/chapter-number - title
                # 需要添加library/comics前缀以匹配媒体服务路径
                new_path = f"library/comics/{chapter.file_path}"
                chapter_dir = Path(MANGA_ROOT).parent.parent / new_path
                
            if chapter_dir.exists():
                files = sorted(chapter_dir.glob("*.*"))
                if 0 < page_index <= len(files):
                    image_path = files[page_index - 1]
                    
                    # 根据文件扩展名确定媒体类型
                    media_type = "image/jpeg"
                    if image_path.suffix.lower() == ".png":
                        media_type = "image/png"
                    elif image_path.suffix.lower() == ".webp":
                        media_type = "image/webp"
                    
                    return FileResponse(
                        path=image_path,
                        media_type=media_type,
                        filename=image_path.name
                    )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"图片文件不存在 (章节: {chapter_id}, 页面: {page_index})"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取页面图片失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取图片失败: {str(e)}"
        )


@router.post("/chapters/{chapter_id}/download", response_model=BaseResponse, summary="下载章节到本地")
async def download_chapter_to_local(
    chapter_id: int = PathParam(..., description="章节 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    下载单个章节到本地存储
    
    触发章节下载任务，返回下载状态
    """
    try:
        from app.services.manga_import_service import download_chapter
        
        # 获取章节信息
        stmt = select(MangaChapterLocal).where(MangaChapterLocal.id == chapter_id)
        result = await db.execute(stmt)
        chapter = result.scalar_one_or_none()
        
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"章节不存在 (ID: {chapter_id})"
            )
        
        if chapter.status == MangaChapterStatus.READY:
            return success_response(
                data={"status": "already_ready", "chapter_id": chapter_id},
                message="章节已存在，无需重复下载"
            )
        
        # 创建下载任务
        from app.services.manga_download_job_service import MangaDownloadJobService
        from app.models.manga_download_job import DownloadJobMode
        
        # 获取系列信息以获取源信息
        stmt = select(MangaSeriesLocal).where(MangaSeriesLocal.id == chapter.series_id)
        result = await db.execute(stmt)
        series = result.scalar_one_or_none()
        
        if not series:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"系列不存在 (ID: {chapter.series_id})"
            )
        
        # 创建章节下载任务
        job = await MangaDownloadJobService.create_job(
            db=db,
            user_id=current_user.id,
            source_id=series.source_id,
            source_type=chapter.source_type if hasattr(chapter, 'source_type') else "UNKNOWN",
            source_series_id=series.remote_series_id,
            source_chapter_id=chapter.remote_chapter_id,
            mode=DownloadJobMode.CHAPTER,
            target_local_series_id=series.id,
        )
        
        return success_response(
            data={
                "chapter_id": chapter_id,
                "status": "job_created",
                "job_id": job.id,
                "job_status": job.status.value,
                "message": "下载任务已创建，正在后台处理"
            },
            message="下载任务已创建"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载章节失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载章节失败: {str(e)}"
        )


@router.post("/series/{series_id}/download", response_model=BaseResponse, summary="下载整部作品到本地")
async def download_series_to_local(
    series_id: int = PathParam(..., description="系列 ID"),
    payload: Optional[dict] = Body(None, description="下载选项"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    下载整部作品的多个章节到本地存储
    
    创建批量下载任务，返回任务信息
    """
    try:
        # 获取系列信息
        stmt = select(MangaSeriesLocal).where(MangaSeriesLocal.id == series_id)
        result = await db.execute(stmt)
        series = result.scalar_one_or_none()
        
        if not series:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"系列不存在 (ID: {series_id})"
            )
        
        # 创建下载任务
        from app.services.manga_download_job_service import MangaDownloadJobService
        from app.models.manga_download_job import DownloadJobMode
        
        # 设置任务优先级（基于下载模式）
        priority = 0
        if payload:
            if payload.get('mode') == 'LATEST_N':
                priority = 10  # 最新章节优先级较高
            elif payload.get('mode') == 'ALL':
                priority = 5   # 全部下载优先级中等
        
        # 创建系列下载任务
        job = await MangaDownloadJobService.create_job(
            db=db,
            user_id=current_user.id,
            source_id=series.source_id,
            source_type="UNKNOWN",  # 系列下载时source_type从系列获取
            source_series_id=series.remote_series_id,
            source_chapter_id=None,  # 整部下载时为空
            mode=DownloadJobMode.SERIES,
            target_local_series_id=series.id,
            priority=priority,
        )
        
        return success_response(
            data={
                "series_id": series_id,
                "job_id": job.id,
                "status": "job_created",
                "job_status": job.status.value,
                "mode": payload.get('mode', 'DEFAULT') if payload else 'DEFAULT',
                "message": "批量下载任务已创建，正在后台处理"
            },
            message="批量下载任务已创建"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量下载章节失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量下载失败: {str(e)}"
        )


# === 下载任务管理 API ===

@router.get("/download-jobs/summary", response_model=BaseResponse, summary="获取下载任务统计")
async def get_download_jobs_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取当前用户的下载任务统计信息
    
    包含各状态的任务数量
    """
    try:
        # 统计各状态任务数量
        total_jobs = await MangaDownloadJobService.count_jobs(
            db=db, user_id=current_user.id
        )
        pending_jobs = await MangaDownloadJobService.count_jobs(
            db=db, user_id=current_user.id, status_filter="PENDING"
        )
        running_jobs = await MangaDownloadJobService.count_jobs(
            db=db, user_id=current_user.id, status_filter="RUNNING"
        )
        success_jobs = await MangaDownloadJobService.count_jobs(
            db=db, user_id=current_user.id, status_filter="SUCCESS"
        )
        failed_jobs = await MangaDownloadJobService.count_jobs(
            db=db, user_id=current_user.id, status_filter="FAILED"
        )
        
        summary = MangaDownloadJobSummary(
            total_jobs=total_jobs,
            pending_jobs=pending_jobs,
            running_jobs=running_jobs,
            completed_jobs=success_jobs + failed_jobs,
            failed_jobs=failed_jobs,
        )
        
        return success_response(
            data=summary.model_dump(),
            message="获取任务统计成功"
        )
        
    except Exception as e:
        logger.error(f"获取下载任务统计失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务统计失败: {str(e)}"
        )


@router.get("/download-jobs", response_model=BaseResponse, summary="获取下载任务列表")
async def list_download_jobs(
    status_filter: Optional[str] = Query(None, description="状态过滤: active/completed/PENDING/RUNNING/SUCCESS/FAILED"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取当前用户的下载任务列表
    
    支持按状态过滤和分页
    """
    try:
        from sqlalchemy.orm import joinedload
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 获取任务列表
        jobs = await MangaDownloadJobService.list_jobs(
            db=db,
            user_id=current_user.id,
            status_filter=status_filter,
            limit=page_size,
            offset=offset,
        )
        
        # 获取总数
        total = await MangaDownloadJobService.count_jobs(
            db=db,
            user_id=current_user.id,
            status_filter=status_filter,
        )
        
        # 获取关联信息
        job_reads = []
        for job in jobs:
            # 获取源信息
            source = await db.get(MangaSource, job.source_id)
            target_series = None
            if job.target_local_series_id:
                target_series = await db.get(MangaSeriesLocal, job.target_local_series_id)
            
            job_read = MangaDownloadJobRead(
                **job.__dict__,
                source_name=source.name if source else None,
                target_series_title=target_series.title if target_series else None,
            )
            job_reads.append(job_read)
        
        total_pages = (total + page_size - 1) // page_size
        
        return success_response(
            data={
                "items": [job.model_dump() for job in job_reads],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            },
            message=f"获取到 {len(job_reads)} 个下载任务"
        )
        
    except Exception as e:
        logger.error(f"获取下载任务列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务列表失败: {str(e)}"
        )


@router.get("/download-jobs/{job_id}", response_model=BaseResponse, summary="获取下载任务详情")
async def get_download_job(
    job_id: int = PathParam(..., description="任务 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取指定下载任务的详细信息
    
    包含源信息和目标系列信息
    """
    try:
        # 获取任务详情（包含关联信息）
        job_details = await MangaDownloadJobService.get_job_details_with_relations(
            db=db,
            job_id=job_id,
            user_id=current_user.id,  # 用户只能查询自己的任务
        )
        
        if not job_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"下载任务不存在 (ID: {job_id})"
            )
        
        job = job_details["job"]
        source = job_details["source"]
        target_series = job_details["target_series"]
        
        job_read = MangaDownloadJobRead(
            **job.__dict__,
            source_name=source.name if source else None,
            target_series_title=target_series.title if target_series else None,
        )
        
        return success_response(
            data=job_read.model_dump(),
            message="获取任务详情成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取下载任务详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务详情失败: {str(e)}"
        )

