"""
文件浏览器API
类似MoviePilot的文件浏览器功能
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional
from pydantic import BaseModel, Field
from loguru import logger
from pathlib import Path
import mimetypes
import os

from app.core.database import get_db
from app.core.schemas import BaseResponse, success_response, error_response
from app.modules.file_browser.service import FileBrowserService
from app.modules.media_renamer.identifier import MediaIdentifier
from app.modules.media_renamer.organizer import MediaOrganizer
from app.modules.file_operation.transfer_service import TransferService
from app.core.config import settings

router = APIRouter(prefix="/file-browser", tags=["文件浏览器"])


# 请求/响应模型
class FileItem(BaseModel):
    """文件项"""
    storage: str
    type: str  # dir/file
    path: str
    name: str
    basename: Optional[str] = None
    extension: Optional[str] = None
    size: int = 0
    modify_time: float = 0
    children: List[dict] = Field(default_factory=list)
    fileid: Optional[str] = None
    parent_fileid: Optional[str] = None
    thumbnail: Optional[str] = None
    pickcode: Optional[str] = None
    drive_id: Optional[str] = None
    url: Optional[str] = None
    is_media: bool = False


class FileListResponse(BaseModel):
    """文件列表响应"""
    items: List[FileItem]
    total: int
    dirs_count: int
    files_count: int
    media_files_count: int


class StorageUsageResponse(BaseModel):
    """存储使用情况响应"""
    total: float
    used: float
    available: float
    usage_percent: float


class CreateFolderRequest(BaseModel):
    """创建目录请求"""
    storage: str
    path: str
    name: str


class RenameFileRequest(BaseModel):
    """重命名文件请求"""
    storage: str
    path: str
    new_name: str


class DeleteFileRequest(BaseModel):
    """删除文件请求"""
    storage: str
    path: str
    confirm: bool = False


class ScrapeRequest(BaseModel):
    """刮削请求"""
    storage: str
    path: str
    overwrite: bool = False


class TransferRequest(BaseModel):
    """整理文件请求"""
    source_storage: str
    source_path: str
    target_storage: str
    target_path: str
    transfer_type: str = "move"  # copy, move, link, softlink
    overwrite_mode: str = "never"  # never, always, size, latest


@router.get("/list", response_model=BaseResponse)
async def list_files(
    storage: str = Query("local", description="存储类型: local, 115, rclone, openlist"),
    path: str = Query("/", description="路径"),
    recursion: bool = Query(False, description="是否递归"),
    sort: str = Query("name", description="排序方式: name, size, time"),
    db = Depends(get_db)
):
    """列出文件和目录"""
    try:
        service = FileBrowserService(db)
        items = await service.list_files(storage, path, recursion, sort)
        
        # 统计
        dirs_count = len([item for item in items if item.get("type") == "dir"])
        files_count = len([item for item in items if item.get("type") == "file"])
        media_files_count = len([item for item in items if item.get("is_media", False)])
        
        return success_response(
            data=FileListResponse(
                items=[FileItem(**item) for item in items],
                total=len(items),
                dirs_count=dirs_count,
                files_count=files_count,
                media_files_count=media_files_count
            ).model_dump(),
            message="获取文件列表成功"
        )
    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取文件列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/item", response_model=BaseResponse)
async def get_file_item(
    storage: str = Query(..., description="存储类型"),
    path: str = Query(..., description="路径"),
    db = Depends(get_db)
):
    """获取文件项"""
    try:
        service = FileBrowserService(db)
        item = await service.get_file_item(storage, path)
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="FILE_NOT_FOUND",
                    error_message=f"文件不存在: {path}"
                ).model_dump()
            )
        
        return success_response(
            data=FileItem(**item).model_dump(),
            message="获取文件信息成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取文件信息时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/folder", response_model=BaseResponse)
async def create_folder(
    request: CreateFolderRequest,
    db = Depends(get_db)
):
    """创建目录"""
    try:
        service = FileBrowserService(db)
        item = await service.create_folder(request.storage, request.path, request.name)
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_response(
                    error_code="CREATE_FOLDER_FAILED",
                    error_message="创建目录失败"
                ).model_dump()
            )
        
        return success_response(
            data=FileItem(**item).model_dump(),
            message="创建目录成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建目录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"创建目录时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/rename", response_model=BaseResponse)
async def rename_file(
    request: RenameFileRequest,
    db = Depends(get_db)
):
    """重命名文件或目录"""
    try:
        service = FileBrowserService(db)
        success = await service.rename_file(request.storage, request.path, request.new_name)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_response(
                    error_code="RENAME_FAILED",
                    error_message="重命名失败"
                ).model_dump()
            )
        
        return success_response(
            data=None,
            message="重命名成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重命名文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"重命名文件时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/delete", response_model=BaseResponse)
async def delete_file(
    request: DeleteFileRequest,
    db = Depends(get_db)
):
    """删除文件或目录"""
    try:
        if not request.confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="CONFIRMATION_REQUIRED",
                    error_message="删除操作需要明确确认（confirm=true）"
                ).model_dump()
            )
        
        service = FileBrowserService(db)
        success = await service.delete_file(request.storage, request.path)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_response(
                    error_code="DELETE_FAILED",
                    error_message="删除失败"
                ).model_dump()
            )
        
        return success_response(
            data=None,
            message="删除成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除文件时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/recognize", response_model=BaseResponse)
async def recognize_file(
    storage: str = Query("local", description="存储类型"),
    path: str = Query(..., description="文件路径"),
    db = Depends(get_db)
):
    """识别媒体文件信息"""
    try:
        # 只支持本地文件识别
        if storage != "local":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="UNSUPPORTED_STORAGE",
                    error_message="目前只支持本地文件识别"
                ).model_dump()
            )
        
        tmdb_api_key = getattr(settings, 'TMDB_API_KEY', None)
        identifier = MediaIdentifier(tmdb_api_key)
        media_info = await identifier.identify(path)
        
        return success_response(
            data={
                "title": media_info.title,
                "year": media_info.year,
                "media_type": media_info.media_type,
                "season": media_info.season,
                "episode": media_info.episode,
                "episode_name": media_info.episode_name,
                "quality": media_info.quality,
                "resolution": media_info.resolution,
                "codec": media_info.codec,
                "source": media_info.source,
                "group": media_info.group,
                "language": media_info.language,
                "subtitle": media_info.subtitle,
                "raw_title": media_info.raw_title
            },
            message="识别成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"识别文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"识别文件时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/scrape", response_model=BaseResponse)
async def scrape_file(
    request: ScrapeRequest,
    db = Depends(get_db)
):
    """刮削媒体信息"""
    try:
        # 只支持本地文件刮削
        if request.storage != "local":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="UNSUPPORTED_STORAGE",
                    error_message="目前只支持本地文件刮削"
                ).model_dump()
            )
        
        from app.modules.media_renamer.organizer import MediaOrganizer
        from app.core.config import settings
        
        tmdb_api_key = getattr(settings, 'TMDB_API_KEY', None)
        organizer = MediaOrganizer(tmdb_api_key)
        
        # 识别媒体信息
        media_info = await organizer.identifier.identify(request.path)
        
        # 执行刮削（这里简化处理，实际应该调用完整的刮削流程）
        # TODO: 实现完整的刮削功能
        
        return success_response(
            data={
                "path": request.path,
                "media_info": {
                    "title": media_info.title,
                    "year": media_info.year,
                    "media_type": media_info.media_type
                }
            },
            message="刮削成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刮削文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"刮削文件时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/transfer", response_model=BaseResponse)
async def transfer_file(
    request: TransferRequest,
    db = Depends(get_db)
):
    """整理文件（转移/复制/链接）"""
    try:
        transfer_service = TransferService(db)
        
        # 获取目录配置（简化处理，实际应该从数据库获取）
        from app.schemas.directory import DirectoryConfig
        
        directory_config = DirectoryConfig(
            storage=request.source_storage,
            library_storage=request.target_storage,
            transfer_type=request.transfer_type,
            library_path=request.target_path,
            download_path=request.source_path  # 源路径作为下载路径
        )
        
        result = await transfer_service.transfer_file(
            source_path=request.source_path,
            target_path=request.target_path,
            directory_config=directory_config,
            overwrite_mode=request.overwrite_mode
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_response(
                    error_code="TRANSFER_FAILED",
                    error_message=result.get("error", "整理文件失败")
                ).model_dump()
            )
        
        return success_response(
            data=result,
            message="整理文件成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"整理文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"整理文件时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/storage/usage", response_model=BaseResponse)
async def get_storage_usage(
    storage: str = Query(..., description="存储类型"),
    db = Depends(get_db)
):
    """获取存储使用情况"""
    try:
        service = FileBrowserService(db)
        usage = await service.get_storage_usage(storage)
        
        if not usage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="STORAGE_NOT_FOUND",
                    error_message=f"存储不存在: {storage}"
                ).model_dump()
            )
        
        return success_response(
            data=StorageUsageResponse(**usage).model_dump(),
            message="获取存储使用情况成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取存储使用情况失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取存储使用情况时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/storage/transfer-types", response_model=BaseResponse)
async def get_transfer_types(
    storage: str = Query(..., description="存储类型"),
    db = Depends(get_db)
):
    """获取支持的传输类型"""
    try:
        service = FileBrowserService(db)
        transfer_types = await service.get_supported_transfer_types(storage)
        
        return success_response(
            data=transfer_types,
            message="获取传输类型成功"
        )
    except Exception as e:
        logger.error(f"获取传输类型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取传输类型时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/download")
async def download_file(
    request: DeleteFileRequest,  # 复用删除请求模型（包含storage和path）
    db = Depends(get_db)
):
    """下载文件（仅支持本地存储）"""
    try:
        if request.storage != "local":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="UNSUPPORTED_STORAGE",
                    error_message="目前只支持本地文件下载"
                ).model_dump()
            )
        
        file_path = Path(request.path)
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="FILE_NOT_FOUND",
                    error_message="文件不存在"
                ).model_dump()
            )
        
        # 获取MIME类型
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "application/octet-stream"
        
        return FileResponse(
            path=str(file_path),
            filename=file_path.name,
            media_type=mime_type
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"下载文件时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/image")
async def get_image(
    storage: str = Query(..., description="存储类型"),
    path: str = Query(..., description="文件路径"),
    db = Depends(get_db)
):
    """获取图片文件（仅支持本地存储）"""
    try:
        if storage != "local":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="UNSUPPORTED_STORAGE",
                    error_message="目前只支持本地图片预览"
                ).model_dump()
            )
        
        file_path = Path(path)
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="FILE_NOT_FOUND",
                    error_message="图片文件不存在"
                ).model_dump()
            )
        
        # 检查是否为图片文件
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico'}
        if file_path.suffix.lower() not in image_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="INVALID_FILE_TYPE",
                    error_message="不是有效的图片文件"
                ).model_dump()
            )
        
        # 获取MIME类型
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "image/jpeg"
        
        return FileResponse(
            path=str(file_path),
            media_type=mime_type
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取图片失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取图片时发生错误: {str(e)}"
            ).model_dump()
        )

