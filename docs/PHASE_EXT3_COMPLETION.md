# Phase EXT-3 完成报告：外部索引设置与状态展示

## 1. 概述

Phase EXT-3 的目标是在现有 External Indexer Bridge 基础上，增加设置与状态展示、前端调试面板，并为后续 UI 集成预留扩展点。本阶段完成了后端管理 API、前端管理页面、搜索结果来源标记等功能。

## 2. 完成的工作

### 2.1 后端 API（`backend/app/api/ext_indexer.py`）

创建了外部索引管理 API，提供以下只读接口：

#### 2.1.1 GET `/api/ext-indexer/settings`

返回当前生效的配置信息：
- `enabled`: 是否启用外部索引
- `module`: 外部索引模块路径
- `engine_base_url`: 外部引擎服务地址（从 `external_indexer_engine.config` 读取）
- `timeout_seconds`: HTTP 请求超时时间
- `min_results`: 最小结果阈值

**实现要点：**
- 从 `app.core.config` 读取 `EXTERNAL_INDEXER_*` 配置
- 从 `external_indexer_engine.config.get_engine_settings()` 读取引擎配置
- 所有异常都被捕获，返回友好的错误信息

#### 2.1.2 GET `/api/ext-indexer/status`

返回运行状态信息：
- `enabled`: 是否启用
- `runtime_loaded`: `DynamicModuleRuntime` 是否加载成功
- `has_engine`: `external_indexer_engine.core` 是否导入成功
- `last_error`: 最近一次错误（目前为占位，返回 null）
- `notes`: 状态说明文本

**实现要点：**
- 检查 `get_runtime()` 返回的运行时实例
- 检查 `runtime.is_loaded` 属性
- 尝试导入 `external_indexer_engine.core` 判断引擎是否可用
- 提供友好的状态说明

#### 2.1.3 GET `/api/ext-indexer/sites`

返回支持的站点列表：
- `sites`: 站点 ID 列表
- `count`: 站点数量

**实现要点：**
- 优先从 `site_importer.load_all_site_configs()` 获取站点配置
- 如果加载失败，回退到从注册表 `list_registered_sites()` 获取
- 所有异常都被捕获，返回空列表

### 2.2 搜索结果来源标记（`backend/app/schemas/search.py`）

在 `SearchResultItem` 模型中新增 `source` 字段：

```python
source: Optional[Literal["local", "external"]] = Field(None, description="搜索结果来源：local=本地索引，external=外部索引")
```

**用途：**
- 为前端搜索结果展示提供来源标识
- 本地索引结果标记为 `source="local"`
- 外部索引结果标记为 `source="external"`

### 2.3 搜索结果集成更新（`backend/app/modules/search/indexed_search_service.py`）

更新了搜索结果生成逻辑：

1. **本地索引结果**：在创建 `SearchResultItem` 时设置 `source="local"`
2. **外部索引结果**：在转换 `ExternalTorrentResult` 为 `SearchResultItem` 时设置 `source="external"`

**实现位置：**
- 本地索引：`IndexedSearchService._search_from_index()` 方法中
- 外部索引：`IndexedSearchService._search_with_external_indexer()` 方法中

### 2.4 前端管理页面（`frontend/src/pages/ExternalIndexer.vue`）

创建了完整的外部索引管理页面，包含以下功能区域：

#### 2.4.1 配置概览卡片

- 显示启用状态（已启用/未启用）
- 显示模块路径、引擎地址、超时时间、最小结果阈值
- 如果未启用，显示醒目的警告提示

#### 2.4.2 运行状态卡片

- 显示运行时加载状态（成功/失败）
- 显示引擎模块状态（已加载/未加载）
- 显示最近错误（如果有）
- 显示状态说明文本
- 提供刷新按钮

#### 2.4.3 站点列表卡片

- 显示已配置的站点数量
- 以 Chip 组件展示站点 ID 列表
- 如果无站点，显示友好提示

#### 2.4.4 调试测试区域

- 提供测试表单：站点 ID、搜索关键词、页码
- 点击"测试"按钮调用 `/api/debug/ext-indexer/search`
- 以表格形式展示测试结果：标题、站点、种子ID、大小、做种数、下载数、发布时间
- 提供友好的加载和错误提示

**技术实现：**
- 使用 Vue 3 Composition API
- 使用 Vuetify 3 组件库
- 使用 `vue-toastification` 显示提示消息
- 使用 `@/services/api` 进行 HTTP 请求
- 响应式设计，适配不同屏幕尺寸

### 2.5 路由和菜单集成

#### 2.5.1 路由配置（`frontend/src/router/index.ts`）

新增路由：
```typescript
{
  path: '/external-indexer',
  name: 'ExternalIndexer',
  component: () => import('@/pages/ExternalIndexer.vue'),
  meta: { requiresAuth: true, title: '外部索引管理', badge: '实验' }
}
```

#### 2.5.2 侧边栏菜单（`frontend/src/layouts/components/AppDrawer.vue`）

在"其他功能"区域新增菜单项：
```vue
<v-list-item
  prepend-icon="mdi-bridge"
  title="外部索引（实验）"
  value="external-indexer"
  :to="{ name: 'ExternalIndexer' }"
  :active="$route.name === 'ExternalIndexer'"
>
  <template v-slot:append>
    <v-chip size="x-small" color="info" variant="flat">实验</v-chip>
  </template>
</v-list-item>
```

### 2.6 API 路由注册（`backend/app/api/__init__.py`）

在 `api_router` 中注册外部索引管理路由：
```python
api_router.include_router(ext_indexer.router)  # 外部索引管理（路由已包含/api/ext-indexer前缀）
```

