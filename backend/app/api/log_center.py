"""
实时日志中心API
提供WebSocket实时日志推送、日志查询、导出等功能
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger

from app.modules.log_center.service import get_log_center, LogLevel, LogSource
from app.core.schemas import (
    BaseResponse,
    success_response,
    error_response
)

router = APIRouter(prefix="/log-center", tags=["实时日志中心"])


class LogQueryRequest(BaseModel):
    """日志查询请求"""
    level: Optional[str] = None
    source: Optional[str] = None
    component: Optional[str] = None
    keyword: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 1000


class LogStatisticsResponse(BaseModel):
    """日志统计响应"""
    total: int
    by_level: dict
    by_source: dict
    error_count: int
    warning_count: int


@router.websocket("/ws/logs")
async def websocket_logs(
    websocket: WebSocket,
    level: Optional[str] = Query(None, description="日志级别过滤（逗号分隔，如：ERROR,WARNING）"),
    source: Optional[str] = Query(None, description="日志来源过滤（逗号分隔，如：core,api）"),
    component: Optional[str] = Query(None, description="组件过滤（逗号分隔）"),
    keyword: Optional[str] = Query(None, description="关键词过滤")
):
    """
    WebSocket实时日志推送端点
    
    支持查询参数过滤：
    - level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
    - source: 日志来源（core, plugin, downloader, media_server, scheduler, api）
    - component: 组件名称
    - keyword: 关键词搜索
    """
    await websocket.accept()
    
    log_center = get_log_center()
    
    # 准备过滤器
    filters = {}
    if level:
        filters["level"] = [l.strip().upper() for l in level.split(",")]
    if source:
        filters["source"] = [s.strip().lower() for s in source.split(",")]
    if component:
        filters["component"] = [c.strip() for c in component.split(",")]
    if keyword:
        filters["keyword"] = keyword
    
    try:
        # 添加到日志中心
        await log_center.add_websocket(websocket, filters)
        
        # 发送连接成功消息
        import json
        await websocket.send_text(json.dumps({
            "type": "connection",
            "status": "connected",
            "message": "实时日志连接已建立",
            "filters": filters
        }, ensure_ascii=False))
        
        # 发送最近100条日志（如果符合过滤器）
        recent_logs = await log_center.get_logs(limit=100, **filters)
        for log_entry in reversed(recent_logs):  # 从旧到新发送
            await websocket.send_text(json.dumps({
                "type": "log_entry",
                "data": log_entry
            }, ensure_ascii=False, default=str))
        
        # 保持连接，处理客户端消息
        import json
        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)
                
                if data.get("type") == "update_filters":
                    # 更新过滤器
                    new_filters = data.get("filters", {})
                    log_center.update_filters(websocket, new_filters)
                    
                    await websocket.send_text(json.dumps({
                        "type": "filters_updated",
                        "filters": new_filters
                    }, ensure_ascii=False))
                
                elif data.get("type") == "ping":
                    # 心跳消息
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }, ensure_ascii=False))
                
                elif data.get("type") == "clear_logs":
                    # 清空日志（仅限管理员）
                    # TODO: 添加权限检查
                    await log_center.clear_entries()
                    
                    await websocket.send_text(json.dumps({
                        "type": "logs_cleared",
                        "message": "日志已清空"
                    }, ensure_ascii=False))
                
            except json.JSONDecodeError:
                # 忽略无效的JSON消息
                pass
            except Exception as e:
                logger.error(f"处理WebSocket消息失败: {e}")
    
    except WebSocketDisconnect:
        await log_center.remove_websocket(websocket)
        logger.info("WebSocket日志连接已断开")
    except Exception as e:
        logger.error(f"WebSocket日志连接错误: {e}")
        await log_center.remove_websocket(websocket)


@router.post("/query", response_model=BaseResponse)
async def query_logs(request: LogQueryRequest):
    """
    查询日志
    
    返回统一响应格式：
    {
        "success": true,
        "message": "查询成功",
        "data": {
            "logs": [...],
            "total": 100
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        log_center = get_log_center()
        
        logs = await log_center.get_logs(
            level=request.level,
            source=request.source,
            component=request.component,
            keyword=request.keyword,
            start_time=request.start_time,
            end_time=request.end_time,
            limit=request.limit
        )
        
        return success_response(
            data={
                "logs": logs,
                "total": len(logs)
            },
            message="查询成功"
        )
    except Exception as e:
        logger.error(f"查询日志失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"查询日志时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/statistics", response_model=BaseResponse)
async def get_log_statistics(
    hours: int = Query(24, ge=1, le=168, description="统计时间范围（小时）")
):
    """
    获取日志统计信息
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "total": 1000,
            "by_level": {...},
            "by_source": {...},
            "error_count": 10,
            "warning_count": 50
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        log_center = get_log_center()
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        stats = await log_center.get_statistics(
            start_time=start_time,
            end_time=end_time
        )
        
        return success_response(
            data=stats,
            message="获取统计信息成功"
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
    level: Optional[str] = Query(None, description="日志级别过滤"),
    source: Optional[str] = Query(None, description="日志来源过滤"),
    component: Optional[str] = Query(None, description="组件过滤"),
    keyword: Optional[str] = Query(None, description="关键词过滤"),
    hours: int = Query(24, ge=1, le=168, description="导出时间范围（小时）"),
    format: str = Query("text", description="导出格式：text, json, csv")
):
    """
    导出日志
    
    返回文件流
    """
    try:
        log_center = get_log_center()
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        content = await log_center.export_logs(
            level=level,
            source=source,
            component=component,
            keyword=keyword,
            start_time=start_time,
            end_time=end_time,
            format=format
        )
        
        # 确定文件扩展名和MIME类型
        if format == "json":
            media_type = "application/json"
            filename = f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        elif format == "csv":
            media_type = "text/csv"
            filename = f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        else:
            media_type = "text/plain"
            filename = f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        return StreamingResponse(
            iter([content]),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        logger.error(f"导出日志失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"导出日志时发生错误: {str(e)}"
            ).model_dump()
        )


@router.delete("/clear", response_model=BaseResponse)
async def clear_logs():
    """
    清空日志（仅限管理员）
    
    返回统一响应格式：
    {
        "success": true,
        "message": "日志已清空",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        # TODO: 添加权限检查（仅管理员）
        log_center = get_log_center()
        await log_center.clear_entries()
        
        return success_response(message="日志已清空")
    except Exception as e:
        logger.error(f"清空日志失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"清空日志时发生错误: {str(e)}"
            ).model_dump()
        )

