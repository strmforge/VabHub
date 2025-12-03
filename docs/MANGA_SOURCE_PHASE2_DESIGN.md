# MANGA-SOURCE-PHASE-2 设计文档

## 项目目标

让 VabHub 变成 Komga / Suwayomi / OPDS 等外部漫画服务的统一"搜索入口 + 浏览入口 + 追更入口"，真正把「漫画模块走第三方源接入」这句愿望落地。

## P0 巡检结果 - 重大发现

### 🎉 已有基础设施完整度：95%

#### 后端架构 ✅ 完整
- **模型层**：
  - `MangaSource` - 漫画源配置模型（支持 OPDS/SUWAYOMI/KOMGA/GENERIC_HTTP）
  - `MangaSeriesLocal` - 本地漫画系列（已包含 `source_id` + `remote_series_id`）
  - `UserMangaFollow` - 用户追更关系（通过 `series_id` 关联外部源）
  - `MangaChapterLocal` - 本地章节模型

- **适配器层**：
  - `BaseMangaSourceAdapter` - 抽象基类，定义统一接口
  - `KomgaMangaSourceAdapter` - Komga 适配器（完整实现）
  - `SuwayomiSourceAdapter` - Suwayomi 适配器
  - `OpdsSourceAdapter` - OPDS 适配器
  - `GenericHttpAdapter` - 通用 HTTP 适配器
  - `MangaSourceAdapterFactory` - 工厂模式实现

- **服务层**：
  - `manga_source_service.py` - 漫画源管理服务
  - `manga_remote_service.py` - 远程漫画服务
  - `manga_follow_service.py` - 追更服务
  - `manga_follow_sync.py` - 追更同步 Runner

- **API 层**：
  - `GET /api/manga/remote/sources` - 列出可用源
  - `GET /api/manga/remote/search` - 搜索漫画（单源）
  - `GET /api/manga/remote/series/{source_id}/{remote_series_id}` - 获取详情
  - `GET /api/manga/remote/series/{source_id}/{remote_series_id}/chapters` - 章节列表
  - `GET /api/manga/remote/sources/{source_id}/libraries` - 库列表
  - `GET /api/manga/remote/sources/{source_id}/libraries/{library_id}/series` - 按库浏览

#### 前端架构 ✅ 完整
- **页面组件**：
  - `MangaRemoteExplorer.vue` - 远程漫画浏览页面（功能完整）
  - `MangaFollowCenterPage.vue` - 追更中心页面
  - `MangaLibraryPage.vue` - 本地漫画库页面
  - `MangaReaderPage.vue` - 漫画阅读器

- **类型定义**：
  - `mangaSource.ts` - 漫画源相关类型
  - `mangaFollow.ts` - 追更相关类型
  - `mangaLocal.ts` - 本地漫画类型

- **API 服务**：
  - `mangaRemoteApi` - 远端漫画 API 客户端
  - `mangaFollowApi` - 追更 API 客户端
  - `mangaLocalApi` - 本地漫画 API 客户端

### 🎯 Phase 2 真正需要做的

基于巡检结果，Phase 2 的重点从"重新构建"转向"功能增强和集成"：

#### 缺失的核心功能
1. **聚合搜索** - 跨源搜索功能（现有 API 只支持单源搜索）
2. **"追这部"功能** - 现有是"导入到本地"，需要改为不下载的追更
3. **外部 URL 构建** - "在原站打开"按钮功能
4. **统一搜索入口** - 前端聚合搜索界面

#### 数据流设计
```
用户搜索 -> 聚合搜索API -> 并发调用多源适配器 -> 合并结果 -> 展示
     ↓
点击"追这部" -> 创建MangaSeriesLocal记录(不下载) -> 创建UserMangaFollow -> 追更Runner监控
     ↓
章节更新 -> 追更Runner检测 -> 发送MANGA_UPDATED通知 -> TG/Web端展示
```

## Phase 2 实施计划

### P1 – 后端：聚合搜索 + 外部URL构建

