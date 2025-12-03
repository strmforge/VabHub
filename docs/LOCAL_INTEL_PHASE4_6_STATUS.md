# Local Intel Phase 4-6 实施状态

**实施时间**: 2025-11-18  
**状态**: ✅ **Phase 4-6 代码实施完成**

---

## 📋 实施概览

本次完成了 Local Intel 的 Phase 4-6，实现了：
- **Phase 4**: 站点 HTTP + HTML 解析 + 调度（本地抓站）
- **Phase 5**: 移动/删源前 HR 安全检查（防误删）
- **Phase 6**: API + 前端看板（人能看见的本地大脑）

---

## ✅ Phase 4: 站点 HTTP + HTML 解析 + 调度

### 完成内容

1. **HTTP 客户端实现**
   - 创建 `app/core/intel_local/http_clients_impl.py`
   - 实现 `HttpxSiteHttpClient`，基于 `httpx.AsyncClient` + Site 模型的 cookie
   - 支持 `fetch_hr_page()` 和 `fetch_inbox_page()`

2. **HTML 解析器实现**
   - 更新 `app/core/intel_local/parsers/hr_html_parser.py`
     - 实现 `parse_hr_page_generic()`（NexusPHP 通用格式）
     - 实现 `parse_hr_page_hdsky()`（基于通用解析）
   - 更新 `app/core/intel_local/parsers/inbox_html_parser.py`
     - 实现 `parse_inbox_page_generic()`（NexusPHP 通用格式）
     - 实现 `parse_inbox_page_ttg()`（特殊处理无主题消息）

3. **启动时注册 HTTP 客户端**
   - 在 `app/core/intel_local/factory.py` 中添加 `register_site_http_clients()`
   - 在 `backend/main.py` 的 lifespan 中调用注册函数
   - 自动从数据库加载已激活且有 cookie 的站点，匹配 `intel_sites` 配置后注册

4. **站点配置扩展**
   - 在 `HRConfig` 和 `InboxConfig` 中添加 `page_path` 字段
   - 支持从 YAML 配置中读取页面路径

### 已接入的站点

- **hdsky**: HR 页面解析 + 站内信解析（NexusPHP 格式）
- **ttg**: 站内信解析（特殊处理无主题消息）

### 文件清单

- `backend/app/core/intel_local/http_clients_impl.py` (新建)
- `backend/app/core/intel_local/parsers/hr_html_parser.py` (更新)
- `backend/app/core/intel_local/parsers/inbox_html_parser.py` (更新)
- `backend/app/core/intel_local/site_profiles.py` (更新，添加 page_path)
- `backend/app/core/intel_local/factory.py` (更新，添加注册函数)
- `backend/main.py` (更新，启动时注册客户端)

---

## ✅ Phase 5: 移动/删源前 HR 安全检查

### 完成内容

1. **Engine 安全检查方法**
   - 在 `app/core/intel_local/engine.py` 中添加 `is_move_safe()` 方法
   - 查询 `hr_cases` 表，检查种子是否有未完成的 HR 记录
   - 逻辑：
     - HR 已完成/不存在 → 安全（可删除）
     - HR ACTIVE/UNKNOWN + 已过期 → 安全
     - HR ACTIVE/UNKNOWN + 已满足保种要求 → 安全
     - HR ACTIVE/UNKNOWN + 未完成 → 不安全（不应删除）

2. **文件传输服务集成**
   - 更新 `app/modules/file_operation/transfer_service.py`
   - 在 `transfer_file()` 中，删除源文件前调用 HR 检查
   - 如果不安全，自动将 `MOVE` 改为 `COPY`（保留源文件）

### 接入位置

- **核心函数**: `app/modules/file_operation/transfer_service.py::transfer_file()`
- **检查逻辑**: `app/core/intel_local/engine.py::is_move_safe()`

### 文件清单

