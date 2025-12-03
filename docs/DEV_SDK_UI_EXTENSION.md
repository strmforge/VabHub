# VabHub 插件 UI 扩展指南

## 概述

DEV-SDK-2 允许插件在 VabHub 的 Web 界面中添加自定义面板，无需编写前端代码。插件只需在 `plugin.json` 中声明面板配置，并在后端提供数据，前端会自动渲染。

## 面板位置 (Placement)

| 位置 ID | 说明 | 页面 |
|---------|------|------|
| `home_dashboard` | 首页仪表盘 | `/` |
| `admin_dashboard` | 管理员面板 | `/admin` |
| `task_center` | 任务中心 | `/tasks` |
| `reading_center` | 阅读中心 | `/reading` |
| `dev_plugin` | 插件开发中心 | `/dev/plugins` |
| `custom` | 自定义 | - |

## 面板类型 (Type)

### metric_grid

多个统计卡片，适合展示关键指标。

**payload 格式：**
```json
{
  "cards": [
    {
      "label": "用户数",
      "value": 1234,
      "unit": "人",
      "icon": "mdi-account",
      "color": "blue",
      "trend": "up"  // 可选: up, down, flat
    }
  ]
}
```

### list

表格/列表数据。

**payload 格式：**
```json
{
  "columns": [
    { "key": "name", "title": "名称", "width": 200 },
    { "key": "status", "title": "状态", "align": "center" }
  ],
  "rows": [
    { "name": "项目A", "status": "正常" }
  ],
  "total": 100
}
```

### markdown

Markdown 格式的文本内容。

**payload 格式：**
```json
{
  "content": "# 标题\n\n这是 **Markdown** 内容。"
}
```

### status_card

单个状态卡片。

**payload 格式：**
```json
{
  "status": "ok",  // ok, warning, error, unknown
  "message": "服务运行正常",
  "icon": "mdi-check-circle",  // 可选
  "details": {  // 可选
    "uptime": "99.9%"
  }
}
```

### log_stream

日志流展示。

**payload 格式：**
```json
{
  "entries": [
    {
      "timestamp": "2024-01-01T12:00:00Z",
      "level": "info",  // info, warn, error, debug
      "message": "日志内容"
    }
  ]
}
```

## plugin.json 配置

```json
{
  "id": "my_plugin",
  "ui_panels": [
    {
      "id": "my_metrics",
      "title": "我的指标",
      "description": "展示一些统计数据",
      "placement": "home_dashboard",
      "type": "metric_grid",
      "order": 10,
      "enabled_by_default": true,
      "config": {
        "cols": 3
      }
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 面板唯一 ID |
| `title` | string | 是 | 显示标题 |
| `description` | string | 否 | 描述文字 |
| `placement` | string | 是 | 放置位置 |
| `type` | string | 是 | 面板类型 |
| `order` | number | 否 | 排序权重（默认 100） |
| `enabled_by_default` | boolean | 否 | 默认启用（默认 true） |
| `config` | object | 否 | 渲染配置 |

## 后端实现

### 实现 PanelProvider

```python
class MyPanelProvider:
    def get_panel_data(self, panel_id: str, context: dict) -> dict:
        """
        返回面板数据
        
        Args:
            panel_id: 面板 ID（plugin.json 中声明的）
            context: 上下文信息，包含 user_id, username 等
            
        Returns:
            面板数据，格式由面板类型决定
        """
        if panel_id == "my_metrics":
            return {
                "cards": [
                    {"label": "计数", "value": 42, "icon": "mdi-counter"}
                ]
            }
        return {}
```

### 注册 Provider

```python
def register_plugin(registry):
    plugin_id = "my_plugin"
    registry.register_panel_provider(plugin_id, MyPanelProvider())
```

## API 端点

### 列出面板

```
GET /api/plugin_panels?placement=home_dashboard
```

**响应：**
```json
[
  {
    "plugin_id": "my_plugin",
    "plugin_name": "我的插件",
    "panel": {
      "id": "my_metrics",
      "title": "我的指标",
      "type": "metric_grid",
      ...
    }
  }
]
```

### 获取面板数据

```
GET /api/plugin_panels/{plugin_id}/{panel_id}/data
```

**响应：**
```json
{
  "type": "metric_grid",
  "meta": {},
  "payload": {
    "cards": [...]
  }
}
```

## 完整示例

参考 `plugins-example/hello-world/` 目录：

- `plugin.json`：包含 `ui_panels` 配置
- `backend/hello_plugin/main.py`：包含 `HelloWorldPanelProvider`

## 注意事项

1. **面板 ID 唯一性**：同一插件内的面板 ID 必须唯一
2. **数据格式**：确保返回的数据格式与面板类型匹配
3. **错误处理**：如果数据获取失败，前端会显示错误信息
4. **性能**：面板数据会在页面加载时获取，避免耗时操作
5. **刷新**：用户可以点击刷新按钮重新获取面板数据
