# READING-NOTIFY-1 技术规范文档

> 阅读事件集成到通知中心系统的完整技术实现

## 概述

READING-NOTIFY-1 将阅读相关事件（漫画更新、电子书导入、有声书就绪）集成到现有通知中心系统，提供标准化的通知类型、统一的 payload 结构和增强的 Web UI 体验。

## 实施阶段

### P0 - 现状巡检 & 设计确认 ✅
- 分析通知中心核心架构：`Notification` + `UserNotification` 模型
- 理解现有 `MANGA_UPDATED` 通知实现流程
- 确认 `NotificationService` 和 `notify_manga_updated` helper 结构
- 设计统一 payload 结构方案

### P1 - 后端：阅读通知类型 & Payload 统一 ✅

#### 新增通知类型
```python
# backend/app/models/enums/notification_type.py
class NotificationType(str, Enum):
    # ... 现有类型
    READING_EBOOK_IMPORTED = "READING_EBOOK_IMPORTED"  # 新增
```

#### 统一 Payload Schema
```python
# backend/app/schemas/notification_reading.py
class ReadingBasePayload(BaseModel):
    media_type: ReadingMediaType
    title: str
    cover_url: Optional[str]
    route_name: str
    route_params: Dict[str, Any]
    source_label: Optional[str]

class MangaUpdatedPayload(ReadingBasePayload):
    notification_type: Literal["MANGA_UPDATED"]
    series_id: int
    new_chapters: List[str]
    total_new_count: int
    last_updated_at: Optional[datetime]
    latest_chapter_id: Optional[int]

class EbookImportedPayload(ReadingBasePayload):
    notification_type: Literal["READING_EBOOK_IMPORTED"]
    ebook_id: int
    imported_at: Optional[datetime]
    source_type: Optional[str]

class AudiobookReadyPayload(ReadingBasePayload):
    notification_type: Literal["AUDIOBOOK_READY"]
    audiobook_id: int
    from_ebook_id: Optional[int]
    generated_at: Optional[datetime]
    total_chapters: Optional[int]
    source_type: Optional[str]
```

#### 统一 Helper 函数
```python
# backend/app/services/notification_service.py
async def notify_manga_updated_for_user(session, *, user_id: int, payload: dict) -> UserNotification
async def notify_ebook_imported(session, *, user_id: int, payload: dict) -> UserNotification  
async def notify_audiobook_ready_for_user(session, *, user_id: int, payload: dict) -> UserNotification
```

### P2 - 触发点接入 ✅

#### Manga 追更通知
- **文件**: `backend/app/runners/manga_follow_sync.py`
- **触发**: 漫画同步检测到新章节
- **更新**: 使用 `notify_manga_updated_for_user` + 标准化 payload

#### EBook 导入通知
- **文件**: `backend/app/api/novel_demo.py`
- **触发**: TXT 文件导入完成
- **新增**: 调用 `notify_ebook_imported` 发送通知

#### TTS 有声书通知
- **文件**: `backend/app/modules/tts/notification_service.py`
- **触发**: TTS 任务成功完成
- **更新**: 使用 `notify_audiobook_ready_for_user` + 标准化 payload

### P3 - Web 通知中心 UI ✅

#### 前端类型定义
```typescript
// frontend/src/types/notify.ts
export type NotificationType = 
  | 'MANGA_UPDATED' | 'READING_EBOOK_IMPORTED' | 'AUDIOBOOK_READY'
  // ... 其他类型
```

#### 专用通知组件
```vue
<!-- frontend/src/components/notification/ReadingNotificationCard.vue -->
<template>
  <v-card class="reading-notification-card">
    <!-- 封面图片 + 媒体类型图标 -->
    <!-- 标题 + 来源标签 -->
    <!-- 阅读特有信息（新增章节数等） -->
    <!-- 一键跳转按钮 -->
  </v-card>
</template>
```

#### 页面集成
- **文件**: `frontend/src/pages/UserNotifications.vue`
- **增强**: 使用 `isReadingNotification()` 判断，阅读通知使用新组件渲染

### P4 - Telegram 渠道集成 ⏸️
- **状态**: 延后实施（Web UI 已完成，Telegram 格式化为增强功能）
- **计划**: 在 `factory.py` 中添加阅读通知特殊格式化逻辑

### P5 - 通知设置 & 文档更新 ✅
- 更新 `READING_CENTER_OVERVIEW.md` 包含通知系统说明
- 创建 `READING_NOTIFY_1_TECHNICAL_SPEC.md` 技术文档

