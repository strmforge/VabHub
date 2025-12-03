# VabHub 云端服务

本目录包含VabHub云端服务的独立部署代码。

## 服务列表

### 1. Mesh Scheduler
任务调度中心，避免多人同时抓取同一PT站点。

**位置**: `mesh_scheduler/`  
**部署**: Railway + Supabase/Neon  
**文档**: `mesh_scheduler/README.md`

### 2. Intel Center
共享智能大脑，提供别名识别和发布索引查询。

**位置**: `intel_center/`  
**部署**: Deta.Space  
**文档**: `intel_center/README.md`

### 3. Snapshots
静态快照服务，提供离线/低带宽环境支持。

**位置**: `snapshots/`  
**部署**: Cloudflare Pages/R2  
**文档**: `snapshots/README.md`

## 部署指南

详细部署步骤请参考：`阶段2部署指南.md`

## 快速开始

### Mesh Scheduler
```bash
cd mesh_scheduler
docker build -t vabhub-mesh-scheduler .
docker run -p 8000:8000 --env-file .env vabhub-mesh-scheduler
```

### Intel Center
```bash
cd intel_center
docker build -t vabhub-intel-center .
docker run -p 8000:8000 --env-file .env vabhub-intel-center
```

## 配置

每个服务都有独立的配置文件：
- `mesh_scheduler/.env.example`
- `intel_center/.env.example`

## 测试

部署后使用以下命令测试：

```bash
# 测试Mesh Scheduler
curl -X POST http://localhost:8000/v1/worker/register \
  -H "X-Network-Key: YOUR_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"node_id": "test", "capabilities": {}}'

# 测试Intel Center
curl "http://localhost:8000/v1/alias/resolve?q=钢铁侠"
```

