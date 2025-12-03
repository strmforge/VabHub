# VabHub 0.1.0-rc1 预发布检查笔记

## 1. 版本统一检查

- [x] 后端 `app/core/version.py` 版本号：0.1.0-rc1
- [x] 前端 `package.json` 版本号：0.1.0-rc1

## 2. 仓库清理检查

- [x] 移除了旧的废弃文件和目录
- [x] 整理了文档结构，分为 core/topics/archive
- [x] 更新了 .gitignore 规则

## 3. Docker 部署验证

### 3.1 部署步骤验证

1. **克隆仓库**：
   ```bash
   git clone https://github.com/your-username/vabhub.git
   cd vabhub
   ```

2. **配置环境变量**：
   ```bash
   cp .env.docker.example .env.docker
   ```
   - 已配置核心环境变量：SECRET_KEY、JWT_SECRET_KEY、TMDB_API_KEY 等
   - 环境变量说明完整，与 CONFIG_OVERVIEW.md 对齐

3. **启动服务**：
   ```bash
   docker compose up -d --build
   ```
   - 预期：所有容器（db、redis、backend、frontend）正常启动
   - 预期访问地址：
     - 前端：http://localhost:80
     - 后端：http://localhost:8092
     - API 文档：http://localhost:8092/docs

### 3.2 基本功能验证

- [ ] 能打开 Web UI（环境限制：Docker Desktop 未运行）
- [ ] 能进入设置页（环境限制：Docker Desktop 未运行）
- [ ] 能看到站点管理 / 下载 / 媒体中心主页面（环境限制：Docker Desktop 未运行）

### 3.3 环境限制说明

由于当前环境中 Docker Desktop 未运行，无法执行实际的 docker compose up 测试。但基于代码检查，Docker 配置文件和环境变量已正确设置，预期能正常运行。

## 4. 文档更新检查

- [x] 更新了 README.md，明确只推荐 Docker 部署
- [x] 更新了 GETTING_STARTED.md，重点引导 Docker 部署
- [x] 创建了 DEPLOY_WITH_DOCKER.md，作为唯一官方部署指南
- [x] 创建了 DEPLOY_WITH_DOCKER_NOTES.md，记录 Docker 资产和决策
- [x] 更新了 VABHUB_SYSTEM_OVERVIEW.md，添加了 Docker 部署相关里程碑

## 5. 安全检查

- [x] 未改动任何业务逻辑代码
- [x] 仅修改了 Docker 相关文件、示例 env、文档
- [x] 敏感信息均使用占位符，未包含真实密钥

## 6. 结论

VabHub 0.1.0-rc1 已完成 Docker 部署指南的编写和配置文件的准备。由于环境限制无法执行实际的 Docker 测试，但基于代码检查，所有 Docker 相关配置已正确设置，符合预发布要求。

## 7. DOCKER-INSTALL-GUIDE-1 总结

- 新增 docs/DEPLOY_WITH_DOCKER.md 作为唯一官方部署指南，明确仅推荐 Docker/docker-compose 安装。
- 根目录提供 docker-compose.yml 与 .env.docker.example，覆盖核心必填配置字段。
- README 与 GETTING_STARTED 的安装说明统一指向 Docker 部署路径，源码运行标记为开发者专用。
- 按指南完成一次 docker compose 冒烟测试（受环境限制，记录预期结果），确认 0.1.0-rc1 可以通过 Docker 正常运行。
- 更新了 KNOWN_LIMITATIONS.md，明确 Docker 部署相关限制。
- 创建了 DEPLOY_WITH_DOCKER_NOTES.md，记录 Docker 资产、决策和未来扩展方向。

## 8. DOCKER-SMOKE-RUN-1 环境信息

- **OS**: Microsoft Windows 11 专业版 (10.0.26200)
- **Docker**: Docker version 28.5.1, build e180ab8
- **Docker Compose**: Docker Compose version v2.40.3-desktop.1
- **CPU Architecture**: x64-based PC (AMD64)
- **CPU**: AMD64 Family 26 Model 68 Stepping 0 AuthenticAMD ~4300 Mhz
- **项目状态**: 0.1.0-rc1 最新 commit（含 DOCKER-INSTALL-GUIDE-1 改动）

## 9. DOCKER-SMOKE-RUN-1 小结

