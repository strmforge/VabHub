# BACKEND-CI-2 失败用例分析

## 失败类型标签说明

| 标签 | 说明 |
|------|------|
| `db_state` | 依赖数据库状态 / 污染数据库 |
| `global_state` | 污染全局单例 / 缓存 / 配置 |
| `external_service` | 调用真实网络、文件系统、第三方 API |
| `order_dependent` | 单独跑绿、整套跑红 |
| `logic_bug` | 业务逻辑 bug |
| `env_assumption` | 假设某些 env / 配置 / 本地文件存在 |
| `mock_issue` | Mock 设置不完整或错误 |
| `schema_mismatch` | 模型/Schema 不匹配 |

---

## 高优先级 (核心链路)

### CookieCloud API (12 tests)

| NodeID | 标签 | 推荐策略 |
|--------|------|----------|
| `test_get_settings_success` | `db_state`, `order_dependent` | 添加 get_db override |
| `test_get_settings_not_found` | `db_state`, `order_dependent` | 添加 get_db override |
| `test_trigger_sync_success` | `mock_issue`, `global_state` | 修复 module mock 路径 |
| `test_trigger_sync_rate_limited` | `mock_issue`, `global_state` | 修复 module mock 路径 |
| `test_trigger_sync_not_enabled` | `mock_issue`, `global_state` | 修复 module mock 路径 |
| `test_trigger_sync_immediate_success` | `db_state`, `mock_issue` | 添加 get_db override |
| `test_trigger_site_sync_success` | `db_state`, `order_dependent` | 添加 get_db override |
| `test_test_connection_success` | `mock_issue` | 修复断言 |
| `test_test_connection_no_settings` | `mock_issue` | 修复断言文本匹配 |
| `test_get_status_success` | `db_state`, `order_dependent` | 添加 get_db override |
| `test_get_status_no_settings` | `db_state`, `order_dependent` | 添加 get_db override |
| `test_empty_host_url` | `logic_bug` | 修复断言 |

### TTS Playground API (5 tests)

| NodeID | 标签 | 推荐策略 |
|--------|------|----------|
| `test_playground_synthesize_basic_dummy_success` | `global_state`, `order_dependent` | 添加 TTS 状态重置 + get_db override |
| `test_playground_synthesize_rate_limited` | `global_state`, `order_dependent` | 同上 |
| `test_playground_synthesize_respects_ebook_profile` | `db_state`, `global_state` | 同上 |
| `test_playground_audio_endpoint_serves_file` | `global_state` | 同上 |
| `test_playground_synthesize_requires_debug_mode` | `global_state` | API module settings 补丁 |

### TTS User Flow API (7 tests)

| NodeID | 标签 | 推荐策略 |
|--------|------|----------|
| `test_enqueue_tts_job_for_work_basic` | `db_state`, `global_state` | get_db override + TTS 状态重置 |
| `test_enqueue_tts_job_skips_when_existing_active_job` | `db_state`, `global_state` | 同上 |
| `test_enqueue_tts_job_ebook_not_found` | `db_state` | get_db override |
| `test_get_tts_status_for_ebook_with_tts_audiobook` | `db_state`, `global_state` | 同上 |
| `test_get_tts_status_for_ebook_without_job` | `db_state`, `global_state` | 同上 |
| `test_overview_api_basic` | `db_state`, `order_dependent` | 同上 |
| `test_overview_api_status_filter` | `db_state`, `order_dependent` | 同上 |

### TTS User Batch API (4 tests)

| NodeID | 标签 | 推荐策略 |
|--------|------|----------|
| `test_preview_basic_filter_and_limit` | `db_state`, `global_state` | get_db override |
| `test_enqueue_respects_skip_if_has_tts_*` | `db_state`, `global_state` | 同上 |
| `test_enqueue_respects_max_new_jobs` | `db_state`, `global_state` | 同上 |
| `test_enqueue_skips_when_active_job_exists` | `db_state`, `global_state` | 同上 |

---

## 中优先级 (状态污染 / 顺序依赖)

### TTS Jobs API (3 tests)

| NodeID | 标签 | 推荐策略 |
|--------|------|----------|
| `test_run_next_executes_queued_job` | `db_state`, `global_state` | get_db override |
| `test_list_jobs_filters_by_status` | `db_state`, `order_dependent` | 同上 |
| `test_get_job_returns_job_detail` | `db_state`, `order_dependent` | 同上 |

### TTS Job Rerun Rate Limit (2 tests)

