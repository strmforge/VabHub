# DOCKER-IMAGE-RELEASE-1 Report

**任务**: 0.0.1-rc1 官方 Docker 镜像发布  
**日期**: 2025-12-06  
**版本**: 0.0.1-rc1（保持不变）

---

## 1. 概述

本次任务目标：让用户可以"拉官方镜像 + 配 env + docker compose up"直接跑 VabHub。

### 完成情况

| 目标 | 状态 |
|------|------|
| GHCR 官方镜像命名确定 | ✅ |
| docker-compose.prod.yml 改为 All-in-One | ✅ |
| .env.docker.example 添加 VABHUB_VERSION | ✅ |
| 部署文档更新 | ✅ |
| README 更新官方镜像信息 | ✅ |
| 系统总览添加里程碑 | ✅ |

---

## 2. 镜像信息

### 2.1 官方镜像

| 镜像 | 架构 | 说明 |
|------|------|------|
| `ghcr.io/strmforge/vabhub` | All-in-One | 前后端合一单镜像 |

### 2.2 Tag 策略

| Tag | 触发条件 | 示例 |
|-----|----------|------|
| `latest` | push main 分支 | `ghcr.io/strmforge/vabhub:latest` |
| `v<version>` | push v* tag | `ghcr.io/strmforge/vabhub:v0.0.1-rc1` |
| `<sha>` | 所有构建 | `ghcr.io/strmforge/vabhub:11d4d56` |

---

## 3. 文件变更

### 3.1 修改文件

| 文件 | 变更内容 |
|------|----------|
| `docker-compose.prod.yml` | 改为 All-in-One 架构，使用 GHCR 镜像 |
| `.env.docker.example` | 添加 `VABHUB_VERSION` 变量 |
| `docs/user/DEPLOY_WITH_DOCKER.md` | 添加官方镜像部署章节 |
| `README.md` | 添加官方镜像引用 |
| `docs/VABHUB_SYSTEM_OVERVIEW.md` | 添加里程碑 |

### 3.2 新增文件

| 文件 | 说明 |
|------|------|
| `docs/ci/DOCKER-IMAGE-RELEASE-1-baseline.md` | 基线文档 |
| `docs/ci/DOCKER-IMAGE-RELEASE-1-report.md` | 本报告 |

---

## 4. 使用流程

### 4.1 生产部署（推荐）

```bash
# 1. 配置环境变量
cp .env.docker.example .env.docker
# 编辑 .env.docker，设置 VABHUB_VERSION=0.0.1-rc1

# 2. 拉取官方镜像
docker compose -f docker-compose.prod.yml --env-file .env.docker pull

# 3. 启动服务
docker compose -f docker-compose.prod.yml --env-file .env.docker up -d

# 4. 访问应用
# http://<宿主机 IP>:52180
```

### 4.2 升级

```bash
# 1. 修改 .env.docker 中的 VABHUB_VERSION
# 2. 拉取新镜像并重启
docker compose -f docker-compose.prod.yml --env-file .env.docker pull
docker compose -f docker-compose.prod.yml --env-file .env.docker up -d
```

---

## 5. CI 状态

### 5.1 现有 CI (ci.yml)

CI 已配置 Docker 构建推送：

- **触发条件**: push main / push v* tag
- **构建内容**: All-in-One 镜像
- **推送目标**: GHCR (`ghcr.io/strmforge/vabhub`)

### 5.2 CI 检查

| 检查 | 命令 | 状态 |
|------|------|------|
| 后端 | `scripts/dev_check_backend.sh` | ✅ 已配置 |
| 前端 | `pnpm dev_check` | ✅ 已配置 |
| Docker 构建 | `docker/build-push-action` | ✅ 已配置 |

---

## 6. 架构一致性

| 组件 | 架构 | 状态 |
|------|------|------|
| `docker-compose.yml` | All-in-One | ✅ |
| `docker-compose.prod.yml` | All-in-One | ✅ (本次修复) |
| `ci.yml` | All-in-One | ✅ |
| `Dockerfile` (根目录) | All-in-One | ✅ |

---

## 7. 注意事项

1. **镜像推送**: 需要有 GHCR 写权限的账号推送 tag，触发 CI 构建
2. **首次部署**: 镜像为公开镜像，无需登录即可拉取
3. **版本管理**: 通过 `VABHUB_VERSION` 环境变量控制镜像版本

---

## 8. 后续建议

- [ ] 推送 `v0.0.1-rc1` tag 触发首次官方镜像构建
- [ ] 验证镜像可正常拉取和运行
- [ ] 考虑添加多架构支持 (amd64 + arm64)

---

**参考文档**:
- `docs/ci/DOCKER-IMAGE-RELEASE-1-baseline.md`
- `docs/user/DEPLOY_WITH_DOCKER.md`
- `docs/releases/0.0.1-rc1.md`
