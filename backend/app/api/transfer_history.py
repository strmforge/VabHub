"""
转移历史记录API
参考MoviePilot的实现
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from loguru import logger

from app.core.database import get_db
from app.core.schemas import BaseResponse, success_response, error_response
from app.modules.transfer_history.service import TransferHistoryService
from app.models.transfer_history import TransferHistory

router = APIRouter(prefix="/transfer-history", tags=["转移历史"])


class TransferHistoryResponse(BaseModel):
    """转移历史响应"""
    id: int
    src: str
    dest: str
    src_storage: str
    dest_storage: str
    mode: str
    type: Optional[str] = None
    category: Optional[str] = None
    title: Optional[str] = None
    year: Optional[str] = None
    tmdbid: Optional[int] = None
    seasons: Optional[str] = None
    episodes: Optional[str] = None
    file_size: Optional[int] = None
    status: bool
    errmsg: Optional[str] = None
    date: Optional[str] = None
    created_at: str
    
    class Config:
        from_attributes = True


class TransferHistoryListResponse(BaseModel):
    """转移历史列表响应"""
    list: List[TransferHistoryResponse]
    total: int
    page: int
    count: int


class ManualTransferRequest(BaseModel):
    """手动整理请求"""
    history_id: int = Field(..., description="原始转移历史记录ID")
    
    # 目的相关
    dest_storage: str = Field(..., description="目标存储类型")
    dest_path: str = Field(..., description="目标基础路径")
    operation_mode: Literal["move", "copy", "link", "auto"] = Field(..., description="整理方式")
    
    # 媒体识别相关
    media_type: Literal["auto", "movie", "tv", "anime"] = Field(default="auto", description="媒体类型")
    tmdb_id: Optional[int] = Field(None, description="TMDB ID")
    season: Optional[int] = Field(None, description="季号")
    episodes: Optional[str] = Field(None, description="集范围")
    
    # 规则和选项
    use_classification: bool = Field(default=True, description="按类型分类")
    delete_source: bool = Field(default=False, description="整理完成后删除源文件")
    reuse_history_meta: bool = Field(default=True, description="复用历史识别信息")


class ManualTransferConfigResponse(BaseModel):
    """手动整理配置响应"""
    id: int
    src: str
    dest: str
    src_storage: str
    dest_storage: str
    mode: str
    type: Optional[str] = None
    category: Optional[str] = None
    title: Optional[str] = None
    year: Optional[str] = None
    tmdbid: Optional[int] = None
    seasons: Optional[str] = None
    episodes: Optional[str] = None
    status: bool
    errmsg: Optional[str] = None
    
    class Config:
        from_attributes = True


@router.get("/", response_model=BaseResponse)
async def get_transfer_history(
    title: Optional[str] = Query(None, description="搜索标题（支持模糊搜索）"),
    page: int = Query(1, ge=1, description="页码"),
    count: int = Query(50, ge=1, le=100, description="每页数量"),
    status_filter: Optional[str] = Query(None, description="状态过滤: success/failed"),
    db = Depends(get_db)
):
    """
    查询转移历史记录
    
    支持按标题搜索，支持分页和状态过滤
    """
    try:
        service = TransferHistoryService(db)
        
        # 处理状态过滤
        status_bool = None
        if status_filter == "success":
            status_bool = True
        elif status_filter == "failed":
            status_bool = False
        
        # 如果有标题搜索，使用按标题查询
        if title:
            # 处理特殊关键词
            if title == "失败":
                title = None
                status_bool = False
            elif title == "成功":
                title = None
                status_bool = True
            
            if title:
                histories = await service.list_by_title(title, page, count, status_bool)
                total = await service.count_by_title(title, status_bool)
            else:
                histories = await service.list_by_page(page, count, status_bool)
                total = await service.count(status_bool)
        else:
            histories = await service.list_by_page(page, count, status_bool)
            total = await service.count(status_bool)
        
        return success_response(
            data=TransferHistoryListResponse(
                list=[TransferHistoryResponse.model_validate(h) for h in histories],
                total=total,
                page=page,
                count=count
            ).model_dump(),
            message="获取转移历史成功"
        )
    except Exception as e:
        logger.error(f"获取转移历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取转移历史时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/{history_id}", response_model=BaseResponse)
async def delete_transfer_history(
    history_id: int,
    db = Depends(get_db)
):
    """删除转移历史记录"""
    try:
        service = TransferHistoryService(db)
        success = await service.delete_history(history_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="HISTORY_NOT_FOUND",
                    error_message="转移历史记录不存在"
                ).model_dump()
            )
        
        return success_response(message="删除成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除转移历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除转移历史时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/{history_id}/manual-config", response_model=BaseResponse)
async def get_manual_transfer_config(
    history_id: int,
    db = Depends(get_db)
):
    """
    获取手动整理配置信息
    
    返回指定转移历史记录的基本信息，用于手动整理弹窗的初始填充
    """
    try:
        service = TransferHistoryService(db)
        
        # 查询历史记录
        from sqlalchemy import select
        result = await db.execute(
            select(TransferHistory).where(TransferHistory.id == history_id)
        )
        history = result.scalar_one_or_none()
        
        if not history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="HISTORY_NOT_FOUND",
                    error_message="转移历史记录不存在"
                ).model_dump()
            )
        
        # 返回配置信息
        config_response = ManualTransferConfigResponse.model_validate(history)
        
        return success_response(
            data=config_response.model_dump(),
            message="获取手动整理配置成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取手动整理配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取手动整理配置时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/manual-transfer", response_model=BaseResponse)
async def execute_manual_transfer(
    request: ManualTransferRequest,
    db = Depends(get_db)
):
    """
    执行手动整理
    
    对指定的转移历史记录执行手动整理操作
    """
    try:
        service = TransferHistoryService(db)
        
        # 1. 读取原始 TransferHistory 记录
        from sqlalchemy import select
        result = await db.execute(
            select(TransferHistory).where(TransferHistory.id == request.history_id)
        )
        original_history = result.scalar_one_or_none()
        
        if not original_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="HISTORY_NOT_FOUND",
                    error_message="转移历史记录不存在"
                ).model_dump()
            )
        
        # 2. 构造媒体信息
        media_info = {
            "title": original_history.title,
            "year": original_history.year,
            "type": original_history.type,
            "tmdbid": original_history.tmdbid,
            "imdbid": original_history.imdbid,
            "tvdbid": original_history.tvdbid,
            "doubanid": original_history.doubanid,
            "season": original_history.seasons,
            "episode": original_history.episodes,
            "category": original_history.category
        }
        
        # 3. 用户指定的媒体信息覆盖历史信息
        if request.tmdb_id:
            media_info["tmdbid"] = request.tmdb_id
        if request.media_type != "auto":
            media_info["type"] = request.media_type
        if request.season:
            media_info["season"] = f"S{request.season:02d}"
        if request.episodes:
            media_info["episode"] = request.episodes
        
        # 4. 处理目标路径（如果用户未指定，使用原目标目录）
        from pathlib import Path
        dest_path = request.dest_path
        if not dest_path:
            # 使用原目标路径的父目录作为默认目标目录
            original_dest_path = Path(original_history.dest)
            parent_dir = original_dest_path.parent
            # 安全检查：如果父目录为空或等于根目录，使用原目标目录
            if not parent_dir or str(parent_dir) == str(parent_dir.root):
                dest_path = str(original_dest_path)
            else:
                dest_path = str(parent_dir)
        
        # 5. 构造 DirectoryConfig
        from app.schemas.directory import DirectoryConfig
        directory_config = DirectoryConfig(
            library_path=dest_path,  # 使用处理后的目标路径
            storage=original_history.src_storage,
            library_storage=request.dest_storage,
            transfer_type=request.operation_mode,
            media_type=media_info.get("type"),  # 修复字段映射：media_info 使用 "type" 键
            media_category=media_info.get("category")
        )
        
        # 6. 生成目标路径
        target_path = await _generate_target_path(
            original_history.src,
            dest_path,  # 使用处理后的目标路径
            media_info,
            request.use_classification
        )
        
        # 7. 调用 TransferService 执行整理
        from app.modules.file_operation.transfer_service import TransferService
        transfer_service = TransferService(db)
        
        result = await transfer_service.transfer_file(
            source_path=original_history.src,
            target_path=target_path,
            directory_config=directory_config,
            media_info=media_info if media_info else None
        )
        
        return success_response(
            data={
                "success": result.get("success", False),
                "target_path": target_path,  # 使用已生成的目标路径
                "error": result.get("error")
            },
            message="手动整理完成" if result.get("success") else "手动整理失败"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行手动整理失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"执行手动整理时发生错误: {str(e)}"
            ).model_dump()
        )


async def _generate_target_path(
    source_path: str,
    dest_base_dir: str,
    media_info: dict,
    use_classification: bool
) -> str:
    """
    生成目标文件路径
    """
    try:
        from pathlib import Path
        from app.modules.media_renamer.organizer import MediaOrganizer
        from app.modules.media_renamer.parser import MediaInfo
        from app.core.config import settings
        
        # 创建 MediaOrganizer 实例
        tmdb_api_key = getattr(settings, 'TMDB_API_KEY', None)
        organizer = MediaOrganizer(tmdb_api_key)
        
        # 构造 MediaInfo 对象
        media_info_obj = MediaInfo(
            title=media_info.get("title", "Unknown"),
            year=media_info.get("year"),
            media_type=media_info.get("type", "movie"),  # 修复字段映射：media_info 使用 "type" 键
            season=media_info.get("season"),
            episode=media_info.get("episode")
        )
        
        # 生成新文件名
        new_name = organizer.renamer.generate_name(media_info_obj)
        
        # 获取文件扩展名
        extension = Path(source_path).suffix
        
        # 构建目标路径
        if use_classification:
            # 使用分类器（如果可用）
            try:
                tmdb_data = await organizer.identifier._query_tmdb(media_info_obj)
                media_category = await organizer.classifier.classify(media_info_obj, tmdb_data)
                target_path = organizer._build_target_path(
                    dest_base_dir,
                    media_info_obj,
                    new_name,
                    extension,
                    media_category
                )
            except Exception:
                # 分类失败，使用基础路径
                target_path = organizer._build_target_path(
                    dest_base_dir,
                    media_info_obj,
                    new_name,
                    extension,
                    None
                )
        else:
            # 不使用分类
            target_path = organizer._build_target_path(
                dest_base_dir,
                media_info_obj,
                new_name,
                extension,
                None
            )
        
        return str(target_path)
        
    except Exception as e:
        logger.warning(f"生成目标路径失败，使用基础路径: {e}")
        # 回退到基础路径
        from pathlib import Path
        return str(Path(dest_base_dir) / Path(source_path).name)

