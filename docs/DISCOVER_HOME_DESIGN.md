# 发现页设计文档

> 本文件记录发现页的公共 key 策略、数据源接入和后续扩展方向。
> 创建于 0.0.3 DISCOVER-MUSIC-HOME

---

## 1. 公共 Key 策略

### 1.1 设计原则

**发现页与刮削分离**：
- 发现页使用「公共 key」展示热门内容，不写入本地库
- 刮削使用「私有 key」获取完整元数据，写入本地库

### 1.2 配置优先级

```
发现页 TMDB Key 获取顺序：
1. PUBLIC_TMDB_DISCOVER_KEY (公共 key)
2. TMDB_API_KEY (私有 key)
3. 返回 None，对应 section 显示空状态
```

### 1.3 环境变量

| 变量名 | 用途 | 默认值 |
|--------|------|--------|
| `PUBLIC_TMDB_DISCOVER_KEY` | 发现页 TMDB 热门内容 | 无 |
| `ENABLE_PUBLIC_METADATA_KEYS` | 总开关 | true |
| `PUBLIC_BANGUMI_ENABLED` | Bangumi 数据源开关 | true |

### 1.4 安全边界

- **禁止日志输出 key 值**：只输出「使用了公共 key / 使用了私有 key」
- **公共 key 不用于刮削**：避免 rate limit 影响用户的库数据完整性
- **CI 环境不依赖外部服务**：测试中 mock 所有外部调用

---

## 2. 当前接入的数据源

### 2.1 TMDB

- **接口**：`/trending/{media_type}/week`, `/movie/popular`, `/tv/popular`
- **需要 Key**：是
- **缓存 TTL**：30 分钟
- **返回内容**：热门电影/剧集列表

### 2.2 豆瓣

- **接口**：内部 `DoubanClient` API
- **需要 Key**：否（直接爬取）
- **缓存 TTL**：30 分钟
- **返回内容**：热门电影/剧集列表

### 2.3 Bangumi

- **接口**：`api.bgm.tv/calendar`, `api.bgm.tv/search`
- **需要 Key**：否（公共 API）
- **缓存 TTL**：1-6 小时
- **返回内容**：热门番剧列表

---

## 3. API 响应结构

### 3.1 `/api/discover/home` 响应

```json
{
  "tmdb_configured": true,
  "tmdb_message": "当前使用公共数据源",
  "sections": [
    {
      "title": "本周热门电影",
      "items": [...],
      "more_link": "/search?source=tmdb"
    }
  ],
  "has_public_keys": true,
  "has_private_keys": false,
  "key_source": "public"
}
```

### 3.2 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `tmdb_configured` | bool | 兼容 0.0.2，表示是否有可用 key |
| `key_source` | string | "public" / "private" / "none" |
| `has_public_keys` | bool | 是否配置了公共 key |
| `has_private_keys` | bool | 是否配置了私有 key |

---

## 4. 后续扩展方向

### 4.1 DISCOVER-HOME-2 预留

- [ ] 支持用户自定义数据源优先级
- [ ] 添加更多榜单源（IMDb、烂番茄等）
- [ ] 支持按地区/语言筛选热门内容

### 4.2 与 PT 规则中心联动

- [ ] 从发现页一键创建订阅规则
- [ ] 显示「已订阅」标记

---

## 5. 相关文件

- `backend/app/core/public_metadata_config.py` - 公共 key 配置层
- `backend/app/services/discover_service.py` - 发现页聚合服务
- `backend/app/api/discover.py` - 发现页 API
- `frontend/src/pages/Discover.vue` - 发现页前端

---

*最后更新：2025-12-13 DISCOVER-MUSIC-HOME-0.0.3*
