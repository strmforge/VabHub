"""
文件清理API
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from pydantic import BaseModel
from loguru import logger

from app.core.schemas import BaseResponse, success_response, error_response
from app.modules.file_cleaner.service import FileCleanerService, CleanupResult

router = APIRouter(prefix="/file-cleaner", tags=["文件清理"])


# 请求/响应模型
class CleanDirectoryRequest(BaseModel):
    """清理目录请求"""
    directory: str
    dry_run: bool = True
    include_subdirs: bool = True
    max_file_size_mb: Optional[int] = None


class CleanBySizeRequest(BaseModel):
    """按大小清理请求"""
    directory: str
    max_size_mb: int = 10
    dry_run: bool = True
    include_subdirs: bool = True


class CleanByAgeRequest(BaseModel):
    """按年龄清理请求"""
    directory: str
    days: int = 7
    dry_run: bool = True
    include_subdirs: bool = True


class CleanupResultResponse(BaseModel):
    """清理结果响应"""
    cleaned_files: int
    cleaned_dirs: int
    total_size: int
    total_size_mb: float
    files_removed: list
    dirs_removed: list
    dry_run: bool


class DirectoryStatsResponse(BaseModel):
    """目录统计响应"""
    total_files: int
    total_dirs: int
    total_size: int
    total_size_mb: float
    temp_files: int
    temp_dirs: int
    temp_size: int
    temp_size_mb: float


@router.post("/clean", response_model=BaseResponse)
async def clean_directory(request: CleanDirectoryRequest):
    """清理目录"""
    try:
        cleaner = FileCleanerService()
        result = await cleaner.clean_directory(
            directory=request.directory,
            dry_run=request.dry_run,
            include_subdirs=request.include_subdirs,
            max_file_size_mb=request.max_file_size_mb
        )
        
        return success_response(
            data=CleanupResultResponse(
                cleaned_files=result.cleaned_files,
                cleaned_dirs=result.cleaned_dirs,
                total_size=result.total_size,
                total_size_mb=round(result.total_size / 1024 / 1024, 2),
                files_removed=result.files_removed,
                dirs_removed=result.dirs_removed,
                dry_run=request.dry_run
            ).model_dump(),
            message=f"清理完成: {result.cleaned_files} 个文件, {result.cleaned_dirs} 个目录"
        )
    except Exception as e:
        logger.error(f"清理目录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"清理目录时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/clean-by-size", response_model=BaseResponse)
async def clean_by_size(request: CleanBySizeRequest):
    """按大小清理文件"""
    try:
        cleaner = FileCleanerService()
        result = await cleaner.clean_by_size(
            directory=request.directory,
            max_size_mb=request.max_size_mb,
            dry_run=request.dry_run,
            include_subdirs=request.include_subdirs
        )
        
        return success_response(
            data=CleanupResultResponse(
                cleaned_files=result.cleaned_files,
                cleaned_dirs=result.cleaned_dirs,
                total_size=result.total_size,
                total_size_mb=round(result.total_size / 1024 / 1024, 2),
                files_removed=result.files_removed,
                dirs_removed=result.dirs_removed,
                dry_run=request.dry_run
            ).model_dump(),
            message=f"按大小清理完成: {result.cleaned_files} 个文件"
        )
    except Exception as e:
        logger.error(f"按大小清理失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"按大小清理时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/clean-by-age", response_model=BaseResponse)
async def clean_by_age(request: CleanByAgeRequest):
    """按年龄清理文件"""
    try:
        cleaner = FileCleanerService()
        result = await cleaner.clean_by_age(
            directory=request.directory,
            days=request.days,
            dry_run=request.dry_run,
            include_subdirs=request.include_subdirs
        )
        
        return success_response(
            data=CleanupResultResponse(
                cleaned_files=result.cleaned_files,
                cleaned_dirs=result.cleaned_dirs,
                total_size=result.total_size,
                total_size_mb=round(result.total_size / 1024 / 1024, 2),
                files_removed=result.files_removed,
                dirs_removed=result.dirs_removed,
                dry_run=request.dry_run
            ).model_dump(),
            message=f"按年龄清理完成: {result.cleaned_files} 个文件"
        )
    except Exception as e:
        logger.error(f"按年龄清理失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"按年龄清理时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/stats", response_model=BaseResponse)
async def get_directory_stats(
    directory: str = Query(..., description="目录路径")
):
    """获取目录统计信息"""
    try:
        cleaner = FileCleanerService()
        stats = await cleaner.get_directory_stats(directory)
        
        return success_response(
            data=DirectoryStatsResponse(
                total_files=stats["total_files"],
                total_dirs=stats["total_dirs"],
                total_size=stats["total_size"],
                total_size_mb=round(stats["total_size"] / 1024 / 1024, 2),
                temp_files=stats["temp_files"],
                temp_dirs=stats["temp_dirs"],
                temp_size=stats["temp_size"],
                temp_size_mb=round(stats["temp_size"] / 1024 / 1024, 2)
            ).model_dump(),
            message="获取目录统计成功"
        )
    except Exception as e:
        logger.error(f"获取目录统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取目录统计时发生错误: {str(e)}"
            ).model_dump()
        )

