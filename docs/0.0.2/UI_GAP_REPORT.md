# VabHub 0.0.2-0.0.3 现状巡检报告

> 禁止重复造轮子清单 - IDE 必读

---

## 1. 已有但可能未正确使用的后端 API

### 1.1 健康检查 ✅ 已存在
| 端点 | 位置 | 状态 |
|------|------|------|
| `GET /health` | `main.py:363` | ✅ 已在根路径注册 |
| `GET /healthz` | `main.py:381` | ✅ K8s 兼容端点 |
| `GET /api/health` | `api/health.py` | ✅ 详细健康检查 |

### 1.2 发现页 ✅ 已存在
| 端点 | 位置 | 状态 |
|------|------|------|
| `GET /api/discover/home` | `api/discover.py` | ✅ 多源聚合 (0.0.3) |
| `GET /api/douban/hot/movie` | `api/douban.py` | ✅ 豆瓣热门电影 |
| `GET /api/douban/hot/tv` | `api/douban.py` | ✅ 豆瓣热门剧集 |
| `GET /api/bangumi/popular` | `api/bangumi.py` | ✅ Bangumi 热门 |
| `GET /api/bangumi/calendar` | `api/bangumi.py` | ✅ 每日放送 |

### 1.3 榜单系统 ✅ 已存在
| 端点 | 位置 | 状态 |
|------|------|------|
| `GET /api/charts/*` | `api/charts.py` | ✅ 音乐+影视榜单 |
| `GET /api/music/home` | `api/music_home.py` | ✅ 音乐首页 (0.0.3) |

### 1.4 推荐系统 ✅ 已存在
| 端点 | 位置 | 状态 |
|------|------|------|
| `GET /api/recommendations/*` | `api/recommendation.py` | ✅ 推荐系统 |

### 1.5 日志系统 ✅ 已存在
| 端点 | 位置 | 状态 |
|------|------|------|
| `GET /api/log-center/*` | `api/log_center.py` | ✅ 日志查询/导出 |
| `WS /api/log-center/ws` | `api/log_center.py` | ✅ 实时日志推送 |

---

## 2. 已有但可能未挂菜单的前端页面

| 页面 | 文件 | 路由 | 导航状态 |
|------|------|------|----------|
| 发现页 | `Discover.vue` | `/discover` | ✅ 已挂 |
| 日志中心 | `LogCenter.vue` | `/logs` | ⚠️ 需确认 |
| 音乐中心 | `MusicCenter.vue` | `/music` | ✅ 已挂 |
| 音乐订阅 | `MusicSubscriptions.vue` | `/music/subscriptions` | ✅ 已挂 |
| 下载任务 | `Downloads.vue` | `/downloads` | ✅ 已挂 |
| 通知中心 | `Notifications.vue` | `/notifications` | ⚠️ 需确认 |
| 媒体库预览 | `LibraryPreview.vue` | `/library` | ⚠️ 需确认 |
| 日历 | `Calendar.vue` | `/calendar` | ⚠️ 需确认 |

---

## 3. 关键问题诊断

### 3.1 PostgreSQL 连接耗尽 (`too many clients already`)

**根因分析**：
- 当前连接池配置：`pool_size=10, max_overflow=20`
- **缺少**：`pool_timeout`, `pool_recycle` 参数
- **缺少**：scheduler/后台任务的 session 生命周期管理

**修复方案** (P2)：
```python
# database.py 需要添加
pool_timeout=30,      # 获取连接超时
pool_recycle=1800,    # 30分钟回收连接
```

### 3.2 `/health` 返回 404

**根因分析**：
- `/health` 端点**已存在**于 `main.py:363`
- 可能是请求时服务未完全启动，或被 SPA 路由拦截

**验证命令**：
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/health
```

---

## 4. 禁止重复实现的功能清单

以下功能**已存在**，IDE 不得重新实现：

1. ❌ 不要新建 health 端点 - 已有 `/health`, `/healthz`, `/api/health`
2. ❌ 不要新建发现页 API - 已有 `/api/discover/home`
3. ❌ 不要新建豆瓣/Bangumi 集成 - 已有 `api/douban.py`, `api/bangumi.py`
4. ❌ 不要新建榜单 API - 已有 `/api/charts/*`
5. ❌ 不要新建日志 API - 已有 `/api/log-center/*`
6. ❌ 不要新建推荐 API - 已有 `/api/recommendations/*`

---

## 5. 需要补充的内容

### 5.1 导航结构调整 (P1)
- [ ] 影视发现放回主位
- [ ] 确保所有页面都有空态引导

### 5.2 数据库连接池优化 (P2)
- [ ] 添加 `pool_timeout`, `pool_recycle` 参数
- [ ] 确保后台任务正确释放连接

### 5.3 前端页面接入 (P3-P5)
- [ ] 发现页调用已有 API
- [ ] 音乐首页调用已有榜单 API
- [ ] 日志页面调用已有日志 API

---

*最后更新: 2025-12-13 DISCOVER-MUSIC-HOME-0.0.3 P0*
