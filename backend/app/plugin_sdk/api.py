"""
VabHub SDK API
PLUGIN-SDK-1 实现
PLUGIN-SDK-2 扩展：宿主服务能力 + 权限模型
PLUGIN-UX-3 扩展：配置客户端
PLUGIN-SAFETY-1 扩展：细粒度权限 + 审计日志
"""

from pathlib import Path
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass

from app.plugin_sdk.context import PluginContext
from app.plugin_sdk.logging import PluginLogger
from app.plugin_sdk.http_client import HttpClient
from app.plugin_sdk.notify import NotifyClient
from app.plugin_sdk.types import PluginCapability

if TYPE_CHECKING:
    from app.plugin_sdk.download import DownloadClient
    from app.plugin_sdk.media import MediaClient
    from app.plugin_sdk.cloud115 import Cloud115Client
    from app.plugin_sdk.config_client import ConfigClient


@dataclass
class PluginEnv:
    """
    插件环境信息
    
    提供主系统版本、基础 URL 等只读信息。
    """
    
    _ctx: PluginContext
    
    @property
    def app_name(self) -> str:
        """应用名称"""
        return "VabHub"
    
    @property
    def app_version(self) -> str:
        """应用版本"""
        return self._ctx.app_version or "unknown"
    
    @property
    def base_url(self) -> str:
        """应用基础 URL"""
        return self._ctx.base_url or "http://localhost:8092"
    
    @property
    def plugin_id(self) -> str:
        """当前插件 ID"""
        return self._ctx.plugin_id
    
    @property
    def plugin_name(self) -> str:
        """当前插件显示名称"""
        return self._ctx.plugin_name
    
    @property
    def debug(self) -> bool:
        """是否为调试模式"""
        try:
            from app.core.config import settings
            return settings.DEBUG
        except Exception:
            return False


@dataclass
class PluginPaths:
    """
    插件路径辅助类
    
    提供插件数据目录、缓存目录等路径访问。
    """
    
    _ctx: PluginContext
    
    @property
    def data_dir(self) -> Path:
        """
        插件数据目录
        
        用于存储插件配置、持久化数据等。
        目录会自动创建。
        """
        self._ctx.data_dir.mkdir(parents=True, exist_ok=True)
        return self._ctx.data_dir
    
    @property
    def cache_dir(self) -> Path:
        """
        插件缓存目录
        
        用于存储临时缓存文件。
        """
        return self._ctx.get_cache_dir()
    
    @property
    def log_dir(self) -> Path:
        """
        插件日志目录
        
        用于存储插件自己的日志文件。
        """
        return self._ctx.get_log_dir()
    
    def config_path(self, filename: str = "config.json") -> Path:
        """获取配置文件路径"""
        return self._ctx.get_config_path(filename)


