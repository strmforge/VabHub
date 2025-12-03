# 任务中心概述

> TASK-1 实现文档

## 概念

任务中心统一展示 VabHub 中的各类后台任务，包括 TTS 生成任务、音乐下载任务等，提供按类型、状态过滤的功能。

## 功能特性

### 任务来源
- **TTS 任务**：来自 `tts_jobs` 表
- **音乐下载任务**：来自 `music_download_jobs` 表
- 未来可扩展：PT 下载任务、订阅刷新任务等

### 过滤功能
- 按媒体类型：小说/有声书/漫画/音乐/影视/其他
- 按任务类型：下载/TTS/导入/订阅/其他
- 按状态：等待中/运行中/成功/失败/跳过

### 任务状态映射

#### TTS 任务
| 原始状态 | 映射状态 |
|----------|----------|
| queued | pending |
| running | running |
| success | success |
| partial | success |
| failed | failed |

#### 音乐下载任务
| 原始状态 | 映射状态 |
|----------|----------|
| pending | pending |
| searching | running |
| found | pending |
| not_found | failed |
| submitted | running |
| downloading | running |
| importing | running |
| completed | success |
| failed | failed |
| skipped_duplicate | skipped |

## 后端 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/task_center/tasks` | 获取任务列表 |

### 查询参数
- `media_type`: 媒体类型过滤
- `kind`: 任务类型过滤
- `status`: 状态过滤
- `page`: 页码
- `page_size`: 每页数量

## 前端路由

| 路径 | 名称 | 组件 |
|------|------|------|
| `/tasks` | `TaskCenter` | `TaskCenterPage.vue` |

## 文件清单

### 后端
- `backend/app/schemas/task_center.py` - DTO 定义
- `backend/app/services/task_center_service.py` - 聚合服务
- `backend/app/api/task_center.py` - API 路由

### 前端
- `frontend/src/types/taskCenter.ts` - 类型定义
- `frontend/src/pages/TaskCenterPage.vue` - 页面组件
- `frontend/src/services/api.ts` - `taskCenterApi`