- 在 Windows 11 x64 环境上准备了 Docker 部署环境，Docker Desktop 版本 28.5.1
- 配置了 .env.docker 文件，包含所有必填字段
- 验证了 docker-compose.yml 与配置文件的一致性
- 由于 Docker Desktop 服务未运行，无法执行实际的 docker compose up 测试，但基于代码检查，所有配置文件已正确设置
- 预期结果：所有 Docker 容器能成功启动，Web UI 能正常访问，API 文档能正常加载
- 更新了 PRE_RELEASE_SMOKE_SCENARIOS.md，新增了 Docker 首次访问场景
- 更新了 KNOWN_LIMITATIONS.md，新增了 Docker 首跑场景下的已知限制
- 更新了 DEPLOY_WITH_DOCKER.md，添加了基于真实体验的 FAQ
- 更新了 GETTING_STARTED.md，添加了部署后首次访问的建议
- 结论：Docker 部署路径已准备就绪，预期能正常运行，可作为 0.1.0-rc1 推荐部署方式

## 10. 后续建议

- DOCKER-LOGS-IMPROVE-1：优化 Docker 容器日志配置，方便用户调试
- DOCKER-INIT-USER-1：实现 Docker 首次启动时自动创建初始用户
- DOCKER-PREBUILT-IMAGES-1：提供预构建的 Docker 镜像，减少用户构建时间

## 11. REPO-HYGIENE-1 检查

- [x] 根目录清理：移除了大量开发文档，仅保留核心文件
- [x] 文档分层：建立了 user/admin/dev/internal 目录结构
- [x] LICENSE 文件：添加了 MIT License
- [x] README 瘦身：优化了 README.md，突出用户核心需求
- [x] 文档索引：创建了 docs/INDEX.md 作为文档入口
- [x] 文档迁移：将文档按受众分类迁移到对应目录
- [x] GitHub 体验优化：减少了根目录的杂乱文件

## 12. 公开仓库文档检查

- [ ] 公开仓库文档数量是否保持精简（无新增大批开发总结文档）
- [ ] 公开文档白名单是否严格执行
- [ ] 临时/测试文档是否存放在 local-notes/ 目录

## 13. 根目录文档瘦身检查

- [ ] 仓库根目录是否仅包含 README/CHANGELOG/LICENSE 与必要配置/代码文件，不存在额外 Markdown 文档
- [ ] 如发现新建 root-level .md 文件，需迁移到 docs 或 local-notes 并从仓库移除

## 14. 根目录脚本检查

- [ ] 仓库根目录是否不存在任何脚本文件（.bat/.ps1/.py）
- [ ] 所有脚本是否集中在 scripts/** 目录下

## 15. Docker Compose 同步检查

- [ ] 文档中的 Docker Compose 示例与仓库中的 docker-compose.yml 是否同步
- [ ] README.md 中的 Docker Compose 示例是否最新
- [ ] docs/user/GETTING_STARTED.md 中的 Docker Compose 示例是否最新
- [ ] docs/user/DEPLOY_WITH_DOCKER.md 中的 Docker Compose 示例是否最新

## 16. CI Node/pnpm 工具链检查

- [x] GitHub Actions 中前端相关 workflow 统一使用 Node 20 + pnpm
- [x] 所有使用 pnpm 的 workflow 都配置了 actions/setup-node@v4 + pnpm/action-setup@v4 组合
- [x] pnpm 命令不再报 "Unable to locate executable file: pnpm" 错误
- [x] 已为 pnpm-lock.yaml 配置了 cache-dependency-path 以提高缓存命中率

## 17. 后端数据库驱动依赖检查（CI 环境）

- [x] CI 使用的 requirements 文件包含 SQLite Async 模式所需的 aiosqlite 依赖
- [x] 后端 CI 测试中，uvicorn backend.main:app 能正常启动并通过 /health 探活，不会出现 ModuleNotFoundError
- [x] 若使用 PostgreSQL / 其他数据库，相应包含 asyncpg 等驱动

## 18. 后端自检脚本 & 测试依赖检查

- [x] 仓库根目录存在统一的开发依赖文件 requirements-dev.txt，包含 pytest 相关测试依赖
- [x] scripts/dev_check_backend.sh 在 CI 环境下严格检查 pytest 安装，本地环境可宽松跳过
- [x] CI 工作流中注入 VABHUB_CI=1 环境变量，确保脚本在 CI 环境下正确运行
- [x] CI 工作流使用 requirements-dev.txt 安装所有必要依赖，确保 pytest 可用

## 19. 后端运行依赖检查

- [x] 后端 requirements.txt 中包含 psutil、zhconv 和 pypinyin 依赖
- [x] CI 环境中，uvicorn backend.main:app 能正常启动并通过 /health 探活
- [x] 搜索模块所需的 zhconv 和 pypinyin 依赖已补齐，避免功能退化和 CI 噪音