# 首页仪表盘概述

> HOME-1 实现文档

## 概念

首页仪表盘是 VabHub 的统一入口，提供一眼看到所有媒体类型的阅读/收听进度、最近新增内容、后台服务状态和任务汇总。

## 功能特性

### 快速统计
- 小说/电子书数量
- 漫画系列数量
- 音乐作品数量
- 最近7天活动数

### 继续阅读/收听
- 聚合小说、有声书、漫画的进行中项目
- 显示进度百分比
- 点击直接跳转到对应阅读器/播放器

### 最近新增
- 显示最近添加的小说、漫画、音乐
- 按创建时间排序
- 点击跳转到详情页

### Runner 状态
- 显示后台服务（TTS、漫画追更、音乐同步等）状态
- 提示配置命令

### 任务汇总
- 运行中任务数
- 等待中任务数
- 最近失败任务数

## 后端 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/home/dashboard` | 获取首页仪表盘数据 |

### 响应结构

```typescript
interface HomeDashboardResponse {
  stats: HomeQuickStat[]
  up_next: HomeUpNextItem[]
  recent_items: HomeRecentItem[]
  runners: HomeRunnerStatus[]
  tasks: HomeTaskSummary
}
```

## 前端路由

| 路径 | 名称 | 组件 |
|------|------|------|
| `/` | `HomeDashboard` | `HomeDashboard.vue` |

## 文件清单

### 后端
- `backend/app/schemas/home_dashboard.py` - DTO 定义
- `backend/app/services/home_dashboard_service.py` - 聚合服务
- `backend/app/api/home.py` - API 路由

### 前端
- `frontend/src/types/home.ts` - 类型定义
- `frontend/src/pages/HomeDashboard.vue` - 页面组件
- `frontend/src/services/api.ts` - `homeApi`
