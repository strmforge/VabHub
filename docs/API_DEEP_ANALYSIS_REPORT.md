# VabHub Backend API 深入分析报告

> 生成时间: 2025-11-30
> 分析范围: `backend/app/api/` 目录下所有 API 文件

---

## 一、API 架构总览

### 1.1 技术栈
- **框架**: FastAPI
- **数据库**: SQLAlchemy (异步)
- **数据验证**: Pydantic v2
- **日志**: Loguru
- **认证**: OAuth2 + JWT

### 1.2 统一响应模式
所有 API 使用统一的响应格式（`BaseResponse`）:
```json
{
  "success": true,
  "message": "操作成功",
  "data": {...},
  "timestamp": "2025-01-XX..."
}
```

### 1.3 文件统计
- **总文件数**: 136+ 个 API 文件
- **核心业务模块**: 30+
- **Dev/Admin 模块**: 20+

---

## 二、核心业务模块深入分析

### 2.1 媒体管理系统

#### 2.1.1 `media.py` - TMDB 集成 (1219行)
**功能**: 媒体搜索和 TMDB API 集成

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/search` | GET | 搜索媒体（电影/剧集） |
| `/details/{tmdb_id}` | GET | 获取媒体详情 |
| `/seasons/{tmdb_id}` | GET | 获取剧集季信息 |
| `/credits/{tmdb_id}` | GET | 获取演职员表 |
| `/person/{person_id}` | GET | 获取人物详情 |
| `/similar/{tmdb_id}` | GET | 获取类似内容 |
| `/recommendations/{tmdb_id}` | GET | 获取推荐内容 |

**特点**:
- 全面缓存策略（搜索1小时，详情24小时）
- 支持代理访问 TMDB API
- 完整的 CRUD 操作支持

#### 2.1.2 `library.py` - 统一媒体库 (422行)
**功能**: 跨媒体类型的统一视图

**核心端点**: `GET /preview`

**支持的媒体类型**:
- Movie（电影）
- TV（电视剧）
- Anime（动画）
- EBook（电子书）
- Audiobook（有声书）
- Comic（漫画）
- Music（音乐）

**特点**:
- 批量查询避免 N+1
- 多表联合排序
- WorkFormats 多形态标记

---

### 2.2 电子书/小说系统

#### 2.2.1 `ebook.py` - 电子书管理 (274行)
**功能**: 电子书作品 CRUD

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 列表（支持筛选/分页） |
| `/{ebook_id}` | GET | 详情（含文件列表） |
| `/stats/summary` | GET | 统计信息 |

**数据模型**:
- `EBook` - 作品主体
- `EBookFile` - 文件实例（支持多格式）

#### 2.2.2 `novel_center.py` - 小说中心 (320行)
**功能**: 小说聚合视图（含 TTS/听书进度）

**核心端点**: `GET /list`

**聚合数据**:
- EBook 基本信息
- TTS 任务状态
- 听书进度
- 阅读进度

#### 2.2.3 `novel_reader.py` - 小说阅读器 (310行)
**功能**: 章节阅读、进度管理、书内搜索

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/novels/{id}/chapters` | GET | 章节列表 |
| `/novels/{id}/chapters/{idx}` | GET | 章节正文 |
| `/user/novels/reading-progress/by-ebook/{id}` | GET/POST | 阅读进度 |
| `/novels/{id}/search` | GET | 书内搜索 |

---

### 2.3 有声书系统

#### 2.3.1 `audiobook.py` - 有声书管理 (314行)
**功能**: AudiobookFile CRUD

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 列表（筛选/分页） |
| `/{id}` | GET | 详情（含作品信息） |
| `/stats/summary` | GET | 统计 |
| `/by-ebook/{id}` | GET | 按作品获取 |

#### 2.3.2 `audiobook_center.py` - 有声书中心 (402行)
**功能**: 有声书聚合视图

**聚合数据**:
- 作品摘要
- TTS 状态
- 听书进度
- 阅读进度

---

### 2.4 TTS 系统 (11个文件)

#### 架构概览
```
TTS 系统
├── 用户侧 API
│   ├── tts_user_flow.py      # 用户 TTS 流程
│   └── tts_user_batch.py     # 用户批量操作
├── Dev/Admin API
│   ├── tts_jobs.py           # 任务管理
│   ├── tts_playground.py     # 调试测试
│   ├── tts_regen.py          # 重新生成
│   ├── tts_storage.py        # 存储管理
│   ├── tts_voice_presets.py  # 声线预设
│   ├── tts_work_batch.py     # 作品批量
│   └── tts_work_profile.py   # 作品配置
└── 管理总览
    └── admin_tts_settings.py # 设置总览
```

