# BACKEND-REGRESSION-DECISION-1

## 问题描述

`test_decision_minimal.py` 在 CI 环境下失败：
```
ModuleNotFoundError: No module named 'scripts'
```

## 根因

脚本使用了错误的导入路径：
```python
from scripts.api_test_config import API_BASE_URL, api_url
```

但 `backend/scripts/` 不是一个 Python 包（没有 `__init__.py`），且 CI 环境没有将其加入 `PYTHONPATH`。

## 解决方案

统一所有测试脚本的导入模式：

```python
import sys
from pathlib import Path

# 确保 scripts 目录在 sys.path（支持 CI 环境）
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from api_test_config import API_BASE_URL, api_url  # 同目录导入
```

## 修改文件

| 文件 | 变更 |
|------|------|
| `test_decision_minimal.py` | 修复导入路径 |
| `test_music_minimal.py` | 修复导入路径 |
| `test_graphql_minimal.py` | 使用统一配置 |
| `quick_test.py` | 修复导入路径 |
| `test_functional.py` | 修复导入路径 |
| `test_rsshub_minimal.py` | 修复导入路径 |
| `test_api_endpoints.py` | 修复导入路径 |
| `test_backend_basic.py` | 修复导入路径 |
| `test_integration.py` | 修复导入路径 |
| `test_new_features.py` | 修复导入路径 |
| `test_performance.py` | 修复导入路径 |
| `test_register.py` | 修复导入路径 |
| `test_short_drama_minimal.py` | 修复导入路径 |
| `verify_api_routes.py` | 修复导入路径 |

## 验证方法

```bash
# 本地验证
python backend/scripts/test_decision_minimal.py
python backend/scripts/test_all.py --skip-music-execute

# CI 验证
# 推送后运行 Backend Regression workflow
```

## 影响范围

| 环境 | 影响 |
|------|------|
| CI (Backend Regression) | ✅ 修复：脚本可正常导入 |
| 本地开发 | ✅ 无破坏性变更 |
| 生产环境 | ✅ 无影响 |

---

*Created: 2025-12-06*
