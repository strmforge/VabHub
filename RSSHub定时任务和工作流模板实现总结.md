# RSSHub定时任务和工作流模板实现总结

**完成时间**: 2025-01-XX  
**任务范围**: 定时任务注册、工作流模板系统实现

---

## 📋 一、实现内容

### ✅ 1. 定时任务注册

**文件**: `backend/app/core/scheduler.py`

**实现内容**:
- ✅ 添加 `_process_rsshub_subscriptions()` 方法
- ✅ 注册RSSHub定时任务（每30分钟执行一次）
- ✅ 处理所有用户的RSSHub订阅
- ✅ 统计处理结果

**任务配置**:
- **ID**: `process_rsshub_subscriptions`
- **名称**: `RSSHub订阅处理`
- **触发方式**: 每30分钟执行一次
- **功能**: 遍历所有用户，处理每个用户的启用RSSHub订阅

---

### ✅ 2. 工作流模板系统

**文件**: `backend/app/modules/rsshub/workflow_templates.py`

**实现内容**:
- ✅ `RSSHubWorkflowTemplate` - 工作流模板类
- ✅ `RSSHubWorkflowTemplateManager` - 工作流模板管理器
- ✅ 6种默认工作流模板：
  - **video（电影）**: 自动创建订阅，按片名+年份匹配，自动下载
  - **tv（电视剧）**: 自动创建订阅，按剧名+SxxExx匹配，自动下载
  - **variety（综艺）**: 自动创建订阅，按标题匹配，自动下载
  - **anime（番剧）**: 自动创建订阅，按番剧名+季数+集数匹配，自动下载
  - **music（音乐）**: 创建音乐订阅，暂不自动下载（等待音乐功能完善）
  - **mixed（混合）**: 自动检测类型，根据类型选择处理方式

**模板结构**:
```python
{
    "template_id": "rsshub_video_default",
    "name": "RSSHub电影自动订阅",
    "media_type": "video",
    "description": "自动从RSSHub电影榜单创建订阅，按片名+年份匹配PT资源",
    "actions": [
        {
            "type": "create_subscription",
            "config": {...}
        },
        {
            "type": "search_and_download",
            "config": {...}
        }
    ]
}
```

---

### ✅ 3. 工作流动作处理器扩展

**文件**: `backend/app/modules/workflow/engine.py`

**新增动作处理器**:
- ✅ `create_subscription` - 创建订阅
- ✅ `create_music_subscription` - 创建音乐订阅
- ✅ `search_and_download` - 搜索并下载
- ✅ `detect_media_type` - 检测媒体类型
- ✅ `add_to_queue` - 添加到队列

**实现细节**:
- `create_subscription`: 从上下文提取媒体信息，创建订阅，支持质量规则配置
- `create_music_subscription`: 创建音乐订阅，支持多平台
- `search_and_download`: 执行搜索，选择第一个结果进行下载
- `detect_media_type`: 使用媒体信息提取器检测类型
- `add_to_queue`: 添加到队列（目前仅记录日志，等待队列系统实现）

---

### ✅ 4. RSSHub调度器集成

**文件**: `backend/app/modules/rsshub/scheduler.py`

**更新内容**:
- ✅ `_enqueue_items_to_workflow()` - 使用工作流模板执行
- ✅ `_get_workflow_template()` - 从模板管理器获取模板
- ✅ 集成工作流引擎执行逻辑
- ✅ 支持媒体类型自动检测

**执行流程**:
1. 提取媒体信息（标题、年份、季数、集数等）
2. 检测媒体类型（如果提取的类型与传入的不同，使用提取的类型）
3. 获取对应类型的工作流模板
4. 构建工作流上下文（包含RSS项、媒体信息、用户ID等）
5. 执行工作流模板中的动作
6. 记录执行结果

---

## 📋 二、工作流模板配置

### 2.1 电影（video）模板

**动作**:
1. **create_subscription**: 创建电影订阅
   - 匹配模式: `title_year`（按片名+年份）
   - 自动下载: `true`
   - 质量规则: 最低1080p，优先HDR、Dolby Vision
2. **search_and_download**: 搜索并下载
   - 站点: 所有站点
   - 最低做种数: 5

### 2.2 电视剧（tv）模板

**动作**:
1. **create_subscription**: 创建电视剧订阅
   - 匹配模式: `title_season_episode`（按剧名+季数+集数）
   - 自动下载: `true`
   - 质量规则: 最低1080p，优先HDR
2. **search_and_download**: 搜索并下载
   - 站点: 所有站点
   - 最低做种数: 5

### 2.3 综艺（variety）模板

**动作**:
1. **create_subscription**: 创建订阅（使用tv类型）
   - 匹配模式: `title`
   - 自动下载: `true`
   - 质量规则: 最低720p
2. **search_and_download**: 搜索并下载
   - 站点: 所有站点
   - 最低做种数: 3

### 2.4 番剧（anime）模板

**动作**:
1. **create_subscription**: 创建订阅
   - 匹配模式: `title_season_episode`
   - 自动下载: `true`
   - 质量规则: 最低1080p，优先HDR
