# Local Intel Phase 8 实施状态

**实施时间**: 2025-01-XX  
**状态**: ✅ **Phase 8 代码实施完成**

---

## 📋 实施概览

本次完成了 Local Intel 的 Phase 8：下载任务与系统设置的深度集成，实现了：
- **下载任务列表联动 Local Intel 状态**：在下载任务列表中显示 HR 状态和站点状态
- **Local Intel 全局配置开关 + 模式**：在系统设置中添加 Local Intel 配置管理
- **订阅/自动任务的基础 Intel 感知**：订阅刷新时检查站点状态，选择种子时检查 HR 风险

---

## ✅ 下载任务列表联动 Local Intel 状态

### 后端 API 扩展

**文件**：`backend/app/api/download.py`

**修改内容**：
- 在 `DownloadTaskResponse` 中添加两个新字段：
  - `intel_hr_status: Optional[str]`：HR 状态（SAFE, ACTIVE, RISK, UNKNOWN）
  - `intel_site_status: Optional[str]`：站点状态（OK, THROTTLED, ERROR, UNKNOWN）
- 在 `list_downloads` API 中实现批量查询逻辑：
  - 收集所有任务的 `site_id` 和 `torrent_id`
  - 批量查询 `hr_cases` 表，判断 HR 状态
  - 批量查询 `site_guard_events` 表，判断站点健康状态
  - 为每个下载任务填充 `intel_hr_status` 和 `intel_site_status`

**HR 状态判断逻辑**：
- `SAFE`：HR 已完成、失败或不存在，或已满足保种要求
- `ACTIVE`：HR 进行中，剩余时间 >= 24 小时
- `RISK`：HR 进行中，剩余时间 < 24 小时
- `UNKNOWN`：无法获取 HR 信息

**站点状态判断逻辑**：
- `OK`：站点正常，无错误或错误次数 <= 3
- `THROTTLED`：站点被限流（`block_until` 在未来）
- `ERROR`：站点错误（最近 24 小时内错误次数 > 3）
- `UNKNOWN`：无法获取站点信息

### 前端 UI 显示

**文件**：`frontend/src/components/downloads/DownloadList.vue`

**修改内容**：
- 在下载任务列表中添加两个状态列：
  - HR 状态：使用彩色 `v-chip` 显示，带图标
  - 站点状态：使用彩色 `v-chip` 显示，带图标
- 实现状态颜色映射：
  - HR 状态：SAFE（绿色）、ACTIVE（黄色）、RISK（红色）、UNKNOWN（灰色）
  - 站点状态：OK（绿色）、THROTTLED（黄色）、ERROR（红色）、UNKNOWN（灰色）
- 实现点击跳转功能：点击状态标签可跳转到 Local Intel 面板，并预填站点过滤

**状态显示函数**：
- `getHRStatusColor`、`getHRStatusIcon`、`getHRStatusText`
- `getSiteStatusColor`、`getSiteStatusIcon`、`getSiteStatusText`
- `goToLocalIntel`：跳转到 Local Intel 面板

---

## ✅ Local Intel 全局配置开关 + 模式

### 后端 API

**文件**：`backend/app/api/intel.py`

**新增配置项**：
- `intel_subscription_respect_site_guard`：订阅任务是否尊重站点风控状态（默认 `true`）

**API 端点**：
- `GET /api/intel/settings`：获取 Local Intel 配置
- `PUT /api/intel/settings`：更新 Local Intel 配置

**配置项列表**：
1. `intel_enabled`：是否启用 Local Intel（默认 `true`）
2. `intel_hr_mode`：HR 保护模式（`strict` / `relaxed`，默认 `strict`）
3. `intel_move_check_enabled`：是否在 MOVE 前强制执行 HR 检查（默认 `true`）
4. `intel_subscription_respect_site_guard`：订阅任务是否尊重站点风控状态（默认 `true`）

### 前端设置页面

**文件**：`frontend/src/pages/Settings.vue`

**修改内容**：
- 在 Local Intel 设置分类中添加新的配置开关：
  - "订阅任务尊重站点风控状态"：启用后，订阅刷新时会自动跳过被限流站点的订阅，并在选择种子下载时检查 HR 风险并记录提醒
- 更新 `intelSettings` 对象，添加 `intel_subscription_respect_site_guard` 字段
- 更新注意事项，说明订阅任务感知功能的作用

---

## ✅ 订阅/自动任务的基础 Intel 感知

### 订阅刷新时检查站点状态

**文件**：`backend/app/modules/subscription/refresh_engine.py`

**修改内容**：
- 在 `get_subscriptions_to_refresh` 方法中添加 Local Intel 感知逻辑
- 检查每个订阅关联的站点是否被限流：
  - 如果订阅指定了站点列表，检查每个站点是否被限流
  - 如果所有站点都被限流，跳过该订阅的刷新
  - 如果至少有一个站点未被限流，保留该订阅
- 记录跳过的订阅数量和原因

**实现细节**：
- 使用 `before_pt_scan` 检查站点状态
- 检查配置开关 `intel_subscription_respect_site_guard`
- 如果检查失败，保守策略：不过滤订阅

### 选择种子时检查 HR 风险

**文件**：`backend/app/modules/subscription/service.py`

**修改内容**：
- 在 `execute_search` 方法中，选择最佳结果后、创建下载任务前，添加 HR 风险检查
- 检查逻辑：
  - 获取种子的 `site_id` 和 `torrent_id`
  - 查询 `hr_cases` 表，查找对应的 HR 记录
  - 如果 HR 状态为 `ACTIVE` 或 `UNKNOWN`：
    - 检查剩余时间：如果 < 24 小时，记录高风险警告
    - 检查保种要求：如果未满足，记录高风险警告
  - 记录警告日志，但不阻止下载（仅提醒）
