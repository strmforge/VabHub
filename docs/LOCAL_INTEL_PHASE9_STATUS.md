# Local Intel Phase 9 实施状态

**实施时间**: 2025-01-XX  
**状态**: ✅ **Phase 9 代码实施完成**

---

## 📋 实施概览

本次完成了 Local Intel 的 Phase 9：本地 PT 种子索引 + 搜索增强，实现了：
- **9A：Torrent 索引表 + ORM + 仓库层**：创建了 `torrent_index` 表和对应的 Repository
- **9B：Indexer（全站扫描 + 增量刷新）**：实现了种子列表抓取和解析，支持与 SiteGuard 联动
- **9C：SearchService 重构为「索引优先 + 站点补充」**：优先从本地索引查询，不足时补充实时站点搜索
- **9D：前端搜索体验升级**：显示 HR/Free/站点状态等新字段，支持 HR 过滤

---

## ✅ 9A：Torrent 索引表 + ORM + 仓库层

### 数据库表结构

**表名**：`torrent_index`

**字段**：
- `id`: 主键
- `site_id`: 站点ID（索引）
- `torrent_id`: 种子ID（索引）
- `title_raw`: 原始标题（索引，用于搜索）
- `title_clean`: 清洗后的标题（可选）
- `category`: 分类（索引）
- `is_hr`: HR 标记（0/1）
- `is_free`: 免费标记（0/1）
- `is_half_free`: 半免费标记（0/1）
- `size_bytes`: 文件大小（字节）
- `seeders`: 做种数（索引）
- `leechers`: 下载数
- `completed`: 完成数（可选）
- `published_at`: 发布时间（索引）
- `last_seen_at`: 最后看到时间（索引）
- `is_deleted`: 删除标记（0/1，索引）
- `deleted_at`: 删除时间
- `created_at`, `updated_at`: 时间戳

**索引**：
- 唯一索引：`(site_id, torrent_id)`
- 单列索引：`title_raw`, `published_at`, `category`, `seeders`, `is_deleted`

### Repository 层

**文件**：
- `backend/app/core/intel_local/repo/torrent_index_repo.py`：协议和数据结构
- `backend/app/core/intel_local/repo/sqlalchemy.py`：SQLAlchemy 实现

**核心方法**：
- `upsert_many(rows)`: 批量插入/更新（如果 `last_seen_at` 更近则更新）
- `mark_deleted(site_id, torrent_id, deleted_at)`: 标记为已删除
- `query_for_search(params)`: 根据搜索参数查询
- `get_by_site_and_tid(site_id, torrent_id)`: 根据站点和种子ID获取

### 迁移脚本

**文件**：`backend/scripts/migrate_local_intel_schema.py`

**新增函数**：`create_torrent_index_table()`

**执行方式**：
```bash
cd backend
python scripts/migrate_local_intel_schema.py
```

---

## ✅ 9B：Indexer（全站扫描 + 增量刷新）

### TorrentIndexer 类

**文件**：`backend/app/core/intel_local/indexer.py`

**核心方法**：

1. **`sync_site_full(site_id, max_pages=100, pages_per_batch=10)`**
   - 全站慢速扫描
   - 每 `pages_per_batch` 页检查一次 SiteGuard
   - 如果被限流，停止扫描
   - 支持分页抓取，避免请求过快

2. **`sync_site_incremental(site_id, max_pages=5)`**
   - 增量扫描最近 N 页
   - 检查 SiteGuard，如果被限流则跳过
   - 只 upsert `last_seen_at` 更近的记录

### 种子列表解析器

**文件**：`backend/app/core/intel_local/parsers/torrent_list_parser.py`

**解析函数**：
- `parse_torrent_list_page_generic()`: 通用 NexusPHP 格式解析
- `parse_torrent_list_page_hdsky()`: HDsky 特定解析（目前复用通用解析）

**解析字段**：
- `torrent_id`: 从链接中提取（如 `detail.php?id=12345`）
- `title_raw`: 从链接文本提取
- `category`: 从分类列提取
- `is_hr`, `is_free`, `is_half_free`: 从标题或特殊标记提取
- `size_bytes`: 从大小列解析（支持 GB/TB/MB/KB）
- `seeders`, `leechers`, `completed`: 从数字列提取
- `published_at`: 从时间列解析

### 与 SiteGuard 联动

- 全站扫描：每 `pages_per_batch` 页检查一次，如果被限流则停止
- 增量扫描：扫描前检查，如果被限流则跳过
- 错误处理：连续失败 3 次则停止扫描

### 与站内信删种通知联动

