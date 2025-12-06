# RSSHUB-MINIMAL-1: CI 环境下 RSSHub 测试跳过逻辑

## 问题描述

在 CI 环境（GitHub Actions）中运行 `test_all.py --skip-music-execute` 时，`test_rsshub_minimal.py` 因为"未能获取到任何 RSSHub 源"而失败：

```
ERROR test_rsshub_minimal 失败: 未能获取到任何 RSSHub 源，请确认后台已同步配置
[FAIL] test_rsshub_minimal.py 失败（退出码 1）
```

**原因**：CI 环境中没有配置任何 RSSHub 源，脚本将"源列表为空"视为错误。

## 解决方案

修改 `backend/scripts/test_rsshub_minimal.py`，在 `VABHUB_CI=1` 环境下，当未检测到任何 RSSHub 源时：

- 输出 WARNING 日志
- 以退出码 0 正常退出（跳过检查）

本地开发环境仍保持严格校验（无源时报错退出码 1）。

## 修改文件

- `backend/scripts/test_rsshub_minimal.py`

## 行为说明

### 本地开发环境

- 若系统中未配置任何 RSSHub 源，脚本会报错并返回退出码 1，提醒开发者先完成 RSSHub 配置。

### CI 环境（`VABHUB_CI=1`）

- 若未配置任何 RSSHub 源，则认为当前环境尚未启用 RSSHub 功能。
- 脚本打印 WARNING 日志并以退出码 0 结束，以避免在早期阶段因为未使用 RSSHub 而阻塞整套回归测试。

## 验证命令

```bash
# CI 模式：无源时应跳过（退出码 0）
cd backend
VABHUB_CI=1 python scripts/test_rsshub_minimal.py

# 开发模式：无源时应报错（退出码 1）
cd backend
python scripts/test_rsshub_minimal.py

# 完整回归测试
cd backend
VABHUB_CI=1 python scripts/test_all.py --skip-music-execute
```

## 关联任务

- BACKEND-REGRESSION-DECISION-2: Decision 最小回归脚本对齐
- BACKEND-REGRESSION-MUSIC-1: 音乐订阅 API 修复
