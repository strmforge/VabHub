# VabHub下一步工作计划 - 前端WebSocket集成

**更新时间**: 2025-01-XX  
**当前状态**: 后端WebSocket已实现，需要前端集成

---

## 📋 一、当前状态

### ✅ 已完成（后端）
- ✅ WebSocket服务器实现（`backend/app/api/websocket.py`）
- ✅ 连接管理器（`ConnectionManager`）
- ✅ 主题订阅机制
- ✅ 消息广播功能
- ✅ 心跳检测（ping/pong）
- ✅ 后台任务（定期推送仪表盘数据）

### ⏳ 待实现（前端）
- ⏳ WebSocket客户端封装
- ⏳ 仪表盘实时数据更新
- ⏳ 下载任务实时进度更新
- ⏳ 系统资源实时监控
- ⏳ 自动重连机制

---

## 📋 二、实施计划

### 阶段1：WebSocket客户端封装（优先级：高）⭐⭐⭐⭐⭐

**目标**: 创建可复用的WebSocket客户端

**任务清单**:
1. **创建WebSocket服务**
   - 文件：`frontend/src/services/websocket.ts`
   - 功能：
     - WebSocket连接管理
     - 自动重连机制
     - 主题订阅管理
     - 消息处理
     - 心跳检测

2. **创建WebSocket Store**
   - 文件：`frontend/src/stores/websocket.ts`
   - 功能：
     - 连接状态管理
     - 订阅主题管理
     - 消息队列管理
     - 错误处理

**预计时间**: 1-2小时

---

### 阶段2：仪表盘实时更新（优先级：高）⭐⭐⭐⭐⭐

**目标**: 仪表盘数据实时更新

**任务清单**:
1. **更新Dashboard.vue**
   - 集成WebSocket客户端
   - 订阅`dashboard`主题
   - 实时更新仪表盘数据
   - 显示连接状态

2. **更新Dashboard Store**
   - 添加WebSocket消息处理
   - 实时更新统计数据
   - 优化数据合并逻辑

**预计时间**: 1-2小时

---

### 阶段3：下载任务实时更新（优先级：高）⭐⭐⭐⭐

**目标**: 下载任务进度实时更新

**任务清单**:
1. **更新Downloads.vue**
   - 集成WebSocket客户端
   - 订阅`downloads`主题
   - 实时更新下载进度
   - 实时更新下载状态

2. **更新Download Store**
   - 添加WebSocket消息处理
   - 实时更新任务列表
   - 优化进度显示

**预计时间**: 1-2小时

---

### 阶段4：系统资源实时监控（优先级：中）⭐⭐⭐

**目标**: 系统资源实时监控

**任务清单**:
1. **更新SystemResourceMonitor组件**
   - 集成WebSocket客户端
   - 订阅`system`主题
   - 实时更新系统资源数据
   - 优化图表更新

**预计时间**: 1小时

---

## 📋 三、技术实现

### 3.1 WebSocket客户端封装

**实现方案**:
```typescript
// frontend/src/services/websocket.ts
class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectTimer: number | null = null
  private heartbeatTimer: number | null = null
  private subscriptions: Set<string> = new Set()
  private messageHandlers: Map<string, Function[]> = new Map()
  
  connect(): void
  disconnect(): void
  subscribe(topics: string[]): void
  unsubscribe(topics: string[]): void
  onMessage(type: string, handler: Function): void
  send(message: object): void
}
```

### 3.2 仪表盘实时更新

**实现方案**:
```typescript
// 在Dashboard.vue中
import { useWebSocket } from '@/services/websocket'

const ws = useWebSocket()
ws.subscribe(['dashboard'])
ws.onMessage('dashboard_update', (data) => {
  dashboardStore.updateData(data)
})
```

### 3.3 下载任务实时更新

**实现方案**:
```typescript
// 在Downloads.vue中
const ws = useWebSocket()
ws.subscribe(['downloads'])
ws.onMessage('download_update', (data) => {
  downloadStore.updateTask(data)
})
```

---

## 📋 四、详细实施步骤

### 步骤1：创建WebSocket服务

**文件**: `frontend/src/services/websocket.ts`

**功能**:
- WebSocket连接管理
- 自动重连（指数退避）
- 主题订阅
- 消息路由
- 心跳检测

### 步骤2：创建WebSocket Store

**文件**: `frontend/src/stores/websocket.ts`

**功能**:
- 连接状态
- 订阅主题列表
- 消息队列
- 错误处理

### 步骤3：集成到仪表盘

**文件**: `frontend/src/pages/Dashboard.vue`

**修改**:
- 导入WebSocket服务
- 订阅`dashboard`主题
- 处理`dashboard_update`消息
- 实时更新数据

### 步骤4：集成到下载管理

**文件**: `frontend/src/pages/Downloads.vue`

**修改**:
- 导入WebSocket服务
- 订阅`downloads`主题
- 处理`download_update`消息
- 实时更新进度

### 步骤5：集成到系统监控

**文件**: `frontend/src/components/dashboard/SystemResourceMonitor.vue`

**修改**:
- 导入WebSocket服务
- 订阅`system`主题
- 处理`system_update`消息
- 实时更新图表

---

## 📋 五、预期效果

### 5.1 用户体验提升

- ✅ 仪表盘数据实时更新（无需刷新）
- ✅ 下载进度实时显示
- ✅ 系统资源实时监控
- ✅ 连接状态可视化

### 5.2 性能优化

- ✅ 减少HTTP轮询请求
- ✅ 降低服务器负载
- ✅ 提升响应速度

---

## 📋 六、测试计划

### 6.1 功能测试

- ✅ WebSocket连接测试
- ✅ 主题订阅测试
- ✅ 消息接收测试
- ✅ 自动重连测试

### 6.2 性能测试

- ✅ 连接稳定性测试
- ✅ 消息处理性能测试
- ✅ 内存泄漏测试

---

## 📋 七、后续优化

### 7.1 功能增强

- 消息队列管理
- 离线消息缓存
- 消息优先级
- 批量消息处理

### 7.2 性能优化

- 消息压缩
- 连接池管理
- 智能重连策略

---

**文档生成时间**: 2025-01-XX  
**推荐方案**: 阶段1（WebSocket客户端封装）  
**预计时间**: 1-2小时  
**优先级**: ⭐⭐⭐⭐⭐

