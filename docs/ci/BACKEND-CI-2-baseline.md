# BACKEND-CI-2 基线报告

**生成时间**: 2025-12-05  
**代码基线**: VabHub-RC1-202512050224 快照  
**环境**: Windows 11, Python 3.11.9, SQLite (test), pytest 7.4.3

## 运行命令

```bash
cd backend
python -m ruff check app alembic scripts tools --statistics
python -m mypy . --ignore-missing-imports
python -m pytest tests/ -v --tb=no -q
```

---

## Ruff 报错摘要

| 规则 | 数量 | 说明 |
|------|------|------|
| F401 | 931 | unused-import |
| E402 | 209 | module-import-not-at-top-of-file |
| E712 | 106 | true-false-comparison |
| F541 | 95 | f-string-missing-placeholders |
| F821 | 86 | undefined-name |
| F841 | 79 | unused-variable |
| E722 | 67 | bare-except |
| F811 | 19 | redefined-while-unused |
| E741 | 3 | ambiguous-variable-name |
| E711 | 2 | none-comparison |
| F601 | 1 | multi-value-repeated-key-literal |
| F823 | 1 | undefined-local |
| **总计** | **1599** | |

**备注**: 931 个 F401 中大部分是可选依赖检测（try/except ImportError 模式），不应自动删除。

---

## mypy 报错摘要

| 类别 | 数量 | 说明 |
|------|------|------|
| 总错误数 | 3795 | 473 个文件 |
| 主要类型 | - | name-defined, attr-defined, call-arg, assignment |

**备注**: 当前无 mypy.ini 配置文件，需创建配置以合理忽略部分检查或逐步修复。

---

## pytest 报错摘要

### 整体统计

```
484 passed, 65 failed, 9 skipped
```

### 失败用例分类

| 模块 | 失败数 | 主要原因 |
|------|--------|----------|
| CookieCloud API | 12 | 状态污染 / Mock 问题 |
| CookieCloud Integration | 1 | 状态污染 |
| Inbox Dev API | 3 | ResponseValidationError |
| TTS Job Rerun | 2 | 状态污染 (assert 'failed' == 'partial') |
| TTS Jobs API | 3 | 状态污染 |
| TTS Playground | 5 | 状态污染 / 路由问题 |
| TTS Storage Service | 2 | 文件权限 / 断言错误 |
| TTS User Batch | 4 | 400 vs 200 状态码 |
| TTS User Flow | 7 | 400/500 vs 200 状态码 |
| User Notifications | 3 | severity 参数不存在 |
| Video Importer | 5 | 路径配置差异 |
| Filter Rule Group | 1 | 返回格式差异 |
| Safety Integration | 8 | HrCase mock / NotificationService 缺方法 |
| Safety Performance | 4 | HrCase mock / NotificationService 缺方法 |
| Subscription | 5 | Mock 问题 / 断言错误 |

### 失败用例详细列表

