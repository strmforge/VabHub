"""
插件管理API
支持插件热更新
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import json
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, status
from loguru import logger
from pydantic import BaseModel

from app.core.database import get_db
from app.core.plugins.hot_reload import HotReloadManager
from app.core.schemas import BaseResponse, error_response, success_response

router = APIRouter()


class PluginConfigPayload(BaseModel):
    values: Dict[str, Any]


class PluginInstallRequest(BaseModel):
    download_url: Optional[str] = None


REGISTRY_PATH = Path("templates/plugin_registry.json")

# 全局热重载管理器实例
_hot_reload_manager: Optional[HotReloadManager] = None


def get_hot_reload_manager() -> HotReloadManager:
    """获取热重载管理器实例"""
    global _hot_reload_manager
    if _hot_reload_manager is None:
        _hot_reload_manager = HotReloadManager(plugins_dir="plugins")
        _hot_reload_manager.start_watching()
    return _hot_reload_manager


@router.get("/status", response_model=BaseResponse)
async def get_plugin_status():
    """
    获取插件状态
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "hot_reload_enabled": true,
            "loaded_plugins": {...},
            "plugin_states": {...}
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        manager = get_hot_reload_manager()
        
        status_data = {
            "hot_reload_enabled": manager.hot_reload_enabled,
            "loaded_plugins": list(manager.loaded_plugins.keys()),
            "plugin_states": manager.get_all_plugin_status(),
            "plugin_metadata": {
                name: meta.__dict__
                for name, meta in manager.plugin_metadata.items()
            },
        }
        
        return success_response(data=status_data, message="获取插件状态成功")
    except Exception as e:
        logger.error(f"获取插件状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取插件状态时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/reload/{plugin_name}", response_model=BaseResponse)
async def reload_plugin(
    plugin_name: str
):
    """
    手动重载插件
    
    返回统一响应格式：
    {
        "success": true,
        "message": "重载成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        manager = get_hot_reload_manager()
        success = await manager.reload_plugin(plugin_name)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message=f"插件 {plugin_name} 不存在或重载失败"
                ).model_dump()
            )
        
        return success_response(message=f"插件 {plugin_name} 重载成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重载插件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"重载插件时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/load", response_model=BaseResponse)
async def load_plugin(
    plugin_file: str = Body(..., description="插件文件路径")
):
    """
    加载插件
    
    返回统一响应格式：
    {
        "success": true,
        "message": "加载成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        manager = get_hot_reload_manager()
        # 从文件路径提取插件名称
        plugin_name = Path(plugin_file).stem
        success = manager._load_plugin(plugin_name)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="BAD_REQUEST",
                    error_message=f"加载插件失败: {plugin_file}"
                ).model_dump()
            )
        
        return success_response(message="插件加载成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"加载插件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"加载插件时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/unload/{plugin_name}", response_model=BaseResponse)
async def unload_plugin(
    plugin_name: str
):
    """
    卸载插件
    
    返回统一响应格式：
    {
        "success": true,
        "message": "卸载成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        manager = get_hot_reload_manager()
        success = await manager.unload_plugin(plugin_name)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    error_code="NOT_FOUND",
                    error_message=f"插件 {plugin_name} 不存在"
                ).model_dump()
            )
        
        return success_response(message=f"插件 {plugin_name} 卸载成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"卸载插件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"卸载插件时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/list", response_model=BaseResponse)
async def list_plugins():
    """
    列出所有插件
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "plugins": [...],
            "plugin_states": {...}
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        manager = get_hot_reload_manager()
        
        plugin_states = manager.get_all_plugin_status()
        plugin_list: List[Dict[str, Any]] = []

        all_names = set(plugin_states.keys()) | set(manager.loaded_plugins.keys())
        for plugin_name in sorted(all_names):
            plugin_list.append(
                {
                    "name": plugin_name,
                    "loaded": plugin_name in manager.loaded_plugins,
                    "state": plugin_states.get(plugin_name, {}),
                    "metadata": (
                        manager.get_plugin_metadata(plugin_name).__dict__
                        if manager.get_plugin_metadata(plugin_name)
                        else None
                    ),
                }
            )

        return success_response(
            data={
                "plugins": plugin_list,
                "plugin_states": plugin_states
            },
            message="获取插件列表成功"
        )
    except Exception as e:
        logger.error(f"获取插件列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取插件列表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/hot-reload/enable", response_model=BaseResponse)
