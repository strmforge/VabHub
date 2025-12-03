# Phase EXT-1 完成报告：外部索引桥接骨架实现

## 概述

Phase EXT-1 完成了外部索引桥接（External Indexer Bridge）的完整骨架实现，为 VabHub 提供了集成外部 PT 索引引擎的统一接口层。

## 设计目标

1. **完全独立**：不依赖任何第三方项目，不出现任何品牌名称
2. **动态加载**：通过模块路径动态加载外部索引引擎
3. **优雅降级**：外部索引失败不影响主流程
4. **统一接口**：提供标准化的搜索、RSS、详情、下载链接接口

## 新增文件

### 核心模块（`backend/app/core/ext_indexer/`）

1. **`__init__.py`**
   - 统一导出所有公共接口和类
   - 提供清晰的模块 API

2. **`models.py`**
   - `ExternalTorrentResult`：外部索引搜索结果模型
   - `ExternalTorrentDetail`：外部索引种子详情模型
   - `ExternalSiteConfig`：外部站点配置模型

3. **`interfaces.py`**
   - `ExternalSiteAdapter`：单站适配器协议
   - `ExternalIndexerRuntime`：外部索引运行时协议
   - `ExternalAuthBridge`：外部授权桥接协议

4. **`registry.py`**
   - 全局注册表，管理站点适配器、运行时和授权桥接
   - 线程安全的注册和获取机制

5. **`runtime.py`**
   - `DynamicModuleRuntime`：动态模块运行时实现
   - 通过 `importlib` 动态加载外部模块
   - 优雅处理加载失败和调用异常

6. **`auth_bridge.py`**
   - `ExternalAuthState`：授权状态数据模型
   - `NoopExternalAuthBridge`：默认空操作授权桥接

7. **`site_importer.py`**
   - `load_all_site_configs()`：从 YAML 配置文件加载站点配置
   - `get_site_config()`：获取指定站点配置
   - 支持配置缓存和错误处理

8. **`search_provider.py`**
   - `ExternalIndexerSearchProvider`：外部索引搜索提供者
   - 整合多个外部站点的搜索结果
   - 自动去重和结果转换

9. **`debug_api_notes.md`**
   - 完整的调试 API 使用文档
   - 外部模块接口约定说明
   - 故障排查指南

### API 模块

10. **`backend/app/api/external_indexer_debug.py`**
    - `GET /api/debug/ext-indexer/sites`：列出所有外部站点配置
    - `GET /api/debug/ext-indexer/search`：调试搜索接口
    - `GET /api/debug/ext-indexer/status`：获取外部索引桥接状态

## 修改文件

### 配置

1. **`backend/app/core/config.py`**
   - 新增 `EXTERNAL_INDEXER_ENABLED`：是否启用外部索引桥接
   - 新增 `EXTERNAL_INDEXER_MODULE`：外部索引模块路径
   - 新增 `EXTERNAL_INDEXER_MIN_RESULTS`：最小结果阈值
   - 新增 `EXTERNAL_INDEXER_TIMEOUT_SECONDS`：超时时间

### 启动逻辑

2. **`backend/main.py`**
   - 在 `lifespan` 事件中添加外部索引桥接初始化逻辑
   - 动态加载外部模块并设置运行时
   - 优雅处理初始化失败

### 搜索服务集成

3. **`backend/app/modules/search/indexed_search_service.py`**
   - 在 `IndexedSearchService.search()` 中集成外部索引搜索
   - 当本地索引结果不足时，自动补充外部索引结果
   - 自动去重和结果转换
   - 结合 Local Intel 状态信息

### API 路由

4. **`backend/app/api/__init__.py`**
   - 导入并注册 `external_indexer_debug` 路由

## 核心功能

### 1. 动态模块加载

外部索引引擎通过模块路径动态加载，不绑定任何特定项目：

```python
runtime = DynamicModuleRuntime("external_indexer_engine.core")
```

