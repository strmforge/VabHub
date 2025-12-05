# VabHub 安全策略：敏感信息管理

> 本文档定义了 VabHub 项目中敏感信息（密码、密钥、Token 等）的管理规范。

---

## 1. 核心原则

### 1.1 绝对禁止

- ❌ **禁止**在代码中硬编码任何真实密码、API Key、Token
- ❌ **禁止**在 docker-compose.yml 中使用明文密码默认值
- ❌ **禁止**提交 `.env`、`.env.docker` 等包含真实凭据的文件
- ❌ **禁止**在 UI 组件中展示真实账号密码（如下载器配置示例）

### 1.2 推荐做法

- ✅ 所有敏感配置使用环境变量 `${VAR_NAME}`
- ✅ 使用 `.env.example` 模板文件，值用占位符（如 `CHANGE-ME-xxx`）
- ✅ 在 `.gitignore` 中排除所有真实环境文件
- ✅ 提交前运行 `scripts/secret_scan.sh` 检查

---

## 2. 文件分类

### 2.1 可以提交的文件

| 文件 | 说明 |
|------|------|
| `.env.example` | 模板文件，包含占位符密码 |
| `.env.docker.example` | Docker 模板，包含占位符密码 |
| `docker-compose.yml` | 使用 `${VAR}` 变量引用 |

### 2.2 绝对不能提交的文件

| 文件 | 说明 |
|------|------|
| `.env` | 本地开发真实配置 |
| `.env.docker` | Docker 部署真实配置 |
| `.env.local` | 任何 `.local` 后缀文件 |
| `*.pem`, `*.key` | 私钥文件 |

---

## 3. 密码占位符规范

### 3.1 标准占位符格式

```bash
# 数据库密码
DB_PASSWORD=CHANGE-ME-use-strong-random-password

# API 密钥
SECRET_KEY=change-this-in-production-use-strong-random-string

# 第三方服务
TMDB_API_KEY=your-tmdb-api-key-here
```

### 3.2 占位符要求

- 必须明显是占位符，不能像真实密码
- 推荐使用 `CHANGE-ME-xxx` 或 `change-this-xxx` 格式
- 在占位符前添加注释说明必须修改

---

## 4. Docker Compose 规范

### 4.1 正确写法

```yaml
environment:
  # ⚠️ 必须在 .env.docker 中设置
  POSTGRES_PASSWORD: ${DB_PASSWORD:?Please set DB_PASSWORD}
```

### 4.2 错误写法

```yaml
environment:
  # ❌ 错误：硬编码密码
  POSTGRES_PASSWORD: "mypassword123"
  
  # ❌ 错误：使用默认值
  POSTGRES_PASSWORD: ${DB_PASSWORD:-default_password}
```

---

## 5. 前端组件规范

### 5.1 下载器配置相关

对于 Downloads.vue、SpeedLimitDialog.vue 等组件：

- ❌ 不在 UI 上展示任何真实账号/密码示例
- ❌ 不使用 `admin/123456` 等典型密码作为提示
- ✅ 使用中性说明："请在设置页面配置下载器认证信息"
- ✅ 如需展示格式，使用 `username` / `password` 等占位词

### 5.2 表单字段

```vue
<!-- ✅ 正确：使用占位符提示 -->
<v-text-field
  v-model="password"
  type="password"
  label="密码"
  placeholder="请输入下载器密码"
/>

<!-- ❌ 错误：展示示例密码 -->
<v-text-field
  v-model="password"
  type="password"
  label="密码（如：admin123）"
/>
```

---

## 6. 开发流程

### 6.1 提交前检查

```bash
# 运行敏感信息扫描
./scripts/secret_scan.sh

# 严格模式（CI 中使用）
./scripts/secret_scan.sh --strict
```

### 6.2 代码审查要点

- 检查新增的环境变量是否有默认值
- 检查 docker-compose 变更是否包含明文密码
- 检查文档示例是否使用占位符

---

## 7. 事故响应

### 7.1 发现泄露后的步骤

1. **立即旋转密码** - 生成新密码替换泄露的凭据
2. **代码脱敏** - 将硬编码改为环境变量
3. **评估影响** - 判断是否需要历史清理
4. **文档记录** - 创建事故报告

### 7.2 参考文档

- `docs/SECURITY_SECRET_INCIDENT-20251206.md` - 事故报告模板
- `docs/SECURITY_SECRET_HISTORY_CLEANING.md` - 历史清理指南

---

## 8. 历史事故记录

| 日期 | 事故 | 影响 | 状态 |
|------|------|------|------|
| 2025-12-06 | GitGuardian 报警：vabhub_password | 低（占位符密码） | ✅ 已处理 |

---

## 9. 贡献者须知

如果您要为 VabHub 贡献代码：

1. 阅读本文档，了解敏感信息管理规范
2. 确保不在 PR 中包含任何真实凭据
3. 使用 `scripts/secret_scan.sh` 自检
4. 如不确定某项配置是否敏感，请在 PR 中询问
