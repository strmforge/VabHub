# VabHub 小说 & 有声书子系统总览

## 1. 引言：这份文档讲什么？

本文档面向 NAS / PT 玩家，介绍 VabHub 小说 & 有声书子系统的整体架构、使用流程和接入方式。

### 核心要点

**核心流程：**
```
TXT/EPUB → EBook →（可选）TTS 有声书 → 小说中心 / 有声书中心 / 阅读器 / 我的书架
```

**关键设计理念：**
- **目录名完全由用户配置**：Inbox（待整理目录）和媒体库目录都通过 Settings 配置，项目不写死路径。
- **TTS 不是必须的**：不配置 TTS 也可以完整使用"小说管理 + 在线阅读"功能。
- **与下载器解耦**：项目不关心你用哪个下载器，只关心完成后的文件落到哪里。

---

## 2. 核心概念与角色

### 2.1 Inbox / 待整理目录

**概念：** 一个或多个"下载/乱放的文件集中堆放点"，通过 Docker 映射与 Settings 配置。

**特点：**
- 不要求叫特定名字；只是一个角色。
- 可以混放电影、剧集、TXT、EPUB、有声书音频等。
- 通过环境变量 `INBOX_ROOT` 配置（默认：`./data/inbox`）。

**典型用法：**
- PT 下载器完成后自动移动到某个目录（用户配置）。
- 用户手动拷贝 TXT / EPUB 到 Inbox。

### 2.2 媒体库目录（小说库 / 电影库等）

**概念：** 用于存放整理后的 EBook / 有声书 / 视频。

**特点：**
- 同样通过配置/映射决定，不写死路径。
- 整理后的文件会按规则归档到媒体库。

### 2.3 EBook

**概念：** 统一表示一部小说/作品的实体（不管源头是 TXT 还是 EPUB）。

**特点：**
- 从 Inbox 中的 TXT/EPUB 文件导入生成。
- 包含作品元数据（标题、作者、系列、语言等）。
- 可以关联多个有声书文件（TTS 生成或原生导入）。

### 2.4 有声书

**概念：** 对应某作品的音频版本。

**来源：**
- **TTS 生成**：通过 TTS Job 队列生成。
- **原生有声书**：将来可接入/导入的原生有声书文件。

### 2.5 阅读进度 & 听书进度

**UserNovelReadingProgress：**
- 记录当前用户看到哪一章（`current_chapter_index`）。
- 记录章节内位置（`position_in_chapter`）。
- 标记是否已完成（`is_finished`）。

**UserAudiobookProgress：**
- 记录听到哪一章（`current_file_id`）。
- 记录播放位置（`position_seconds`）。
- 标记是否已完成（`is_finished`）。

---

## 3. 整体流程总览

### 3.1 完整链路（文字说明）

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 文件进入 Inbox                                                │
│    - 来源 1：PT 下载器完成后自动移动到某个目录（用户配置）      │
│    - 来源 2：用户手动拷贝 TXT / EPUB 到 Inbox                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. Inbox 扫描 / Organizer                                        │
│    - 通过 Runner 或 Dev API 触发扫描                            │
│    - InboxRouter 识别媒体类型：                                  │
│      • 视频 → 电影/剧集整理                                      │
│      • .txt / .epub → NovelInbox → NovelToEbookPipeline        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. NovelInbox 导入                                              │
│    - NovelInboxImportLog 记录每个文件导入状态（成功/跳过/失败）  │
│    - 避免重复导入同一文件                                        │
│    - 可选：导入成功后自动创建 TTS Job                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. TTS 流水线（可选）                                            │
│    - TTSJob 放入队列                                             │
│    - Runner CLI 周期运行：                                       │
│      python -m app.cli.run_tts_jobs                             │
│    - 调用 Dummy / HTTP TTS 引擎生成有声书音频                   │
│    - TTS 存储清理 Runner：                                       │
│      python -m app.cli.run_tts_storage_cleanup                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. 前端使用                                                      │
│    - 小说中心：全局小说视角（EBook + TTS + 阅读/听书进度）      │
│    - 有声书中心：以有声书/听书为主视角                          │
│    - 小说 Inbox 日志：导入日志 & 手动扫描入口                   │
│    - 小说阅读器：按章节阅读正文，自动记阅读进度                 │
│    - WorkDetail 播放器：听有声书，记听书进度                    │
│    - 我的书架：聚合当前用户正在读/正在听/已完成作品             │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 用户自己负责的部分

**明确标注：**
- ✅ **下载器配置** → 把文件丢进 Inbox 根目录。
- ✅ **如选择接入 TTS 引擎**：自行搭建 HTTP 服务或配置云厂商。

---

## 4. 「从 PT / 下载器 到 小说中心」详细说明

### 4.1 核心原则

**项目不关心你用谁下载，只关心完成后的文件落到哪里。**

