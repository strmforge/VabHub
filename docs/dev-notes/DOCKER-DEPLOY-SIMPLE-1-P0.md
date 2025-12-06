# DOCKER-DEPLOY-SIMPLE-1 P0 现状巡检

## 1. 密钥相关现状

### 1.1 SecretManager (✅ 已存在)
- **位置**: `backend/app/core/secret_manager.py`
- **功能**:
  - 支持从 ENV 或 JSON 文件读取密钥
  - 自动生成密钥并持久化到 `./data/.vabhub_secrets.json`
  - 优先使用 ENV，其次使用文件中的值
- **集成状态**:
  - 已在 `main.py` lifespan 中调用 `initialize_secrets()`
  - `config.py` 有动态属性 `SECRET_KEY_DYNAMIC`、`JWT_SECRET_KEY_DYNAMIC`

### 1.2 需修改点
| 文件 | 问题 | 修改方案 |
|------|------|----------|
| `.env.docker.example` | SECRET_KEY/JWT_SECRET_KEY 仍有占位值 | 注释掉，标记为高级可选 |

---

## 2. 管理员创建现状

### 2.1 当前状态 (❌ 不满足需求)
- **无启动时自动创建逻辑**
- 只有手动脚本 `backend/scripts/create_admin.py`
- 文档说需要调用 `/api/auth/register` API

### 2.2 需实现
- `ensure_initial_superuser()` 函数
- 支持 `SUPERUSER_NAME` / `SUPERUSER_PASSWORD` 环境变量
- 集成到 `main.py` lifespan
- 无 ENV 密码时自动生成随机密码并输出到日志

---

## 3. docker-compose.yml 现状

### 3.1 已有能力 (✅)
- 单端口 52180 映射
- SUPERUSER_NAME/SUPERUSER_PASSWORD 环境变量支持
- vabhub / db / redis 三服务结构

### 3.2 需修改点
| 项目 | 问题 | 修改方案 |
|------|------|----------|
| volumes | 使用 named volumes | 改为直接路径示例 `/volume1/docker/vabhub/...` |
| 注释 | 挂载说明不够清晰 | 添加详细的媒体/下载/inbox 挂载示例 |

---

## 4. .env.docker.example 现状

### 4.1 需修改点
| 变量 | 当前状态 | 修改方案 |
|------|----------|----------|
| SECRET_KEY | 有占位值 | 注释掉，标记为高级可选 |
| JWT_SECRET_KEY | 有占位值 | 注释掉，标记为高级可选 |
| SUPERUSER_NAME | 无 | 添加，标记为可选 |
| SUPERUSER_PASSWORD | 无 | 添加，标记为推荐设置 |

---

## 5. 文档不一致点

### 5.1 README.md
| 问题 | 修改方案 |
|------|----------|
| 显示多端口 80/8092 | 统一为 52180 |
| 服务说明表有 backend/frontend | 改为 vabhub/db/redis |

### 5.2 docs/user/DEPLOY_WITH_DOCKER.md
| 问题 | 修改方案 |
|------|----------|
| SECRET_KEY/JWT_SECRET_KEY 标记为必需 | 改为可选，说明自动生成 |
| 有 80/8092 端口说明 | 统一为 52180 |
| 创建初始用户需要调用 API | 改为使用 ENV 或查看日志 |

### 5.3 docs/user/GETTING_STARTED.md
| 问题 | 修改方案 |
|------|----------|
| 显示多端口 80/8092 | 统一为 52180 |
| 有 backend/frontend 服务表格 | 改为 vabhub/db/redis |
| 需要手动调用 /api/auth/register | 改为查看日志或使用 ENV |

---

## 6. 实施顺序

1. **P1**: 密钥管理 - SecretManager 已满足需求，只需清理 ENV 文件
2. **P2**: 实现 `ensure_initial_superuser()` 并集成到启动流程
3. **P3**: 更新 docker-compose.yml 挂载示例
4. **P4**: 更新 .env.docker.example
5. **P5**: 统一文档
6. **P6**: 端到端验证
7. **P7**: 代码质量检查
8. **PZ**: 更新 CHANGELOG 和系统总览

---

*Created: 2025-12-06*