**文件**：`backend/app/core/intel_local/inbox_watcher.py`

**修改**：在处理 `InboxEventType.TORRENT_DELETED` 时，调用 `TorrentIndexRepository.mark_deleted()` 标记索引中的种子为已删除。

---

## ✅ 9C：SearchService → 「索引优先 + 站点补充」重构

### SearchQuery 和 SearchResultItem DTO

**文件**：`backend/app/schemas/search.py`

**SearchQuery**：
- `keyword`: 搜索关键词
- `category`: 分类过滤
- `site_ids`: 站点过滤
- `hr_filter`: HR 过滤（"any", "exclude_hr", "hr_only"）
- `min_seeders`, `max_seeders`: 做种数范围
- `min_size_gb`, `max_size_gb`: 大小范围
- `sort`: 排序方式（"default", "seeders", "published_at", "size"）
- `limit`, `offset`: 分页

**SearchResultItem**：
- 基础字段：`site_id`, `torrent_id`, `title_raw`, `size_bytes`, `seeders`, `leechers`, `published_at`
- 属性字段：`is_hr`, `is_free`, `is_half_free`, `is_deleted`, `category`
- Local Intel 状态：`intel_hr_status`, `intel_site_status`
- 下载字段：`magnet_link`, `torrent_url`

### IndexedSearchService

**文件**：`backend/app/modules/search/indexed_search_service.py`

**搜索流程**：

1. **从本地索引查询**：
   - 使用 `TorrentIndexRepository.query_for_search()` 查询
   - 应用所有过滤条件（关键词、分类、站点、HR、做种数、大小）
   - 获取 Local Intel 状态（HR 状态、站点状态）

2. **结果不足时补充实时搜索**：
   - 如果索引结果 < `min_results_threshold`（默认 20），调用原有 `SearchService`
   - 去重：如果索引中已有，跳过
   - 可选：将实时搜索结果写入索引（当前未实现，避免影响性能）

3. **排序**：
   - 根据 `sort` 参数排序（做种数、发布时间、大小）

### API 层更新

**文件**：`backend/app/api/search.py`

**修改**：
- 如果启用 Local Intel，优先使用 `IndexedSearchService`
- 如果索引搜索失败或无结果，回退到原有 `SearchService`
- 保持向后兼容：结果格式与原有 API 一致

### 订阅选种逻辑更新

**文件**：`backend/app/modules/subscription/service.py`

**修改**：
- 在 `execute_search()` 中，如果启用 Local Intel，优先使用 `IndexedSearchService`
- 保持原有 Local Intel 感知逻辑（站点限流检查、HR 风险检查）

---

## ✅ 9D：前端搜索体验升级

### SearchResultCard 组件更新

**文件**：`frontend/src/components/search/SearchResultCard.vue`

**新增显示**：
- **HR 状态标签**：显示 `intel_hr_status`（SAFE/ACTIVE/RISK）
- **站点状态标签**：显示 `intel_site_status`（OK/THROTTLED/ERROR）
- **Free/半 Free 标签**：显示 `is_free` 和 `is_half_free`
- **HR 标记**：显示 `is_hr`

**详情对话框**：
- 显示 Local Intel 状态信息
- 显示 Free/HR 标记

### SearchFilters 组件更新

**文件**：`frontend/src/components/search/SearchFilters.vue`

**新增筛选**：
- **HR 过滤**：下拉选择（全部/排除 HR/仅 HR）

### Search 页面更新

**文件**：`frontend/src/pages/Search.vue`

**修改**：
- 在 `Filters` 接口中添加 `hr_filter` 字段
- 在 `handleSearch()` 中将 `hr_filter` 传递给 API（通过 `exclude` 字段）

---

## 📝 使用指南

### 1. 数据库迁移

```bash
cd backend
python scripts/migrate_local_intel_schema.py
```

确认 `torrent_index` 表已创建。

### 2. 手动触发全站扫描

```python
from app.core.intel_local.indexer import TorrentIndexer
from app.core.database import AsyncSessionLocal

indexer = TorrentIndexer()
result = await indexer.sync_site_full("hdsky", max_pages=50)
print(result)
```

### 3. 手动触发增量扫描

```python
indexer = TorrentIndexer()
result = await indexer.sync_site_incremental("hdsky", max_pages=5)
print(result)
```

### 4. 搜索 API 调用

```bash
# 基础搜索（会自动使用索引）
curl -X POST "http://localhost:8092/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "权力的游戏",
    "media_type": "tv",
    "min_seeders": 10,
    "exclude": "hr"
  }'
```

### 5. 前端搜索页面

