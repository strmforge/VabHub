# 系统控制台概述

> ADMIN-1 实现文档

## 概念

系统控制台为管理员提供后台服务状态、外部源状态和存储概览的统一视图。

## 功能特性

### Tab 结构

#### Runner & 定时任务
- 显示各后台服务状态
- 提供 systemd 配置命令参考
- 服务列表：
  - TTS 生成服务
  - TTS 清理服务
  - 漫画追更同步
  - 音乐榜单同步
  - 音乐下载服务
  - 音乐状态同步

#### 外部源状态
- 漫画源列表及状态
- 音乐榜单源列表及状态
- 显示最近检查时间

#### 存储概览
- 小说/电子书库统计
- 漫画库统计
- 音乐库统计
- TTS 存储路径

## 后端 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/dashboard` | 获取控制台汇总数据 |
| GET | `/api/admin/runners` | 获取 Runner 状态 |
| GET | `/api/admin/external_sources` | 获取外部源状态 |
| GET | `/api/admin/storage` | 获取存储概览 |

## 前端路由

| 路径 | 名称 | 组件 |
|------|------|------|
| `/admin` | `AdminDashboard` | `AdminDashboard.vue` |

## 配置说明

### systemd timer 示例

```ini
# /etc/systemd/system/vabhub-tts-worker.timer
[Unit]
Description=VabHub TTS Worker Timer

[Timer]
OnCalendar=*:0/5
Persistent=true

[Install]
WantedBy=timers.target
```

## 文件清单

### 后端
- `backend/app/api/admin_status.py` - API 路由

### 前端
- `frontend/src/types/admin.ts` - 类型定义
- `frontend/src/pages/admin/AdminDashboard.vue` - 页面组件
- `frontend/src/services/api.ts` - `adminApi`
