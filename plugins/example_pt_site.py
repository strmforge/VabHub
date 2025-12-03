"""
示例插件：虚拟 PT 站点演示。
"""

from typing import Dict, Any

from app.core.plugins.spec import PluginMetadata, PluginContext, PluginHooks


PLUGIN_METADATA = PluginMetadata(
    id="example_pt_site",
    name="示例 PT 站点",
    version="0.1.0",
    description="演示如何通过插件向 VabHub 注入 PT 站点逻辑。",
    author="VabHub",
    tags=["demo", "pt"],
)

DEFAULT_CONFIG = {
    "enabled": True,
    "welcome_message": "欢迎使用示例站点插件！",
    "auto_seed": False,
}


def register(context: PluginContext) -> PluginHooks:
    context.config.ensure_defaults(DEFAULT_CONFIG)
    context.logger.info("插件 register() 已执行，默认配置已写入。")

    def _on_startup(ctx: PluginContext) -> None:
        cfg = ctx.config.all()
        ctx.logger.info(
            f"[example_pt_site] on_startup -> enabled={cfg.get('enabled')}, "
            f"welcome={cfg.get('welcome_message')}"
        )

    def _on_shutdown(ctx: PluginContext) -> None:
        ctx.logger.info("[example_pt_site] on_shutdown -> 再见！")

    return PluginHooks(on_startup=_on_startup, on_shutdown=_on_shutdown)