async def enable_hot_reload():
    """
    启用热更新
    
    返回统一响应格式：
    {
        "success": true,
        "message": "热更新已启用",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        manager = get_hot_reload_manager()
        manager.enable_hot_reload()
        
        return success_response(message="热更新已启用")
    except Exception as e:
        logger.error(f"启用热更新失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"启用热更新时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/hot-reload/disable", response_model=BaseResponse)
async def disable_hot_reload():
    """
    禁用热更新
    
    返回统一响应格式：
    {
        "success": true,
        "message": "热更新已禁用",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        manager = get_hot_reload_manager()
        manager.disable_hot_reload()
        
        return success_response(message="热更新已禁用")
    except Exception as e:
        logger.error(f"禁用热更新失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"禁用热更新时发生错误: {str(e)}"
            ).model_dump()
        )


def _get_config_store_or_404(manager: HotReloadManager, plugin_name: str):
    store = manager.get_config_store(plugin_name)
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                error_code="NOT_FOUND",
                error_message=f"插件 {plugin_name} 未加载或不支持配置",
            ).model_dump(),
        )
    return store


@router.get("/{plugin_name}/config", response_model=BaseResponse)
async def get_plugin_config(plugin_name: str):
    """获取插件配置（以 JSON KV 形式返回）。"""
    try:
        manager = get_hot_reload_manager()
        store = _get_config_store_or_404(manager, plugin_name)
        return success_response(
            data={"values": store.all()},
            message="获取插件配置成功",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"获取插件配置失败: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取插件配置时发生错误: {str(exc)}",
            ).model_dump(),
        )


@router.post("/{plugin_name}/config", response_model=BaseResponse)
async def update_plugin_config(plugin_name: str, payload: PluginConfigPayload):
    """覆盖式更新插件配置。"""
    try:
        manager = get_hot_reload_manager()
        store = _get_config_store_or_404(manager, plugin_name)
        store.set_all(payload.values)
        return success_response(message="插件配置已更新", data={"values": store.all()})
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"更新插件配置失败: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"更新插件配置时发生错误: {str(exc)}",
            ).model_dump(),
        )


def _load_registry_data() -> Dict[str, Any]:
    if REGISTRY_PATH.exists():
        try:
            return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning(f"读取插件注册表失败: {exc}")
    return {"official": [], "community": []}


def _is_host_allowed(host: str, allowed_hosts: List[str]) -> bool:
    if not allowed_hosts:
        return False
    host = host.lower()
    for entry in allowed_hosts:
        pattern = entry.lower().strip()
        if not pattern:
            continue
        if pattern.startswith("*."):
            suffix = pattern[1:]
            if host.endswith(suffix):
                return True
        elif host == pattern:
            return True
    return False


