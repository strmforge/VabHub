# Local Intel Phase 7 实施状态

**实施时间**: 2025-11-18  
**状态**: ✅ **Phase 7 代码实施完成**

---

## 📋 实施概览

本次完成了 Local Intel 的 Phase 7：前后端打通 & 可视化面板，实现了：
- **补完 `/api/intel/events` 查询逻辑**：从数据库查询站内信事件和站点风控事件
- **完善 `/api/intel/sites` 查询逻辑**：查询站点健康状态（成功时间、错误时间、限流状态、错误次数）
- **实现前端 Local Intel 面板**：HR 任务表格、智能事件时间线、站点健康状态卡片
- **路由和导航集成**：添加到前端路由和导航菜单

---

## ✅ 后端 API 补完

### 1. `/api/intel/events` 查询逻辑

**实现内容**：
- 从 `inbox_events` 表查询站内信事件
- 从 `site_guard_events` 表查询站点风控事件
- 支持参数：
  - `site`：按站点过滤
  - `limit`：返回数量限制（默认 100）
  - `since`：时间起点（ISO 格式字符串）
- 统一事件格式，按时间倒序返回

**事件类型映射**：
- `penalty` → `HR_PENALTY`
- `delete` → `TORRENT_DELETED`
- `throttle` → `SITE_THROTTLED`
- `other` → `OTHER`

**返回格式**：
```json
{
  "items": [
    {
      "id": "inbox_123",
      "site": "hdsky",
      "type": "HR_PENALTY",
      "title": "hdsky: HR_PENALTY",
      "message": "种子 ID: 12345. 事件类型: penalty",
      "torrent_id": "12345",
      "created_at": "2025-11-18T10:00:00"
    }
  ]
}
```

### 2. `/api/intel/sites` 查询逻辑

**实现内容**：
- 查询最近成功时间（从 HR 记录和站内信记录推断）
- 查询最近错误时间（从风控事件获取）
- 判断站点是否处于限流状态（检查 `block_until` 是否在未来）
- 统计最近 24 小时内的错误次数

**返回格式**：
```json
{
  "items": [
    {
      "id": "hdsky",
      "name": "HDsky",
      "last_ok": "2025-11-18T09:00:00",
      "last_error": "2025-11-18T08:00:00",
      "is_throttled": false,
      "error_count": 0
    }
  ]
}
```

---

## ✅ 前端 Local Intel 面板

### 页面结构

**文件位置**：`frontend/src/pages/LocalIntel.vue`

**三个主要区域**：

1. **HR 任务表格区域**
   - 使用 `v-data-table` 显示 HR 任务列表
   - 支持按站点和状态过滤
   - 显示列：站点、标题、HR 状态、截止时间、已保种时间、风险等级
   - 风险等级颜色标识：高风险（红色）、中风险（黄色）、低风险（绿色）

2. **智能事件时间线区域**
   - 使用 `v-timeline` 组件展示事件
   - 支持按站点过滤
   - 事件卡片显示：时间、站点、类型、标题、消息、种子ID
   - 不同类型事件使用不同颜色和图标

3. **站点健康状态区域**
   - 使用卡片网格布局
   - 每个站点显示：名称、上次成功时间、上次错误时间、错误次数、是否限流
   - 限流中的站点用警告色标识
   - 每个站点提供"手动刷新"按钮

### 功能特性

- **自动加载**：页面加载时自动获取三个区域的数据
- **手动刷新**：提供"刷新全部"按钮和各个区域的独立刷新按钮
- **站点过滤**：HR 任务和事件支持按站点过滤
- **状态过滤**：HR 任务支持按状态过滤
- **错误处理**：使用 Toast 提示显示错误信息
- **加载状态**：显示加载动画和加载提示

---

## ✅ 路由和导航集成

### 路由配置

**文件**：`frontend/src/router/index.ts`

**路由项**：
```typescript
{
  path: '/local-intel',
  name: 'LocalIntel',
  component: () => import('@/pages/LocalIntel.vue'),
  meta: { requiresAuth: true, title: 'Local Intel 智能监控', badge: 'PRO' }
}
```