#### 2.4.1 `tts_user_flow.py` - 用户 TTS 流程 (273行)
**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/jobs/enqueue-for-work/{id}` | POST | 创建 TTS 任务 |
| `/jobs/status/by-ebook/{id}` | GET | 查询状态 |
| `/jobs/overview` | GET | 任务概览列表 |

**特点**:
- 复用现有活跃任务（queued/running/partial）
- 章节进度统计

#### 2.4.2 `tts_jobs.py` - 任务管理 (263行, Dev模式)
**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/enqueue-for-work/{id}` | POST | 入队任务 |
| `/run-next` | POST | 执行下一个 |
| `/run-batch` | POST | 批量执行 |
| `/` | GET | 任务列表 |
| `/{id}` | GET | 任务详情 |

#### 2.4.3 `tts_voice_presets.py` - 声线预设 (221行)
**功能**: TTS 声线预设 CRUD
- 支持 provider/language/voice/speed/pitch 配置
- is_default 唯一性保证
- 删除时自动解绑 Profile

#### 2.4.4 `tts_work_profile.py` - 作品配置 (191行)
**功能**: 作品级 TTS 配置
- 可绑定预设（preset_id）
- 支持独立配置覆盖

#### 2.4.5 `tts_storage.py` - 存储管理 (311行)
**功能**: TTS 存储目录管理

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/policy` | GET | 获取存储策略 |
| `/overview` | GET | 存储概览 |
| `/preview` | POST | 预览清理计划 |
| `/cleanup` | POST | 执行清理 |
| `/auto-run` | POST | 自动清理 |

**清理模式**: manual / policy

#### 2.4.6 `admin_tts_settings.py` - 设置总览 (434行)
**功能**: 只读 TTS 总览

**返回信息**:
- 配置状态
- 健康检查
- 限流信息
- 使用统计
- 预设使用情况（含热度分析）
- 作品 Profile 总览
- 存储概览

**热度分类**: hot / sleeping / cold / normal

---

### 2.5 漫画系统

#### 2.5.1 `manga_local.py` - 本地漫画 (810行)
**功能**: 本地漫画系列/章节管理

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/series` | GET | 系列列表 |
| `/series/{id}` | GET | 系列详情 |
| `/series/{id}/chapters` | GET | 章节列表 |
| `/chapters/{id}/pages` | GET | 页面列表 |
| `/import-from-remote` | POST | 从远程导入 |
| `/download-jobs` | GET | 下载任务 |

**特点**:
- 支持新旧路径格式兼容
- 封面/页面 URL 生成
- 远程同步功能