@router.get("/registry", response_model=BaseResponse)
async def get_plugin_registry():
    """
    获取插件注册表
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": {
            "official": [...],
            "community": [...]
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        manager = get_hot_reload_manager()
        
        registry_data = _load_registry_data()
        official_registry = registry_data.get("official", [])
        loaded_plugins = list(manager.loaded_plugins.keys())
        registry = {
            "official": official_registry,
            "community": [
                {
                    "id": plugin_name,
                    "name": manager.plugin_metadata.get(plugin_name, PluginMetadata(
                        id=plugin_name,
                        name=plugin_name,
                        version="unknown",
                        description=f"插件 {plugin_name}"
                    )).name,
                    "version": manager.plugin_metadata.get(plugin_name, PluginMetadata(
                        id=plugin_name,
                        name=plugin_name,
                        version="unknown",
                        description=""
                    )).version,
                    "description": manager.plugin_metadata.get(plugin_name, PluginMetadata(
                        id=plugin_name,
                        name=plugin_name,
                        version="unknown",
                        description=""
                    )).description,
                    "installed": True,
                }
                for plugin_name in loaded_plugins
            ],
        }
        
        return success_response(
            data=registry,
            message="获取插件注册表成功"
        )
    except Exception as e:
        logger.error(f"获取插件注册表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取插件注册表时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/{pid}/install", response_model=BaseResponse)
async def install_plugin(
    pid: str,
    payload: Optional[PluginInstallRequest] = Body(default=None),
    repo_url: Optional[str] = None,
):
    """
    安装插件
    
    返回统一响应格式：
    {
        "success": true,
        "message": "安装成功",
        "data": {
            "plugin_id": "...",
            "installed": true
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        if not settings.PLUGIN_REMOTE_INSTALL_ENABLED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_response(
                    error_code="REMOTE_INSTALL_DISABLED",
                    error_message="已禁用远程插件安装，请在环境变量中启用 PLUGIN_REMOTE_INSTALL_ENABLED",
                ).model_dump(),
            )

        manager = get_hot_reload_manager()

        if pid in manager.loaded_plugins:
            return success_response(
                data={
                    "plugin_id": pid,
                    "installed": True,
                    "message": "插件已存在",
                },
                message="插件已安装",
            )

        registry = _load_registry_data()
        source_url = (
            (payload.download_url if payload and payload.download_url else None)
            or repo_url
        )

        if not source_url:
            for entry in registry.get("official", []):
                if entry.get("id") == pid and entry.get("download_url"):
                    source_url = entry.get("download_url")
                    break

        if not source_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="MISSING_DOWNLOAD_URL",
                    error_message="未提供 download_url，且注册表中未找到对应插件的下载地址",
                ).model_dump(),
            )

        parsed = urlparse(source_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    error_code="INVALID_URL",
                    error_message="仅支持 http/https 下载地址",
                ).model_dump(),
            )

        if not _is_host_allowed(parsed.hostname, settings.PLUGIN_REMOTE_ALLOWED_HOSTS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_response(
                    error_code="HOST_NOT_ALLOWED",
                    error_message="下载地址未在允许的域名列表中，已阻止安装",
                ).model_dump(),
            )

        plugin_path = Path(manager.plugins_dir) / f"{pid}.py"
        plugin_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            async with httpx.AsyncClient(timeout=30.0) as http_client:
                response = await http_client.get(source_url)
                response.raise_for_status()
                content = response.content
                if len(content) > settings.PLUGIN_INSTALL_MAX_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=error_response(
                            error_code="FILE_TOO_LARGE",
                            error_message=f"插件文件过大，超过限制 {settings.PLUGIN_INSTALL_MAX_BYTES} 字节",
                        ).model_dump(),
                    )
                plugin_path.write_bytes(content)

            await manager.reload_plugin(pid)
            return success_response(
                data={"plugin_id": pid, "installed": True},
                message="插件安装成功",
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"安装插件 {pid} 失败: {exc}")
            if plugin_path.exists():
                try:
                    plugin_path.unlink()
                except Exception as cleanup_err:
                    logger.warning(f"清理插件文件失败: {cleanup_err}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_response(
                    error_code="INSTALL_FAILED",
                    error_message=f"安装插件时发生错误: {str(exc)}",
                ).model_dump(),
            )
    except Exception as e:
        logger.error(f"安装插件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"安装插件时发生错误: {str(e)}"
            ).model_dump()
        )

manager = get_hot_reload_manager()
for _plugin_name, _plugin_router in manager.get_rest_routers().items():
    router.include_router(
        _plugin_router,
        prefix=f"/{_plugin_name}",
        tags=[f"插件扩展:{_plugin_name}"],
    )