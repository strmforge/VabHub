# 音乐模块概览 (MusicCenter v1)

本文档介绍 VabHub 音乐库模块的整体架构和使用方式。

## 1. 功能概述

MusicCenter v1 提供以下核心功能：

- **本地音乐库浏览**：按专辑、艺术家、曲目浏览本地音乐文件
- **音乐文件导入**：从指定目录扫描并导入音乐文件
- **Web 播放器**：在浏览器中播放本地音乐
- **音乐订阅**：订阅艺术家/专辑，自动下载新发布的音乐
- **音乐榜单**：获取各平台音乐榜单（QQ音乐、网易云等）

## 2. 数据模型

### 后端模型（`backend/app/models/music.py`）

| 模型 | 说明 |
|------|------|
| `Music` | 音乐作品/专辑主表，存储标题、艺术家、专辑等元数据 |
| `MusicFile` | 音乐文件表，存储文件路径、格式、时长、比特率等 |
| `MusicTrack` | 音乐曲目表（用于在线平台曲目） |
| `MusicSubscription` | 音乐订阅表 |
| `MusicPlaylist` | 播放列表表 |
| `MusicChartRecord` | 榜单记录表 |

### 前端类型（`frontend/src/types/music.ts`）

| 类型 | 说明 |
|------|------|
| `MusicAlbum` | 专辑信息 |
| `MusicArtist` | 艺术家信息 |
| `MusicTrack` | 曲目信息 |
| `MusicFile` | 文件信息 |
| `MusicAlbumDetail` | 专辑详情（含曲目列表） |
| `MusicStats` | 音乐库统计 |

## 3. API 接口

### 本地音乐库 API

```
GET /api/music/library/albums
```
- 获取专辑列表，支持关键字搜索和分页

```
GET /api/music/library/albums/{album_id}
```
- 获取专辑详情，包含曲目列表

```
GET /api/music/library/artists
```
- 获取艺术家列表

```
GET /api/music/library/tracks
```
- 获取曲目列表

```
GET /api/music/library/stats
```
- 获取音乐库统计

```
GET /api/music/library/stream/{file_id}
```
- 流式播放音乐文件

### 其他 API

- `POST /api/music/search` - 搜索音乐
- `GET /api/music/charts` - 获取音乐榜单
- `POST /api/music/subscriptions` - 创建音乐订阅
- `POST /api/music/library/scan` - 扫描音乐库

## 4. 音乐导入 Runner

### 使用方式

```bash
# 预览模式（不实际写入）
python -m app.runners.music_import --root /path/to/music --dry-run

# 实际导入
python -m app.runners.music_import --root /path/to/music
```

### 支持的格式

- MP3, FLAC, M4A, AAC, OGG, WAV, APE, WMA

### 元数据解析

导入器会尝试使用 `mutagen` 库解析音频文件的 ID3/Vorbis 标签。如果无法解析，会从文件名中提取艺术家和标题：

- `艺术家 - 歌曲名.mp3` → 艺术家: "艺术家", 标题: "歌曲名"
- `歌曲名.mp3` → 艺术家: "Unknown", 标题: "歌曲名"

## 5. 前端页面

### MusicCenter.vue

路由：`/music`

功能：
- 统计卡片：显示艺术家数、专辑数、曲目数、总大小
- 标签页切换：专辑 / 艺术家 / 曲目
- 专辑网格：点击打开专辑详情对话框
- 迷你播放器：底部固定，显示当前播放曲目

## 6. 配置项

### 依赖

后端需要安装 `mutagen` 库以解析音频元数据：

```bash
pip install mutagen
```

## 7. 开发注意事项

1. **文件路径**：`MusicFile.file_path` 存储绝对路径，确保服务器可访问
2. **流式播放**：使用 `FileResponse` 返回音频文件，支持 Range 请求
3. **元数据解析**：优先使用 ID3 标签，回退到文件名解析
4. **分页**：所有列表 API 支持分页，默认每页 20 条

## 8. 后续计划

- [ ] 播放列表管理
- [ ] 播放历史记录
- [ ] 歌词显示
- [ ] 封面图片管理
- [ ] 全局音乐播放器（跨页面）