访问：`http://localhost:3000/search`

- 输入关键词搜索
- 使用高级筛选（包括 HR 过滤）
- 查看搜索结果中的 Local Intel 状态标签

---

## 🔧 配置要求

1. **数据库表**
   - 确保已运行迁移脚本创建 `torrent_index` 表

2. **站点配置**
   - 确保 `config/intel_sites/*.yaml` 中有站点配置
   - 确保数据库 `sites` 表中有对应站点记录且 `is_active=True` 且有 `cookie`

3. **Local Intel 开关**
   - 确保 `INTEL_ENABLED=true` 在配置中启用
   - 索引搜索功能会自动启用（如果 Local Intel 启用）

---

## ⚠️ 注意事项

1. **索引数据来源**
   - 索引数据来自 Indexer 抓取，需要手动或定时触发扫描
   - 初始状态下索引可能为空，搜索会回退到实时站点搜索
   - 随着 Indexer 运行，索引会逐渐丰富

2. **全站扫描策略**
   - 全站扫描是慢速的，会与 SiteGuard 联动避免被限流
   - 建议在低峰期手动触发全站扫描
   - 日常使用增量扫描即可

3. **搜索性能**
   - 索引搜索比实时搜索快得多
   - 但如果索引数据不全，可能找不到最新资源
   - 系统会自动补充实时搜索，确保结果完整

4. **HR 过滤**
   - HR 过滤基于索引中的 `is_hr` 字段
   - 如果索引未更新，HR 过滤可能不准确
   - 建议定期运行 Indexer 保持索引新鲜

5. **站点状态显示**
   - 站点状态来自 Local Intel 的 SiteGuard
   - 如果站点未配置或未触发风控，状态可能显示为 "UNKNOWN"

---

## 📊 测试建议

### 1. 数据库迁移测试

```bash
cd backend
python scripts/migrate_local_intel_schema.py
# 检查输出，确认 torrent_index 表创建成功
```

### 2. Indexer 测试

```python
# 在 Python 交互式环境中
import asyncio
from app.core.intel_local.indexer import TorrentIndexer

indexer = TorrentIndexer()
result = await indexer.sync_site_incremental("hdsky", max_pages=2)
print(result)
# 检查数据库，确认 torrent_index 表有数据
```

### 3. 搜索 API 测试

```bash
# 测试索引搜索
curl -X POST "http://localhost:8092/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "测试",
    "page_size": 10
  }'

# 检查返回结果中是否包含 intel_hr_status 和 intel_site_status 字段
```

### 4. 前端页面测试

1. 访问 `/search` 页面
2. 输入关键词搜索
3. 验证搜索结果中是否显示 HR/站点状态标签
4. 使用 HR 过滤功能
5. 点击结果卡片，查看详情中的 Local Intel 信息

### 5. 订阅选种测试

1. 创建一个订阅
2. 触发订阅搜索
3. 检查日志，确认使用了 IndexedSearchService
4. 验证选种结果是否正常

---

## 🚀 后续优化建议

1. **Indexer 调度自动化**
   - 在 `app/core/scheduler.py` 中添加定时任务
   - 每天凌晨执行增量扫描
   - 每周执行一次全站扫描（可选）

2. **解析器扩展**
   - 为更多站点实现特定解析器（如 TTG、Audiences）
   - 优化通用解析器的准确性

3. **索引更新策略**
   - 实现"隐性增量"：将实时搜索结果写入索引
   - 实现索引过期策略：删除过旧的记录

4. **搜索性能优化**
   - 添加全文搜索索引（如 SQLite FTS5）
   - 实现搜索结果缓存

5. **前端功能增强**
   - 添加"查看站点 Intel 状态"快捷链接
   - 添加索引数据统计显示（如"索引中有 X 条记录"）

---

## 📋 自测清单

- [x] 运行迁移脚本后，数据库中存在 `torrent_index` 表
- [ ] 调用 Indexer 对 hdsky 执行增量扫描后，`torrent_index` 有数据
- [ ] 搜索一个站内确实存在但以前经常搜不到的关键字，能在新搜索页面看到来自本地索引的结果
- [ ] 在站点被限流后，Index 仍可返回已有结果，但 SearchService 会优先使用索引而不是继续撞站点
- [ ] 订阅在选种时调用了新的 SearchService 且行为正常
- [ ] 前端搜索页面显示 HR/站点状态标签
- [ ] HR 过滤功能正常工作
- [ ] 站内信删种通知能正确标记索引中的种子为已删除

---

**完成时间**: 2025-01-XX  
**实施人员**: Cursor AI Assistant