## 3. 新增/修改的文件列表

### 后端文件

1. **`backend/app/api/ext_indexer.py`**（新建）
   - 外部索引管理 API 实现

2. **`backend/app/api/__init__.py`**（修改）
   - 导入 `ext_indexer` 模块
   - 注册外部索引管理路由

3. **`backend/app/schemas/search.py`**（修改）
   - 在 `SearchResultItem` 中新增 `source` 字段

4. **`backend/app/modules/search/indexed_search_service.py`**（修改）
   - 本地索引结果设置 `source="local"`
   - 外部索引结果设置 `source="external"`

### 前端文件

1. **`frontend/src/pages/ExternalIndexer.vue`**（新建）
   - 外部索引管理页面完整实现

2. **`frontend/src/router/index.ts`**（修改）
   - 新增 `/external-indexer` 路由

3. **`frontend/src/layouts/components/AppDrawer.vue`**（修改）
   - 在侧边栏菜单中新增"外部索引（实验）"入口

## 4. API 接口说明

### 4.1 管理 API（`/api/ext-indexer/*`）

| 路径 | 方法 | 说明 | 响应格式 |
|------|------|------|----------|
| `/api/ext-indexer/settings` | GET | 获取配置信息 | `{ enabled, module, engine_base_url, timeout_seconds, min_results }` |
| `/api/ext-indexer/status` | GET | 获取运行状态 | `{ enabled, runtime_loaded, has_engine, last_error, notes }` |
| `/api/ext-indexer/sites` | GET | 获取站点列表 | `{ sites: string[], count: number }` |

### 4.2 调试 API（`/api/debug/ext-indexer/*`）

调试 API 在 Phase EXT-2 中已实现，本阶段前端页面调用了：
- `GET /api/debug/ext-indexer/search?site=...&q=...&page=...`

## 5. 使用说明

### 5.1 访问管理页面

1. 启动 VabHub 后端和前端服务
2. 登录系统
3. 在左侧菜单的"其他功能"区域找到"外部索引（实验）"
4. 点击进入外部索引管理页面

### 5.2 查看配置和状态

- 页面加载时自动刷新配置、状态和站点列表
- 点击"刷新状态"按钮可手动刷新所有信息
- 配置卡片显示当前生效的配置（只读）
- 状态卡片显示运行时和引擎模块的加载状态

### 5.3 测试搜索功能

1. 在"调试测试"区域填写：
   - 站点 ID（例如：`test-site`）
   - 搜索关键词（例如：`test`）
   - 页码（默认为 1）
2. 点击"测试"按钮
3. 查看返回的搜索结果表格

**注意：** 如果外部索引未启用或引擎服务不可用，测试搜索可能返回空结果或错误。

## 6. 技术细节

### 6.1 错误处理

- 所有 API 接口都使用 `try-except` 捕获异常
- 返回友好的错误信息，不暴露堆栈信息
- 前端使用 `vue-toastification` 显示错误提示

### 6.2 配置读取

- 后端配置从 `app.core.config.settings` 读取
- 引擎配置从 `external_indexer_engine.config.get_engine_settings()` 读取
- 所有配置都是只读，通过环境变量设置

### 6.3 状态检查

- `runtime_loaded`: 检查 `get_runtime()` 返回的运行时实例及其 `is_loaded` 属性
- `has_engine`: 尝试导入 `external_indexer_engine.core` 模块

### 6.4 前端组件

- 使用 Vuetify 3 的 `v-card`、`v-data-table`、`v-chip` 等组件
- 使用 `PageHeader` 组件统一页面头部样式
- 响应式布局，适配移动端和桌面端

## 7. 已知限制与 TODO

### 7.1 已知限制

1. **错误记录**：`last_error` 字段目前为占位，未实现持久化错误记录
2. **站点配置**：站点列表依赖配置文件或注册表，如果两者都不可用，将返回空列表
3. **只读配置**：所有配置都是只读，需要通过环境变量修改

### 7.2 后续优化建议

1. **错误记录**：实现错误日志持久化，记录最近 N 次错误
2. **配置管理**：考虑提供配置修改 API（需要权限控制）
3. **站点管理**：提供站点启用/禁用、添加/删除等管理功能
4. **性能监控**：添加搜索响应时间、成功率等指标
5. **搜索结果展示**：在搜索结果页面显示来源标签（`source="external"`）

## 8. 验收标准

### 8.1 后端验收

- [x] API 接口能正常返回 JSON 响应
- [x] 配置读取正确（从环境变量和引擎配置）
- [x] 状态检查逻辑正确（运行时和引擎模块）
- [x] 异常处理完善（不抛堆栈给前端）
- [x] 搜索结果包含 `source` 字段

### 8.2 前端验收

- [x] 页面能正常加载和显示
- [x] 配置、状态、站点列表能正确显示
- [x] 刷新功能正常工作
- [x] 测试搜索功能正常工作
- [x] 错误提示友好
- [x] 路由和菜单正确集成

## 9. 总结

Phase EXT-3 成功完成了外部索引的设置与状态展示、前端调试面板等功能，为后续的 UI 集成和功能扩展打下了良好基础。所有功能都遵循了"只读配置"、"优雅降级"、"友好错误提示"等设计原则，确保了系统的稳定性和用户体验。

---

**完成时间：** 2024年（Phase EXT-3）  
**相关文档：**
- `docs/PHASE_EXT1_COMPLETION.md` - Phase EXT-1 完成报告
- `docs/PHASE_EXT2_COMPLETION.md` - Phase EXT-2 完成报告
- `external_indexer_engine/README_EXT_ENGINE.md` - 外部索引引擎模块文档

