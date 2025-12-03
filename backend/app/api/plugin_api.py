"""
插件对外 HTTP API
PLUGIN-UX-3 实现

提供插件自定义 API 的路由挂载
路由格式：/api/plugin/{plugin_id}/{path}
"""

from typing import Any, Callable, Awaitable, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from loguru import logger

from app.core.database import get_session
from app.core.auth import require_admin
from app.models.user import User
from app.services.plugin_registry import get_plugin_registry


router = APIRouter(prefix="/plugin", tags=["plugin-api"])


class PluginRoute(BaseModel):
    """插件路由定义"""
    path: str           # 不含 /api/plugin/{plugin_id}
    method: str         # GET/POST/PUT/DELETE
    summary: Optional[str] = None
    # handler 不能序列化，仅用于运行时


@router.api_route(
    "/{plugin_id}/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    summary="插件 API 代理",
)
async def plugin_api_proxy(
    plugin_id: str,
    path: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """
    代理插件 API 请求
    
    将请求转发到插件注册的 handler。
    默认仅允许管理员调用。
    """
    registry = get_plugin_registry()
    
    # 检查插件是否加载
    loaded = registry.loaded_plugins.get(plugin_id)
    if not loaded:
        raise HTTPException(status_code=404, detail=f"插件未加载: {plugin_id}")
    
    if not loaded.has_routes:
        raise HTTPException(status_code=404, detail=f"插件未注册任何路由: {plugin_id}")
    
    # 匹配路由
    method = request.method.upper()
    matched_route = None
    
    for route in loaded.routes:
        route_path = getattr(route, 'path', '').lstrip('/')
        route_method = getattr(route, 'method', 'GET').upper()
        
        if route_path == path and route_method == method:
            matched_route = route
            break
    
    if not matched_route:
        raise HTTPException(
            status_code=404,
            detail=f"路由不存在: {method} /api/plugin/{plugin_id}/{path}"
        )
    
    # 获取 handler
    handler = getattr(matched_route, 'handler', None)
    if not callable(handler):
        raise HTTPException(status_code=500, detail="路由 handler 无效")
    
    # 调用 handler
    try:
        # 准备上下文
        ctx = {
            "request": request,
            "user_id": current_user.id,
            "username": current_user.username,
            "session": session,
        }
        
        # 获取请求数据
        if method in ("POST", "PUT"):
            try:
                body = await request.json()
            except Exception:
                body = {}
        else:
            body = dict(request.query_params)
        
        # 调用插件 handler
        result = await handler(ctx, body, loaded.sdk)
        
        # 返回结果
        if isinstance(result, dict):
            return JSONResponse(content={"success": True, "data": result})
        else:
            return JSONResponse(content={"success": True, "data": str(result)})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[plugin-api] {plugin_id}/{path} error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{plugin_id}",
    summary="列出插件 API 路由",
)
async def list_plugin_routes(
    plugin_id: str,
    current_user: User = Depends(require_admin),
):
    """
    列出插件注册的所有 API 路由
    """
    registry = get_plugin_registry()
    
    loaded = registry.loaded_plugins.get(plugin_id)
    if not loaded:
        raise HTTPException(status_code=404, detail=f"插件未加载: {plugin_id}")
    
    routes = []
    for route in loaded.routes:
        routes.append({
            "path": f"/api/plugin/{plugin_id}/{getattr(route, 'path', '').lstrip('/')}",
            "method": getattr(route, 'method', 'GET').upper(),
            "summary": getattr(route, 'summary', None),
        })
    
    return {"success": True, "data": routes}
