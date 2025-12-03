# 通知中心重构 - 变更日志

## 概述
本次重构实现了通知中心的分类体系、批量操作功能，并优化了用户界面和交互体验。

## 主要变更

### 🏗️ 架构变更
- **新增通知分类体系**：6个分类（阅读、下载、音乐、插件、系统、其他）
- **后端API统一化**：所有用户通知API统一到 `/api/user/notifications/*` 路径
- **组件增强**：ReadingNotificationCard 支持选择功能，NotificationDrawer 支持快速过滤

### 📡 API 变更

#### 新增端点
- `GET /api/user/notifications/unread-count-by-category` - 获取按分类统计的未读数量
- `POST /api/user/notifications/mark-read` - 批量标记已读（支持ID列表和分类）
- `DELETE /api/user/notifications/batch` - 批量删除通知（支持ID列表和分类）

#### 更新端点
- `GET /api/user/notifications/` - 新增 `category` 过滤参数
- `DELETE /api/user/notifications/{id}` - 新增用户权限验证
- `DELETE /api/user/notifications/` - 新增用户权限验证

#### 响应格式变更
```typescript
// 新增分类字段
interface UserNotificationItem {
  id: number
  user_id: number
  type: string
  category: NotificationCategory  // 新增字段
  media_type?: string
  title: string
  message: string
  is_read: boolean
  created_at: string
  payload?: any
}

// 分类未读统计响应
interface CategoryUnreadCountResponse {
  unread_by_category: Record<string, number>
  total_unread: number
}
```

### 🎨 前端组件变更

#### UserNotifications.vue (全屏页)
- **布局重构**：左右两栏布局（分类过滤 + 通知列表）
- **批量操作工具栏**：全选、批量标记已读、批量删除
- **URL参数同步**：过滤状态保存在URL中，支持分享和刷新
- **分类统计卡片**：显示各分类未读数量

#### NotificationDrawer.vue (抽屉组件)
- **快速分类过滤**：水平分类芯片组，支持未读数量徽章
- **全屏页联动**："查看全部通知"按钮，保持过滤状态跳转
- **状态同步优化**：与全屏页保持状态一致性

#### ReadingNotificationCard.vue (阅读通知卡片)
- **选择功能**：新增 `selectable`、`selected` props 和 `@toggle-select` 事件
- **向后兼容**：默认不显示选择框，不影响现有使用

### 🔧 类型定义变更

#### 新增类型
```typescript
type NotificationCategory = 'reading' | 'download' | 'music' | 'plugin' | 'system' | 'other'
```

#### 更新接口
- `UserNotificationItem` 新增 `category` 字段
- `UserNotificationListQuery` 新增 `category` 过滤参数
- `MarkReadRequest` 复用于批量删除操作

### 🛠️ 后端实现变更

#### 新增文件
- `backend/app/core/notification_categories.py` - 通知分类体系核心逻辑

#### 更新文件
- `backend/app/api/notifications_user.py` - 新增批量操作端点，修复权限验证
- `backend/app/schemas/notify.py` - 新增分类相关字段和验证

## 兼容性说明

### ✅ 向后兼容
- 现有通知创建代码无需修改，系统自动根据通知类型分配分类
- 现有API调用继续工作，响应格式向后兼容
- 组件使用保持向后兼容，新功能通过可选props启用

### ⚠️ 注意事项
- 通知列表API响应新增 `category` 字段，客户端应忽略未知字段
- 批量删除为硬删除，操作不可恢复
- 抽屉组件高度计算已调整，需检查UI显示

## 性能优化

### 🚀 性能提升
- 分类统计使用数据库聚合查询，减少不必要的计算
- 前端采用乐观UI更新，提升用户体验
- 批量操作减少API调用次数

### 📊 监控指标
- 通知列表API响应时间 < 200ms
- 分类统计API响应时间 < 100ms
- 批量操作支持最多1000条通知

## 安全增强

### 🔒 权限验证
- 所有API端点增加用户权限验证
- 批量操作仅限用户自己的通知
- 删除操作增加确认对话框

### 🛡️ 数据验证
- API参数严格验证，防止无效输入
- 分类参数使用枚举验证
- 批量操作限制最大数量

## 使用示例

### 分类过滤
```typescript
// 按分类获取通知
const response = await notificationApi.list({
  category: 'reading',
  limit: 20,
  offset: 0
})

// 获取分类未读统计
const stats = await notificationApi.getCategoryUnreadCount()
console.log(stats.unread_by_category.reading) // 5
```

### 批量操作
```typescript
// 批量标记已读
await notificationApi.markReadBatch([1, 2, 3])

// 按分类批量标记已读
await notificationApi.markCategoryRead('reading')

// 批量删除
await notificationApi.deleteBatch([1, 2, 3])

// 按分类批量删除
await notificationApi.deleteCategory('reading')
```

### 组件使用
```vue
<!-- 带选择功能的通知卡片 -->
<ReadingNotificationCard
  :notification="notification"
  :selectable="true"
  :selected="selectedIds.has(notification.id)"
  @toggle-select="handleToggleSelect"
/>

<!-- 抽屉组件（自动支持分类过滤） -->
<NotificationDrawer v-model="drawerOpen" />
```

## 测试覆盖

### 🧪 功能测试
- [x] 通知分类自动分配
- [x] 分类过滤功能
- [x] 批量操作（标记已读、删除）
- [x] 状态同步机制
- [x] URL参数持久化

### 🔍 集成测试
- [x] 前后端API集成
- [x] 组件间状态同步
- [x] 用户权限验证
- [x] 错误处理机制

### 🎯 用户体验测试
- [x] 交互流程完整性
- [x] 视觉一致性检查
- [x] 响应式布局适配
- [x] 无障碍访问支持

## 部署说明

### 📋 部署清单
1. 更新后端代码并重启服务
2. 更新前端构建并部署
3. 验证API端点响应正常
4. 检查通知分类自动分配
5. 测试批量操作功能

### 🔄 数据库变更
本次重构无需数据库迁移，所有变更为代码层面。

### ⚙️ 配置更新
无需额外配置，系统自动启用新功能。

## 后续规划

### 🚀 功能扩展
- 通知模板系统
- 通知推送配置
- 通知归档功能
- 高级过滤条件

### 🔧 技术优化
- 实时通知推送
- 离线通知支持
- 通知搜索功能
- 性能监控集成

---

**版本**: 2.0.0  
**发布日期**: 2024-12-XX  
**维护团队**: VabHub 开发团队
