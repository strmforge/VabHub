"""
Plugin SDK 公共类型定义

PLUGIN-SDK-1 实现
PLUGIN-SDK-2 扩展：能力枚举
PLUGIN-SAFETY-1 扩展：细粒度权限
"""

from enum import Enum
from typing import Any, TypedDict, Optional, Protocol
from datetime import datetime


# ============== PLUGIN-SDK-2：SDK 能力枚举 ==============

class PluginCapability(str, Enum):
    """
    插件 SDK 能力枚举
    
    插件需要在 plugin.json 的 sdk_permissions 中声明所需能力，
    未声明的能力调用时会被 SDK 拒绝。
    
    命名约定：领域.操作（如 download.add）
    
    PLUGIN-SAFETY-1：支持细粒度权限，同时保持向后兼容
    """
    
    # ============== 下载能力（细粒度） ==============
    DOWNLOAD_ADD = "download.add"        # 创建下载任务（新增，替代 download.write）
    DOWNLOAD_READ = "download.read"      # 查询下载任务状态
    
    # ============== 媒体库能力 ==============
    MEDIA_READ = "media.read"            # 查询媒体库（电影/电视/有声书等）
    
    # ============== 115 云存储能力（细粒度） ==============
    CLOUD115_ADD_OFFLINE = "cloud115.add_offline"  # 创建 115 离线任务（新增，替代 cloud115.task）
    CLOUD115_READ = "cloud115.read"      # 读取 115 目录/文件信息
    
    # ============== TTS 能力（预留） ==============
    TTS_CONTROL = "tts.control"          # 控制 TTS 队列（新增）
    
    # ============== 向后兼容的旧权限（已弃用但仍然支持） ==============
    DOWNLOAD_WRITE = "download.write"    # 创建下载任务（旧版，映射到 download.add + download.read）
    CLOUD115_TASK = "cloud115.task"      # 创建 115 离线任务（旧版，映射到 cloud115.add_offline + cloud115.read）


# ============== PLUGIN-SAFETY-1：权限映射函数 ==============

def map_legacy_permissions(permissions: list[str]) -> list[str]:
    """
    将旧权限映射到新的细粒度权限
    
    Args:
        permissions: 原始权限列表
        
    Returns:
        映射后的权限列表（包含新权限和未映射的旧权限）
    """
    mapped = set(permissions)
    
    # 旧权限映射
    legacy_mappings = {
        PluginCapability.DOWNLOAD_WRITE.value: [
            PluginCapability.DOWNLOAD_ADD.value,
            PluginCapability.DOWNLOAD_READ.value,
        ],
        PluginCapability.CLOUD115_TASK.value: [
            PluginCapability.CLOUD115_ADD_OFFLINE.value,
            PluginCapability.CLOUD115_READ.value,
        ],
    }
    
    for old_perm, new_perms in legacy_mappings.items():
        if old_perm in mapped:
            # 添加新权限
            mapped.update(new_perms)
            # 保留旧权限（向后兼容）
    
    return list(mapped)


def is_deprecated_permission(permission: str) -> bool:
    """
    检查是否为已弃用的权限
    
    Args:
        permission: 权限字符串
        
    Returns:
        是否已弃用
    """
    deprecated = {
        PluginCapability.DOWNLOAD_WRITE.value,
        PluginCapability.CLOUD115_TASK.value,
    }
    return permission in deprecated


def get_permission_suggestion(permission: str) -> Optional[str]:
    """
    获取弃用权限的替换建议
    
    Args:
        permission: 权限字符串
        
    Returns:
        建议的新权限或 None
    """
    suggestions = {
        PluginCapability.DOWNLOAD_WRITE.value: "使用 download.add 创建任务，download.read 查询任务",
        PluginCapability.CLOUD115_TASK.value: "使用 cloud115.add_offline 创建离线任务，cloud115.read 读取目录",
    }
    return suggestions.get(permission)


# 能力分类：安全级别
SAFE_CAPABILITIES = {
    # 这些能力相对安全，不会产生破坏性影响
    PluginCapability.DOWNLOAD_READ,
    PluginCapability.MEDIA_READ,
    PluginCapability.CLOUD115_READ,
}

DANGEROUS_CAPABILITIES = {
    # 这些能力可能产生副作用，需要用户注意
    PluginCapability.DOWNLOAD_WRITE,
    PluginCapability.CLOUD115_TASK,
}


# 能力中文名称映射（用于 UI 显示）
CAPABILITY_LABELS: dict[str, str] = {
    "download.read": "下载（读取）",
    "download.write": "下载（写入）",
    "media.read": "媒体库读取",
    "cloud115.task": "115 离线任务",
    "cloud115.read": "115 目录读取",
}


def get_capability_label(cap: str) -> str:
    """获取能力的中文标签"""
    return CAPABILITY_LABELS.get(cap, cap)


def is_dangerous_capability(cap: str) -> bool:
    """判断是否为危险能力"""
    try:
        return PluginCapability(cap) in DANGEROUS_CAPABILITIES
    except ValueError:
        return False


# ============== PLUGIN-UX-3：插件 API 路由 ==============

class PluginRoute:
    """
    插件路由定义
    
    插件可以通过 get_routes(sdk) 返回此类实例列表来注册自己的 HTTP API。
    
    Example:
        def get_routes(sdk: VabHubSDK) -> list[PluginRoute]:
            async def hello_handler(ctx, body, sdk):
                return {"message": "Hello from plugin!"}
            
            return [
                PluginRoute(
                    path="hello",
                    method="GET",
                    summary="Say hello",
                    handler=hello_handler
                )
            ]
    """
    
    def __init__(
        self,
        path: str,
        method: str = "GET",
        summary: Optional[str] = None,
        handler: Optional[Any] = None,
    ):
        """
        初始化路由
        
        Args:
            path: 路由路径（不含 /api/plugin/{plugin_id}/）
            method: HTTP 方法（GET/POST/PUT/DELETE）
            summary: 路由描述
            handler: 处理函数，签名为 async def handler(ctx, body, sdk)
        """
        self.path = path.lstrip('/')
        self.method = method.upper()
        self.summary = summary
        self.handler = handler


class PluginEnvInfo(TypedDict):
    """插件环境信息"""
    app_name: str
    app_version: str
    base_url: str
    debug: bool


class NotifyPayload(TypedDict, total=False):
    """通知 payload 结构"""
    route_name: Optional[str]
    route_params: Optional[dict[str, Any]]
    extra: Optional[dict[str, Any]]


class HttpResponse(TypedDict):
    """HTTP 响应结构"""
    status_code: int
    headers: dict[str, str]
    text: str
    json: Optional[Any]


class EventPayload(TypedDict, total=False):
    """事件 payload 基础结构"""
    timestamp: str
    source: str
    data: dict[str, Any]