### 导航菜单

**文件**：`frontend/src/layouts/components/AppDrawer.vue`

**菜单位置**：位于"其他功能"部分，在"调度器监控"和"系统自检"之间

**菜单项**：
- 图标：`mdi-brain`
- 标题：`Local Intel 智能监控`
- 标签：`PRO`（黄色警告色）

---

## 📝 使用指南

### 1. 访问页面

在浏览器中打开：
```
http://localhost:3000/local-intel
```

或通过左侧导航菜单 → "其他功能" → "Local Intel 智能监控" 访问。

### 2. 查看 HR 任务

- 页面加载时自动显示所有 HR 任务
- 使用顶部过滤器按站点或状态筛选
- 点击刷新按钮重新加载数据

### 3. 查看智能事件

- 页面加载时自动显示最近 100 条事件
- 使用顶部过滤器按站点筛选
- 事件按时间倒序排列，最新事件在顶部

### 4. 查看站点健康状态

- 页面加载时自动显示所有配置站点的健康状态
- 限流中的站点用黄色警告色标识
- 点击"手动刷新"按钮可触发站点刷新

### 5. API 调用示例

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

## 🔧 配置要求

1. **数据库表**
   - 确保已运行 `migrate_local_intel_schema.py` 创建相关表
   - 表包括：`hr_cases`, `inbox_events`, `site_guard_events`, `site_guard_profiles`, `inbox_cursor`

2. **站点配置**
   - 确保 `config/intel_sites/*.yaml` 中有站点配置
   - 确保数据库 `sites` 表中有对应站点记录且 `is_active=True` 且有 `cookie`

3. **Local Intel 开关**
   - 确保 `INTEL_ENABLED=true` 在配置中启用

---

## ⚠️ 注意事项

1. **事件数据来源**
   - 事件数据来自站内信解析和站点风控记录
   - 如果站点未配置站内信或未触发风控，事件列表可能为空
   - 需要先触发站点刷新（手动或自动）才会生成事件记录

2. **站点健康状态**
   - 成功时间从 HR 记录和站内信记录推断，如果都没有记录，显示"未知"
   - 错误时间从风控事件获取，如果没有风控事件，显示"无"
   - 限流状态检查 `block_until` 是否在未来，如果已过期则显示为未限流

3. **前端 API 调用**
   - 使用项目现有的 `api` 实例（`@/services/api`）
   - API 路径使用 `/intel/...` 前缀
   - 错误处理使用 Toast 提示

---

## 📊 测试建议

1. **后端 API 测试**
   ```bash
   # 测试 HR 任务列表
   curl -X GET "http://localhost:8092/api/intel/hr-tasks"
   
   # 测试智能事件
   curl -X GET "http://localhost:8092/api/intel/events?limit=10"
   
   # 测试站点健康状态
   curl -X GET "http://localhost:8092/api/intel/sites"
   ```

2. **前端页面测试**
   - 访问 `/local-intel` 页面
   - 验证三个区域的数据是否正确加载
   - 测试过滤功能（站点、状态）
   - 测试刷新功能（全部刷新、单个区域刷新、站点手动刷新）
   - 验证错误提示是否正常显示

3. **数据生成测试**
   - 手动触发站点刷新：`POST /api/admin/local-intel/refresh/{site_id}`
   - 观察事件时间线是否出现新事件
   - 观察站点健康状态是否更新

---

## 🚀 后续优化建议

1. **事件查询优化**
   - 添加事件类型过滤（只显示 HR_PENALTY 等）
   - 支持分页加载更多历史事件
   - 添加事件搜索功能

2. **前端功能增强**
   - 添加事件详情展开/折叠
   - 添加 HR 任务详情查看（点击查看详情）
   - 添加站点健康趋势图表（使用 Chart.js）
   - 添加自动刷新功能（定时刷新数据）

3. **用户体验优化**
   - 添加数据为空时的友好提示
   - 优化加载状态显示
   - 添加数据导出功能（导出 HR 任务列表、事件列表）

---

**完成时间**: 2025-11-18  
**实施人员**: Cursor AI Assistant

