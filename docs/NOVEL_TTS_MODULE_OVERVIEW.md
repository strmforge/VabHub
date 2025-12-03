# 小说 / TTS / 有声书模块概览

本文档面向开发者和高级用户，介绍 VabHub 中小说、TTS 有声书生成及播放的整体架构。

## 1. 背景与流程

```
TXT/EPUB 文件 → EBook 模型 → TTS Job → Audiobook 文件 → 用户播放
```

1. **导入**：用户将 TXT/EPUB 文件放入 inbox 目录，或通过 Web 上传
2. **解析**：系统解析文件元数据（标题、作者、章节等），创建 `EBook` 记录
3. **TTS 生成**：用户触发 TTS 任务，后台 Runner 调用 TTS 服务逐章生成音频
4. **有声书**：生成的音频文件关联到 `Audiobook` 模型，用户可在 Web 端播放
5. **进度同步**：阅读进度（`UserReadingProgress`）和听书进度（`UserAudiobookProgress`）分别记录

## 2. 关键模型

### 后端模型（`backend/app/models/`）

| 模型 | 说明 |
|------|------|
| `EBook` | 电子书主表，存储标题、作者、系列、语言等元数据 |
| `EBookFile` | 电子书文件表，一本书可有多个格式（TXT/EPUB/PDF） |
| `Audiobook` | 有声书主表，关联到 EBook |
| `AudiobookFile` | 有声书音频文件表，每章一个文件 |
| `TTSJob` | TTS 任务表，记录任务状态、进度、错误信息 |
| `UserReadingProgress` | 用户阅读进度表 |
| `UserAudiobookProgress` | 用户听书进度表 |

### 前端类型（`frontend/src/types/`）

| 类型文件 | 主要类型 |
|----------|----------|
| `novel.ts` | `NovelCenterItem`, `NovelCenterEBookSummary` |
| `audiobook.ts` | `AudiobookCenterItem`, `UserAudiobookChapter` |
| `tts.ts` | `TTSJob`, `UserWorkTTSStatus`, `TTSStorageOverviewResponse` |

## 3. 关键 API

### 小说中心聚合接口

```
GET /api/novel-center/list
```
- 返回小说列表，包含阅读进度、TTS 状态、听书进度
- 支持分页、关键字搜索、作者/系列筛选

### TTS 任务接口

```
POST /api/tts/user/enqueue/{ebook_id}
```
- 为指定电子书创建 TTS 生成任务

```
GET /api/tts/user/status/{ebook_id}
```
- 获取指定电子书的 TTS 状态（是否有有声书、任务进度等）

### 有声书播放接口

```
GET /api/audiobook/user/work-status/{ebook_id}
```
- 获取指定作品的有声书状态（章节列表、播放进度等）

```
GET /api/audiobook/user/stream/{file_id}
```
- 流式获取音频文件内容

```
POST /api/audiobook/user/progress
```
- 上报播放进度

## 4. Runner（后台任务）

### TTS 生成 Worker

```bash
python -m app.runners.tts_worker
```

- 从任务队列中取出待处理的 TTS Job
- 调用 TTS 服务（如 Edge TTS、Azure TTS）逐章生成音频
- 更新任务状态和进度
- 建议：每 5-10 分钟运行一次，或作为常驻服务

### TTS 存储清理

```bash
python -m app.runners.tts_cleanup
```

- 按策略清理过期的 TTS 缓存文件
- 不会删除已导入的有声书文件
- 建议：每天运行一次（如凌晨 3:00）

## 5. 前端页面映射

| 路由 | 组件 | 说明 |
|------|------|------|
| `/novels` | `NovelCenter.vue` | 小说中心，浏览和管理电子书 |
| `/audiobooks` | `AudiobookCenter.vue` | 有声书中心，浏览和管理有声书 |
| `/tts-center` | `TTSCenter.vue` | TTS 任务中心，查看和管理 TTS 任务 |
| `/works/:ebookId` | `WorkDetail.vue` | 作品详情页，包含 TTS 操作和有声书播放器 |
| `/novels/:ebookId/read` | `NovelReader.vue` | 小说阅读器 |
| `/dev/tts-storage` | `DevTTSStorage.vue` | TTS 存储管理（Dev） |

## 6. 配置项

### TTS 服务配置

在 `backend/app/core/config.py` 或环境变量中配置：

- `TTS_PROVIDER`: TTS 服务提供商（edge/azure/...）
- `TTS_STORAGE_ROOT`: TTS 缓存文件存储路径
- `TTS_RATE_LIMIT`: TTS 请求限流配置

### 存储策略

TTS 存储清理策略可在 `DevTTSStorage.vue` 页面查看，包括：

- Playground 文件保留策略
- Job 文件保留策略
- 其他文件保留策略

## 7. 开发注意事项

1. **类型安全**：前端使用 TypeScript，确保 API 响应类型与后端 Pydantic 模型对齐
2. **进度同步**：播放器每隔一定时间自动上报进度，避免频繁请求
3. **错误处理**：TTS 任务可能因限流或服务异常失败，需在 UI 中友好展示
4. **文件清理**：TTS 缓存文件会占用大量空间，需定期清理

## 8. 相关文档

- `backend/app/api/novel_center.py` - 小说中心 API
- `backend/app/api/tts_user.py` - TTS 用户 API
- `backend/app/api/audiobook_user.py` - 有声书用户 API
- `backend/app/services/tts_service.py` - TTS 服务实现
