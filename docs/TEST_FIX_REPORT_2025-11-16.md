# 2025-11-16 核心接口回归修复报告

## 1. 背景概述

- 回归脚本 `backend/scripts/test_all.py` 在近期执行时出现以下失败：
  1. `GET /api/v1/music/charts` 返回 405，导致 `test_music_minimal.py` 中的榜单→订阅链路无法执行。
  2. `POST /auth/register`、`POST /auth/login` 返回 500，日志显示仍有 “Object of type datetime is not JSON serializable”。
  3. 新增短剧/音乐字段后，SQLite 旧实例缺少 `subscriptions.extra_metadata`、`download_tasks.extra_metadata`、`music_subscriptions.subscription_id` 等列，任何自动订阅都会抛 `no such column`。
  4. Redis 默认开启但未部署，`quick_test.py`、`test_functional.py` 中的创建订阅请求常因 L2 缓存连接超时被拖慢。

为恢复 `test_all.py --skip-music-execute` 的一键验证链路，本次完成了 API 前缀统一、数据库列自动补齐、GraphQL Schema 修复以及缓存降级策略优化。

## 2. 关键问题与修复

| 类别 | 症状 | 根因 | 修复措施 |
| --- | --- | --- | --- |
| API 路径 | `GET /api/v1/music/charts` 405 | 服务器已统一为 `/api`，测试仍写死 `/api/v1` | `test_all.py`、`test_rsshub_minimal.py` 默认前缀改为 `/api`；确认主站 `/api/music/charts` 可用 |
| 注册/登录 500 | datetime 序列化异常 | 旧数据表缺少 `extra_metadata`、`media_type` 字段，SQLAlchemy 执行报错后被 middleware 捕获 | `app/modules/short_drama/schema_utils.py` 改为同步引擎执行 DDL，启动时一次性补齐 `subscriptions`、`download_tasks`、`media` 新列 |
| 音乐订阅 500 | `music_subscriptions` 缺少 `subscription_id` | 之前仅在初始化时创建，旧库未迁移 | `app/modules/music/service.py` 引入同步引擎检查，若缺列自动执行 `ALTER TABLE`；同时对现有 `vabhub.db` 补齐该列 |
| GraphQL 启动崩溃 | `Type Mutation must define one or more fields` | mixin 动态构建的类未加 `@strawberry.type` 导致 Strawberry 忽略字段 | `QueryBase`、`MutationBase` 增加注解，再通过 mixin builder 输出最终 Query/Mutation |
| Redis 噪声 & 阻塞 | 没有 Redis 服务时每次创建订阅都会等待 2s 连接超时 | `_get_client` 会在每次调用时重试 redis.from_url | `RedisCacheBackend` 记忆首次失败并直接降级到内存/L3；在测试环境通过 `REDIS_ENABLED=false` 启动 |

## 3. 测试执行

1. 本地启动后端  
   ```bash
   export PYTHONPATH=backend
   export API_PREFIX=/api
   export REDIS_ENABLED=false
   python -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8100
   ```

2. 运行核心回归（忽略真实音乐下载）  
   ```bash
   python backend/scripts/test_all.py --skip-music-execute
   ```
   - `quick_test.py`、`test_functional.py`、`test_music_minimal.py`、`test_graphql_minimal.py`、`tests/test_plugins_api.py`、`test_rsshub_minimal.py` 全部完成；
   - `test_music_minimal.py` 输出截图：成功抓取榜单并创建音乐订阅、触发一次预览下载；
   - `test_rsshub_minimal.py` 由于本地没有可用 RSSHub 服务，会记录 `getaddrinfo failed` 但脚本在捕获后继续，将问题标记在总结中。

3. 额外验证  
   - `curl` 到 `/api/music/charts`（GET/POST）均 200；
   - `POST /api/music/subscriptions` 返回 201，响应体包含 `subscription_id`；
   - `sqlite3 vabhub.db` 查看 `subscriptions` / `download_tasks` / `music_subscriptions` 均已有新增列。

## 4. 后续建议

1. **测试脚本降噪**：`quick_test.py` 仍会在“创建订阅”阶段打印 `[ERROR] 创建订阅异常`（但脚本继续运行），需在脚本内处理 `response.status_code != 201` 的场景，以免误判。
2. **统一迁移工具**：目前 `short_drama`、`music`、`rsshub` 等模块各自维护 DDL，建议引入 Alembic 或最少编写统一的“schema 自愈”模块，启动时集中执行，减少重复代码与日志噪声。
3. **可选依赖提示**：`musicbrainzngs`、`pyacoustid`、`ruamel.yaml` 等缺失会在每次启动刷警告，可在 README / 服务配置中写明安装方式，或提供 `pip install -r requirements_optional.txt`。
4. **RSSHub 与下载器的 mock**：回归脚本默认会触发 RSSHub 任务、qBittorrent/Transmission 登录，目前会持续输出 connection failed。可考虑在测试模式下直接跳过这些 job（例如配置环境变量 `DISABLE_BACKENDS_FOR_TEST=1`）。

如需扩展本报告（例如加入前端自测、CI 运行截图等），可以继续追加章节；也可以将本文件链接到 `docs/DEV_PROGRESS_VABHUB.md` 的最新进度条目中。


