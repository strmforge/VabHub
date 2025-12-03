# VabHub Mesh Scheduler

任务调度中心，避免多人同时抓取同一PT站点。

## 功能

- 节点注册和管理
- 任务分发和租约机制
- 站点指针管理
- 防重复抓取

## API端点

### POST /v1/worker/register
节点注册，声明可抓取的站点。

**请求头**:
- `X-Network-Key`: 网络共享密钥

**请求体**:
```json
{
  "node_id": "worker-001",
  "capabilities": {
    "sites": ["site1", "site2"]
  }
}
```

### POST /v1/jobs/lease
节点领取任务（租约）。

**请求头**:
- `X-Network-Key`: 网络共享密钥

**请求体**:
```json
{
  "node_id": "worker-001",
  "want_sites": ["site1"],
  "max_jobs": 1
}
```

### POST /v1/jobs/finish
回报抓取完成，推进站点指针。

**请求头**:
- `X-Network-Key`: 网络共享密钥

**请求体**:
```json
{
  "job_id": 1,
  "node_id": "worker-001",
  "success": true,
  "new_cursor_value": "cursor-123"
}
```

## 配置

### 环境变量

```env
APP_ENV=production
DB_URL=postgresql+asyncpg://user:password@host:5432/vabhub_mesh
NETWORK_SHARED_KEY=YOUR_RANDOM_SECRET_KEY
MAX_WORKERS_PER_SITE=3
LEASE_DURATION_SECONDS=300
```

## 部署

### Railway部署

1. 创建Railway项目
2. 连接Supabase/Neon Postgres数据库
3. 设置环境变量
4. 部署代码

### Docker部署

```bash
docker build -t vabhub-mesh-scheduler .
docker run -p 8000:8000 --env-file .env vabhub-mesh-scheduler
```

## 数据库

使用PostgreSQL（Supabase/Neon免费版）。

表结构：
- `workers` - 节点信息
- `jobs` - 任务信息
- `site_cursors` - 站点指针