```
tests/test_cookiecloud_api.py::TestCookieCloudAPI::test_get_settings_success
tests/test_cookiecloud_api.py::TestCookieCloudAPI::test_get_settings_not_found
tests/test_cookiecloud_api.py::TestCookieCloudAPI::test_trigger_sync_success
tests/test_cookiecloud_api.py::TestCookieCloudAPI::test_trigger_sync_rate_limited
tests/test_cookiecloud_api.py::TestCookieCloudAPI::test_trigger_sync_not_enabled
tests/test_cookiecloud_api.py::TestCookieCloudAPI::test_trigger_sync_immediate_success
tests/test_cookiecloud_api.py::TestCookieCloudAPI::test_trigger_site_sync_success
tests/test_cookiecloud_api.py::TestCookieCloudAPI::test_test_connection_success
tests/test_cookiecloud_api.py::TestCookieCloudAPI::test_test_connection_no_settings
tests/test_cookiecloud_api.py::TestCookieCloudAPI::test_get_status_success
tests/test_cookiecloud_api.py::TestCookieCloudAPI::test_get_status_no_settings
tests/test_cookiecloud_api.py::TestCookieCloudAPI::test_empty_host_url
tests/test_cookiecloud_integration.py::TestCookieCloudIntegration::test_sync_with_domain_whitelist_filtering
tests/test_inbox_dev_api.py::test_inbox_preview_empty_dir
tests/test_inbox_dev_api.py::test_inbox_preview_with_sample_files
tests/test_inbox_dev_api.py::test_inbox_run_once_basic
tests/test_tts_job_rerun_rate_limit.py::test_job_becomes_partial_when_rate_limited_and_stores_resume_index
tests/test_tts_job_rerun_rate_limit.py::test_job_rerun_uses_resume_index_and_eventually_success
tests/test_tts_jobs_api.py::test_run_next_executes_queued_job
tests/test_tts_jobs_api.py::test_list_jobs_filters_by_status
tests/test_tts_jobs_api.py::test_get_job_returns_job_detail
tests/test_tts_playground_api.py::test_playground_synthesize_basic_dummy_success
tests/test_tts_playground_api.py::test_playground_synthesize_rate_limited
tests/test_tts_playground_api.py::test_playground_synthesize_respects_ebook_profile
tests/test_tts_playground_api.py::test_playground_audio_endpoint_serves_file
tests/test_tts_playground_api.py::test_playground_synthesize_requires_debug_mode
tests/test_tts_storage_service.py::test_scan_storage_collects_files_and_categories
tests/test_tts_storage_service.py::test_execute_cleanup_deletes_files_and_handles_errors
tests/test_tts_user_batch_api.py::test_preview_basic_filter_and_limit
tests/test_tts_user_batch_api.py::test_enqueue_respects_skip_if_has_tts_and_only_without_audiobook
tests/test_tts_user_batch_api.py::test_enqueue_respects_max_new_jobs
tests/test_tts_user_batch_api.py::test_enqueue_skips_when_active_job_exists
tests/test_tts_user_flow_api.py::test_enqueue_tts_job_for_work_basic
tests/test_tts_user_flow_api.py::test_enqueue_tts_job_skips_when_existing_active_job
tests/test_tts_user_flow_api.py::test_enqueue_tts_job_ebook_not_found
tests/test_tts_user_flow_api.py::test_get_tts_status_for_ebook_with_tts_audiobook
tests/test_tts_user_flow_api.py::test_get_tts_status_for_ebook_without_job
tests/test_tts_user_flow_api.py::test_overview_api_basic
tests/test_tts_user_flow_api.py::test_overview_api_status_filter
tests/test_user_notifications_model_and_service.py::test_create_notification_success
tests/test_user_notifications_model_and_service.py::test_create_notification_for_different_statuses
tests/test_user_notifications_model_and_service.py::test_create_notification_without_ebook
tests/test_video_importer.py::test_video_importer_uses_movie_library_root_for_movie
tests/test_video_importer.py::test_video_importer_tv_uses_tv_library_root
tests/test_video_importer.py::test_video_importer_anime_uses_anime_library_root_or_tv
tests/test_video_importer.py::test_video_importer_short_drama_uses_tv_or_short_drama_root
tests/test_video_importer.py::test_video_importer_calls_organizer
tests/filter_rule_group/test_service_basic.py::TestFilterRuleGroupService::test_resolve_groups_for_subscription_success
tests/safety/test_integration.py::TestSafetyPolicyIntegration::test_download_with_active_hr_blocked
tests/safety/test_integration.py::TestSafetyPolicyIntegration::test_delete_with_low_ratio_blocked
tests/safety/test_integration.py::TestSafetyPolicyIntegration::test_move_with_hr_require_copy
tests/safety/test_integration.py::TestSafetyPolicyIntegration::test_safety_engine_performance
tests/safety/test_integration.py::TestSafetyPolicyIntegration::test_safety_notification_integration
tests/safety/test_integration.py::TestSafetyPolicyRegression::test_backward_compatibility
tests/safety/test_integration.py::TestSafetyPolicyRegression::test_error_handling_robustness
tests/safety/test_integration.py::TestSafetyPolicyRegression::test_configuration_validation
tests/safety/test_performance.py::TestSafetyPolicyPerformance::test_single_evaluation_performance
tests/safety/test_performance.py::TestSafetyPolicyPerformance::test_concurrent_evaluation_performance
tests/safety/test_performance.py::TestSafetyPolicyPerformance::test_notification_performance_impact
tests/safety/test_performance.py::TestSystemPerformanceRegression::test_download_service_performance_with_safety
tests/subscription/test_default_config_service.py::TestDefaultSubscriptionConfigService::test_get_default_config_from_database
tests/subscription/test_default_config_service.py::TestDefaultSubscriptionConfigService::test_get_default_config_invalid_media_type
tests/subscription/test_default_config_service.py::TestDefaultSubscriptionConfigService::test_get_default_config_json_string_value
tests/subscription/test_default_config_service.py::TestDefaultSubscriptionConfigService::test_get_default_config_invalid_json
tests/subscription/test_default_config_service.py::TestDefaultSubscriptionConfigService::test_save_default_config_exclude_none
```

---

## 下一步

1. P1: 对失败用例进行分类和隔离需求分析
2. P2: 修复数据库相关测试隔离
3. P3: 修复全局状态污染
4. P4: 外部依赖隔离
5. P5: 测试分层标记
6. P6: Ruff/mypy 收尾
7. P7: 全量验证
