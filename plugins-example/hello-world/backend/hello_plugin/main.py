"""
Hello World 示例插件 - 入口模块
DEV-SDK-1/2 示例

演示如何实现：
- SearchProvider：全局搜索扩展
- BotCommandExtension：Telegram Bot 命令扩展
- WorkflowExtension：工作流扩展
- PluginPanelProvider：UI 面板数据提供
"""

import asyncio
from typing import Any, Optional, Iterable

from sqlalchemy.ext.asyncio import AsyncSession

# 注意：以下导入假设插件在 VabHub 环境中运行
# 插件开发者需要确保这些模块可用


# ============== Search Provider ==============

class HelloSearchProvider:
    """
    示例搜索提供者
    
    当用户搜索包含 "hello" 的关键词时，返回一条演示结果
    """
    id = "hello_world.sample_search"
    
    async def search(
        self,
        session: AsyncSession,
        query: str,
        scope: Optional[str] = None,
        limit: int = 10,
    ) -> Iterable[Any]:
        """执行搜索"""
        # 只有当查询包含 "hello" 时才返回结果
        if "hello" not in query.lower():
            return []
        
        # 延迟导入，避免在插件加载时就依赖 VabHub 模块
        from app.schemas.global_search import GlobalSearchItem
        
        return [
            GlobalSearchItem(
                media_type="plugin",
                id="hello_world_result",
                title="来自 HelloWorld 插件的搜索结果",
                sub_title=f"你搜索了：{query}",
                cover_url=None,
                route_name="PluginDevCenter",
                route_params={},
            )
        ]


# ============== Bot Command Extension ==============

class HelloBotCommand:
    """
    示例 Bot 命令
    
    响应 /hello 命令
    """
    command = "hello"
    
    async def handle(self, ctx: Any) -> None:
        """处理 /hello 命令"""
        user_name = ctx.user.username if ctx.user else "朋友"
        
        await ctx.reply_text(
            f"👋 你好，{user_name}！\n\n"
            f"这是来自 **HelloWorld 插件** 的问候。\n"
            f"插件系统工作正常！"
        )


# ============== Workflow Extension ==============

class HelloDemoWorkflow:
    """
    示例工作流
    
    演示一个简单的异步任务
    """
    id = "hello_world.demo_job"
    name = "HelloWorld 演示任务"
    description = "一个简单的演示工作流，会等待 1 秒然后返回 payload 内容"
    
    async def run(
        self,
        session: AsyncSession,
        payload: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """执行工作流"""
        # 模拟一些处理时间
        await asyncio.sleep(1)
        
        return {
            "message": "Hello from HelloWorld workflow!",
            "echo": payload or {},
            "status": "completed",
        }


# ============== Panel Provider ==============

class HelloWorldPanelProvider:
    """
    示例面板数据提供者
    
    为 ui_panels 中声明的面板提供数据
    """
    
    def get_panel_data(self, panel_id: str, context: dict[str, Any]) -> dict[str, Any]:
        """获取面板数据"""
        if panel_id == "hello_metrics":
            return self._get_metrics_data(context)
        elif panel_id == "hello_info":
            return self._get_info_data(context)
        else:
            return {"error": f"Unknown panel: {panel_id}"}
    
    def _get_metrics_data(self, context: dict[str, Any]) -> dict[str, Any]:
        """返回 metric_grid 数据"""
        return {
            "cards": [
                {
                    "label": "示例专辑",
                    "value": 42,
                    "unit": "个",
                    "icon": "mdi-album",
                    "color": "blue"
                },
                {
                    "label": "示例任务",
                    "value": 8,
                    "unit": "个",
                    "icon": "mdi-rocket",
                    "color": "orange"
                },
                {
                    "label": "插件版本",
                    "value": "0.2.0",
                    "unit": "",
                    "icon": "mdi-puzzle",
                    "color": "green"
                }
            ]
        }
    
    def _get_info_data(self, context: dict[str, Any]) -> dict[str, Any]:
        """返回 markdown 数据"""
        username = context.get("username", "访客")
        return {
            "content": f"""# Hello World 插件

你好，**{username}**！这是来自 Hello World 示例插件的信息面板。

## 功能

- **搜索扩展**：搜索 "hello" 可以看到插件结果
- **Bot 命令**：发送 `/hello` 给 Telegram Bot
- **Workflow**：在 Workflows 标签页执行演示任务
- **UI 面板**：你正在看的就是！

## 插件信息

- 版本：0.2.0
- 作者：VabHub Team
"""
        }


# ============== 插件注册入口 ==============

def register_plugin(registry: Any) -> None:
    """
    插件注册函数
    
    这是插件的入口点，VabHub 会在加载插件时调用此函数。
    
    Args:
        registry: PluginRegistry 实例，用于注册扩展点
    """
    plugin_id = "vabhub.example.hello_world"
    
    # 注册搜索提供者
    registry.register_search_provider(plugin_id, HelloSearchProvider())
    
    # 注册 Bot 命令
    registry.register_bot_command(plugin_id, HelloBotCommand())
    
    # 注册工作流
    registry.register_workflow(plugin_id, HelloDemoWorkflow())
    
    # 注册面板数据提供者
    registry.register_panel_provider(plugin_id, HelloWorldPanelProvider())
