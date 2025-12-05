# 安全事故报告：GitGuardian Generic Password 告警

**日期**: 2025-12-06  
**任务**: SECRET-HYGIENE-1  
**严重级别**: 低（仅为默认占位符密码，非真实生产密码）

---

## 1. 泄露点定位

### 1.1 GitGuardian 报警内容

- **仓库**: strmforge/VabHub
- **分支**: main
- **类型**: Generic Password
- **内容**: `vabhub_password` 作为默认数据库密码出现在多个文件中

### 1.2 涉及文件清单

| 文件 | 行号 | 变量/位置 | 类型 |
|------|------|----------|------|
| `docker-compose.yml` | 21, 60 | `DB_PASSWORD` 默认值 | compose 默认密码 |
| `docker-compose.prod.yml` | 24, 63 | `DB_PASSWORD` 默认值 | compose 默认密码 |
| `README.md` | 64, 79 | 示例代码 | 文档示例 |
| `.env.docker.example` | 15, 16 | `DB_PASSWORD`, `DATABASE_URL` | 模板示例 |
| `.env.example` | 34, 44 | `DATABASE_URL`, `DB_PASSWORD` | 模板示例 |
| `docs/user/DEPLOY_WITH_DOCKER.md` | 54, 85, 342 | 示例代码和表格 | 文档示例 |
| `docs/DOCKER_DEPLOYMENT.md` | 45 | 环境变量表格 | 文档示例 |
| `docs/ci/DOCKER-SMOKE-RUN-1-report.md` | 170, 236, 372 | CI 报告示例 | 文档示例 |

---

## 2. 影响评估

### 2.1 泄露内容类型

- **类型**: PostgreSQL 数据库默认密码
- **实际值**: `vabhub_password`（占位符/示例密码）

### 2.2 影响范围

| 环境 | 是否受影响 | 说明 |
|------|-----------|------|
| 公网生产环境 | ❌ 无 | 不存在公网部署 |
| 云服务 | ❌ 无 | 未使用云数据库 |
| 家宽/NAS | ⚠️ 低风险 | 如使用默认密码，建议更换 |
| 本地开发 | ✅ 安全 | 仅本机访问 |

### 2.3 风险结论

**低风险**：
- 这是模板/示例中的占位符密码，不是真实生产密码
- 数据库服务未暴露公网
- 仅家宽局域网可访问

---

## 3. 修复计划

### 3.1 代码脱敏 (P2)

- [ ] 将所有 `vabhub_password` 改为明确的占位符（如 `change-me-in-production`）
- [ ] 在 compose 文件中移除默认密码，强制用户设置

### 3.2 文档更新 (P2)

- [ ] 更新所有文档中的示例密码为占位符
- [ ] 添加安全警告，提醒用户必须更改默认密码

### 3.3 防护措施 (P4)

- [ ] 添加 secret 扫描脚本
- [ ] 创建安全策略文档

---

## 4. 密码旋转状态

### 4.1 环境清单

| 环境 | 密码旋转 | 状态 |
|------|----------|------|
| 本地开发 | 用户自行处理 | 📋 TODO |
| 家宽 NAS | 用户自行处理 | 📋 TODO |

### 4.2 用户操作建议

如果您在真实环境中使用了 `vabhub_password`：

1. 生成新的安全密码（20+ 字符，含大小写数字）
2. 更新 `.env.docker` 中的 `DB_PASSWORD`
3. 更新 PostgreSQL 数据库用户密码：
   ```bash
   docker exec -it vabhub-db psql -U vabhub -c "ALTER USER vabhub PASSWORD 'new-secure-password';"
   ```
4. 重启服务：`docker compose restart`

---

## 5. 修复完成记录

- [x] 2025-12-06: 创建事故报告
- [x] 2025-12-06: 代码脱敏完成
  - docker-compose.yml: 移除默认密码，改用必填变量
  - docker-compose.prod.yml: 同上
  - .env.docker.example: 改用 `CHANGE-ME-xxx` 占位符
  - .env.example: 同上
  - README.md: 更新示例代码
  - docs/user/DEPLOY_WITH_DOCKER.md: 更新示例和表格
- [x] 2025-12-06: 文档更新完成
  - docs/SECURITY_SECRETS_POLICY.md: 安全策略文档
  - docs/SECURITY_SECRET_HISTORY_CLEANING.md: 历史清理指南
- [x] 2025-12-06: 扫描脚本添加
  - scripts/secret_scan.sh: 敏感信息扫描脚本
- [ ] 待验证: GitGuardian 验证通过（推送后自动触发）
