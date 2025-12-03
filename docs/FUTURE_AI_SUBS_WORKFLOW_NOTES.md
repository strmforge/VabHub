# FUTURE-AI-SUBS-WORKFLOW-1 设计笔记

> 未来 AI 订阅工作流助手 v1：自然语言 → 订阅规则草案

---

## 1. 现有订阅模型梳理

### 1.1 核心订阅模型

#### Subscription（媒体订阅）
**文件**: `backend/app/models/subscription.py`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | int | 是 | 主键 |
| `user_id` | int | 是 | 用户 ID |
| `title` | str | 是 | 订阅标题 |
| `original_title` | str | 否 | 原始标题 |
| `year` | int | 否 | 年份 |
| `media_type` | str | 是 | 媒体类型：movie / tv / anime / short_drama / music |
| `tmdb_id` | int | 否 | TMDB ID |
| `tvdb_id` | int | 否 | TVDB ID |
| `imdb_id` | str | 否 | IMDB ID |
| `poster` | str | 否 | 海报 URL |
| `backdrop` | str | 否 | 背景图 URL |
| `status` | str | 是 | 状态：active / paused / completed |
| `season` | int | 否 | 季数（电视剧） |
| `total_episode` | int | 否 | 总集数 |
| `start_episode` | int | 否 | 起始集数 |
| `quality` | str | 否 | 质量：4K / 1080p / 720p |
| `resolution` | str | 否 | 分辨率 |
| `effect` | str | 否 | 特效：HDR / Dolby Vision |
| `sites` | JSON | 否 | 订阅站点 ID 列表 |
| `downloader` | str | 否 | 下载器 |
| `save_path` | str | 否 | 保存路径 |
| `min_seeders` | int | 是 | 最小做种数（默认 5） |
| `auto_download` | bool | 是 | 自动下载 |
| `best_version` | bool | 是 | 洗版 |
| `include` | str | 否 | 包含规则（关键字/正则） |
| `exclude` | str | 否 | 排除规则 |
| `filter_group_ids` | JSON | 是 | 过滤规则组 ID 列表 |
| `allow_hr` | bool | 是 | 是否允许 HR/H&R |
| `allow_h3h5` | bool | 是 | 是否允许 H3/H5 |
| `strict_free_only` | bool | 是 | 只下载 free/促销种 |

#### RSSSubscription（RSS 订阅）
**文件**: `backend/app/models/rss_subscription.py`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | int | 是 | 主键 |
| `user_id` | int | 是 | 用户 ID |
| `name` | str | 是 | 订阅名称 |
| `url` | str | 是 | RSS URL |
| `site_id` | int | 否 | 关联站点 ID |
| `enabled` | bool | 是 | 是否启用 |
| `interval` | int | 是 | 刷新间隔（分钟） |
| `filter_rules` | JSON | 否 | 过滤规则 |
| `download_rules` | JSON | 否 | 下载规则 |
| `filter_group_ids` | JSON | 是 | 过滤规则组 ID 列表 |

### 1.2 RSSHub 订阅模型

**文件**: `backend/app/models/rsshub.py`

#### RSSHubSource（RSSHub 源）
| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | str | 源 ID（主键） |
| `name` | str | 源名称 |
| `url_path` | str | RSSHub URL 路径 |
| `type` | str | 类型：video / tv / variety / anime / music / mixed |
| `group` | str | 分组：rank / update |
| `description` | str | 描述 |
| `is_template` | bool | 是否为模板 |
| `default_enabled` | bool | 默认是否启用 |

#### UserRSSHubSubscription（用户 RSSHub 订阅）
| 字段 | 类型 | 说明 |
|------|------|------|
| `user_id` | int | 用户 ID（主键） |
| `target_id` | str | 目标 ID（主键） |
| `target_type` | str | 目标类型：source / composite |
| `enabled` | bool | 是否启用 |

### 1.3 字段分类

#### 必填 + 强约束字段
- `media_type`：决定订阅走哪条处理链路
- `title`：订阅标识
- `sites` 或 RSSHub 源：决定数据来源
- `quality` / `min_resolution`：质量下限

#### 可选增强字段
- `include` / `exclude`：高级过滤
- `filter_group_ids`：过滤规则组
- `allow_hr` / `strict_free_only`：安全策略
- `effect`：特效偏好

---

## 2. 订阅与其他模块的打通关系

### 2.1 数据流向