#### 聚合搜索 API
```python
# 新增 GET /api/manga/remote/aggregated-search
async def aggregated_search(
    q: str,
    sources: Optional[List[int]] = None,  # 指定源ID列表，不传则全源
    limit: int = 20
):
    """并发调用多源搜索，合并结果"""
    # 1. 获取启用的漫画源
    # 2. 并发调用各源适配器的 search_series
    # 3. 合并结果，按源分组
    # 4. 返回 AggregatedSearchResult
```

#### 外部 URL 构建
```python
# 新增 GET /api/manga/remote/series/{source_id}/{remote_series_id}/external-url
async def get_external_url(source_id: int, remote_series_id: str):
    """调用适配器的 build_external_url 方法"""
    # 各适配器实现 build_external_url 方法
    # Komga: {base_url}/series/{remote_series_id}
    # Suwayomi: {base_url}/manga/{remote_series_id}
    # OPDS: 根据具体实现
```

#### "追更" API 增强
```python
# 修改 POST /api/manga/follow
# 新增 follow_mode: "LOCAL" | "REMOTE"
# REMOTE模式：只创建记录，不下载章节
async def follow_manga(
    source_id: int,
    remote_series_id: str,
    follow_mode: str = "REMOTE"
):
    """创建追更记录，支持远程源追更"""
```

### P2 – 前端：统一搜索入口 + 追更功能

#### 新增 MangaSourceSearchPage.vue
- 全局搜索框（支持聚合搜索）
- 源过滤器（全部/Komga/Suwayomi/OPDS）
- 搜索结果卡片（显示源chips）
- "追这部"按钮（替代"导入"）
- "在原站打开"按钮

#### 增强 MangaRemoteExplorer.vue
- 添加"追这部"功能
- 添加"在原站打开"按钮
- 优化为"浏览模式"而非"导入模式"

#### 集成到漫画中心
- 在 `MangaFollowCenterPage` 添加"从外部源导入"入口
- 统一显示本地和外部源追更
- 用chips区分来源类型

### P3 – 追更体系集成

#### 追更 Runner 增强
```python
# manga_follow_sync.py 增强
# 支持对 REMOTE 模式的追更记录进行章节检查
# 不下载章节，只检测更新并发送通知
```

#### 通知体系
- `MANGA_UPDATED` 通知支持外部源
- 通知消息包含源信息
- TG 端显示来源chips

### P4 – 文档和配置示例

#### 配置文档
- Komga 接入指南
- Suwayomi 接入指南  
- OPDS 接入指南
- 聚合搜索使用说明

#### 配置示例
- `.env.example` 补充漫画源相关配置
- 示例配置文件

### P5 – QA 验收

#### 功能场景
- 聚合搜索：多源搜索结果合并
- 源过滤：按源类型筛选
- 追更流程：外部源追更 → 通知 → 书架显示
- 外部跳转：原站打开功能

## 技术债务记录

### 已知问题
1. **代码重复**：`MangaRemoteExplorer.vue` 和未来的 `MangaSourceSearchPage.vue` 可能有重复逻辑
2. **API 一致性**：现有 API 设计风格需要统一
3. **错误处理**：聚合搜索的超时和错误处理机制

### 未来优化方向
1. **组件抽取**：搜索结果卡片组件化
2. **缓存策略**：搜索结果缓存，提升性能
3. **智能推荐**：基于用户历史的源推荐

## Phase 2 边界

### ✅ 可以做
- 跨源搜索漫画
- 展示系列详情和章节列表
- 一键"追这部"（不下载）
- 在原站打开
- 追更通知和书架集成

### ❌ 暂不做
- 真正把章节下载到本地（那是 Phase 3）
- 内置漫画阅读器（那是 Phase 3）
- 离线阅读功能
- 本地存储管理

## 总结

Phase 2 的核心价值是**统一搜索入口 + 追更入口**，让用户能够：
1. 在一个地方搜索所有配置的漫画源
2. 不下载章节的情况下追更外部漫画
3. 通过 VabHub 的通知体系接收更新提醒
4. 统一管理本地和外部源的追更列表

这是一个**轻量级集成**方案，避免了复杂的本地存储和阅读器开发，快速实现"第三方源接入"的核心价值。