### 2. 搜索集成点

在 `IndexedSearchService` 中的集成逻辑：

1. 优先使用本地索引查询
2. 如果结果不足，补充实时站点搜索
3. 如果结果仍不足且外部索引已启用，补充外部索引结果
4. 所有结果自动去重
5. 结合 Local Intel 状态信息

### 3. 降级策略

- **模块加载失败**：记录警告日志，禁用外部索引功能，不影响主流程
- **搜索调用失败**：记录警告日志，返回已有结果，不阻塞搜索
- **授权检查失败**：跳过该站点，继续搜索其他站点
- **结果转换失败**：跳过该结果，继续处理其他结果

### 4. 配置开关

通过环境变量控制外部索引功能：

- `EXTERNAL_INDEXER_ENABLED=false`：完全禁用外部索引
- `EXTERNAL_INDEXER_MODULE` 未设置：外部索引不初始化
- `EXTERNAL_INDEXER_MIN_RESULTS=20`：只有本地结果 < 20 时才补充外部索引

## 外部模块接口约定

外部索引引擎模块需要实现以下异步函数：

1. `search_torrents(site_id, keyword, *, media_type, categories, page) -> List[Dict]`
2. `fetch_rss(site_id, *, limit) -> List[Dict]`
3. `get_detail(site_id, torrent_id) -> Optional[Dict]`
4. `get_download_link(site_id, torrent_id) -> Optional[str]`

详细接口规范见 `backend/app/core/ext_indexer/debug_api_notes.md`。

## 调试 API

### 列出站点

```bash
curl http://localhost:8092/api/debug/ext-indexer/sites
```

### 测试搜索

```bash
curl "http://localhost:8092/api/debug/ext-indexer/search?site=example_site&q=test&page=1"
```

### 检查状态

```bash
curl http://localhost:8092/api/debug/ext-indexer/status
```

## 自检清单

- [x] 所有模块可以正常导入
- [x] 配置项已添加到 `Settings` 类
- [x] 启动逻辑已集成到 `main.py`
- [x] 搜索服务已集成外部索引
- [x] 调试 API 已注册并可用
- [x] 文档已创建

## 测试建议

1. **导入测试**：
   ```bash
   cd backend
   python -c "from app.core.ext_indexer import *; print('OK')"
   ```

2. **配置测试**：
   - 设置 `EXTERNAL_INDEXER_ENABLED=true`
   - 设置 `EXTERNAL_INDEXER_MODULE=test_module`
   - 启动应用，检查日志中的初始化信息

3. **调试 API 测试**：
   - 访问 `/api/debug/ext-indexer/status` 检查状态
   - 访问 `/api/debug/ext-indexer/sites` 查看站点列表

4. **搜索集成测试**：
   - 执行搜索，检查日志中是否有外部索引调用记录
   - 验证结果是否正确合并和去重

## 后续工作

1. **实现外部索引引擎模块**：按照接口约定实现具体的外部索引引擎
2. **站点配置管理**：在 `config/external_sites/` 目录下创建站点配置文件
3. **授权桥接实现**：替换默认的 `NoopExternalAuthBridge` 为真正的授权检查实现
4. **性能优化**：添加结果缓存、并发控制等优化
5. **前端集成**：在搜索页面显示外部索引来源标识

## 注意事项

1. **不出现第三方项目名称**：所有代码、注释、文档中都不包含任何第三方项目名称
2. **优雅降级**：外部索引失败不影响主流程
3. **配置驱动**：通过环境变量控制功能开关
4. **接口约定**：外部模块需要严格按照接口约定实现

## 总结

Phase EXT-1 成功实现了外部索引桥接的完整骨架，为 VabHub 提供了集成外部 PT 索引引擎的统一接口层。所有功能都经过精心设计，确保优雅降级、配置驱动、接口清晰，为后续的实际集成工作奠定了坚实基础。