```
用户创建订阅
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ SubscriptionService.create_subscription()           │
│ - 验证 media_type                                    │
│ - 初始化刷新时间                                      │
│ - 存入数据库                                         │
└─────────────────────────────────────────────────────┘
    │
    ▼ (定时任务 / 手动触发)
┌─────────────────────────────────────────────────────┐
│ SubscriptionRefreshEngine                           │
│ - 根据 sites 调用 External Indexer 搜索              │
│ - 根据 RSSHub 订阅抓取 RSS 源                        │
│ - 应用 filter_rules / filter_group_ids 过滤         │
└─────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ RuleEngine + DecisionService                        │
│ - 应用 allow_hr / strict_free_only 安全策略          │
│ - HR 风险评估（Local Intel）                         │
│ - 质量/分辨率匹配                                    │
└─────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ 下载任务创建                                         │
│ - 创建 DownloadTask                                  │
│ - 发送到下载器                                       │
└─────────────────────────────────────────────────────┘
```

### 2.2 依赖模块

| 模块 | 职责 | 路径 |
|------|------|------|
| `SubscriptionService` | 订阅 CRUD | `modules/subscription/service.py` |
| `SubscriptionRefreshEngine` | 订阅刷新执行 | `modules/subscription/refresh_engine.py` |
| `RuleEngine` | 规则匹配 | `modules/subscription/rule_engine.py` |
| `FilterRuleGroupService` | 过滤规则组 | `modules/filter_rule_group/service.py` |
| `RSSHubService` | RSSHub 源管理 | `modules/rsshub/service.py` |
| `External Indexer` | PT 站点搜索 | `core/ext_indexer/` |
| `Local Intel` | HR 风险评估 | `core/intel_local/` |
| `DecisionService` | 下载决策 | `modules/decision/` |

---

## 3. v1 支持范围

### 3.1 媒体类型

| 类型 | 状态 | 说明 |
|------|------|------|
| 电影（movie） | ✅ v1 支持 | |
| 电视剧（tv） | ✅ v1 支持 | |
| 动漫（anime） | ✅ v1 支持 | |
| 短剧（short_drama） | ⏳ v2 考虑 | 需要额外 metadata |
| 音乐（music） | ⏳ v2 考虑 | 独立订阅表 |
| 小说/漫画 | ⏳ v2 考虑 | 独立模块 |

### 3.2 来源类型

| 来源 | 状态 | 说明 |
|------|------|------|
| RSSHub 榜单/更新源 | ✅ v1 支持 | 通过 RSSHubSource |
| PT 站点搜索 | ✅ v1 支持 | 通过 sites 字段 |
| 自定义 RSS URL | ⏳ v2 考虑 | RSSSubscription |

### 3.3 操作类型

| 操作 | 状态 | 说明 |
|------|------|------|
| 新建订阅规则 | ✅ v1 支持 | 创建 Subscription |
| 生成变种草案 | ⏳ v2 考虑 | 基于现有规则修改 |
| 更新现有规则 | ⏳ v2 考虑 | 需要更复杂的映射 |

### 3.4 安全约束（v1 必须遵守）

- ✅ 所有草案默认 `auto_download=False`（需手动启用）
- ✅ 默认 `allow_hr=False`（不允许 HR）
- ✅ 默认 `strict_free_only=False`（但会在 AI 说明中提示）
- ✅ 不直接写数据库，需用户确认后才应用
- ✅ 源/站点 ID 必须在系统中存在

---

## 4. 依赖的模块清单

### 4.1 后端依赖

```
AI Orchestrator (FUTURE-AI-ORCHESTRATOR-1)
├── AIOrchestratorService          # 编排服务
├── SUBS_ADVISOR 模式              # 订阅顾问模式
├── GetSiteAndSubOverviewTool      # 站点概览
├── GetSearchPreviewTool           # 搜索预览
├── GetTorrentIndexInsightTool     # HR 洞察
└── GetRecommendationPreviewTool   # 推荐预览

Subscription Module
├── SubscriptionService            # 订阅服务
├── RuleEngine                     # 规则引擎
└── FilterRuleGroupService         # 过滤规则组

RSSHub Module
├── RSSHubService                  # RSSHub 服务
├── RSSHubSource                   # 源配置
└── UserRSSHubSubscription         # 用户订阅

External Indexer
├── SearchProvider                 # 搜索提供者
└── SiteConfig                     # 站点配置
```

### 4.2 前端依赖

```
Vue 3 + Vuetify 3
├── aiOrchestratorApi              # Orchestrator API
├── subscriptionApi                # 订阅 API
└── rsshubApi                      # RSSHub API
```

---

## 5. 实现进度