- `backend/app/core/intel_local/engine.py` (更新，添加 is_move_safe)
- `backend/app/modules/file_operation/transfer_service.py` (更新，集成 HR 检查)

---

## ✅ Phase 6: API + 前端看板

### 完成内容

1. **后端 API**
   - 创建 `app/api/intel.py`
   - 实现三个只读 API：
     - `GET /api/intel/hr-tasks`: HR 任务列表（支持站点/状态过滤，按风险排序）
     - `GET /api/intel/events`: 智能事件列表（TODO: 从数据库查询）
     - `GET /api/intel/sites`: 站点健康状态列表

2. **API 路由注册**
   - 在 `app/api/__init__.py` 中注册 `intel.router`

### API 端点

- `GET /api/intel/hr-tasks?site=hdsky&status=ACTIVE`
  - 返回 HR 任务列表，包含：id, site, torrent_id, title, hr_status, deadline, seeding_time, risk_level

- `GET /api/intel/events?site=ttg&limit=50`
  - 返回智能事件列表（TODO: 需要完善数据库查询）

- `GET /api/intel/sites`
  - 返回站点健康状态列表，包含：id, name, last_ok, last_error, is_throttled, error_count

### 文件清单

- `backend/app/api/intel.py` (新建)
- `backend/app/api/__init__.py` (更新，注册路由)

---

## 📝 使用指南

### 1. 手动触发站点刷新

使用已有的调试 API：

```bash
POST /api/admin/local-intel/refresh/{site_id}
```

例如：
```bash
curl -X POST http://localhost:8092/api/admin/local-intel/refresh/hdsky
```

返回示例：
```json
{
  "site": "hdsky",
  "actions": [
    {
      "type": "hr_record_progress",
      "site": "hdsky",
      "torrent_id": "12345",
      "title": "某剧 S01E01",
      "level": "info",
      "payload": {
        "required_seed_hours": 72.0,
        "seeded_hours": 48.0,
        "ratio": 0.67
      }
    }
  ]
}
```

### 2. 查看 HR 任务列表

```bash
GET /api/intel/hr-tasks?site=hdsky
```

### 3. 查看站点健康状态

```bash
GET /api/intel/sites
```

### 4. HR 保护验证

当下载任务完成并尝试移动/删除源文件时：
- 如果种子有未完成的 HR 记录，系统会自动将 `MOVE` 改为 `COPY`
- 日志中会显示：`LocalIntel: protect source file for HR candidate torrent (site=hdsky, torrent_id=12345)`

---

## 🔧 配置要求

1. **站点配置** (`config/intel_sites/*.yaml`)
   - 确保站点配置文件中包含 `hr.page_path` 或 `inbox.page_path`
   - 示例：`hdsky.yaml` 中 `hr.page_path: "hr.php"`

2. **数据库站点表**
   - 确保 `sites` 表中有对应站点的记录
   - 站点必须 `is_active=True` 且有 `cookie` 字段

3. **Local Intel 开关**
   - 确保 `INTEL_ENABLED=true` 在配置中启用

---

## ⚠️ 注意事项

1. **站点匹配**
   - HTTP 客户端注册时，会尝试匹配数据库中的站点名和 `intel_sites` 配置中的 `site` 字段
   - 如果匹配失败，该站点不会注册 HTTP 客户端

2. **HTML 解析**
   - 当前解析器基于 BeautifulSoup，对 NexusPHP 标准格式支持较好
   - 如果站点页面结构特殊，可能需要调整解析逻辑

3. **前端看板**
   - Phase 6 只完成了后端 API，前端页面需要后续实现
   - 建议在"高级/实验室"页面中添加 Local Intel 面板

4. **事件查询**
   - `/api/intel/events` 目前返回空列表，需要完善 `inbox_events` 表的查询逻辑

---

## 🚀 后续优化建议

1. **完善事件查询**
   - 实现从 `inbox_events` 表查询最近事件
   - 实现从 `site_guard_events` 表查询风控事件

