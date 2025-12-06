# BACKEND-REGRESSION-DECISION-1 P0 现状巡检

## 问题描述

`test_decision_minimal.py` 在 CI 环境下失败：
```
ModuleNotFoundError: No module named 'scripts'
```

## 现状发现

### 脚本导入方式对比

| 脚本 | 导入方式 | 状态 |
|------|----------|------|
| `test_decision_minimal.py` | `from scripts.api_test_config import ...` | ❌ 错误 |
| `test_music_minimal.py` | `from scripts.api_test_config import ...` | ❌ 错误 |
| `test_graphql_minimal.py` | 内联定义 `API_BASE_URL` | ⚠️ 不统一 |
| `api_test_config.py` | 公共配置模块 | ✅ 正确 |

### 目录结构确认

```
backend/
├── scripts/
│   ├── api_test_config.py      # 公共配置
│   ├── test_decision_minimal.py
│   ├── test_music_minimal.py
│   ├── test_graphql_minimal.py
│   ├── test_all.py
│   └── ...
└── ...
```

**关键发现**：
- `backend/scripts/` 目录下**没有** `scripts/` 子目录
- 项目根目录也**没有**顶层 `scripts` 包
- 因此 `from scripts.api_test_config` 在 CI 环境下无法解析

### 根因分析

1. 脚本使用 `from scripts.api_test_config` 假设存在 `scripts` 包
2. 但实际项目结构中 `scripts` 不是一个 Python 包（无 `__init__.py`）
3. CI 环境没有将 `backend/scripts` 加入 `PYTHONPATH`
4. 本地偶尔能跑是因为 IDE 自动添加了路径

## 修复方案

统一所有脚本使用以下模式：

```python
import sys
from pathlib import Path

# 确保 scripts 目录在 sys.path
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from api_test_config import API_BASE_URL, api_url  # 同目录导入
```

---

## 解决方案小结（已实施）

### 修改文件

共修复 14 个测试脚本：
- `test_decision_minimal.py`
- `test_music_minimal.py`
- `test_graphql_minimal.py`
- `quick_test.py`
- `test_functional.py`
- `test_rsshub_minimal.py`
- `test_api_endpoints.py`
- `test_backend_basic.py`
- `test_integration.py`
- `test_new_features.py`
- `test_performance.py`
- `test_register.py`
- `test_short_drama_minimal.py`
- `verify_api_routes.py`

### 验证结果

- ✅ 所有脚本语法检查通过
- ✅ 导入测试成功
- ✅ 无 `ModuleNotFoundError`

---

*Created: 2025-12-06*
*Updated: 2025-12-06 - 已完成修复*
