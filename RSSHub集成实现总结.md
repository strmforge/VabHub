# RSSHub集成实现总结

**完成时间**: 2025-01-XX  
**任务范围**: 按照 `vabhub_rsshub_pack/docs/rsshub_integration.md` 实现RSSHub集成

---

## 📋 一、实现内容

### ✅ 1. 数据模型

**文件**: `backend/app/models/rsshub.py`

**实现内容**:
- ✅ `RSSHubSource` - RSSHub源表
- ✅ `RSSHubComposite` - RSSHub组合订阅表
- ✅ `UserRSSHubSubscription` - 用户RSSHub订阅状态表
- ✅ `rsshub_composite_source` - 组合订阅与源的关联表

**字段说明**:
- `RSSHubSource`: id, name, url_path, type, group, description, is_template, default_enabled
- `RSSHubComposite`: id, name, type, description, default_enabled
- `UserRSSHubSubscription`: user_id, target_id, target_type, enabled, last_checked_at, last_item_hash

---

### ✅ 2. RSSHub客户端封装

**文件**: `backend/app/core/rsshub/client.py`

**实现内容**:
- ✅ `RSSHubClient` - RSSHub客户端类
- ✅ `fetch_rss(path)` - 获取RSS Feed（返回XML字符串）
- ✅ `fetch_rss_items(path, limit)` - 获取RSS Feed并解析为项列表（用于预览）
- ✅ 单例模式（`get_rsshub_client()`）
- ✅ 错误处理和日志记录

**环境变量**:
- `RSSHUB_BASE_URL`: RSSHub基础URL，默认 `http://rsshub:1200`

---

### ✅ 3. 配置加载服务

**文件**: `backend/app/modules/rsshub/config_loader.py`

**实现内容**:
- ✅ `RSSHubConfigLoader` - 配置加载器类
- ✅ `load_sources_rank()` - 加载榜单源配置
- ✅ `load_sources_updates()` - 加载更新源配置
- ✅ `load_composites()` - 加载组合订阅配置
- ✅ `sync_sources_to_db()` - 同步源配置到数据库
- ✅ `sync_composites_to_db()` - 同步组合订阅配置到数据库
- ✅ `sync_all_to_db()` - 同步所有配置到数据库

**配置文件路径**:
- 默认: `项目根目录/vabhub_rsshub_pack/config/rsshub/`
- 支持自定义路径

**启动时自动同步**:
- 在 `main.py` 的 `lifespan` 中添加了配置同步逻辑

---

### ✅ 4. RSSHub服务层

**文件**: `backend/app/modules/rsshub/service.py`

**实现内容**:
- ✅ `RSSHubService` - RSSHub服务类
- ✅ `list_sources()` - 获取源列表（附带用户订阅状态）
- ✅ `list_composites()` - 获取组合订阅列表（附带用户订阅状态和源列表）
- ✅ `toggle_subscription()` - 切换订阅状态
- ✅ `preview_source()` - 预览源内容
- ✅ `get_user_subscriptions()` - 获取用户的RSSHub订阅列表

**功能特性**:
- 支持按group、type过滤
- 自动关联用户订阅状态
- 组合订阅包含关联的源ID列表

---

### ✅ 5. RSSHub API端点

**文件**: `backend/app/api/rsshub.py`

**实现端点**:
- ✅ `GET /api/v1/rsshub/sources` - 获取源列表
  - 查询参数: `group`（rank/update）、`type`（video/tv/variety/anime/music/mixed）
  - 返回: 源列表，每个源包含enabled状态
- ✅ `GET /api/v1/rsshub/composites` - 获取组合订阅列表
  - 查询参数: `type`（类型过滤）
  - 返回: 组合订阅列表，每个组合包含enabled状态和源列表
- ✅ `POST /api/v1/rsshub/subscriptions/{target_type}/{target_id}/toggle` - 切换订阅状态
  - 请求体: `{"enabled": true/false}`
  - 返回: 切换结果
- ✅ `GET /api/v1/rsshub/sources/{source_id}/preview` - 预览源内容
  - 查询参数: `limit`（1-20，默认5）
  - 返回: RSS项列表（前N条）

**路由注册**:
- 已在 `backend/app/api/__init__.py` 中注册，前缀 `/rsshub`

---

### ✅ 6. 定时任务调度器

**文件**: `backend/app/modules/rsshub/scheduler.py`

**实现内容**:
- ✅ `RSSHubScheduler` - RSSHub定时任务调度器
- ✅ `process_user_subscriptions()` - 处理用户的所有RSSHub订阅
- ✅ `_process_source_subscription()` - 处理单源订阅
- ✅ `_process_composite_subscription()` - 处理组合订阅（合并、去重）
- ✅ `_deduplicate_items()` - 对RSS项进行去重（基于标题规范化）
- ✅ `_generate_dedup_key()` - 生成去重key
- ✅ `_enqueue_items_to_workflow()` - 将RSS项入队到工作流

**处理流程**:
1. 获取用户的所有启用订阅
2. 对于单源：直接抓取RSS，找到新项（与last_item_hash比较）
3. 对于组合订阅：
   - 抓取所有关联源的RSS
   - 合并所有项
   - 基于标题规范化去重
   - 找到新项
4. 处理新项：入队到工作流
5. 更新last_item_hash和last_checked_at