| NodeID | 标签 | 推荐策略 |
|--------|------|----------|
| `test_job_becomes_partial_*` | `global_state`, `order_dependent` | TTS rate limiter 重置 |
| `test_job_rerun_uses_resume_index_*` | `global_state`, `order_dependent` | 同上 |

### Inbox Dev API (3 tests)

| NodeID | 标签 | 推荐策略 |
|--------|------|----------|
| `test_inbox_preview_empty_dir` | `schema_mismatch` | 修复 ResponseValidationError |
| `test_inbox_preview_with_sample_files` | `schema_mismatch` | 同上 |
| `test_inbox_run_once_basic` | `schema_mismatch` | 同上 |

### User Notifications (3 tests)

| NodeID | 标签 | 推荐策略 |
|--------|------|----------|
| `test_create_notification_success` | `schema_mismatch` | 移除 severity 参数或更新 model |
| `test_create_notification_for_different_statuses` | `schema_mismatch` | 同上 |
| `test_create_notification_without_ebook` | `schema_mismatch` | 同上 |

### Video Importer (5 tests)

| NodeID | 标签 | 推荐策略 |
|--------|------|----------|
| 所有 5 个测试 | `env_assumption` | 使用 tmp_path 替代真实路径 |

### TTS Storage Service (2 tests)

| NodeID | 标签 | 推荐策略 |
|--------|------|----------|
| `test_scan_storage_*` | `external_service` | 文件权限问题，使用 tmp_path |
| `test_execute_cleanup_*` | `external_service` | 同上 |

---

## 低优先级 (集成测试 / 外部依赖)

### Safety Integration (8 tests)

| NodeID | 标签 | 推荐策略 |
|--------|------|----------|
| `test_download_with_active_hr_blocked` | `mock_issue` | 修复 HrCase mock |
| `test_delete_with_low_ratio_blocked` | `mock_issue` | 同上 |
| `test_move_with_hr_require_copy` | `mock_issue` | 同上 |
| `test_safety_engine_performance` | `mock_issue` | 同上 |
| `test_safety_notification_integration` | `mock_issue` | 添加缺失方法 mock |
| `test_backward_compatibility` | `schema_mismatch` | 修复 DecisionContext |
| `test_error_handling_robustness` | `schema_mismatch` | 修复 SafetyContext |
| `test_configuration_validation` | `schema_mismatch` | 修复 SiteSafetySettings |

### Safety Performance (4 tests)

| NodeID | 标签 | 推荐策略 |
|--------|------|----------|
| 所有 4 个测试 | `mock_issue`, `schema_mismatch` | 标记为 `@pytest.mark.integration` |

### Subscription (5 tests)

| NodeID | 标签 | 推荐策略 |
|--------|------|----------|
| `test_get_default_config_from_database` | `mock_issue` | 修复 AsyncMock |
| `test_get_default_config_invalid_media_type` | `logic_bug` | 修复业务逻辑 |
| `test_get_default_config_json_string_value` | `mock_issue` | 修复 AsyncMock |
| `test_get_default_config_invalid_json` | `mock_issue` | 修复 AsyncMock |
| `test_save_default_config_exclude_none` | `schema_mismatch` | 修复 ValidationError |

### Filter Rule Group (1 test)

| NodeID | 标签 | 推荐策略 |
|--------|------|----------|
| `test_resolve_groups_for_subscription_success` | `logic_bug` | 修复返回格式断言 |

---

## 修复优先级路线图

### Phase 1 - 基础设施 (P2-P3)
1. 统一 DB fixture，实现事务回滚
2. 统一 get_db override
3. 添加 TTS/通知/配置 状态重置 fixtures

### Phase 2 - 高优先级测试 (P2-P4)
1. CookieCloud API 测试
2. TTS 全链路测试 (Playground, User Flow, User Batch, Jobs)
3. Inbox Dev API

### Phase 3 - 中优先级测试 (P4)
1. User Notifications (schema 修复)
2. Video Importer (路径 mock)
3. TTS Storage Service (文件系统 mock)

### Phase 4 - 低优先级测试 (P4-P5)
1. Safety tests → 标记为 `@pytest.mark.integration`
2. Subscription tests → 修复 mock
3. Filter Rule Group → 修复断言

---

## 统计汇总

| 优先级 | 测试数 | 主要问题 |
|--------|--------|----------|
| 高 | 28 | db_state, global_state |
| 中 | 16 | order_dependent, schema_mismatch |
| 低 | 21 | integration, external_service |
| **总计** | **65** | |
