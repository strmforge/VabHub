# BACKEND-CI-1 初始报告

## 执行环境
- 时间：2025-12-04 09:28:37
- 命令：`python -m pytest tests/ -v --tb=short --maxfail=10`
- 环境：Windows + Python 3.11 + SQLite（开发模式）

## 测试结果概览
- **总状态**: 严重失败
- **错误数**: 10+ errors (在maxfail=10限制下)
- **警告数**: 84 warnings (主要是Pydantic V2迁移警告)
- **主要阻塞**: SQLAlchemy CompileError

## 关键错误类型分析

### 1. SQLAlchemy CompileError (致命阻塞)
**典型错误**: `sqlalchemy.exc.CompileError: (in table 'upload_tasks', column 'id'): Compiler <sqlalchemy.dia...`

**影响测试文件**:
- `tests/test_admin_library_settings_api.py` (6个测试)
- `tests/test_admin_tts_settings_api.py` (4个测试)
- 预计影响更多文件...

**根本原因**: 
- `upload_tasks` 表的 `id` 列定义存在编译错误
- 可能是模型定义与数据库迁移不匹配
- 需要检查 `app/models` 中的相关模型定义

### 2. Pydantic V2 迁移警告 (非阻塞但需修复)
**典型警告**: `PydanticDeprecatedSince20: Pydantic V1 style @validator validators are deprecated`

**影响文件**:
- `app/schemas/site_manager.py:172`
- `app/schemas/cookiecloud.py` (多处)
- `app/api/graphql/router.py:18`
- `app/api/rsshub.py:178`

**修复建议**: 迁移到 Pydantic V2 的 `@field_validator` 语法

## 红灯分组表

| 错误类型 | 典型报错信息 | 涉及的测试文件 | 优先级 |
|---------|-------------|---------------|--------|
| SQLAlchemy CompileError | `(in table 'upload_tasks', column 'id')` | test_admin_library_settings_api.py, test_admin_tts_settings_api.py | P1 (致命) |
| Pydantic V1 Validator | `@validator` deprecated | site_manager.py, cookiecloud.py | P7 (收尾) |
| GraphQL Deprecation | `graphiql` argument deprecated | graphql/router.py | P7 (收尾) |
| FastAPI Regex | `regex` deprecated, use `pattern` | rsshub.py | P7 (收尾) |

## 预计影响范围
基于错误模式，预计以下模块会受到影响：
1. **Admin API** (library settings, TTS settings)
2. **Upload/Task 系统** (upload_tasks 表相关)
3. **Schema 定义** (Pydantic 迁移)
4. **RSSHub 系统** (regex 参数)
5. **GraphQL 系统** (graphiql 参数)

## 下一步行动
1. **P1**: 修复 upload_tasks 表的 SQLAlchemy 编译错误
2. **P2**: 检查数据库迁移与模型定义的一致性
3. **P3**: 逐步修复 Pydantic V2 迁移问题
4. **P4**: 处理其他 deprecation 警告

## 技术债务
- 大量 Pydantic V1 语法需要迁移到 V2
- FastAPI 参数需要更新 (regex -> pattern)
- GraphQL 配置需要更新

---
*报告生成时间: 2025-12-04 09:30*
*任务: BACKEND-CI-1 P0 阶段*