2. **前端看板实现**
   - 创建 `LocalIntel.vue` 页面
   - 显示 HR 任务表格和事件时间线

3. **调度优化**
   - 实现增量抓取（只抓最近 N 页/最近 N 天）
   - 完善 Site Guard 的风控检测和节流逻辑

4. **错误处理**
   - 增强 HTTP 请求的错误处理和重试机制
   - 记录连续错误，自动延长轮询间隔

---

## 📊 测试建议

1. **HTTP 客户端测试**
   - 确保站点 cookie 有效
   - 手动调用 `register_site_http_clients()` 验证注册

2. **HTML 解析测试**
   - 使用真实站点页面 HTML 测试解析器
   - 验证解析出的 torrent_id、时长、截止时间等字段

3. **HR 保护测试**
   - 创建一个有 HR 记录的下载任务
   - 验证移动文件时是否自动改为 COPY

4. **API 测试**
   - 使用 Postman 或 curl 测试三个 API 端点
   - 验证返回数据格式是否符合预期

---

---

## ✅ Phase 7: 前后端打通 & 可视化面板

### 完成内容

1. **补完 `/api/intel/events` 查询逻辑**
   - 从 `inbox_events` 表查询站内信事件（HR_PENALTY, TORRENT_DELETED, SITE_THROTTLED）
   - 从 `site_guard_events` 表查询站点风控事件
   - 支持按站点过滤、时间起点过滤、数量限制
   - 统一事件格式，按时间倒序返回

2. **完善 `/api/intel/sites` 查询逻辑**
   - 查询最近成功时间（从 HR 记录和站内信记录推断）
   - 查询最近错误时间（从风控事件获取）
   - 判断站点是否处于限流状态
   - 统计最近 24 小时内的错误次数

3. **前端 Local Intel 面板**
   - 创建 `frontend/src/pages/LocalIntel.vue`
   - 实现三个主要区域：
     - **HR 任务表格**：显示站点、标题、HR 状态、截止时间、已保种时间、风险等级
     - **智能事件时间线**：使用 Vuetify Timeline 组件展示事件，支持按站点过滤
     - **站点健康状态卡片**：显示每个站点的健康指标和手动刷新按钮
   - 支持站点过滤、状态过滤、手动刷新等功能

4. **路由和导航集成**
   - 在 `frontend/src/router/index.ts` 中添加 `/local-intel` 路由
   - 在 `frontend/src/layouts/components/AppDrawer.vue` 中添加导航菜单项
   - 菜单项位于"其他功能"部分，带有 "PRO" 标签

### 文件清单

- `backend/app/api/intel.py` (更新，补完 events 和 sites 查询逻辑)
- `frontend/src/pages/LocalIntel.vue` (新建)
- `frontend/src/router/index.ts` (更新，添加路由)
- `frontend/src/layouts/components/AppDrawer.vue` (更新，添加菜单项)

---

## 📝 使用指南（更新）

### 1. 访问 Local Intel 面板

在浏览器中打开：
```
http://localhost:3000/local-intel
```

或通过左侧导航菜单 → "其他功能" → "Local Intel 智能监控" 访问。

### 2. 查看 HR 任务列表

- 页面会自动加载所有 HR 任务
- 支持按站点和状态过滤
- 表格显示：站点、标题、HR 状态、截止时间、已保种时间、风险等级
- 风险等级颜色标识：高风险（红色）、中风险（黄色）、低风险（绿色）

### 3. 查看智能事件时间线

- 页面会自动加载最近 100 条智能事件
- 支持按站点过滤
- 事件类型包括：
  - **HR_PENALTY**（红色）：HR 扣分通知
  - **TORRENT_DELETED**（黄色）：种子删除通知
  - **SITE_THROTTLED**（黄色）：站点风控/限流
  - **OTHER**（蓝色）：其他事件

### 4. 查看站点健康状态