### P6 - QA 验收 & 自检清单 ⏳

## 技术架构

### 后端数据流
```
触发事件 → Helper函数 → NotificationService → UserNotification表 → Web UI显示
                ↓
        notify_user_by_id → 外部渠道（Telegram等）
```

### 前端组件结构
```
UserNotifications.vue
├── ReadingNotificationCard.vue (阅读通知)
│   ├── 封面图片展示
│   ├── 媒体类型图标
│   ├── 来源标签
│   └── 跳转按钮
└── v-list-item (其他通知)
```

### Payload 路由映射
| 通知类型 | 前端路由名称 | 参数示例 |
|----------|-------------|----------|
| MANGA_UPDATED | MangaReaderPage | {series_id, chapter_id} |
| READING_EBOOK_IMPORTED | NovelReader | {ebookId} |
| AUDIOBOOK_READY | AudiobookCenter | {audiobook_id} |

## 关键设计决策

### 1. 统一 Payload 结构
- **优势**: 前端组件可统一处理，易于维护和扩展
- **包含**: 媒体类型、标题、封面、路由信息、来源标签

### 2. 组件化 UI 设计
- **ReadingNotificationCard**: 专门处理阅读通知的视觉展示
- **条件渲染**: 保持与其他通知样式的兼容性

### 3. 路由名称一致性
- **后端 payload.route_name** 与 **前端路由定义** 严格匹配
- **参数格式**: 遵循各阅读页面的参数约定

### 4. 渐进式集成
- **P0-P3**: 核心功能（后端 + Web UI）
- **P4**: 增强功能（Telegram 格式化）
- **P5-P6**: 文档和 QA

## 文件变更清单

### 后端文件
- ✅ `backend/app/models/enums/notification_type.py` - 新增通知类型
- ✅ `backend/app/schemas/notification_reading.py` - 新增统一 payload schema
- ✅ `backend/app/services/notification_service.py` - 新增 helper 函数
- ✅ `backend/app/runners/manga_follow_sync.py` - 更新使用新 payload
- ✅ `backend/app/api/novel_demo.py` - 新增 ebook 导入通知
- ✅ `backend/app/modules/tts/notification_service.py` - 更新使用新 payload

### 前端文件
- ✅ `frontend/src/types/notify.ts` - 新增通知类型定义
- ✅ `frontend/src/components/notification/ReadingNotificationCard.vue` - 新增专用组件
- ✅ `frontend/src/pages/UserNotifications.vue` - 集成新组件

### 文档文件
- ✅ `docs/READING_CENTER_OVERVIEW.md` - 更新包含通知系统说明
- ✅ `docs/READING_NOTIFY_1_TECHNICAL_SPEC.md` - 新增技术规范文档

## 测试要点

### 功能测试
1. **Manga 追更通知**: 模拟新章节，验证通知创建和跳转
2. **EBook 导入通知**: 上传 TXT 文件，验证导入完成通知
3. **TTS 完成通知**: 生成有声书，验证完成通知
4. **Web UI 渲染**: 验证阅读通知卡片正确显示
5. **路由跳转**: 点击通知跳转到对应阅读页面

### 兼容性测试
1. **现有通知**: 确保非阅读通知正常显示
2. **通知列表**: 筛选和分页功能正常
3. **标记已读**: 阅读通知标记已读功能正常

### 性能测试
1. **大量通知**: 验证通知列表加载性能
2. **图片加载**: 封面图片加载和缓存

## 后续扩展

### 可能的增强
1. **Telegram 富媒体**: 支持封面图片和内联按钮
2. **通知偏好**: 用户可配置阅读通知的接收偏好
3. **批量操作**: 批量标记阅读通知为已读
4. **统计面板**: 阅读通知的统计和分析

### 扩展点
1. **新通知类型**: 可轻松添加新的阅读相关通知类型
2. **UI 组件**: ReadingNotificationCard 可扩展支持更多媒体类型
3. **Payload 结构**: 可在 ReadingBasePayload 基础上添加新字段

## 总结

READING-NOTIFY-1 成功实现了阅读事件与通知中心的深度集成，提供了：

- **标准化**: 统一的 payload 结构和 helper 函数
- **用户体验**: 专门的阅读通知卡片和一键跳转
- **可维护性**: 组件化设计和清晰的架构分层
- **可扩展性**: 为未来新的阅读通知类型奠定基础

核心功能（P0-P3）已完成并可投入使用，增强功能（P4）可根据需要后续实施。