class VabHubSDK:
    """
    VabHub 插件 SDK 主入口
    
    插件通过此 SDK 访问主系统能力。
    
    Attributes:
        log: 插件专用 Logger
        env: 环境信息（版本、URL 等）
        paths: 路径辅助（数据目录等）
        http: HTTP 客户端
        notify: 通知客户端
        config: 配置客户端（PLUGIN-UX-3）
        download: 下载服务客户端（需要 download.* 权限）
        media: 媒体库查询客户端（需要 media.read 权限）
        cloud115: 115 云存储客户端（需要 cloud115.* 权限）
    
    Example:
        def setup_plugin(ctx: PluginContext, bus: EventBus, sdk: VabHubSDK) -> None:
            sdk.log.info(f"Plugin {sdk.env.plugin_id} loaded!")
            sdk.log.info(f"Data dir: {sdk.paths.data_dir}")
    """
    
    def __init__(
        self,
        ctx: PluginContext,
        sdk_permissions: Optional[list[str]] = None
    ):
        """
        初始化 SDK
        
        Args:
            ctx: 插件上下文
            sdk_permissions: SDK 权限列表（来自 plugin.json 的 sdk_permissions）
        """
        self._ctx = ctx
        
        # PLUGIN-SAFETY-1: 映射旧权限到细粒度权限
        from app.plugin_sdk.types import map_legacy_permissions
        original_permissions = sdk_permissions or []
        mapped_permissions = map_legacy_permissions(original_permissions)
        self._sdk_permissions: set[str] = set(mapped_permissions)
        
        # 记录权限映射警告
        if len(mapped_permissions) > len(original_permissions):
            from app.plugin_sdk.types import is_deprecated_permission, get_permission_suggestion
            for perm in original_permissions:
                if is_deprecated_permission(perm):
                    suggestion = get_permission_suggestion(perm)
                    self.log.warning(f"Deprecated permission '{perm}' detected. {suggestion}")
        
        # 核心能力（无需权限）
        self.log = PluginLogger(ctx.logger_name)
        self.env = PluginEnv(ctx)
        self.paths = PluginPaths(ctx)
        self.http = HttpClient(ctx)
        self.notify = NotifyClient(ctx)
        
        # PLUGIN-UX-3：配置客户端
        from app.plugin_sdk.config_client import ConfigClient
        self.config = ConfigClient(ctx)
        
        # PLUGIN-SDK-2：宿主服务客户端（懒加载）
        self._download: Optional["DownloadClient"] = None
        self._media: Optional["MediaClient"] = None
        self._cloud115: Optional["Cloud115Client"] = None
    
    @property
    def context(self) -> PluginContext:
        """获取插件上下文"""
        return self._ctx
    
    @property
    def permissions(self) -> set[str]:
        """获取插件已声明的 SDK 权限"""
        return self._sdk_permissions.copy()
    
    def has_permission(self, cap: PluginCapability) -> bool:
        """
        检查插件是否拥有指定权限
        
        Args:
            cap: 能力枚举值
            
        Returns:
            是否拥有该权限
        """
        return cap.value in self._sdk_permissions
    
    def _require_capability(self, cap: PluginCapability) -> None:
        """
        要求插件拥有指定能力，否则抛出异常
        
        Args:
            cap: 能力枚举值
            
        Raises:
            PermissionError: 如果插件未声明该能力
        """
        if cap.value not in self._sdk_permissions:
            self.log.error(
                f"Tried to use capability '{cap.value}' without declaring it"
            )
            raise PermissionError(
                f"Plugin '{self._ctx.plugin_id}' is not allowed to use capability '{cap.value}'. "
                f"Please declare it in plugin.json -> sdk_permissions."
            )
    
    def _audit(self, action: str, payload: Optional[dict[str, Any]] = None) -> None:
        """
        记录审计日志（PLUGIN-SAFETY-1）
        
        异步记录，不阻塞主流程
        
        Args:
            action: 操作类型（如 "download.add_task"）
            payload: 操作参数（不含敏感信息）
        """
        try:
            import asyncio
            from app.services.plugin_monitor_service import PluginMonitorService
            from app.core.database import get_async_session
            
            async def record_audit():
                async for session in get_async_session():
                    await PluginMonitorService.record_audit(
                        session,
                        self._ctx.plugin_id,
                        action,
                        payload
                    )
                    break
            
            # 异步记录，不阻塞主流程
            asyncio.create_task(record_audit())
            
        except Exception as e:
            # 审计日志失败不应该影响主流程
            self.log.warning(f"Failed to record audit for {action}: {e}")
    
    # ============== PLUGIN-SDK-2：宿主服务客户端 ==============
    
    @property
    def download(self) -> "DownloadClient":
        """
        下载服务客户端
        
        需要 download.read 或 download.add 权限（PLUGIN-SAFETY-1 细粒度）
        """
        if self._download is None:
            self._require_capability(PluginCapability.DOWNLOAD_READ)  # 至少需要读取权限
            from app.plugin_sdk.download import DownloadClient
            self._download = DownloadClient(self)
        return self._download
    
    @property
    def media(self) -> "MediaClient":
        """
        媒体库查询客户端
        
        需要 media.read 权限
        """
        if self._media is None:
            from app.plugin_sdk.media import MediaClient
            self._media = MediaClient(self)
        return self._media
    
    @property
    def cloud115(self) -> "Cloud115Client":
        """
        115 云存储客户端
        
        需要 cloud115.add_offline 或 cloud115.read 权限（PLUGIN-SAFETY-1 细粒度）
        """
        if self._cloud115 is None:
            from app.plugin_sdk.cloud115 import Cloud115Client
            self._cloud115 = Cloud115Client(self)
        return self._cloud115
    
    async def cleanup(self) -> None:
        """
        清理资源
        
        在插件卸载时调用，释放 HTTP 客户端等资源。
        """
        await self.http.close()


# ============== SDK 实例管理 ==============

# 全局 SDK 实例缓存
_sdk_instances: dict[str, VabHubSDK] = {}


def get_sdk_for_plugin(plugin_id: str) -> Optional[VabHubSDK]:
    """
    获取指定插件的 SDK 实例
    
    Args:
        plugin_id: 插件 ID
        
    Returns:
        SDK 实例，如果不存在则返回 None
    """
    return _sdk_instances.get(plugin_id)


def register_sdk_instance(plugin_id: str, sdk: VabHubSDK) -> None:
    """
    注册 SDK 实例（内部使用）
    
    Args:
        plugin_id: 插件 ID
        sdk: SDK 实例
    """
    _sdk_instances[plugin_id] = sdk


def unregister_sdk_instance(plugin_id: str) -> Optional[VabHubSDK]:
    """
    注销 SDK 实例（内部使用）
    
    Args:
        plugin_id: 插件 ID
        
    Returns:
        被移除的 SDK 实例
    """
    return _sdk_instances.pop(plugin_id, None)


def get_all_sdk_instances() -> dict[str, VabHubSDK]:
    """获取所有 SDK 实例（内部使用）"""
    return _sdk_instances.copy()
