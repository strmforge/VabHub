# DOWNLOAD-NOTIFY-1 阶段设计文档

## 1. 架构概述

本文档描述了下载 & HR 事件接入通知中心 v1 的设计方案，目标是让用户能够清晰地看到订阅命中、下载完成和 HR 风险等关键事件。

### 1.1 现有架构
- **通知中心**：已完成 NOTIFY-CENTER-2，支持分类过滤、批量操作
- **下载系统**：有完整的 DownloadTask、Subscription 模型和 HR 检测体系
- **分类体系**：`NotificationCategory.DOWNLOAD` 已存在，可直接使用

### 1.2 设计目标
- 订阅命中时通知用户，显示规则和下载信息
- 下载完成时通知入库结果，提供快速跳转
- HR 风险时及时预警，避免站点处罚

## 2. 通知类型定义

### 2.1 新增 NotificationType
```python
class NotificationType(str, Enum):
    # 现有类型...
    DOWNLOAD_SUBSCRIPTION_MATCHED = "DOWNLOAD_SUBSCRIPTION_MATCHED"
    DOWNLOAD_TASK_COMPLETED = "DOWNLOAD_TASK_COMPLETED"
    DOWNLOAD_HR_RISK = "DOWNLOAD_HR_RISK"
```

### 2.2 分类映射
```python
NOTIFICATION_TYPE_CATEGORY_MAP = {
    # 现有映射...
    NotificationType.DOWNLOAD_SUBSCRIPTION_MATCHED: NotificationCategory.DOWNLOAD,
    NotificationType.DOWNLOAD_TASK_COMPLETED: NotificationCategory.DOWNLOAD,
    NotificationType.DOWNLOAD_HR_RISK: NotificationCategory.DOWNLOAD,
}
```

## 3. 触发点映射表

### 3.1 订阅命中触发点
**文件位置**: `backend/app/runners/subscription_checker.py`
**函数**: `handle_subscription_match()` 或类似函数
**触发时机**: 订阅规则命中并准备创建 DownloadTask 时
**用户ID**: `subscription.user_id`

```python
# 伪代码示例
async def handle_subscription_match(subscription: Subscription, torrent_info: dict):
    # 现有逻辑：创建下载任务
    task = await create_download_task(...)
    
    # 新增：发送通知
    payload = DownloadSubscriptionMatchedPayload(
        title=torrent_info['title'],
        site_name=torrent_info['site'],
        subscription_id=subscription.id,
        subscription_name=subscription.title,
        # ...
    )
    await notify_download_subscription_matched(db, subscription.user_id, payload)
```

### 3.2 下载完成触发点
**文件位置**: `backend/app/chain/download.py` 或 `backend/app/api/download.py`
**函数**: `update_task_status()` 或类似函数
**触发时机**: 任务状态从 RUNNING/DOWNLOADING 变为 COMPLETED 时
**用户ID**: `task.user_id` (需要在 DownloadTask 模型中添加)

```python
# 伪代码示例
async def update_task_status(task_id: int, new_status: str):
    # 现有逻辑：更新状态
    task = await get_download_task(task_id)
    task.status = new_status
    
    if new_status == "completed":
        # 新增：发送通知
        payload = DownloadTaskCompletedPayload(
            title=task.title,
            task_id=task.id,
            success=task.import_success,
            # ...
        )
        await notify_download_task_completed(db, task.user_id, payload)
```

### 3.3 HR 风险触发点
**文件位置**: `backend/app/core/intel_local/hr_policy.py`
**函数**: `evaluate_hr_for_site()` 或 `hr_watcher.py` 的监控函数
**触发时机**: 检测到 `LocalIntelAction.HR_MARK_RISK` 时
**用户ID**: 通过 torrent_id 关联找到 DownloadTask，然后获取 `task.user_id`

```python
# 伪代码示例
async def evaluate_hr_for_site(site: str, repo: HRCasesRepository):
    actions = await check_hr_risks(site)
    
    for action in actions:
        if action.type == LocalIntelActionType.HR_MARK_RISK:
            # 查找对应的下载任务
            task = await find_download_task_by_torrent(action.torrent_id)
            if task and not task.hr_notified_at:  # 防重复
                payload = DownloadHrRiskPayload(
                    title=action.title,
                    site_name=site,
                    risk_level="H&R",  # 根据 action 细分
                    # ...
                )
                await notify_download_hr_risk(db, task.user_id, payload)
                
                # 标记已通知
                task.hr_notified_at = datetime.utcnow()
                await db.commit()
```

## 4. Payload Schema 设计

