# BACKEND-CI-4 基线报告

**Date**: 2025-12-05  
**Status**: ✅ 全绿（无需修复）

## 任务目标

修复 6 个 pytest 失败，让 `dev_check_backend.sh` 在 CI 完整跑通。

## 基线确认结果

经验证，任务书中列出的 6 个测试**当前均已通过**：

| 测试 | 状态 | 说明 |
|------|------|------|
| `test_unknown_action_allowed` | ✅ PASSED | SafetyPolicyEngine 对未知 action 正确返回 ALLOW |
| `test_import_local_txt_api_success` | ✅ PASSED | Novel Demo API 正常工作 |
| `test_import_local_txt_api_file_not_found` | ✅ PASSED | 文件不存在错误处理正确 |
| `test_import_local_txt_api_invalid_file` | ✅ PASSED | 无效文件错误处理正确 |
| `test_upload_txt_novel_success` | ✅ PASSED | 小说上传成功，ebook_id 正常返回 |
| `test_run_batch_jobs_updates_status_counts_correctly` | ✅ PASSED | TTS 批处理状态计数正确 |

## 检查结果统计

```
# Ruff
All checks passed!

# mypy
Success: no issues found in 1140 source files

# pytest
447 passed, 111 skipped, 306 warnings in ~77s
```

## 分析

这些测试在之前的 CI 修复会话中可能已被解决，或者是环境因素导致的临时失败。当前代码库状态已满足 BACKEND-CI-4 的目标要求。

### 可能的历史修复点

1. **SafetyPolicyEngine**: 之前的会话可能已添加了对未知 action 的兜底处理
2. **httpx AsyncClient**: 测试文件可能已使用正确的 ASGITransport 适配
3. **Novel Upload API**: 测试 DB 注入可能已正确配置
4. **TTS Job Runner**: 批处理逻辑可能已修复重复处理问题

## 结论

**无需额外修复**。后端 CI 检查已达到全绿状态。