2. **search_and_download**: 搜索并下载
   - 站点: 所有站点
   - 最低做种数: 5

### 2.5 音乐（music）模板

**动作**:
1. **create_music_subscription**: 创建音乐订阅
   - 匹配模式: `title_artist`
   - 自动下载: `false`（等待音乐功能完善）
   - 平台: 所有平台
2. **add_to_queue**: 添加到队列
   - 队列类型: `music`
   - 标签: `RSSHub`

### 2.6 混合（mixed）模板

**动作**:
1. **detect_media_type**: 检测媒体类型
   - 回退类型: `video`
2. **create_subscription**: 创建订阅
   - 媒体类型: `auto`（自动检测）
   - 匹配模式: `auto`
   - 自动下载: `true`

---

## 📋 三、使用说明

### 3.1 定时任务

**自动执行**:
- 系统启动后，定时任务自动注册
- 每30分钟自动执行一次
- 处理所有用户的启用RSSHub订阅

**手动触发**（可选）:
```python
from app.core.scheduler import get_scheduler

scheduler = get_scheduler()
await scheduler._process_rsshub_subscriptions()
```

### 3.2 工作流模板

**获取模板**:
```python
from app.modules.rsshub.workflow_templates import get_workflow_template_manager

manager = get_workflow_template_manager()
template = manager.get_template('video')
print(template.to_dict())
```

**自定义模板**（未来扩展）:
- 可以通过API或配置文件自定义模板
- 支持用户自定义工作流动作

---

## 📋 四、前端界面建议

### 4.1 用户需求分析

根据用户反馈：
> "我希望用户不用知道具体什么榜单之类的，他们只需要在工作流选择对应的使用就行"

**结论**: **不需要单独的RSSHub订阅管理前端页面**

### 4.2 推荐方案

**在工作流配置中集成RSSHub**:
- 在工作流创建/编辑页面添加"RSSHub订阅"选项
- 用户选择媒体类型（电影/电视剧/综艺/番剧/音乐）
- 系统自动使用对应的工作流模板
- 用户无需了解具体的榜单源

**实现方式**:
1. 在工作流配置中添加"RSSHub订阅"触发器类型
2. 用户选择媒体类型（video/tv/variety/anime/music）
3. 系统自动应用对应的工作流模板
4. 用户可以在模板基础上自定义动作

---

## 📋 五、工作流执行流程

### 5.1 完整流程

```
定时任务触发（每30分钟）
    ↓
遍历所有用户
    ↓
获取用户的启用RSSHub订阅
    ↓
对于每个订阅：
    ├─ 单源订阅 → 抓取RSS → 解析项 → 找到新项
    └─ 组合订阅 → 抓取所有源RSS → 合并 → 去重 → 找到新项
    ↓
对于每个新项：
    ├─ 提取媒体信息（标题、年份、季数、集数）
    ├─ 检测媒体类型
    ├─ 获取对应类型的工作流模板
    ├─ 构建工作流上下文
    └─ 执行工作流模板动作
        ├─ create_subscription（创建订阅）
        ├─ search_and_download（搜索并下载）
        └─ 其他动作...
    ↓
更新last_item_hash和last_checked_at
```

### 5.2 工作流动作执行顺序

1. **detect_media_type**（仅mixed类型）: 检测媒体类型
2. **create_subscription** 或 **create_music_subscription**: 创建订阅
3. **search_and_download**: 搜索并下载（如果配置了自动下载）

---

## 📋 六、待完善功能

### ⏳ 1. 工作流动作实现

**需要完善**:
- `create_subscription`: 需要完善订阅创建逻辑（TMDB识别、质量规则匹配等）
- `search_and_download`: 需要完善搜索和下载逻辑（结果选择策略、下载器配置等）
- `add_to_queue`: 需要实现队列系统

### ⏳ 2. 工作流模板自定义

**需要实现**:
- 用户自定义工作流模板
- 模板管理API
- 模板分享功能

### ⏳ 3. 前端集成

**需要实现**:
- 在工作流配置中添加RSSHub订阅选项
- 媒体类型选择器
- 工作流模板预览

---

## 📋 七、总结

### ✅ 已完成

- ✅ 定时任务注册（每30分钟执行）
- ✅ 工作流模板系统（6种默认模板）
- ✅ 工作流动作处理器扩展（5个新动作）
- ✅ RSSHub调度器集成工作流执行

### ⏳ 待完善

- ⏳ 工作流动作的完整实现
- ⏳ 工作流模板自定义功能
- ⏳ 前端工作流配置集成

### 🎯 设计理念

**用户无需了解具体榜单**:
- 用户只需选择媒体类型（电影/电视剧/综艺/番剧/音乐）
- 系统自动使用对应的工作流模板
- 工作流模板封装了所有复杂的处理逻辑

**工作流驱动**:
- 所有RSSHub订阅处理都通过工作流执行
- 用户可以在工作流中自定义处理逻辑
- 支持复杂的工作流动作组合

---

**文档生成时间**: 2025-01-XX  
**任务状态**: 核心功能已完成，待完善工作流动作实现  
**系统状态**: 定时任务已注册，工作流模板系统可用

