"""
VabHub PT 插件模板

由脚手架脚本自动生成，可根据站点需求进一步扩展。
"""

from __future__ import annotations

from app.core.plugins.spec import PluginContext, PluginHooks, PluginMetadata


PLUGIN_METADATA = PluginMetadata(
    id="{{PLUGIN_ID}}",
    name="{{PLUGIN_NAME}}",
    version="{{PLUGIN_VERSION}}",
    description="{{PLUGIN_DESCRIPTION}}",
    author="{{PLUGIN_AUTHOR}}",
    tags=["pt", "demo"],
)

DEFAULT_CONFIG = {
    "enabled": True,
    "site_url": "https://example-pt-site.invalid",
    "auth_cookie": "your_cookie_here",
    "category_mapping": {
        "movie": "201",
        "tv": "202",
    },
}


def register(context: PluginContext) -> PluginHooks:
    """
    插件入口：在此写入默认配置、注册事件或初始化资源。
    """

    context.config.ensure_defaults(DEFAULT_CONFIG)

    def on_startup(ctx: PluginContext) -> None:
        cfg = ctx.config.all()
        ctx.logger.info(
            "[%s] 插件启动，enabled=%s site=%s",
            PLUGIN_METADATA.id,
            cfg.get("enabled"),
            cfg.get("site_url"),
        )

    def on_shutdown(ctx: PluginContext) -> None:
        ctx.logger.info("[%s] 插件关闭", PLUGIN_METADATA.id)

    return PluginHooks(on_startup=on_startup, on_shutdown=on_shutdown)