| 阶段 | 内容 | 状态 |
|------|------|------|
| P0 | 现状巡检 & 订阅模型梳理 | ✅ 完成 |
| P1 | 订阅工作流草案 Draft 数据模型 | ✅ 完成 |
| P2 | Orchestrator SUBS_ADVISOR 模式增强 | ✅ 完成 |
| P3 | 后端订阅工作流服务 | ✅ 完成 |
| P4 | 前端 AI 订阅助手页面 | ✅ 完成 |
| P5 | 测试 & UX 打磨 | ✅ 完成 |
| P6 | 文档 & 总结 | ✅ 完成 |

---

## 6. Draft → 真实订阅模型映射

> Schema 文件：`backend/app/schemas/ai_subs_workflow.py`

### 6.1 SubsWorkflowDraft 字段映射

| Draft 字段 | 真实模型字段 | 说明 |
|------------|-------------|------|
| `name` | `Subscription.title` | 订阅名称 |
| `description` | - | 仅用于 AI 说明 |
| `media_type` | `Subscription.media_type` | 直接映射 |
| `sources[].type=rsshub` | `UserRSSHubSubscription` | 创建 RSSHub 订阅 |
| `sources[].type=pt_search` | `Subscription.sites` | 设置站点列表 |
| `filter_rule.include_keywords` | `Subscription.include` | 逗号分隔 |
| `filter_rule.exclude_keywords` | `Subscription.exclude` | 逗号分隔 |
| `filter_rule.min_resolution` | `Subscription.quality` | 映射到质量 |
| `filter_rule.hr_safe` | `Subscription.allow_hr` | 取反（hr_safe=True → allow_hr=False） |
| `filter_rule.languages` | `Subscription.include` | 追加到包含规则 |
| `action.download_enabled` | `Subscription.auto_download` | 直接映射 |
| `action.target_library` | `Subscription.save_path` | 映射到保存路径 |

### 6.2 映射实现

映射逻辑由 `draft_to_subscription_dict()` 函数实现：

```python
# backend/app/schemas/ai_subs_workflow.py

def draft_to_subscription_dict(draft: SubsWorkflowDraft, user_id: int) -> Dict[str, Any]:
    """将草案转换为订阅创建字典"""
    # 1. 收集 PT 站点 ID
    # 2. 构建 include/exclude 字符串
    # 3. 映射安全策略（hr_safe=True → allow_hr=False）
    # 4. 返回可用于 SubscriptionService.create_subscription() 的字典
```

### 6.3 特殊处理

- **RSSHub 源**：需要先验证 `source_id` 存在，然后创建/更新 `UserRSSHubSubscription`
- **PT 站点**：需要验证站点配置存在，转换为站点 ID 列表
- **质量映射**：`2160p` → `4K`，`1080p` → `1080p`，`720p` → `720p`
- **安全默认值**：`allow_hr=False`, `strict_free_only=False`, `auto_download=False`

---

## 7. 示例

### 7.1 示例提示词

```
帮我订阅最近热门的韩剧，优先 1080p，要有中文字幕
```

### 7.2 示例生成草案

```json
{
  "name": "热门韩剧订阅",
  "description": "订阅最近热门的韩国电视剧",
  "media_type": "tv",
  "sources": [
    {
      "type": "rsshub",
      "id": "douban_korean_drama_hot",
      "name": "豆瓣韩剧热门"
    }
  ],
  "filter_rule": {
    "include_keywords": ["韩剧", "中字", "简体"],
    "exclude_keywords": ["预告", "花絮"],
    "min_resolution": "1080p",
    "hr_safe": true,
    "languages": ["中文", "韩语"]
  },
  "action": {
    "download_enabled": false,
    "dry_run": true,
    "notify_on_match": true
  },
  "ai_explanation": "基于您的需求，我创建了一个韩剧订阅草案。使用豆瓣韩剧热门榜单作为来源，优先 1080p 及以上分辨率，包含中文字幕。为了安全起见，已启用 HR 安全策略。"
}
```

### 7.3 应用后创建的订阅记录

```json
{
  "id": 123,
  "title": "热门韩剧订阅",
  "media_type": "tv",
  "quality": "1080p",
  "include": "韩剧,中字,简体",
  "exclude": "预告,花絮",
  "allow_hr": false,
  "strict_free_only": false,
  "auto_download": false,
  "status": "paused"
}
```

---

## 8. 后续规划

- **v2**: 支持音乐/小说/漫画订阅
- **v2**: 支持更新现有订阅规则
- **v2**: 支持自定义 RSS URL
- **v3**: 支持多轮对话优化草案