- 显示每个站点的：
  - 上次成功时间
  - 上次错误时间
  - 错误次数（最近 24 小时）
  - 是否处于限流状态
- 每个站点卡片提供"手动刷新"按钮，可调用 `/api/admin/local-intel/refresh/{site_id}`

### 5. API 使用示例

#### 获取 HR 任务列表
```bash
curl -X GET "http://localhost:8092/api/intel/hr-tasks?site=hdsky&status=ACTIVE"
```

#### 获取智能事件
```bash
curl -X GET "http://localhost:8092/api/intel/events?site=ttg&limit=50&since=2025-11-15T00:00:00Z"
```

#### 获取站点健康状态
```bash
curl -X GET "http://localhost:8092/api/intel/sites"
```

#### 手动刷新站点
```bash
curl -X POST "http://localhost:8092/api/admin/local-intel/refresh/hdsky"
```

---

## 🔧 配置要求（更新）

1. **站点配置** (`config/intel_sites/*.yaml`)
   - 确保站点配置文件中包含 `hr.page_path` 或 `inbox.page_path`
   - 示例：`hdsky.yaml` 中 `hr.page_path: "hr.php"`

2. **数据库站点表**
   - 确保 `sites` 表中有对应站点的记录
   - 站点必须 `is_active=True` 且有 `cookie` 字段

3. **Local Intel 开关**
   - 确保 `INTEL_ENABLED=true` 在配置中启用

4. **数据库表**
   - 确保已运行 `migrate_local_intel_schema.py` 创建相关表：
     - `hr_cases`
     - `inbox_events`
     - `site_guard_events`
     - `site_guard_profiles`
     - `inbox_cursor`

---

## ⚠️ 注意事项（更新）

1. **站点匹配**
   - HTTP 客户端注册时，会尝试匹配数据库中的站点名和 `intel_sites` 配置中的 `site` 字段
   - 如果匹配失败，该站点不会注册 HTTP 客户端

2. **HTML 解析**
   - 当前解析器基于 BeautifulSoup，对 NexusPHP 标准格式支持较好
   - 如果站点页面结构特殊，可能需要调整解析逻辑

3. **事件数据**
   - 事件数据来自站内信解析和站点风控记录
   - 如果站点未配置站内信或未触发风控，事件列表可能为空

4. **HR 保护逻辑**
   - HR 保护在文件移动/删除前自动生效
   - 如果种子有未完成的 HR 记录，系统会自动将 `MOVE` 改为 `COPY`
   - 日志中会显示保护操作

---

## 🚀 后续优化建议

1. **事件查询优化**
   - 可以考虑添加事件类型过滤
   - 支持分页加载更多历史事件

2. **前端功能增强**
   - 添加事件详情展开/折叠
   - 添加 HR 任务详情查看
   - 添加站点健康趋势图表

3. **调度优化**
   - 实现增量抓取（只抓最近 N 页/最近 N 天）
   - 完善 Site Guard 的风控检测和节流逻辑

4. **错误处理**
   - 增强 HTTP 请求的错误处理和重试机制
   - 记录连续错误，自动延长轮询间隔

---

## 📊 测试建议（更新）

1. **API 测试**
   - 使用 Postman 或 curl 测试三个 API 端点
   - 验证返回数据格式是否符合预期
   - 测试过滤参数是否正常工作

2. **前端测试**
   - 访问 `/local-intel` 页面
   - 验证三个区域的数据是否正确加载
   - 测试过滤和刷新功能
   - 测试手动刷新站点功能

3. **HR 保护测试**
   - 创建一个有 HR 记录的下载任务
   - 验证移动文件时是否自动改为 COPY
   - 查看日志确认保护操作

4. **事件生成测试**
   - 手动触发站点刷新，观察是否生成事件
   - 验证事件时间线是否正确显示

---

**完成时间**: 2025-11-18  
**实施人员**: Cursor AI Assistant  
**Phase 7 完成时间**: 2025-11-18

