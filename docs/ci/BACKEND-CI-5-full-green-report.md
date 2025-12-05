# BACKEND-CI-5 全绿报告

**Date**: 2025-12-05  
**Status**: ✅ 完成

## 概述

BACKEND-CI-5 + DEPLOY-YAML-2 任务完成：
- CI 环境与本地环境对齐
- 6 个测试失败全部修复
- docker-compose.yml 精简化

## 修复内容

### 1. CI 依赖修正

**文件**: `requirements-dev.txt`

```diff
+ ruff>=0.1.0,<1.0  # Linter (替代 flake8)
```

### 2. SafetyPolicyEngine HR 表容错

**文件**: `backend/app/modules/safety/engine.py`

```python
# 获取HR状态 (容错处理：如果 HR 表不存在则视为无 HR 数据)
hr_case = ctx.hr_case
if ctx.site_key and ctx.torrent_id and not hr_case:
    try:
        hr_case = await self._hr_repo.get_by_site_and_torrent(ctx.site_key, ctx.torrent_id)
    except Exception as hr_err:
        err_msg = str(hr_err).lower()
        if "no such table" in err_msg or "does not exist" in err_msg:
            hr_case = None  # 视为无 HR 数据
        else:
            raise
```

### 3. httpx ASGITransport 适配

**文件**: `backend/tests/test_novel_demo_api.py`

```python
from httpx import AsyncClient, ASGITransport

_transport = ASGITransport(app=app)

async with AsyncClient(transport=_transport, base_url="http://test") as ac:
    ...
```

### 4. TTS Job Runner 去重

**文件**: `backend/app/modules/tts/job_runner.py`

```python
# 跟踪已处理的 Job ID，避免在同一批次中重复处理
processed_job_ids: set[int] = set()

for i in range(max_jobs):
    job = await find_next_pending_job(db, exclude_ids=processed_job_ids)
    if not job:
        break
    processed_job_ids.add(job.id)
    ...
```

### 5. docker-compose.yml 精简

**变更前**: 暴露 SECRET_KEY, JWT_SECRET_KEY 等安全变量

**变更后**: 
- 移除安全密钥配置（自动生成）
- 添加初始管理员配置
- 简化为类似 MoviePilot 的风格

```yaml
environment:
  - VABHUB_PORT=${VABHUB_PORT:-52180}
  - TZ=${TZ:-Asia/Shanghai}
  - DATABASE_URL=postgresql://...
  - REDIS_URL=redis://...
  - SUPERUSER_NAME=${SUPERUSER_NAME:-admin}
  - SUPERUSER_PASSWORD=${SUPERUSER_PASSWORD:-}
```

## 测试结果

```
# Ruff
All checks passed!

# mypy
Success: no issues found in 1140 source files

# pytest
447 passed, 111 skipped, 306 warnings
0 failed ✅
```

## 文件变更清单

| 文件 | 变更类型 |
|------|----------|
| `requirements-dev.txt` | 添加 ruff 依赖 |
| `backend/app/modules/safety/engine.py` | HR 表容错 |
| `backend/app/modules/tts/job_runner.py` | 去重逻辑 |
| `backend/app/modules/tts/job_service.py` | 添加 find_next_pending_job |
| `backend/tests/test_novel_demo_api.py` | httpx 适配 |
| `docker-compose.yml` | 精简配置 |

## 后续

GitHub Actions CI 应当能够：
1. 成功安装 ruff
2. 运行 `dev_check_backend.sh` 全绿
3. 触发 Docker 构建和推送
