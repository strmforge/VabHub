# CI 环境变量与 Flag 规范

本文档说明 VabHub CI 中使用的环境变量及其约定，帮助开发者正确使用这些变量。

---

## 1. 核心环境变量

### 1.1 `VABHUB_CI`

| 属性 | 值 |
|------|---|
| **用途** | 标识当前运行在 CI 环境中 |
| **CI 中的值** | `1` |
| **本地默认** | 不设置（空） |

**约定**：
- ✅ **允许**：用于测试脚本中的"环境特判"，例如：
  - `test_rsshub_minimal.py` 在 CI 中无 RSSHub 源时选择跳过而非失败
  - 调整测试超时时间或重试次数
- ❌ **禁止**：在业务逻辑中用 `VABHUB_CI` 改变真实行为

**使用示例**：
```python
import os

if os.getenv("VABHUB_CI") == "1":
    logger.warning("CI 环境，跳过该检查")
    return  # 跳过，不失败
else:
    raise RuntimeError("本地环境必须配置该项")
```

---

### 1.2 `API_PREFIX`

| 属性 | 值 |
|------|---|
| **用途** | API 路由前缀 |
| **CI 中的值** | `/api` |
| **后端配置** | `backend/app/core/config.py` |
| **测试配置** | `backend/scripts/api_test_config.py` |

**约定**：
- 当前后端 API 前缀为 `/api`
- pytest 测试中硬编码了 `/api/...` 路径
- CI 环境必须与后端配置保持一致

**注意**：如果未来要升级到 `/api/v1`，需要同时更新：
1. `backend/app/core/config.py`
2. `backend/scripts/api_test_config.py`
3. 所有 pytest 测试文件
4. CI workflow 中的 `API_PREFIX` 环境变量

---

### 1.3 `API_BASE_URL`

| 属性 | 值 |
|------|---|
| **用途** | API 基础地址 |
| **CI 中的值** | `http://127.0.0.1:8100`（回归测试）或 `http://127.0.0.1:8000`（本地） |
| **测试配置** | `backend/scripts/api_test_config.py` |

**约定**：
- 本地开发通常使用 `http://127.0.0.1:8000`
- CI 回归测试（`test-all.yml`）使用 `http://127.0.0.1:8100` 避免端口冲突

---

### 1.4 `REDIS_ENABLED`

| 属性 | 值 |
|------|---|
| **用途** | 是否启用 Redis 缓存 |
| **CI 中的值** | `false` |
| **本地默认** | 取决于配置 |

**约定**：
- CI 中禁用 Redis 以简化环境
- 本地开发可以根据需要启用或禁用

---

## 2. Workflow 中使用的其他变量

### 2.1 Docker 相关

| 变量 | 用途 | 设置位置 |
|------|------|---------|
| `REGISTRY` | Docker 仓库地址 | workflow 的 `env` 块 |
| `IMAGE_NAME` | 镜像名称 | workflow 的 `env` 块 |
| `DOCKERHUB_USERNAME` | Docker Hub 用户名 | GitHub Secrets |
| `DOCKERHUB_TOKEN` | Docker Hub Access Token | GitHub Secrets |

### 2.2 数据库相关

| 变量 | CI 中的值 | 说明 |
|------|----------|------|
| `DATABASE_URL` | `sqlite:///./.ci_data/vabhub_regression.db` | CI 使用 SQLite |

---

## 3. 新增 CI Flag 的规范

如果需要新增 CI 相关的环境变量，请遵循以下规范：

### 3.1 命名规范

- 使用 `VABHUB_CI_` 前缀
- 使用大写字母和下划线
- 名称要清晰描述用途

**示例**：
- `VABHUB_CI_ALLOW_SLOW_TESTS` - 允许运行慢测试
- `VABHUB_CI_SKIP_INTEGRATION` - 跳过集成测试

### 3.2 文档要求

新增变量时，必须：
1. 在本文档中添加说明
2. 在使用该变量的代码中添加注释
3. 在 CI workflow 中明确设置

### 3.3 使用原则

- **尽量温和**：不要用环境变量掩盖真实问题
- **优先跳过**：如果某检查在 CI 中不适用，跳过而非假装通过
- **记录日志**：当环境变量影响行为时，输出清晰的日志

---

## 4. 当前 Workflow 环境变量一览

### 4.1 `ci.yml`

```yaml
env:
  VABHUB_CI: "1"
  REGISTRY: ghcr.io
  IMAGE_NAME: ghcr.io/strmforge/vabhub
  DOCKERHUB_IMAGE: strmforge/vabhub
```

### 4.2 `test-all.yml`

```yaml
env:
  VABHUB_CI: "1"
  API_PREFIX: /api
  DATABASE_URL: "sqlite:///./.ci_data/vabhub_regression.db"
  REDIS_ENABLED: "false"
  API_BASE_URL: http://127.0.0.1:8100
```

### 4.3 `docker-release.yml`

```yaml
env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ghcr.io/strmforge/vabhub
  DOCKERHUB_IMAGE: strmforge/vabhub
```

---

## 5. 相关文档

- [CI_OVERVIEW.md](./CI_OVERVIEW.md) - CI 总览
- [RSSHUB-MINIMAL-1.md](./RSSHUB-MINIMAL-1.md) - `VABHUB_CI` 在 RSSHub 测试中的应用
