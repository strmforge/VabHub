# Demo 模式概述

> RELEASE-1 R3 实现

## 什么是 Demo 模式？

Demo 模式让用户无需配置 PT 站点、网盘、下载器等外部服务，即可体验 VabHub 的所有核心页面和功能。

适用场景：
- 首次接触 VabHub，想快速了解功能
- 展示/演示用途
- 开发测试（无需真实外部依赖）

## 启用方法

### 1. 设置环境变量

```bash
# .env 文件
APP_DEMO_MODE=true
```

### 2. 运行数据初始化

```bash
# 在后端目录执行
python -m app.runners.demo_seed
```

### 3. 重启服务

```bash
docker compose restart backend
# 或
uvicorn app.main:app --reload
```

## Demo 模式特性

### ✅ 可用功能

| 功能 | 状态 | 说明 |
|------|------|------|
| 首页总览 | ✅ | 显示 Demo 数据统计 |
| 小说中心 | ✅ | 浏览 Demo 小说列表 |
| 漫画中心 | ✅ | 浏览 Demo 漫画 |
| 音乐中心 | ✅ | 浏览 Demo 音乐 |
| 阅读中心 | ✅ | 查看阅读进度 |
| 任务中心 | ✅ | 查看 Demo 任务 |
| 系统控制台 | ✅ | 查看系统状态 |
| 用户设置 | ✅ | 修改个人信息 |

### ⛔ 受限功能

| 功能 | 状态 | 原因 |
|------|------|------|
| 添加下载任务 | ⛔ | 需要真实下载器 |
| PT 站点配置 | ⛔ | 需要账号信息 |
| 网盘配置 | ⛔ | 需要授权凭据 |
| 删除文件 | ⛔ | 防止误操作 |
| TTS 生成 | ⛔ | 需要 TTS 服务 |
| 外部 API 调用 | ⛔ | 防止意外请求 |

## Demo 数据

初始化后包含以下示例数据：

### 用户
- **admin** / admin123 - 管理员账号
- **demo** / demo123 - 普通用户账号

### 内容
- 3 本电子书（三体、遮天、斗破苍穹）
- 3 个漫画系列（海贼王、鬼灭之刃、咒术回战）
- 4 首音乐（周杰伦经典歌曲）
- 4 个任务记录（各种状态示例）

## 前端提示

Demo 模式下，首页顶部会显示醒目的黄色横幅：

```
⚠️ 当前为 Demo 模式：所有下载/外部操作均为模拟，数据仅供体验
```

受限操作的按钮点击后会显示 Toast 提示：
```
Demo 模式下不可用
```

## 技术实现

### 后端

1. **配置项**: `APP_DEMO_MODE` (bool)
2. **版本 API**: `/api/version` 返回 `demo_mode: true`
3. **守卫装饰器**: `@demo_guard("操作名称")`
4. **辅助函数**: `check_demo_mode()`, `is_demo_mode()`

### 前端

1. **状态存储**: `appStore.isDemoMode`
2. **版本获取**: `appApi.getVersion()`
3. **Banner 组件**: `HomeDashboard.vue` 中的 `v-banner`

## 关闭 Demo 模式

```bash
# .env 文件
APP_DEMO_MODE=false
```

重启服务后，Demo 模式关闭，所有功能恢复正常。

## 相关文件

- `backend/app/core/config.py` - Demo 模式配置
- `backend/app/core/demo_guard.py` - 安全守卫
- `backend/app/runners/demo_seed.py` - 数据初始化
- `backend/app/api/version.py` - 版本 API
- `frontend/src/stores/app.ts` - 前端状态
- `frontend/src/pages/HomeDashboard.vue` - Demo Banner
