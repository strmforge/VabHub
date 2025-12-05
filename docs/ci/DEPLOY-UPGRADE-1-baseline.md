# DEPLOY-UPGRADE-1 Baseline Report

**Date**: 2025-12-05  
**Status**: In Progress

## P0: 当前部署基线

### Docker 镜像状态

**架构**: CI-DOCKER-ONE-IMAGE-1 已完成，使用单一 All-in-One 镜像

| 镜像 | 状态 |
|------|------|
| `ghcr.io/strmforge/vabhub:latest` | ✅ 主镜像 (前端+后端合一) |
| `ghcr.io/strmforge/vabhub-backend` | ❌ 已废弃 |
| `ghcr.io/strmforge/vabhub-frontend` | ❌ 已废弃 |

### docker-compose 结构

当前 `docker-compose.yml` 服务列表：

| 服务名 | 镜像 | 端口映射 | 说明 |
|--------|------|----------|------|
| `vabhub` | `ghcr.io/strmforge/vabhub:latest` | `${VABHUB_PORT:-8080}:8000` | 主应用 |
| `db` | `postgres:14-alpine` | 无外部映射 | PostgreSQL |
| `redis` | `redis:7-alpine` | 无外部映射 | Redis 缓存 |

### 端口配置

| 配置项 | 当前值 | 说明 |
|--------|--------|------|
| 宿主机端口 | `${VABHUB_PORT:-8080}` | 默认 8080，与下载器端口冲突风险 |
| 容器内端口 | `8000` | 固定，由 uvicorn 监听 |
| 健康检查 | `http://localhost:8000/health` | 容器内端口 |

### Docker Socket 挂载

**当前状态**: ❌ 未挂载

```yaml
# docker-compose.yml 中无以下配置
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

### 插件与 OCR/Cookie 实现

#### 插件系统

- **实现位置**: `backend/app/plugin_sdk/`, `backend/app/services/plugin_*.py`
- **运行模型**: 插件作为 Python 模块运行于 VabHub 进程内
- **无外部容器**: 未发现"为插件单独起容器"的逻辑

#### CookieCloud 集成

- **实现位置**: `backend/app/modules/cookiecloud/service.py`, `backend/app/api/cookiecloud.py`
- **运行模型**: 通过 HTTP API 调用外部 CookieCloud 服务
- **配置方式**: 用户配置 CookieCloud 服务 URL，VabHub 定时同步 Cookie

#### OCR 相关

- **当前状态**: 未发现独立 OCR 模块
- **潜在用途**: 站点验证码识别（如有需要）

---

## 待改进项 (本任务目标)

| 项目 | 当前状态 | 目标状态 |
|------|----------|----------|
| 默认端口 | 8080 (冲突风险) | 52180 (冷门端口) |
| 端口可配置 | 仅宿主机端口可配 | 内外同步可配 |
| docker.sock | 未挂载 | 挂载 (用于升级) |
| 版本 API | 无 | `/api/admin/version` |
| 升级 API | 无 | `/api/admin/upgrade` |
| 前端升级 UI | 无 | 系统设置页 |
| 插件文档 | 未明确 | 明确"进程内运行" |

---

## 实施进度

| 阶段 | 状态 |
|------|------|
| P0: 基线确认 | ✅ 完成 |
| P1: 端口策略 | ✅ 完成 |
| P2: Docker Socket | ✅ 完成 |
| P3: 版本 API | ✅ 完成 |
| P4: 升级引擎 | ✅ 完成 |
| P5: 前端升级 UI | ✅ 完成 |
| P6: 重启检查 | ✅ 完成 |
| P7: 插件模型 | ✅ 完成 |
| PZ: 文档更新 | ✅ 完成 |

---

## 最终实现

### 端口配置

- **默认端口**: `52180` (避开 8080/7878/8989/9091)
- **环境变量**: `VABHUB_PORT`
- **内外同步**: 容器内端口与宿主机端口相同

### Docker Socket

- **挂载路径**: `/var/run/docker.sock:/var/run/docker.sock:ro`
- **用途**: UI 一键升级
- **可选**: 不挂载则只能手动升级

### 升级 API

| 端点 | 说明 |
|------|------|
| `GET /api/admin/system/version` | 版本信息 |
| `POST /api/admin/system/upgrade` | 升级操作 |
| `GET /api/admin/system/docker-status` | Docker 状态 |

### 插件运行模型

- **插件**: 运行于 VabHub 进程内的 Python 模块
- **外部集成**: CookieCloud、OCR、AI 服务等通过 HTTP API 调用
