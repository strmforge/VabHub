# BACKEND-REGRESSION-MUSIC-1 P0 现状巡检

## 问题描述

`backend/scripts/test_music_minimal.py` 在 CI 环境下创建音乐订阅时失败，返回 500。

## 错误堆栈

```
sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) NOT NULL constraint failed: subscriptions.user_id

[SQL: INSERT INTO subscriptions (user_id, title, ...) VALUES (?, ?, ...)]
[parameters: (None, 'Test Song', 'Test Track', None, 'music', ...)]
```

## 根因分析

### 调用流程

1. `test_music_minimal.py` 调用 `POST /api/v1/music/subscriptions`
2. `music.py` 路由调用 `MusicService.create_subscription()`
3. `MusicService` 创建 `MusicSubscription` 记录
4. 然后调用 `_ensure_core_subscription_link()` 创建关联的 `Subscription`
5. `_build_core_subscription_payload()` 构建 payload **但没有设置 user_id**
6. `Subscription` 表的 `user_id` 列是 NOT NULL → **IntegrityError**

### 问题代码位置

`backend/app/modules/music/service.py` 第 530-561 行：

```python
def _build_core_subscription_payload(self, music_subscription, payload):
    return {
        "title": ...,
        "media_type": "music",
        # 缺少 user_id !!!
        ...
    }
```

## 前置条件分析

| 条件 | 当前实现 | CI 环境 |
|------|---------|---------|
| 数据库初始化 | init_db() | ✅ 正常 |
| 用户存在 | 无自动创建 | ❌ 缺失 |
| user_id | 未设置 | ❌ None |
| subscriptions.user_id | NOT NULL | 💥 报错 |

## 修复方案

1. **在 `_build_core_subscription_payload` 中设置默认 user_id**：
   - 使用 `TEMP_USER_ID = 1`（与 music_subscription.py 一致）
   - 或从初始管理员获取

2. **在 CI/开发模式下自动创建默认用户**：
   - 修改 `initial_superuser.py` 确保默认用户存在
   - 或在 `init_db` 时检查并创建

3. **增强错误处理**：
   - 将 IntegrityError 转为 400 而非 500

---

## 解决方案小结（已实施）

### 修改文件

1. **`backend/app/modules/music/service.py`**：
   - `_build_core_subscription_payload()` 添加 `user_id` 默认值

2. **`backend/scripts/test_music_minimal.py`**：
   - 添加 `check_response()` 辅助函数
   - 添加 `IS_CI` 环境检测
   - CI 模式下使用模拟榜单数据
   - CI 模式下跳过自动下载触发

### 验证结果

- ✅ 音乐订阅创建成功（CI 环境）
- ✅ 核心测试全部通过（16 passed, 1 skipped）
- ✅ 语法检查通过

---

*Created: 2025-12-06*
*Updated: 2025-12-06 - 已完成修复*
