# NOTIFY-CENTER-2 阶段设计文档

## P0 现状巡检发现

### 关键架构发现：双通知系统

通过深入调查发现 VabHub 存在 **两套独立的通知系统**：

#### 1. 系统级通知系统 (Notification)
- **模型**: `backend/app/models/notification.py` 
- **API**: `/api/notifications` (notification.py)
- **用途**: 系统内部通知、渠道管理、状态跟踪
- **特点**: 支持 channels、status、level 等系统级字段

#### 2. 用户级通知系统 (UserNotification) ⭐ **实际使用**
- **模型**: `backend/app/models/user_notification.py`
- **API**: `/api/user/notifications` (notifications_user.py) 
- **用途**: 用户可见的通知（阅读、TTS、音乐等）
- **特点**: 包含 user_id、media_type、target_id、payload 等用户相关字段

### 前端实际使用情况

**前端实际使用的是用户级通知系统**：
- `notificationApi` 调用 `/api/user/notifications/recent` 和 `/api/notifications`
- **注意**: 存在 API 路径不一致问题 - 有些调用指向系统级，有些指向用户级
- `useNotificationStore` 管理用户通知状态
- `UserNotifications.vue` 已存在全屏通知页面

### 现有功能评估

#### ✅ 已具备的能力
1. **用户通知模型完整** - UserNotification 包含所有必要字段
2. **基础 API 完善** - 支持分页、过滤、标记已读、删除
3. **前端组件齐全** - Bell、Drawer、全屏页、专用卡片
4. **状态管理成熟** - Pinia store 支持轮询、乐观更新
5. **阅读通知集成** - READING-NOTIFY-1 已完成

#### ❌ 缺失的能力
1. **通知分类体系** - 缺少 NotificationCategory 概念
2. **高级过滤** - API 支持的过滤条件有限
3. **批量操作增强** - 缺少条件批量标记已读
4. **API 路径混乱** - 前端调用路径不统一

## NOTIFY-CENTER-2 实施策略

### 核心原则
**基于用户级通知系统 (UserNotification) 进行增强，避免重复建设**

### P1-P6 调整后的实施计划

#### P1 - 通知分类体系
**目标**: 为 UserNotification 系统增加分类概念
- 在 `backend/app/core/notification_types.py` 新增 `NotificationCategory`
- 建立 `NotificationType` → `NotificationCategory` 映射
- **不修改数据库结构** - 使用动态映射避免迁移

#### P2 - API 增强 (重点调整)
**目标**: 统一并增强用户通知 API
- **统一 API 路径**: 所有用户通知操作使用 `/api/user/notifications`
- **扩展过滤参数**: category、type、media_type、is_read、时间范围
- **增强批量操作**: 支持条件批量标记已读
- **修复前端 API 调用**: 确保所有调用指向用户级 API

#### P3 - 全屏页增强 (复用现有)
**目标**: 基于现有 `UserNotifications.vue` 增加高级功能
- **复用现有页面**: 不新建页面，在现有基础上增强
- **增加过滤侧栏**: 分类、状态、时间范围过滤
- **增强批量操作**: 条件批量标记已读功能

#### P4 - Drawer 联动
**目标**: 在现有 `NotificationDrawer` 中增加跳转入口
- 添加"查看全部通知"按钮
- 阅读通知卡片增加"只看阅读通知"快捷链接

#### P5 - 批量操作完善
**目标**: 实现安全的条件批量操作
- 后端: `POST /api/user/notifications/mark-read` 支持条件过滤
- 前端: 批量操作栏 + 确认对话框
- 状态同步: 确保 Drawer、Bell、Store 状态一致

#### P6 - 文档与 QA
**目标**: 完善文档和验收测试
- 更新 API 文档
- 编写使用场景说明
- 完整功能测试

### 关键技术决策

1. **数据库策略**: 不增加 category 列，使用 type → category 动态映射
2. **API 统一**: 所有用户通知操作统一到 `/api/user/notifications/*`
3. **组件复用**: 最大化复用现有组件，避免重复开发
4. **向后兼容**: 保持现有 API 接口兼容，仅扩展新功能

### 风险与缓解

**风险**: 前端 API 调用路径混乱可能导致功能异常
**缓解**: P2 阶段优先统一 API 路径，确保前端调用正确

**风险**: 双通知系统可能造成开发混淆
**缓解**: 明确文档说明，统一使用用户级通知系统

## 预期交付成果

完成 NOTIFY-CENTER-2 后，用户将获得：
1. **统一的通知总控制台** - 支持多维度过滤和批量操作
2. **清晰的通知分类** - 阅读、音乐、系统、下载等分类视图
3. **高效的批量管理** - 条件批量标记已读功能
4. **流畅的交互体验** - Drawer 与全屏页无缝联动

## 下一步行动

1. 确认本设计策略是否符合预期
2. 开始 P1 实施：建立通知分类体系
3. 优先解决 API 路径统一问题
