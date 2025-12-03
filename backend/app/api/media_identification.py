"""
媒体识别相关API - 整合过往版本的媒体识别功能
使用统一响应模型
"""

from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File, Query, status
from typing import List, Optional
from pydantic import BaseModel, Field
from pathlib import Path
from loguru import logger

from app.core.database import get_db
from app.modules.media_identification.service import MediaIdentificationService
from app.core.config import settings
from app.core.schemas import (
    BaseResponse,
    PaginatedResponse,
    NotFoundResponse,
    success_response,
    error_response
)

router = APIRouter()

# 文件上传目录
UPLOAD_DIR = Path(settings.TEMP_PATH) / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class IdentificationRequest(BaseModel):
    """识别请求"""
    file_path: str = Field(..., description="文件路径")


class IdentificationResponse(BaseModel):
    """识别响应"""
    success: bool
    title: Optional[str] = None
    year: Optional[int] = None
    season: Optional[int] = None
    episode: Optional[int] = None
    type: Optional[str] = None
    confidence: float = 0.0
    source: Optional[str] = None
    error: Optional[str] = None
    file_path: Optional[str] = None  # 添加文件路径
    file_name: Optional[str] = None  # 添加原始文件名
    file_size: Optional[int] = None  # 添加文件大小


@router.post("/identify", response_model=BaseResponse)
async def identify_media(
    request: IdentificationRequest,
    db=Depends(get_db)
):
    """
    识别媒体文件
    
    返回统一响应格式：
    {
        "success": true,
        "message": "识别成功",
        "data": IdentificationResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = MediaIdentificationService(db)
        result = await service.identify_media(request.file_path)
        return success_response(data=result, message="识别成功")
    except Exception as e:
        logger.error(f"识别媒体文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"识别媒体文件时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/identify/batch", response_model=BaseResponse)
async def batch_identify_media(
    file_paths: List[str] = Body(..., description="文件路径列表"),
    db=Depends(get_db)
):
    """
    批量识别媒体文件
    
    返回统一响应格式：
    {
        "success": true,
        "message": "批量识别完成",
        "data": {
            "total": 10,
            "results": [...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = MediaIdentificationService(db)
        results = await service.batch_identify(file_paths)
        return success_response(
            data={
                "total": len(results),
                "results": results
            },
            message="批量识别完成"
        )
    except Exception as e:
        logger.error(f"批量识别媒体文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"批量识别媒体文件时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/upload", response_model=BaseResponse)
async def upload_file(
    file: UploadFile = File(...),
    db=Depends(get_db)
):
    """
    上传文件用于识别
    
    返回统一响应格式：
    {
        "success": true,
        "message": "上传并识别成功",
        "data": IdentificationResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        # 检查文件大小
        file_size = 0
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=error_response(
                    error_code="FILE_TOO_LARGE",
                    error_message=f"文件大小超过限制 ({settings.MAX_UPLOAD_SIZE / 1024 / 1024 / 1024:.1f}GB)"
                ).model_dump()
            )
        
        # 保存文件
        file_ext = Path(file.filename).suffix if file.filename else ".tmp"
        saved_filename = f"{file.filename}" if file.filename else f"upload_{file_size}{file_ext}"
        saved_path = UPLOAD_DIR / saved_filename
        
        # 如果文件已存在，添加时间戳
        if saved_path.exists():
            import time
            timestamp = int(time.time())
            saved_filename = f"{Path(file.filename).stem}_{timestamp}{file_ext}" if file.filename else f"upload_{timestamp}{file_ext}"
            saved_path = UPLOAD_DIR / saved_filename
        
        with open(saved_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"文件已上传: {saved_path} ({file_size / 1024 / 1024:.2f}MB)")
        
        # 识别文件
        service = MediaIdentificationService(db)
        result = await service.identify_media(
            file_path=str(saved_path),
            file_name=file.filename,
            file_size=file_size
        )
        
        # 添加文件信息
        result["file_path"] = str(saved_path)
        result["file_name"] = file.filename
        result["file_size"] = file_size
        
        return success_response(data=result, message="上传并识别成功")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"上传文件时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/upload/batch", response_model=BaseResponse)
async def upload_files(
    files: List[UploadFile] = File(..., description="文件列表"),
    db=Depends(get_db)
):
    """
    批量上传文件用于识别
    
    返回统一响应格式：
    {
        "success": true,
        "message": "批量上传并识别完成",
        "data": {
            "total": 10,
            "results": [...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        results = []
        
        for file in files:
            try:
                # 检查文件大小
                file_content = await file.read()
                file_size = len(file_content)
                
                if file_size > settings.MAX_UPLOAD_SIZE:
                    results.append({
                        "file_name": file.filename,
                        "success": False,
                        "error": f"文件大小超过限制 ({settings.MAX_UPLOAD_SIZE / 1024 / 1024 / 1024:.1f}GB)"
                    })
                    continue
                
                # 保存文件
                file_ext = Path(file.filename).suffix if file.filename else ".tmp"
                saved_filename = f"{file.filename}" if file.filename else f"upload_{file_size}{file_ext}"
                saved_path = UPLOAD_DIR / saved_filename
                
                # 如果文件已存在，添加时间戳
                if saved_path.exists():
                    import time
                    timestamp = int(time.time())
                    saved_filename = f"{Path(file.filename).stem}_{timestamp}{file_ext}" if file.filename else f"upload_{timestamp}{file_ext}"
                    saved_path = UPLOAD_DIR / saved_filename
                
                with open(saved_path, "wb") as f:
                    f.write(file_content)
                
                # 识别文件
                service = MediaIdentificationService(db)
                result = await service.identify_media(
                    file_path=str(saved_path),
                    file_name=file.filename,
                    file_size=file_size
                )
                
                # 添加文件信息
                result["file_path"] = str(saved_path)
                result["file_name"] = file.filename
                result["file_size"] = file_size
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"处理文件 {file.filename} 失败: {e}")
                results.append({
                    "file_name": file.filename,
                    "success": False,
                    "error": str(e)
                })
        
        return success_response(
            data={
                "total": len(files),
                "results": results
            },
            message="批量上传并识别完成"
        )
        
    except Exception as e:
        logger.error(f"批量上传文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"批量上传文件时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/history", response_model=BaseResponse)
async def get_identification_history(
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    file_path: Optional[str] = Query(None, description="文件路径过滤"),
    title: Optional[str] = Query(None, description="标题过滤"),
    media_type: Optional[str] = Query(None, description="媒体类型过滤"),
    success: Optional[str] = Query(None, description="成功状态过滤"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    db=Depends(get_db)
):
    """
    获取识别历史记录（支持分页）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "items": [...],
            "total": 100,
            "page": 1,
            "page_size": 50,
            "total_pages": 2
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from datetime import datetime
        
        service = MediaIdentificationService(db)
        
        # 解析日期
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except:
                pass
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except:
                pass
        
        # 计算offset（兼容旧参数）
        if offset > 0:
            page = (offset // page_size) + 1
        
        history = await service.get_history(
            limit=limit,
            offset=(page - 1) * page_size,
            file_path=file_path,
            title=title,
            media_type=media_type,
            success=success,
            start_date=start_dt,
            end_date=end_dt
        )
        
        total = await service.get_history_count(
            file_path=file_path,
            title=title,
            media_type=media_type,
            success=success,
            start_date=start_dt,
            end_date=end_dt
        )
        
        # 使用PaginatedResponse
        paginated_data = PaginatedResponse.create(
            items=history,
            total=total,
            page=page,
            page_size=page_size
        )
        
        return success_response(data=paginated_data.model_dump(), message="获取成功")
    except Exception as e:
        logger.error(f"获取识别历史记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取识别历史记录时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/history/{history_id}", response_model=BaseResponse)
async def get_identification_history_by_id(
    history_id: int,
    db=Depends(get_db)
):
    """
    获取单个识别历史记录
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": HistoryResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = MediaIdentificationService(db)
        history = await service.get_history_by_id(history_id)
        
        if not history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"识别历史记录不存在 (ID: {history_id})"
                ).model_dump()
            )
        
        return success_response(data=history, message="获取成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取识别历史记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取识别历史记录时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/history/{history_id}", response_model=BaseResponse)
async def delete_identification_history(
    history_id: int,
    db=Depends(get_db)
):
    """
    删除识别历史记录
    
    返回统一响应格式：
    {
        "success": true,
        "message": "识别历史记录已删除",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = MediaIdentificationService(db)
        success = await service.delete_history(history_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NotFoundResponse(
                    error_code="NOT_FOUND",
                    error_message=f"识别历史记录不存在 (ID: {history_id})"
                ).model_dump()
            )
        
        return success_response(message="识别历史记录已删除")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除识别历史记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"删除识别历史记录时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/history", response_model=BaseResponse)
async def clear_identification_history(
    days: Optional[int] = Query(None, description="清理多少天前的记录"),
    db=Depends(get_db)
):
    """
    清理识别历史记录
    
    返回统一响应格式：
    {
        "success": true,
        "message": "清理完成，删除了 X 条记录",
        "data": {
            "deleted_count": 10
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = MediaIdentificationService(db)
        deleted_count = await service.clear_history(days=days)
        
        return success_response(
            data={"deleted_count": deleted_count},
            message=f"清理完成，删除了 {deleted_count} 条记录"
        )
    except Exception as e:
        logger.error(f"清理识别历史记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"清理识别历史记录时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/history/statistics", response_model=BaseResponse)
async def get_identification_statistics(
    db=Depends(get_db)
):
    """
    获取识别历史统计信息
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {statistics_dict},
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        service = MediaIdentificationService(db)
        statistics = await service.get_statistics()
        
        return success_response(data=statistics, message="获取成功")
    except Exception as e:
        logger.error(f"获取识别历史统计信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取识别历史统计信息时发生错误: {str(e)}"
            ).model_dump()
        )

