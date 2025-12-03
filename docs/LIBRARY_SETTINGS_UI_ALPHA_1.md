# LIBRARY-SETTINGS-UI-ALPHA-1 完成文档

## 概述

实现了"媒体库 & Inbox 设置总览"的后端 API + 前端页面，用于**只读展示**当前配置和健康状态。当前阶段不支持修改配置（修改功能留给后续 Phase）。

## 后端实现

### API 端点

**路径**: `/api/admin/settings/library`

**方法**: `GET`

**响应模型**: `LibrarySettingsResponse`

#### 响应结构

```python
{
  "inbox": {
    "inbox_root": str,              # INBOX_ROOT 配置值
    "enabled": bool,                 # 是否启用（任意一个 INBOX_ENABLE_* 为 True）
    "enabled_media_types": List[str], # 启用的媒体类型列表（"video", "ebook", "audiobook", "novel_txt", "comic", "music"）
    "detection_min_score": float,     # INBOX_DETECTION_MIN_SCORE
    "scan_max_items": int,           # INBOX_SCAN_MAX_ITEMS
    "last_run_at": str | null,        # 最近一次运行时间（ISO 格式）
    "last_run_status": str,          # "never" | "success" | "partial" | "failed" | "empty"
    "last_run_summary": str | null,   # 最近一次运行的摘要信息
    "pending_warning": str | null     # "never_run" | "last_run_failed" | "too_long_without_run" | null
  },
  "library_roots": {
    "movie": str,                    # MOVIE_LIBRARY_ROOT
    "tv": str,                       # TV_LIBRARY_ROOT
    "anime": str,                    # ANIME_LIBRARY_ROOT
    "short_drama": str | null,       # SHORT_DRAMA_LIBRARY_ROOT（可选）
    "ebook": str,                    # EBOOK_LIBRARY_ROOT
    "comic": str | null,             # COMIC_LIBRARY_ROOT（可选）
    "music": str | null              # MUSIC_LIBRARY_ROOT（可选）
  }
}
```

#### 字段说明

**Inbox 部分**:
- `inbox_root`: 统一待整理目录路径
- `enabled`: 当任意一个 `INBOX_ENABLE_*` 为 `True` 时，此字段为 `True`
- `enabled_media_types`: 收集所有值为 `True` 的类型名
- `detection_min_score`: 检测阈值，低于此值的结果判为 unknown
- `scan_max_items`: 一次扫描的最大项目数限制
- `last_run_at`: 最近一次 Inbox 运行的时间（从 `InboxRunLog` 表查询）
- `last_run_status`: 最近一次运行的状态
- `last_run_summary`: 最近一次运行的摘要信息（来自 `InboxRunLog.message`）
- `pending_warning`: 待处理警告
  - `never_run`: 已启用但从未运行过 run-once
  - `last_run_failed`: 最近一次 Inbox 处理失败
  - `too_long_without_run`: 超过 24 小时未运行 run-once

**Library Roots 部分**:
- 所有字段对应 `app/core/config.py` 中的相应配置项
- `short_drama`、`comic`、`music` 为可选字段，可能为 `null`

### 代码组织

1. **Schema 定义**: `app/schemas/library.py`
   - `InboxSettings`
   - `LibraryRootsSettings`
   - `LibrarySettingsResponse`

2. **API 实现**: `app/api/admin_library_settings.py`
   - `get_library_settings()`: 主接口函数
   - 复用 `app/api/smart_health.py` 中的 `get_inbox_health()` helper 函数

3. **Helper 函数**: `app/api/smart_health.py`
   - `get_inbox_health()`: 提取的通用函数，用于获取 Inbox 健康状态

4. **路由注册**: `app/api/__init__.py`
   - 注册到 `/api/admin/settings/library`

### 测试

**测试文件**: `tests/test_admin_library_settings_api.py`

**测试用例**:
- `test_get_library_settings_basic`: 基本配置返回测试
- `test_get_library_settings_inbox_enabled_types`: 不同 INBOX_ENABLE_* 配置测试
- `test_get_library_settings_inbox_all_disabled`: 所有类型禁用测试
- `test_get_library_settings_inbox_last_run_info`: InboxRunLog 查询测试
- `test_get_library_settings_inbox_last_run_failed`: 运行失败情况测试
- `test_get_library_settings_library_roots_optional_fields`: 可选字段测试

## 前端实现

### 页面路径

**路由**: `/dev/library-settings`

**组件**: `src/pages/DevLibrarySettings.vue`

### 页面内容

页面以卡片形式展示以下信息：

#### 1. 收件箱（Inbox）配置卡片