- 确保下载任务的 `extra_metadata` 包含 `site_id` 和 `torrent_id`（用于后续 HR 保护）

**实现细节**：
- 使用 `SqlAlchemyHRCasesRepository` 查询 HR 记录
- 检查配置开关 `intel_subscription_respect_site_guard`
- 如果检查失败，保守策略：继续下载，不记录警告

---

## 📝 使用指南

### 1. 查看下载任务的 Local Intel 状态

在下载任务列表中，每个任务会显示两个状态标签：
- **HR 状态**：显示该种子的 HR 风险等级
- **站点状态**：显示该种子来源站点的健康状态

点击状态标签可跳转到 Local Intel 面板，查看详细信息。

### 2. 配置 Local Intel 设置

在系统设置页面 → "Local Intel 设置" 分类中，可以配置：
- **启用 Local Intel**：总开关
- **HR 保护模式**：严格模式（更谨慎）或宽松模式（减少影响）
- **在 MOVE 前强制执行 HR 检查**：是否在移动文件前检查 HR 状态
- **订阅任务尊重站点风控状态**：是否在订阅刷新时跳过被限流站点

### 3. 订阅任务的 Intel 感知

启用"订阅任务尊重站点风控状态"后：
- **订阅刷新时**：如果订阅关联的所有站点都被限流，该订阅会被跳过，不会执行搜索
- **选择种子时**：如果选择的种子存在 HR 风险，会在日志中记录警告，但不阻止下载

---

## 🔧 配置要求

1. **数据库表**
   - 确保已运行 `migrate_local_intel_schema.py` 创建相关表
   - 表包括：`hr_cases`, `inbox_events`, `site_guard_events`, `site_guard_profiles`, `inbox_cursor`

2. **站点配置**
   - 确保 `config/intel_sites/*.yaml` 中有站点配置
   - 确保数据库 `sites` 表中有对应站点记录且 `is_active=True` 且有 `cookie`

3. **Local Intel 开关**
   - 确保 `INTEL_ENABLED=true` 在配置中启用
   - 在系统设置中启用 `intel_enabled` 和 `intel_subscription_respect_site_guard`

---

## ⚠️ 注意事项

1. **下载任务状态显示**
   - 状态显示依赖 `extra_metadata` 中的 `site_id` 和 `torrent_id`
   - 如果下载任务没有这些信息，状态会显示为 `UNKNOWN`
   - 建议在创建下载任务时确保包含这些信息

2. **订阅任务感知**
   - 订阅刷新时的站点状态检查是"跳过"而非"延迟"
   - 被跳过的订阅会在下次刷新时再次检查
   - 如果所有站点都被限流，订阅会被跳过，但不会记录错误

3. **HR 风险检查**
   - HR 风险检查仅记录警告，不会阻止下载
   - 实际的 HR 保护在文件移动时执行（Phase 5）
   - 如果站点未配置或检查失败，不会记录警告

4. **配置开关**
   - 所有 Local Intel 功能都受 `intel_enabled` 总开关控制
   - 各个子功能有独立的开关，可以单独启用/禁用
   - 建议在生产环境中先测试，再逐步启用功能

---

## 📊 测试建议

### 1. 下载任务状态显示测试

```bash
# 创建测试下载任务（确保包含 site_id 和 torrent_id）
curl -X POST "http://localhost:8092/api/downloads" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Download",
    "magnet_link": "magnet:?xt=urn:btih:...",
    "extra_metadata": {
      "site_id": "hdsky",
      "torrent_id": "12345"
    }
  }'

# 查询下载任务列表，检查状态字段
curl -X GET "http://localhost:8092/api/downloads"
```

### 2. Local Intel 配置测试

```bash
# 获取配置
curl -X GET "http://localhost:8092/api/intel/settings"

# 更新配置
curl -X PUT "http://localhost:8092/api/intel/settings" \
  -H "Content-Type: application/json" \
  -d '{
    "intel_enabled": true,
    "intel_hr_mode": "strict",
    "intel_move_check_enabled": true,
    "intel_subscription_respect_site_guard": true
  }'
```

### 3. 订阅任务感知测试

1. **站点限流测试**：
   - 手动触发站点限流（通过 Site Guard）
   - 创建订阅，关联被限流的站点
   - 触发订阅刷新，验证订阅是否被跳过

2. **HR 风险检查测试**：
   - 创建 HR 记录（通过 HRWatcher）
   - 创建订阅，选择存在 HR 风险的种子
   - 触发订阅自动下载，验证是否记录警告日志

---

## 🚀 后续优化建议

1. **下载任务状态优化**
   - 添加状态详情查看（点击状态标签显示详细信息）
   - 添加批量操作（批量检查 HR 状态、批量跳转到 Local Intel）
   - 添加状态过滤（只显示有 HR 风险的任务）

2. **订阅任务感知优化**
   - 添加延迟重试机制（被跳过的订阅延迟一段时间后重试）
   - 添加优先级调整（高风险订阅降低优先级）
   - 添加通知提醒（站点被限流时发送通知）

3. **配置管理优化**
   - 添加配置导入/导出功能
   - 添加配置验证（检查配置是否合理）
   - 添加配置历史记录（记录配置变更）

---

**完成时间**: 2025-01-XX  
**实施人员**: Cursor AI Assistant

