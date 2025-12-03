"""
日志查看器API
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
from loguru import logger

from app.core.schemas import BaseResponse, success_response, error_response
from app.modules.log.service import LogService
from app.core.config import settings

router = APIRouter(prefix="/logs", tags=["日志"])


# 请求/响应模型
class LogEntry(BaseModel):
    """日志条目"""
    timestamp: str
    level: str
    module: str
    function: str
    line: int
    message: str
    source: str
    raw: str


class LogListResponse(BaseModel):
    """日志列表响应"""
    logs: List[LogEntry]
    total: int
    filtered: int
    offset: int
    limit: int


class LogStatisticsResponse(BaseModel):
    """日志统计响应"""
    total: int
    level_counts: dict
    source_counts: dict
    error_count: int
    warning_count: int
    info_count: int


class LogFileInfo(BaseModel):
    """日志文件信息"""
    name: str
    path: str
    size: int
    modified: str
    type: str


@router.get("/files", response_model=BaseResponse)
async def get_log_files():
    """获取所有日志文件"""
    try:
        log_service = LogService()
        log_files = log_service.get_log_files()
        
        return success_response(
            data=[LogFileInfo(**file).model_dump() for file in log_files],
            message="获取日志文件列表成功"
        )
    except Exception as e:
        logger.error(f"获取日志文件列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取日志文件列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/", response_model=BaseResponse)
async def get_logs(
    log_file: Optional[str] = Query(None, description="日志文件名"),
    level: Optional[str] = Query(None, description="日志级别 (TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)"),
    source: Optional[str] = Query(None, description="日志来源（模块名）"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    start_time: Optional[str] = Query(None, description="开始时间 (ISO格式)"),
    end_time: Optional[str] = Query(None, description="结束时间 (ISO格式)"),
    limit: int = Query(1000, description="每页数量", ge=1, le=10000),
    offset: int = Query(0, description="偏移量", ge=0)
):
    """获取日志"""
    try:
        log_service = LogService()
        
        # 解析时间
        start_time_obj = None
        end_time_obj = None
        
        if start_time:
            try:
                start_time_obj = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_response(
                        error_code="INVALID_DATE_FORMAT",
                        error_message="开始时间格式错误，请使用ISO格式"
                    ).model_dump()
                )
        
        if end_time:
            try:
                end_time_obj = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_response(
                        error_code="INVALID_DATE_FORMAT",
                        error_message="结束时间格式错误，请使用ISO格式"
                    ).model_dump()
                )
        
        # 读取日志
        logs_data = log_service.read_logs(
            log_file=log_file,
            level=level,
            source=source,
            keyword=keyword,
            start_time=start_time_obj,
            end_time=end_time_obj,
            limit=limit,
            offset=offset
        )
        
        return success_response(
            data=LogListResponse(**logs_data).model_dump(),
            message="获取日志成功"
        )
        
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                error_code="LOG_FILE_NOT_FOUND",
                error_message=str(e)
            ).model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取日志失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取日志时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/statistics", response_model=BaseResponse)
async def get_log_statistics(
    log_file: Optional[str] = Query(None, description="日志文件名")
):
    """获取日志统计信息"""
    try:
        log_service = LogService()
        statistics = log_service.get_log_statistics(log_file=log_file)
        
        return success_response(
            data=LogStatisticsResponse(**statistics).model_dump(),
            message="获取日志统计成功"
        )
    except Exception as e:
        logger.error(f"获取日志统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取日志统计时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/export")
async def export_logs(
    log_file: Optional[str] = Query(None, description="日志文件名"),
    level: Optional[str] = Query(None, description="日志级别"),
    source: Optional[str] = Query(None, description="日志来源"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    start_time: Optional[str] = Query(None, description="开始时间 (ISO格式)"),
    end_time: Optional[str] = Query(None, description="结束时间 (ISO格式)")
):
    """导出日志"""
    try:
        log_service = LogService()
        
        # 解析时间
        start_time_obj = None
        end_time_obj = None
        
        if start_time:
            try:
                start_time_obj = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_response(
                        error_code="INVALID_DATE_FORMAT",
                        error_message="开始时间格式错误，请使用ISO格式"
                    ).model_dump()
                )
        
        if end_time:
            try:
                end_time_obj = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_response(
                        error_code="INVALID_DATE_FORMAT",
                        error_message="结束时间格式错误，请使用ISO格式"
                    ).model_dump()
                )
        
        # 导出日志
        output_path = log_service.export_logs(
            log_file=log_file,
            level=level,
            source=source,
            keyword=keyword,
            start_time=start_time_obj,
            end_time=end_time_obj
        )
        
        return FileResponse(
            path=output_path,
            filename=output_path.name,
            media_type="text/plain"
        )
        
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                error_code="LOG_FILE_NOT_FOUND",
                error_message=str(e)
            ).model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出日志失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"导出日志时发生错误: {str(e)}"
            ).model_dump()
        )