显示：
- **INBOX_ROOT**: 统一待整理目录路径
- **启用状态**: "已启用" / "未启用"（带颜色标识）
- **启用的媒体类型**: 用 chips 展示（电影/剧集/动漫/电子书/有声书/漫画/音乐）
- **检测阈值**: `detection_min_score`
- **扫描最大项目数**: `scan_max_items`
- **最近运行状态**: 用颜色区分
  - `success` / `empty`: 绿色
  - `partial`: 黄色
  - `failed` / `never`: 红色/灰色
- **最近运行时间**: 显示相对时间（如"2小时前"）和绝对时间
- **运行摘要**: `last_run_summary`
- **警告**: 若有 `pending_warning`，显示警告图标和中文提示
- **快捷链接**: "查看收件箱预览" 按钮（跳转到 `/dev/inbox-preview`）

#### 2. 视频库根目录卡片

显示：
- **MOVIE_LIBRARY_ROOT**
- **TV_LIBRARY_ROOT**
- **ANIME_LIBRARY_ROOT**
- **SHORT_DRAMA_LIBRARY_ROOT**: 为空时标注"未单独配置，默认继承电视剧库"

#### 3. 书籍/有声书/漫画/音乐库根卡片

显示：
- **EBOOK_LIBRARY_ROOT**
- **COMIC_LIBRARY_ROOT**: 为空时标记为"未配置"
- **MUSIC_LIBRARY_ROOT**: 为空时标记为"未配置"

### UI 状态映射

#### 运行状态颜色映射

- `success`: 绿色（成功）
- `empty`: 蓝灰色（本次没有可处理文件）
- `partial`: 橙色（部分成功）
- `failed` / `never`: 红色/灰色（失败/从未运行）

#### 警告提示映射

- `never_run`: "已启用但从未运行过 run-once"
- `last_run_failed`: "最近一次 Inbox 处理失败"
- `too_long_without_run`: "超过 24 小时未运行 run-once"

### 代码组织

1. **API 封装**: `src/services/api.ts`
   - `adminSettingsApi.getLibrarySettings()`

2. **类型定义**: `src/types/settings.ts`
   - `InboxSettings`
   - `LibraryRootsSettings`
   - `LibrarySettingsResponse`

3. **工具函数**: `src/utils/formatters.ts`
   - `formatDateTime()`: 格式化日期时间
   - `formatRelativeTime()`: 格式化相对时间

4. **路由配置**: `src/router/index.ts`
   - 新增 `/dev/library-settings` 路由

## 使用说明

### 访问页面

1. 启动后端服务
2. 启动前端服务
3. 访问 `http://localhost:5173/dev/library-settings`（或对应的前端地址）

### 配置说明

所有配置项来源于服务端环境变量或配置文件（`app/core/config.py`），当前页面为**只读**，不支持修改。

如需修改配置，请：
1. 修改环境变量（`.env` 文件）
2. 或修改 `app/core/config.py` 中的默认值
3. 重启后端服务

### 最小配置示例

```env
# Inbox 配置
INBOX_ROOT=/video/待整理
INBOX_ENABLE_VIDEO=true
INBOX_ENABLE_EBOOK=true
INBOX_ENABLE_AUDIOBOOK=true
INBOX_ENABLE_MUSIC=true

# 媒体库根目录配置
MOVIE_LIBRARY_ROOT=/115/电影
TV_LIBRARY_ROOT=/115/电视剧
ANIME_LIBRARY_ROOT=/115/动漫
EBOOK_LIBRARY_ROOT=/115/电子书
MUSIC_LIBRARY_ROOT=/115/音乐
```

## 后续计划

- **Phase 2**: 支持通过 UI 修改配置（需要权限控制）
- **Phase 3**: 配置验证和测试功能
- **Phase 4**: 配置历史记录和回滚

## 测试状态

- ✅ 后端 API 测试：6 个测试用例全部通过
- ✅ 前端页面：已创建并集成到路由系统
- ✅ 类型定义：完整的 TypeScript 类型支持
- ✅ 工具函数：时间格式化函数已实现

## 总结

本次实现完成了媒体库和 Inbox 设置的只读总览功能，包括：

1. **后端 API**: `/api/admin/settings/library` 提供完整的配置和健康状态信息
2. **前端页面**: `/dev/library-settings` 以卡片形式清晰展示所有配置项
3. **状态映射**: 完善的 UI 状态映射（颜色、标签、警告提示）
4. **代码复用**: 通过 `get_inbox_health()` helper 函数避免重复逻辑
5. **测试覆盖**: 完整的后端测试用例

当前阶段为只读展示，为后续的配置修改功能打下了良好基础。