---

### ✅ 7. 媒体信息提取器

**文件**: `backend/app/modules/rsshub/media_extractor.py`

**实现内容**:
- ✅ `RSSHubMediaExtractor` - 媒体信息提取器
- ✅ `extract_media_info()` - 从标题中提取媒体信息
- ✅ `_detect_media_type()` - 检测媒体类型

**提取功能**:
- 提取年份（支持多种格式：`(2024)`、`（2024）`、`2024年`）
- 提取季数和集数（支持多种格式：`S01E01`、`第1季第1集`、`第1集`、`EP1`、`EP.1`）
- 检测媒体类型（movie/tv/anime/variety/music）
- 清理标题（移除年份、季数集数标记）

---

## 📋 二、待实现功能

### ⏳ 1. 定时任务注册

**需要**:
- 在 `app/core/scheduler.py` 中注册RSSHub定时任务
- 定期执行 `RSSHubScheduler.process_user_subscriptions()`
- 建议间隔：每30分钟执行一次

**实现示例**:
```python
from app.modules.rsshub.scheduler import RSSHubScheduler
from app.core.database import AsyncSessionLocal

async def process_rsshub_subscriptions():
    """处理所有用户的RSSHub订阅"""
    async with AsyncSessionLocal() as db:
        scheduler = RSSHubScheduler(db)
        # 获取所有用户
        from app.models.user import User
        users = await db.execute(select(User))
        for user in users.scalars().all():
            await scheduler.process_user_subscriptions(user.id)

# 注册定时任务
scheduler.add_job(
    process_rsshub_subscriptions,
    'interval',
    minutes=30,
    id='rsshub_process_subscriptions'
)
```

---

### ⏳ 2. 工作流模板系统

**需要**:
- 实现工作流模板管理
- 为每种type（video/tv/variety/anime/music）设置默认工作流模板
- 在 `_get_workflow_template()` 中返回模板配置

**工作流模板建议**:
- **电影（video）**: 自动查找PT电影规则组，按片名+年份匹配
- **电视剧（tv）**: 按"剧名 + SxxExx"匹配剧集规则组
- **综艺（variety）**: 走综艺规则组
- **番剧（anime）**: 走番剧规则组
- **音乐（music）**: 写入任务池/打标签（等音乐功能完善后再做自动下载）

---

### ⏳ 3. 前端界面

**需要**:
- 创建RSSHub订阅管理页面
- 分三块展示：
  - ① 榜单源：按 `group = rank` 分组展示
  - ② 更新源：按 `group = update` 展示
  - ③ 组合订阅：展示组合订阅列表
- 每条有：
  - 开关（enabled）
  - 类型标签（电影/剧集/综艺/番剧/音乐）
  - "预览"按钮

---

## 📋 三、使用说明

### 3.1 环境变量配置

在 `.env` 文件中配置：

```env
# RSSHub基础URL（Docker内部网络）
RSSHUB_BASE_URL=http://rsshub:1200

# 如果在本机调试，可以使用：
# RSSHUB_BASE_URL=http://localhost:1200
```

### 3.2 配置文件位置

确保配置文件在以下位置：
```
vabhub_rsshub_pack/
└── config/
    └── rsshub/
        ├── rsshub_sources_rank.json
        ├── rsshub_sources_updates.json
        └── rsshub_composites.json
```

### 3.3 API使用示例

**获取源列表**:
```bash
GET /api/v1/rsshub/sources?group=rank&type=video
```

**获取组合订阅列表**:
```bash
GET /api/v1/rsshub/composites?type=video
```

**切换订阅状态**:
```bash
POST /api/v1/rsshub/subscriptions/source/douban_movie_ustop/toggle
{
  "enabled": true
}
```

**预览源内容**:
```bash
GET /api/v1/rsshub/sources/douban_movie_ustop/preview?limit=5
```

---

## 📋 四、数据库迁移

**需要执行数据库迁移**:
1. 创建RSSHub相关表（`rsshub_source`、`rsshub_composite`、`user_rsshub_subscription`、`rsshub_composite_source`）
2. 运行配置同步，将JSON配置加载到数据库

**迁移脚本**:
```python
# 在数据库初始化时自动创建表
# 在main.py启动时自动同步配置
```

---

## 📋 五、测试建议

### 5.1 单元测试

- ✅ RSSHub客户端测试
- ✅ 配置加载器测试
- ✅ 媒体信息提取器测试
- ✅ 去重算法测试

### 5.2 集成测试

- ✅ API端点测试
- ✅ 定时任务测试
- ✅ 工作流集成测试

---

## 📋 六、总结

### ✅ 已完成

- ✅ 数据模型（3个表）
- ✅ RSSHub客户端封装
- ✅ 配置加载服务
- ✅ RSSHub服务层
- ✅ API端点（4个）
- ✅ 定时任务调度器（核心逻辑）
- ✅ 媒体信息提取器

### ⏳ 待完成

- ⏳ 定时任务注册（需要集成到调度器）
- ⏳ 工作流模板系统（需要实现模板管理）
- ⏳ 前端界面（需要创建订阅管理页面）

---

**文档生成时间**: 2025-01-XX  
**任务状态**: 核心功能已完成，待集成和前端实现  
**系统状态**: 后端API可用，等待定时任务注册和前端开发