### 4.1 基础结构
```python
# backend/app/schemas/notification_download.py
class DownloadBasePayload(BaseModel):
    title: str                          # 媒体标题
    site_name: str | None = None        # 站点名称
    category_label: str | None = None   # 媒体类型标签
    resolution: str | None = None       # 分辨率
    source_label: str | None = None     # 来源标签
    route_name: str                     # 前端路由名
    route_params: Dict[str, Any]        # 路由参数
```

### 4.2 具体类型
```python
class DownloadSubscriptionMatchedPayload(DownloadBasePayload):
    notification_type: Literal["DOWNLOAD_SUBSCRIPTION_MATCHED"]
    subscription_id: int
    subscription_name: str
    torrent_id: int | None = None
    rule_labels: list[str] | None = None

class DownloadTaskCompletedPayload(DownloadBasePayload):
    notification_type: Literal["DOWNLOAD_TASK_COMPLETED"]
    task_id: int
    success: bool
    media_type: str | None = None
    season_number: int | None = None
    episode_number: int | None = None
    library_path: str | None = None

class DownloadHrRiskPayload(DownloadBasePayload):
    notification_type: Literal["DOWNLOAD_HR_RISK"]
    risk_level: str                     # "H&R" / "HR" / "H3" / "H5" / "WARN"
    reason: str | None = None
    min_seed_time_hours: int | None = None
    downloaded_bytes: int | None = None
    uploaded_bytes: int | None = None
    ratio: float | None = None
```

## 5. HR 去重策略

### 5.1 数据模型扩展
在 `DownloadTask` 模型中添加字段：
```python
class DownloadTask(Base):
    # 现有字段...
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 新增
    hr_notified_at = Column(DateTime, nullable=True)  # 新增
    hr_notified_level = Column(String(20), nullable=True)  # 新增：记录已通知的风险等级
```

### 5.2 去重逻辑
- **时间去重**：同一任务 24 小时内不重复发送同等级 HR 通知
- **等级去重**：只发送更高级别的 HR 通知（H&R > HR > H3 > H5 > WARN）
- **状态去重**：任务完成后不再发送 HR 通知

### 5.3 实现示例
```python
async def should_send_hr_notification(task: DownloadTask, new_risk_level: str) -> bool:
    # 检查是否已通知过更高级别
    if task.hr_notified_at:
        level_priority = {"H&R": 4, "HR": 3, "H3": 2, "H5": 2, "WARN": 1}
        old_priority = level_priority.get(task.hr_notified_level, 0)
        new_priority = level_priority.get(new_risk_level, 0)
        
        if new_priority <= old_priority:
            return False  # 不发送更低级别的通知
        
        # 检查时间间隔
        if datetime.utcnow() - task.hr_notified_at < timedelta(hours=24):
            return False
    
    return True
```

## 6. 前端组件设计

### 6.1 DownloadNotificationCard 组件
**位置**: `frontend/src/components/notification/DownloadNotificationCard.vue`
**功能**: 根据 `notification_type` 渲染不同样式和信息

### 6.2 类型定义
```typescript
// frontend/src/types/downloadNotify.ts
interface DownloadNotificationPayloadBase {
  title: string;
  site_name?: string;
  category_label?: string;
  resolution?: string;
  source_label?: string;
  route_name: string;
  route_params: Record<string, unknown>;
}

interface DownloadSubscriptionMatchedPayload extends DownloadNotificationPayloadBase {
  notification_type: "DOWNLOAD_SUBSCRIPTION_MATCHED";
  subscription_id: number;
  subscription_name: string;
  torrent_id?: number;
  rule_labels?: string[];
}

// 其他类型...
```

### 6.3 渲染策略
- **订阅命中**: 🎯 图标，绿色主题，显示订阅规则名称
- **下载完成**: ✅ 图标，蓝色主题，显示成功/失败状态
- **HR 风险**: ⚠️ 图标，红色主题，显示风险等级和建议

## 7. 实施优先级

### Phase 1 (核心功能)
1. 后端通知类型和 schema 定义
2. 订阅命中通知触发
3. 基础前端组件

### Phase 2 (完善功能)
1. 下载完成通知触发
2. HR 风险通知触发
3. 去重机制

### Phase 3 (体验优化)
1. Telegram 集成
2. 通知设置
3. 文档完善

## 8. 风险和注意事项

### 8.1 性能考虑
- 通知发送不应阻塞下载流程
- 使用异步方式，失败不影响主业务

### 8.2 数据一致性
- 确保用户ID正确传递
- 避免重复通知

### 8.3 用户体验
- 通知文案要清晰易懂
- 跳转链接要准确有效

---

**文档版本**: v1.0  
**创建日期**: 2024-12-XX  
**维护团队**: VabHub 开发团队
