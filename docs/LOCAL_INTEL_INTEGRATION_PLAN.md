# Local Intel 集成计划

## 第 0 步：理解与总览

### Local Intel 功能概述
- **HR 保护**：阻止误删 HR 种子的源文件
- **站点防风控**：控制扫描节奏，避免触发站点限制
- **站内信监控**：识别 HR 扣分、种子删除、访问限制等事件
- **本地索引预留**：为后续别名识别预留接口

### 集成点分析

#### 1. 下载完成后处理（HR 保护接入点）
**位置**：`VabHub/backend/app/modules/file_operation/transfer_service.py`
- `TransferService.transfer_file()` 方法中，`delete_source` 参数控制是否删除源文件
- 当前逻辑：当 `operation_mode == FileOperationMode.MOVE` 时，`delete_source=True`
- **需要修改**：在决定 `delete_source` 之前，调用 `should_keep_source_after_download(site_id, torrent_id)` 检查 HR 状态

**如何获取 site_id 和 torrent_id**：
- 从 `DownloadTask` 模型的 `extra_metadata` 字段中提取
- 或从订阅任务的 `sites` 字段和搜索结果中提取
- 需要在创建下载任务时，将 `site_id` 和 `torrent_id` 写入 `extra_metadata`

#### 2. 站点扫描入口（Site Guard 接入点）
**位置**：`VabHub/backend/app/modules/subscription/service.py`
- `SubscriptionService.execute_search()` 方法执行订阅搜索
- 可能还有其他全站抓取任务（需要进一步查找）

**需要修改**：
- 在开始抓取前，调用 `before_pt_scan(site_id)` 获取扫描预算
- 根据 `budget["blocked"]` 决定是否跳过
- 根据 `budget["max_pages"]` 和 `budget["max_minutes"]` 控制抓取量

#### 3. 配置加载
**位置**：项目启动时（`main.py` 的 `lifespan` 函数）
- 扫描 `config/intel_sites/*.yaml`
- 解析为 `IntelSiteProfile` 字典
- 注入到相关服务中

#### 4. 定时任务（HR Watcher & Inbox Watcher）
**位置**：`VabHub/backend/app/core/scheduler.py` 或类似的调度系统
- 注册两个周期任务：
  - HR Watcher：每 X 小时执行一次
  - Inbox Watcher：每 Y 分钟执行一次

### 文件结构映射

解压后的文件需要移动到 VabHub 项目结构：
- `core/intel_local/` → `VabHub/backend/app/core/intel_local/`
- `config/intel_sites/` → `VabHub/config/intel_sites/`（保持原路径或统一到项目配置目录）
- `core/search/local_index_stub.py` → `VabHub/backend/app/modules/search/local_index_stub.py`
- `scripts/migrate_local_intel_schema.py` → `VabHub/backend/scripts/migrate_local_intel_schema.py`

### 配置系统
当前项目使用 `app.core.config.Settings`（Pydantic BaseSettings），需要添加：
- `INTEL_ENABLED: bool`
- `INTEL_MODE: str`（暂时只有 "local"）
- `INTEL_HR_GUARD_ENABLED: bool`
- `INTEL_SITE_GUARD_ENABLED: bool`

## 集成步骤

1. ✅ 第 0 步：解压与总览（已完成）
2. ⏳ 第 1 步：把 Local Intel 模块"安放"到项目中
3. ⏳ 第 2 步：接入"删源文件保护"（HR 保护）
4. ⏳ 第 3 步：接入"站点扫描节奏控制"（Site Guard）
5. ⏳ 第 4 步：加载 config/intel_sites/*.yaml 站点配置
6. ✅ 第 5 步：为 HR 页面 & 站内信预留后台任务（骨架）
   - 创建了 `hr_watcher.py` 和 `inbox_watcher.py` 骨架
   - 在调度器中注册了 HR 监控（每 6 小时）和站内信监控（每 30 分钟）任务
   - 预留了 HTTP 请求和 HTML 解析的接口（NotImplementedError）

7. ✅ 第 6 步：为 Local Intel 添加配置开关
   - 在 `config.py` 中统一了配置定义（INTEL_ENABLED, INTEL_MODE, INTEL_HR_GUARD_ENABLED, INTEL_SITE_GUARD_ENABLED）
   - 在 `scheduler_hooks.py` 的入口处集中添加了开关判断
   - 移除了调用点的重复开关判断，统一由 hooks 函数内部处理

8. ✅ 第 7 步：数据库迁移占位
   - 创建了 SQLAlchemy 模型：`HRCase`、`SiteGuardProfile`、`InboxEvent`
   - 实现了迁移脚本 `migrate_local_intel_schema.py`，支持创建三个表
   - 在 `hr_state.py` 和 `site_guard.py` 中添加了 TODO 注释，说明未来如何替换内存缓存为 DB + 内存缓存组合
   - 表结构设计：
     - `hr_cases`: 存储 HR 状态（site + torrent_id 唯一索引）
     - `site_guard_profiles`: 存储站点防护配置（site 唯一索引）
     - `inbox_events`: 存储站内信事件（site + message_hash 唯一索引，用于去重）

9. ✅ Phase 2 骨架（HR / Inbox Watcher）
   - 新增 `events.py`，定义 `InboxEventType` / `InboxEvent`
   - `HRWatcher` / `InboxWatcher` 对齐 Phase 2 设计：抽象 `fetch_hr_rows` / `fetch_new_messages`
   - 新增 `HRRow` / `InboxMessage` 数据结构，watcher 仅处理状态机，HTTP/解析继续 TODO
   - 支持 `load_all_site_profiles()` 显式加载配置，并在单例刷新时同步 profiles
   - 调度任务在未接入 HTTP 前会提示 NotImplemented，避免误报错误

10. ✅ Phase 3A 仓库接口 + SQLAlchemy 实现
    - 引入 `core/intel_local/repo/`，定义 `HRCasesRepository` / `SiteGuardRepository` / `InboxCursorRepository`
    - 新增 SQLAlchemy 实现类：`SqlAlchemyHRCasesRepository`、`SqlAlchemySiteGuardRepository`、`SqlAlchemyInboxCursorRepository`
    - ORM 模型补充 `SiteGuardEvent`、`InboxCursor`，迁移脚本覆盖 `site_guard_events`、`inbox_cursor`
    - `app/core/intel_local/__init__.py` 导出新接口，方便后续接线

11. ✅ Phase 3B HTTP & 解析骨架
    - 新增 `http_clients.py` 提供 `SiteHttpClientRegistry`，支持在启动期注入站点 HTTP 客户端
    - 新增 `parsers/hr_html_parser.py`、`parsers/inbox_html_parser.py`：定义 `ParsedHRRow` / `ParsedInboxMessage`
    - `HRWatcher.fetch_hr_rows` / `InboxWatcher.fetch_new_messages` 现在通过注册表 + 解析器获取数据，默认返回空列表
    - 追加 `LOCAL_INTEL_PHASE3B_NOTES.md`，说明调试与后续扩展建议

12. ✅ Phase 3C 策略引擎 + 动作流
    - 增加 `actions.py`/`hr_policy.py`/`inbox_policy.py`/`engine.py`，统一输出 `LocalIntelAction`
    - 新建 `factory.build_local_intel_engine()` 并在 `main.py` 启动阶段实例化 `LocalIntelEngine`
    - `HRWatcher` / `InboxWatcher` 扩展 `refresh_site`，同步仓库并返回 `InboxEvent`
    - 新增调试 API：`POST /admin/local-intel/refresh/{site_id}` 可查看动作列表

