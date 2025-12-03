# SYSTEM HEALTH - P0 Overview

## 仓库结构概览

- `backend/` — FastAPI + SQLAlchemy 服务端代码，包含 `app/`、`runners/`、`scripts/`
- `frontend/` — Vue 3 + TypeScript + Vuetify 前端项目（Vite 构建）
- `docs/` — 设计/实施/总结文档合集，本次系统健康报告也写在此
- `config/` — 额外配置模板（例如 Nginx / 部署脚本）
- `services/` — 额外的服务或工具脚本
- `docker/`、`docker-compose*.yml` — 容器化/编排配置
- `scripts/`、`tools/` — 实用脚本与工具
- 其它根目录文件（README、*.md、*.bat等）——历史总结与启动脚本

## 版本约束

### Python / 后端
- 依赖来源：`requirements.txt`
- 主要版本：
  - `fastapi==0.104.1`
  - `uvicorn==0.24.0`
  - `sqlalchemy==2.0.23`
  - `pydantic==2.5.0`
  - `pydantic-settings==2.1.0`
  - `python-telegram-bot==20.7`
  - `mypy==1.7.1`、`ruff/flake8`（lint & type check）
- Python 版本：未在 `pyproject` 中声明，依赖文件和现有脚本默认 3.10+（FastAPI + SQLAlchemy 2.x 要求）。运行时以 3.10/3.11 为参考。

### Node / 前端
- 依赖来源：`frontend/package.json`
- 主要工具链：
  - Vue 3 (`vue@^3.4.21`), Vite 5, TypeScript ~5.3, Vuetify 3.5
  - Lint: ESLint 8.56 + `@vue/eslint-config-typescript`
  - Type check: `vue-tsc`

## 各阶段涉及模块范围

- **P1 – 后端 Python 健康检查**：`backend/app/**`（FastAPI、bots、阅读、漫画、下载、notify、runners）。重点命令：`python -m compileall backend/app -q`、`mypy backend/app`、`ruff backend/app`。
- **P2 – 前端 Vue/TS 健康检查**：`frontend/src/**`（阅读中心、下载中心、通知中心、漫画页面等）。命令：`npm run build`、`npm run lint`、`npm run typecheck`。
- **P3 – Bots & Runners & 通知链路**：`backend/app/modules/bots/**`、`backend/app/runners/**`、通知服务、前端通知组件。
- **P4 – 配置 & 环境 & 安全**：`backend/app/core/config.py`、`.env.example`、存储/路径校验逻辑。
- **P5 – 自检命令脚本**：`docs/SYSTEM_HEALTH_SELF_CHECK_COMMANDS.md` +（可选）`scripts/self_check.sh`。
- **P6 – 系统级总结报告**：`docs/SYSTEM_HEALTH_P6_COMPLETION_REPORT.md`。

> 记录完成，继续自动进入 P1 阶段，无需额外确认。

## 补充说明

- Python 版本要求：3.10+（FastAPI + SQLAlchemy 2.x 要求）
- mypy/ruff 配置：根目录暂无 `mypy.ini`/`ruff.toml`，使用默认配置
- 前端构建工具：Vite 5 + vue-tsc
- 本次检查优先保证编译/构建通过，不追求零 warning，重点消除 error 级别问题