#### 2.5.2 `manga_remote.py` - 远程漫画 (315行)
**功能**: 远程漫画源浏览

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/sources` | GET | 源列表 |
| `/sources/{id}/libraries` | GET | 书架列表 |
| `/sources/{id}/search` | GET | 搜索 |
| `/sources/{id}/series/{id}` | GET | 系列详情 |
| `/aggregated-search` | GET | 聚合搜索 |

---

### 2.6 下载系统

#### 2.6.1 `download.py` - 下载管理 (1139行)
**功能**: 下载任务 CRUD、队列管理

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 任务列表 |
| `/{id}` | GET | 任务详情 |
| `/` | POST | 创建任务 |
| `/{id}/pause` | POST | 暂停 |
| `/{id}/resume` | POST | 恢复 |
| `/{id}` | DELETE | 删除 |
| `/batch/*` | POST | 批量操作 |
| `/{id}/queue/*` | POST | 队列调整 |
| `/speed-limit/global` | GET/PUT | 全局限速 |

**特点**:
- Local Intel 集成（HR/站点状态）
- SafetyPolicyEngine 删除前检查
- DOWNLOAD-CENTER-UI 增强字段
- 自动退场机制

---

### 2.7 搜索系统

#### 2.7.1 `search.py` - 搜索 (706行)
**功能**: 多源资源搜索

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/` | POST | 执行搜索 |
| `/stream` | POST | SSE 流式搜索 |
| `/history` | GET | 搜索历史 |

**搜索支持**:
- 关键词搜索
- 媒体 ID 搜索（TMDB/IMDB/豆瓣）
- 多维度筛选
- 智能分组
- IndexedSearchService（Local Intel）
- 查询扩展

---

### 2.8 订阅系统

#### 2.8.1 `subscription.py` - 媒体订阅 (897行)
**功能**: 媒体自动订阅管理

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/` | GET/POST | 列表/创建 |
| `/{id}` | GET/PUT/DELETE | CRUD |
| `/{id}/enable` | POST | 启用 |
| `/{id}/disable` | POST | 禁用 |
| `/{id}/test` | POST | 测试配置 |
| `/{id}/search` | POST | 执行搜索 |
| `/{id}/refresh` | POST | 刷新 |
| `/refresh-all` | POST | 批量刷新 |
| `/{id}/history` | GET | 历史记录 |

**支持媒体类型**: movie / tv / short_drama / music / anime

#### 2.8.2 `rss.py` - RSS 订阅 (588行)
**功能**: RSS 订阅管理

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/subscriptions` | GET/POST | 列表/创建 |
| `/subscriptions/{id}` | GET/PUT/DELETE | CRUD |
| `/subscriptions/{id}/check` | POST | 手动检查 |
| `/items` | GET | RSS 条目列表 |
| `/items/{id}` | GET | 条目详情 |
| `/subscriptions/{id}/stats` | GET | 统计 |

---

### 2.9 站点管理

#### 2.9.1 `site.py` - 站点管理 (778行)
**功能**: PT 站点管理

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/` | GET/POST | 列表/创建 |
| `/{id}` | GET/PUT/DELETE | CRUD |
| `/sync-from-cookiecloud` | POST | Cookie 同步 |
| `/{id}/test` | POST | 连接测试 |
| `/{id}/checkin` | POST | 签到 |
| `/checkin-all` | POST | 批量签到 |
| `/{id}/icon` | GET | 站点图标 |
| `/{id}/ai-adapter/*` | POST | AI 适配 |

---

### 2.10 音乐系统

#### 2.10.1 `music.py` - 音乐管理 (1364行)
**功能**: 音乐搜索、榜单、订阅

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/search` | POST | 搜索音乐 |
| `/charts/platforms` | GET | 榜单平台 |
| `/charts` | GET/POST | 获取榜单 |
| `/charts/history` | GET | 榜单历史 |
| `/tracks/{id}` | GET | 曲目详情 |
| `/trending` | GET | 热门音乐 |
| `/subscriptions` | GET/POST | 音乐订阅 |

**支持平台**: QQ音乐、网易云、TME由你、Billboard中国、Spotify、Apple Music

---

### 2.11 作品中心

#### 2.11.1 `work.py` - 作品中心 (404行)
**功能**: 统一作品详情聚合

**核心端点**: `GET /{ebook_id}`

**聚合内容**:
- EBook + EBookFile
- AudiobookFile
- Comic + ComicFile（启发式匹配）
- Video（启发式匹配）
- Music（启发式匹配）
- WorkLink（手动关联）

**关联方式**:
1. 手动 include（优先）
2. 启发式匹配（series/title）
3. 手动 exclude（过滤）

---

### 2.12 仪表盘

#### 2.12.1 `dashboard.py` - 仪表盘 (645行)
**功能**: 系统总览数据

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 综合仪表盘 |
| `/system-stats` | GET | 系统统计 |
| `/media-stats` | GET | 媒体统计 |
| `/download-stats` | GET | 下载统计 |
| `/storage-stats` | GET | 存储统计 |
| `/music-stats` | GET | 音乐统计 |
| `/downloader-status` | GET | 下载器状态 |
| `/system-resources-history` | GET | 资源历史 |
| `/layout` | GET/POST | 可拖拽布局 |
| `/layouts` | GET | 布局列表 |
| `/widgets` | GET | 组件列表 |

**统计模块**:
- SystemStats（CPU/内存/磁盘/网络）
- MediaStats（电影/剧集/动画）
- DownloadStats（活跃/暂停/完成）
- TTSStats（待处理/运行中）
- PluginStats（总数/活跃/隔离）
- ReadingStats（小说/有声书/漫画）
- RecentEvents（最近活动）

---

### 2.13 认证与通知

#### 2.13.1 `auth.py` - 认证 (304行)
**功能**: 用户认证管理

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/register` | POST | 用户注册 |
| `/login` | POST | 用户登录 |
| `/me` | GET | 当前用户信息 |
| `/logout` | POST | 用户登出 |

**认证方式**: OAuth2 + JWT Bearer Token

#### 2.13.2 `notification.py` - 通知 (414行)
**功能**: 通知管理

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/` | GET/POST | 列表/发送 |
| `/{id}` | GET/DELETE | 详情/删除 |
| `/{id}/read` | POST | 标记已读 |
| `/read-all` | POST | 全部已读 |
| `/unread/count` | GET | 未读数量 |

**通知渠道**: system / telegram / email / wechat / webhook / push

---

### 2.14 健康检查

#### 2.14.1 `smart_health.py` - 智能健康检查 (900行)
**功能**: 智能子系统诊断

**检查模块**:
- **Inbox**: 收件箱状态、最近运行、警告
- **TTS**: 引擎状态、限流信息、任务概览、存储
- **Multi-format Work**: 多形态作品统计

**TTS 健康检查项**:
- 配置状态（enabled/provider/output_root）
- 引擎初始化验证
- UsageTracker 状态
- RateLimiter 状态
- Job 队列概览
- 存储空间统计

---

## 三、API 设计模式总结

### 3.1 通用模式
1. **统一响应**: `BaseResponse` / `success_response()` / `error_response()`
2. **分页支持**: `PaginatedResponse`
3. **异步数据库**: `AsyncSession` + `Depends(get_db)`
4. **缓存策略**: `get_cache()` + TTL 配置
5. **日志记录**: `logger.error/warning/info`

### 3.2 Dev 模式保护
```python
if not settings.DEBUG:
    raise HTTPException(status_code=403, detail="此接口仅在 DEBUG 模式下可用")
```

### 3.3 批量查询优化
```python
# 避免 N+1：批量获取关联数据
ebook_ids = [e.id for e in ebooks]
audiobook_stmt = select(AudiobookFile.ebook_id).where(AudiobookFile.ebook_id.in_(ebook_ids))
```

### 3.4 启发式关联
```python
# 通过 series/title 模糊匹配关联内容
conditions.append(Comic.series.ilike(f"%{ebook.series}%"))
```

---

## 四、关键数据流

### 4.1 TTS 生成流程
```
用户请求 → tts_user_flow.enqueue
    ↓
检查现有任务 → 复用/新建 TTSJob
    ↓
job_service.create_job_for_ebook
    ↓
后台执行 → job_runner.run_batch_jobs
    ↓
tts_engine.synthesize → AudiobookFile
```

### 4.2 作品聚合流程
```
GET /work/{ebook_id}
    ↓
查询 EBook + EBookFile
    ↓
查询 WorkLink (手动关联)
    ↓
查询 AudiobookFile
    ↓
启发式匹配 Comic (series/title)
    ↓
启发式匹配 Video (series/title)
    ↓
启发式匹配 Music (title/album/tags)
    ↓
组装 WorkDetailResponse
```

---

## 五、待优化建议

1. **性能**: 部分聚合 API 可以增加缓存
2. **分页**: 筛选后的分页计算可优化
3. **索引**: 启发式匹配的 ilike 查询可考虑全文索引
4. **事务**: 批量操作可增加事务保护
5. **测试**: 建议增加 API 集成测试覆盖率

---

## 六、附录：文件清单

### 已分析文件 (30+)
| 文件 | 行数 | 类别 |
|------|------|------|
| media.py | 1219 | 核心业务 |
| download.py | 1139 | 核心业务 |
| music.py | 1364 | 核心业务 |
| subscription.py | 897 | 核心业务 |
| manga_local.py | 810 | 核心业务 |
| search.py | 706 | 核心业务 |
| dashboard.py | 645 | 核心业务 |
| rss.py | 588 | 核心业务 |
| site.py | 778 | 核心业务 |
| smart_health.py | 900 | 系统管理 |
| admin_tts_settings.py | 434 | TTS |
| tts_user_flow.py | 273 | TTS |
| tts_jobs.py | 263 | TTS |
| tts_storage.py | 311 | TTS |
| tts_voice_presets.py | 221 | TTS |
| tts_work_profile.py | 191 | TTS |
| tts_playground.py | 281 | TTS |
| tts_regen.py | 133 | TTS |
| tts_user_batch.py | 100 | TTS |
| tts_work_batch.py | 135 | TTS |
| audiobook.py | 314 | 有声书 |
| audiobook_center.py | 402 | 有声书 |
| ebook.py | 274 | 电子书 |
| novel_center.py | 320 | 小说 |
| novel_reader.py | 310 | 小说 |
| work.py | 404 | 作品中心 |
| library.py | 422 | 媒体库 |
| manga_remote.py | 315 | 漫画 |
| auth.py | 304 | 认证 |
| notification.py | 414 | 通知 |

---

## 七、补充分析模块

### 7.1 智能系统模块

#### 7.1.1 `intel.py` - Local Intel API (403行)
**功能**: HR 任务、事件、站点健康状态管理

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/hr-tasks` | GET | HR 任务列表（按风险排序） |
| `/events` | GET | 智能事件列表 |
| `/sites` | GET | 站点健康状态 |
| `/settings` | GET/PUT | Local Intel 配置 |

**特点**:
- 风险等级计算（high/medium/low）
- 事件类型：HR_PENALTY、TORRENT_DELETED、SITE_THROTTLED
- 配置项：intel_enabled、intel_hr_mode、intel_move_check_enabled

#### 7.1.2 `recommendation.py` - 推荐系统 (915行)
**功能**: 多算法推荐引擎

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 个性化推荐 |
| `/similar/{id}` | GET | 相似内容推荐 |
| `/popular` | GET | 热门推荐 |
| `/bangumi` | GET | Bangumi 动漫推荐 |
| `/preferences` | GET/PUT | 用户偏好设置 |
| `/settings` | GET/PUT | 推荐设置 |

**推荐算法**: hybrid / collaborative / content_based / popularity / deep_learning

---

### 7.2 系统管理模块

#### 7.2.1 `downloader.py` - 下载器管理 (381行)
**功能**: qBittorrent/Transmission 实例管理

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/instances` | GET | 下载器实例列表 |
| `/{id}/stats` | GET | 下载器统计 |
| `/{id}/test` | POST | 连接测试 |

**支持下载器**: qBittorrent、Transmission

#### 7.2.2 `backup.py` - 备份系统 (501行)
**功能**: 数据库备份与恢复

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/create` | POST | 创建备份 |
| `/list` | GET | 备份列表 |
| `/{id}` | GET/DELETE | 详情/删除 |
| `/restore` | POST | 恢复备份 |
| `/status` | GET | 备份状态 |
| `/export/config` | GET | 导出配置 |
| `/export/user_data` | GET | 导出用户数据 |

#### 7.2.3 `storage_monitor.py` - 存储监控 (665行)
**功能**: 存储目录监控与预警

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/directories` | GET/POST | 目录列表/创建 |
| `/directories/{id}` | GET/PUT/DELETE | CRUD |
| `/directories/{id}/usage` | GET | 使用情况 |
| `/directories/{id}/history` | GET | 历史数据 |
| `/alerts` | GET | 预警列表 |
| `/statistics` | GET | 监控统计 |
| `/trends` | GET | 使用趋势 |

#### 7.2.4 `health.py` - 健康检查 (216行)
**功能**: 系统健康诊断

**检查项**:
- 数据库连接
- 缓存系统（L1/L2）
- 磁盘空间

**响应状态**: healthy / warning / unhealthy

#### 7.2.5 `settings.py` - 系统设置 (502行)
**功能**: 系统配置管理

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 所有设置 |
| `/category/{cat}` | GET | 分类设置 |
| `/{key}` | GET/PUT/DELETE | 单项 CRUD |
| `/batch` | POST | 批量更新 |
| `/initialize` | POST | 初始化默认值 |
| `/defaults/all` | GET | 获取默认设置 |
| `/safety/global` | GET/POST | 安全策略设置 |

---

### 7.3 第三方集成模块

#### 7.3.1 `douban.py` - 豆瓣 API (455行)
**功能**: 豆瓣媒体信息集成

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/search` | GET | 搜索媒体 |
| `/detail/{id}` | GET | 媒体详情 |
| `/rating/{id}` | GET | 评分信息 |
| `/top250` | GET | 电影 TOP250 |
| `/hot/movie` | GET | 热门电影 |
| `/hot/tv` | GET | 热门剧集 |

**支持类型**: movie / tv / short_drama

#### 7.3.2 `calendar.py` - 日历 (117行)
**功能**: 订阅/下载事件日历

**主要端点**:
| 端点 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 日历事件列表 |
| `/subscription/{id}/ics` | GET | iCalendar 导出 |

**事件类型**: subscription / download / media_update

---

## 八、API 文件完整清单

### 8.1 已深入分析 (40+文件)

| 序号 | 文件 | 行数 | 功能分类 |
|------|------|------|----------|
| 1 | media.py | 1219 | TMDB集成 |
| 2 | download.py | 1139 | 下载管理 |
| 3 | music.py | 1364 | 音乐管理 |
| 4 | subscription.py | 897 | 媒体订阅 |
| 5 | manga_local.py | 810 | 本地漫画 |
| 6 | search.py | 706 | 资源搜索 |
| 7 | dashboard.py | 645 | 仪表盘 |
| 8 | rss.py | 588 | RSS订阅 |
| 9 | site.py | 778 | 站点管理 |
| 10 | smart_health.py | 900 | 智能健康检查 |
| 11 | admin_tts_settings.py | 434 | TTS设置总览 |
| 12 | tts_user_flow.py | 273 | 用户TTS流程 |
| 13 | tts_jobs.py | 263 | TTS任务管理 |
| 14 | tts_storage.py | 311 | TTS存储管理 |
| 15 | tts_voice_presets.py | 221 | TTS声线预设 |
| 16 | tts_work_profile.py | 191 | TTS作品配置 |
| 17 | tts_playground.py | 281 | TTS调试 |
| 18 | tts_regen.py | 133 | TTS重生成 |
| 19 | tts_user_batch.py | 100 | 用户批量TTS |
| 20 | tts_work_batch.py | 135 | TTS作品批量 |
| 21 | audiobook.py | 314 | 有声书管理 |
| 22 | audiobook_center.py | 402 | 有声书中心 |
| 23 | ebook.py | 274 | 电子书管理 |
| 24 | novel_center.py | 320 | 小说中心 |
| 25 | novel_reader.py | 310 | 小说阅读器 |
| 26 | work.py | 404 | 作品中心 |
| 27 | library.py | 422 | 统一媒体库 |
| 28 | manga_remote.py | 315 | 远程漫画 |
| 29 | auth.py | 304 | 认证 |
| 30 | notification.py | 414 | 通知 |
| 31 | intel.py | 403 | Local Intel |
| 32 | recommendation.py | 915 | 推荐系统 |
| 33 | backup.py | 501 | 备份系统 |
| 34 | storage_monitor.py | 665 | 存储监控 |
| 35 | downloader.py | 381 | 下载器管理 |
| 36 | health.py | 216 | 健康检查 |
| 37 | settings.py | 502 | 系统设置 |
| 38 | douban.py | 455 | 豆瓣集成 |
| 39 | calendar.py | 117 | 日历 |

### 8.2 API 目录其他文件 (35+待分析)

```
admin_library_settings.py   admin_status.py         alert_channels.py
audiobooks.py               bangumi.py              category.py
charts.py                   cloud_storage.py        cloud_storage_chain.py
config_admin.py             cookiecloud.py          decision.py
directory.py                duplicate_detection.py  ext_indexer.py
external_indexer_debug.py   file_browser.py         file_cleaner.py
filter_rule_groups.py       gateway.py              global_rules.py
global_search.py            graphql/                hnr.py
home.py                     inbox_dev.py            local_intel_admin.py
log_center.py               logs.py                 manga_follow.py
manga_progress.py           ...
```

---

## 九、系统架构亮点

### 9.1 模块化设计
- **清晰分层**: API → Service → Repository
- **统一响应**: BaseResponse 确保一致性
- **关注点分离**: 每个文件职责单一

### 9.2 智能化特性
- **Local Intel**: HR 监控、站点风控
- **TTS 系统**: 完整的文本转语音流水线
- **推荐引擎**: 多算法融合推荐

### 9.3 多媒体支持
- **7+ 媒体类型**: 电影/剧集/动画/电子书/有声书/漫画/音乐
- **作品聚合**: WorkHub 统一视图
- **多形态标记**: WorkFormats 关联展示

### 9.4 外部集成
- **TMDB**: 电影/剧集元数据
- **豆瓣**: 中文媒体评分
- **Bangumi**: 动漫数据
- **PT 站点**: 自动化下载

---

*报告完成 - 共分析 40+ API 文件，覆盖 15000+ 行代码*
