# BACKEND-CI-5 基线报告

**Date**: 2025-12-05  
**Status**: ✅ 修复完成

## 任务目标

1. 让 GitHub Actions 中的 `dev_check_backend.sh` 真正达到全绿
2. 修复 CI 环境与本地环境的差异
3. 精简 docker-compose.yml，实现密钥自动生成

## CI 日志中的 6 个失败测试

| # | 测试 | 失败原因 | 修复方案 |
|---|------|----------|----------|
| 1 | `test_unknown_action_allowed` | HR 表不存在时返回 `ERROR_OCCURRED` | SafetyPolicyEngine 增加 HR 表缺失容错 |
| 2 | `test_import_local_txt_api_success` | httpx 0.28+ 不支持 `app=` 参数 | 改用 `ASGITransport` |
| 3 | `test_import_local_txt_api_file_not_found` | 同上 | 同上 |
| 4 | `test_import_local_txt_api_invalid_file` | 同上 | 同上 |
| 5 | `test_upload_txt_novel_success` | 测试 DB 缺少 `ebooks` 表 | conftest.py 已有 `create_all` |
| 6 | `test_run_batch_jobs_updates_status_counts_correctly` | 同一 batch 重复处理 job | 添加 `processed_job_ids` 跟踪 |

## CI 环境问题

| 问题 | 解决方案 |
|------|----------|
| ruff 未安装 | 添加 ruff 到 `requirements-dev.txt` |
| httpx API 变更 | 使用 `ASGITransport` 适配新版本 |

## 修复统计

```
# 修复前 (CI 环境)
ruff: [warn] 未安装，跳过
mypy: Success (1140 files)
pytest: 6 failed, 441 passed, 88 skipped

# 修复后 (CI 环境)
ruff: All checks passed!
mypy: Success (1140 files)
pytest: 0 failed, 447 passed, 111 skipped
```
