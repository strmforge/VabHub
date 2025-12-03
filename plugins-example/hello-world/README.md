# Hello World 示例插件

VabHub 插件开发示例，演示如何实现 SearchProvider、Bot 命令和 Workflow 扩展。

## 功能

1. **全局搜索扩展**：当搜索包含 "hello" 的关键词时，返回一条演示结果
2. **Bot 命令扩展**：响应 `/hello` 命令
3. **Workflow 扩展**：一个简单的演示工作流

## 安装

### 方法 1：复制到插件目录

```bash
# 复制整个目录到 PLUGINS_DIR（默认为 backend/plugins）
cp -r plugins-example/hello-world backend/plugins/
```

### 方法 2：Docker 挂载

在 `docker-compose.yml` 中添加卷映射：

```yaml
services:
  vabhub:
    volumes:
      - ./plugins-example/hello-world:/app/plugins/hello-world
```

## 验证

1. **扫描插件**
   - 访问 `/dev/plugins`（插件开发中心）
   - 点击「扫描插件目录」
   - 应该看到 "Hello World 示例插件"

2. **启用插件**
   - 点击「启用」按钮
   - 状态变为「已启用」

3. **测试全局搜索**
   - 在全局搜索框中输入 "hello"
   - 应该看到一条来自插件的搜索结果

4. **测试 Bot 命令**
   - 在 Telegram Bot 中发送 `/hello`
   - 应该收到插件的问候消息

5. **测试 Workflow**
   - 在插件开发中心的 Workflows 标签页
   - 找到 "HelloWorld 演示任务"
   - 点击「执行」，输入任意 JSON payload
   - 应该看到返回结果

## 目录结构

```
hello-world/
├── plugin.json              # 插件清单
├── README.md                # 说明文档
└── backend/
    └── hello_plugin/
        ├── __init__.py      # 包初始化
        └── main.py          # 入口模块
```

## plugin.json 说明

```json
{
  "id": "vabhub.example.hello_world",   // 唯一标识
  "display_name": "Hello World 示例插件", // 显示名称
  "version": "0.1.0",                    // 版本号
  "description": "...",                   // 描述
  "author": "VabHub Team",               // 作者
  "homepage": "https://...",             // 主页 URL
  "backend": {
    "entry_module": "hello_plugin.main"  // Python 入口模块
  },
  "frontend": {
    "entry_point": "dev:hello_plugin"    // 前端入口（预留）
  },
  "capabilities": {
    "search_providers": ["hello_world.sample_search"],
    "bot_commands": ["hello"],
    "workflows": ["hello_world.demo_job"]
  }
}
```

## 开发指南

### 实现 SearchProvider

```python
class MySearchProvider:
    id = "my_plugin.search"
    
    async def search(self, session, query, scope=None, limit=10):
        from app.schemas.global_search import GlobalSearchItem
        # 返回 GlobalSearchItem 列表
        return [...]

def register_plugin(registry):
    registry.register_search_provider("my_plugin", MySearchProvider())
```

### 实现 Bot 命令

```python
class MyBotCommand:
    command = "mycommand"  # 不含斜杠
    
    async def handle(self, ctx):
        await ctx.reply_text("Hello!")

def register_plugin(registry):
    registry.register_bot_command("my_plugin", MyBotCommand())
```

### 实现 Workflow

```python
class MyWorkflow:
    id = "my_plugin.my_job"
    name = "我的任务"
    description = "任务描述"
    
    async def run(self, session, payload=None):
        # 执行任务
        return {"status": "done"}

def register_plugin(registry):
    registry.register_workflow("my_plugin", MyWorkflow())
```

## 注意事项

- 插件运行在 VabHub 同一进程中，没有沙箱隔离
- 插件可以访问 `AsyncSession` 操作数据库，请谨慎使用
- 建议使用延迟导入（在函数内导入）避免循环依赖
- 插件错误会被捕获，不会影响主程序运行

## 许可证

MIT License