### 4.2 典型配置示例

**逻辑示例（用文字描述）：**

1. **下载器配置：**
   - 下载器把所有完成任务移动到 `/downloads/complete`（宿主机路径）。

2. **Docker 映射：**
   - Docker 把 `/downloads/complete` 映射成容器内 `/inbox`。

3. **Settings 配置：**
   - 环境变量 `INBOX_ROOT=/inbox`（容器内路径）。

4. **扫描触发：**
   - Inbox Runner / Dev API 定期/手动扫描 Inbox，并整理所有媒体。

### 4.3 重要说明

**Inbox 可以混放多种媒体：**
- Inbox 里可以混放电影、剧集、TXT、EPUB、有声书音频。
- `InboxRouter` 会根据扩展名/类型路由到不同处理逻辑。
- `NovelInbox` 只处理符合条件的 TXT/EPUB。
- 小说 Inbox 管理页面可以看到每个 TXT 的导入日志，便于排错。

### 4.4 典型做法对比

| 模式 | 描述 | 适用场景 |
|------|------|----------|
| **自动模式** | PT 下载器设置完成目录 → 指向 Inbox → 定时 Runner | 完全自动化，适合长期运行 |
| **半自动模式** | 下载器完成后"移动/软链接"到 Inbox → 通过 Web 点击「扫描一次」 | 需要手动触发扫描，但文件自动移动 |
| **纯手动模式** | 用户自己拷贝 TXT/EPUB 到 Inbox → 手动扫描 | 完全手动控制，适合测试或少量文件 |

---

## 5. 「TTS 不是必需品」& TTS 接入概览

### 5.1 不配置 TTS 的完整使用

**不配置 TTS，系统依然完整可用：**
- ✅ TXT/EPUB 仍然会被导入为 EBook。
- ✅ 小说中心 / 有声书中心 / 阅读器 / 我的书架全部可以使用。
- ❌ 只是没有 TTS 生成的有声书（除非你手动导入音频）。

### 5.2 TTS 接入路线

#### 5.2.1 启用 Dummy 引擎

**用途：** 只用于测试流水线。

**特点：**
- 所有 TTS Job 都生成短静音音频。
- 不调用外部服务，不产生费用。
- 配置：`SMART_TTS_PROVIDER=dummy`（默认）。

#### 5.2.2 使用 HttpTTSEngine 接自己搭建的开源 TTS 服务

**示例：** Piper / Coqui / 其他本地 TTS。

**优点：**
- 完全本地、不依赖厂商、真正"免费 + 可控"。

**配置：**
- `SMART_TTS_PROVIDER=http`
- `SMART_TTS_HTTP_BASE_URL=<你的 TTS 服务地址>`
- `SMART_TTS_HTTP_METHOD=POST`
- `SMART_TTS_HTTP_BODY_TEMPLATE=<请求体模板>`
- 其他相关配置（详见 `SMART_TTS_HTTP_*` 环境变量）。

#### 5.2.3 使用 HttpTTSEngine 接云厂商 TTS

**示例：** 阿里云、腾讯云、Azure 等。

**特点：**
- 完全由用户自己配置 Key 和 Endpoint。
- 项目本身不绑定任何服务商、也不提供 Key。

**配置：**
- 同上，但需要配置云厂商的 API Key 和 Endpoint。

### 5.3 TTS 配置文档

**关于具体环境变量和请求模板：**

项目中已存在 `docs/SMART_TTS_RUNNER_GUIDE.md`，该文档详细说明了 TTS Runner 的使用方法。

**TTS 引擎配置的详细说明：**
- 请参考代码中的 `SMART_TTS_HTTP_*` 环境变量（位于 `app/core/config.py`）。
- 未来版本可能会提供单独的 TTS 接入配置文档，此处只做能力说明。

---

## 6. 前端页面导览：一口气看完小说相关页面

### 6.1 小说中心（`/novels`）

**API：** `GET /api/novels/center/list`

**能看到：**
- 全部 EBook。
- 每本书的 TTS 状态（有无有声书、TTS Job 状态）。
- 听书进度 & 阅读进度。

**可以：**
- 筛选、搜索。
- 一键生成 TTS。
- 跳转到 WorkDetail / NovelReader。

**截图位置：** 此处可插入截图

### 6.2 有声书中心（`/audiobooks`）

**API：** `GET /api/audiobooks/center/list`

**特点：**
- 以"有音频"的作品为主视角。
- 着重强调听书进度 + TTS Job 状态。
- 也展示阅读进度，并可直接跳转阅读。

**截图位置：** 此处可插入截图

### 6.3 小说 Inbox 管理（`/dev/novels/inbox`）

**API：** `GET /api/dev/novels/inbox/*`

**功能：**
- 展示 `NovelInboxImportLog`。
- 能按状态/路径筛选。
- 能手动触发一次 Inbox 扫描（可选是否自动建 TTS Job）。

