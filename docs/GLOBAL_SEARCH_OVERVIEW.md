# 全局搜索概述

> SEARCH-1 实现文档

## 概念

全局搜索（Command Palette）提供跨媒体类型的即时搜索功能，通过 Ctrl+K 快捷键触发，支持搜索小说、漫画、音乐等内容并直接跳转。

## 功能特性

### 快捷键
- `Ctrl+K` / `Cmd+K`：打开/关闭搜索对话框
- `ESC`：关闭
- `↑↓`：导航结果
- `Enter`：选择当前项

### 搜索范围
- 小说/电子书：标题、作者、系列
- 漫画：标题、作者
- 音乐：标题、艺人、专辑

### 结果展示
- 按媒体类型分组
- 显示封面、标题、副标题
- 每种类型最多显示 5 条结果

### 跳转行为
- 小说 → WorkDetail 页面
- 漫画 → MangaReaderPage 页面
- 音乐 → MusicCenter 页面

## 后端 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/search/global` | 全局搜索 |

### 查询参数

- `q`: 搜索关键词（必填）
- `limit_per_type`: 每种类型最多返回数量（默认 5）

### 响应结构

```typescript
interface GlobalSearchResponse {
  items: GlobalSearchItem[]
}

interface GlobalSearchItem {
  media_type: string
  id: string
  title: string
  sub_title?: string
  cover_url?: string
  route_name?: string
  route_params?: Record<string, any>
}
```

## 前端组件

| 组件 | 说明 |
|------|------|
| `GlobalSearchDialog.vue` | 搜索对话框（已更新为 Command Palette 样式） |
| `CommandPalette.vue` | 独立的 Command Palette 组件（备用） |

## 文件清单

### 后端
- `backend/app/schemas/global_search.py` - DTO 定义
- `backend/app/services/global_search_service.py` - 搜索服务
- `backend/app/api/global_search.py` - API 路由

### 前端
- `frontend/src/types/globalSearch.ts` - 类型定义
- `frontend/src/components/common/GlobalSearchDialog.vue` - 搜索对话框
- `frontend/src/services/api.ts` - `globalSearchApi`