**截图位置：** 此处可插入截图

### 6.4 阅读器（`/novels/:ebookId/read`）

**API：** `GET /api/novels/reader/*`

**功能：**
- 左侧章节列表，右侧正文。
- 自动记阅读进度。
- 上一章 / 下一章。

**跳转入口：**
- 小说中心。
- 有声书中心。
- WorkDetail。
- 我的书架。

**截图位置：** 此处可插入截图

### 6.5 作品详情 & 有声书播放器（`/works/:ebookId`）

**API：** `GET /api/works/:ebookId`

**功能：**
- 展示作品信息。
- 有声书播放器：
  - 章节列表。
  - 播放/暂停。
  - 听书进度记忆 / 自动下一章。

**截图位置：** 此处可插入截图

### 6.6 我的书架（`/my/shelf`）

**API：** `GET /api/user/my-shelf`

**特点：**
- 聚合"当前用户有读/有听过的作品"。
- 卡片式展示：
  - 阅读/听书双进度。
  - 最近活动时间。
  - 一键继续阅读/收听。
  - 一键生成 TTS（若无有声书）。

**截图位置：** 此处可插入截图

---

## 7. CLI / Runner 概览（只做入口，不讲实现细节）

### 7.1 小说 Inbox 扫描

**命令：**
```bash
python -m app.cli.run_novel_inbox_scan [--max-files=N] [--generate-tts]
```

**参数：**
- `--max-files N`：最多处理的文件数量（None 表示不限制）。
- `--generate-tts`：是否自动创建 TTS Job。

**示例：**
```bash
# 扫描所有文件，不创建 TTS Job
python -m app.cli.run_novel_inbox_scan

# 最多处理 20 个文件
python -m app.cli.run_novel_inbox_scan --max-files=20

# 最多处理 20 个文件，并自动创建 TTS Job
python -m app.cli.run_novel_inbox_scan --max-files=20 --generate-tts
```

### 7.2 TTS Job Runner

**命令：**
```bash
python -m app.cli.run_tts_jobs [--max-jobs=N] [--no-stop-when-empty]
```

**参数：**
- `--max-jobs N`：单次执行最多处理的 Job 数量（默认：从配置 `SMART_TTS_JOB_RUNNER_MAX_JOBS_PER_RUN` 读取，通常为 5）。
- `--no-stop-when-empty`：当没有 queued Job 时不立即退出（默认：无任务时立即退出）。

**示例：**
```bash
# 处理最多 5 个 Job
python -m app.cli.run_tts_jobs --max-jobs=5

# 处理最多 10 个 Job，无任务时继续轮询
python -m app.cli.run_tts_jobs --max-jobs=10 --no-stop-when-empty
```

### 7.3 TTS 存储清理 Runner

**命令：**
```bash
python -m app.cli.run_tts_storage_cleanup --mode=auto|manual [--dry-run]
```

**参数：**
- `--mode auto|manual`：运行模式。
  - `auto`：遵循配置的策略（间隔、警告级别检查）。
  - `manual`：强制执行，忽略间隔和警告级别检查。
- `--dry-run`：是否只预览不实际删除。

**示例：**
```bash
# 预览模式（不实际删除）
python -m app.cli.run_tts_storage_cleanup --mode=auto --dry-run

# 自动模式（实际删除）
python -m app.cli.run_tts_storage_cleanup --mode=auto

# 手动模式（强制执行）
python -m app.cli.run_tts_storage_cleanup --mode=manual
```

### 7.4 详细文档链接

**关于 Runner 的详细使用说明：**

项目中已存在 `docs/SMART_TTS_RUNNER_GUIDE.md`，该文档详细说明了 TTS Runner 和存储清理 Runner 的使用方法、配置选项和输出示例。

---

## 8. 总结

### 8.1 核心流程回顾

1. **文件进入 Inbox** → 通过下载器或手动拷贝。
2. **Inbox 扫描** → 识别 TXT/EPUB，导入为 EBook。
3. **TTS 生成（可选）** → 通过 TTS Job 队列生成有声书。
4. **前端使用** → 小说中心、有声书中心、阅读器、我的书架。

### 8.2 关键配置

- **Inbox 根目录：** `INBOX_ROOT` 环境变量（默认：`./data/inbox`）。
- **TTS 引擎：** `SMART_TTS_PROVIDER` 环境变量（`dummy` / `http`）。
- **TTS HTTP 配置：** `SMART_TTS_HTTP_*` 系列环境变量。

### 8.3 相关文档

- **TTS Runner 使用指南：** `docs/SMART_TTS_RUNNER_GUIDE.md`
- **API 文档：** 访问 `/docs`（Swagger UI）查看完整 API 文档。

---

**文档版本：** v1.0  
**最后更新：** 2025-01-XX

