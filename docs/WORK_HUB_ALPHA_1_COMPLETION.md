# WORK-HUB-ALPHA-1 完成文档

## 概述

将当前的 `/works/:ebookId` ebook 中心页升级为真正的"作品中心（Work Hub）"，提供统一的作品详情聚合接口，支持电子书、有声书、漫画等多种形态。

## 实现内容

### 一、后端 WorkDetail 聚合 API

**文件**: `app/api/work.py`

#### API 端点

- **路径**: `GET /api/works/{ebook_id}`
- **描述**: 获取作品详情（聚合电子书、有声书、漫画）
- **参数**: `ebook_id` (int) - 电子书作品 ID（作为 work_id）

#### 响应结构 (`WorkDetailResponse`)

```json
{
  "ebook": {
    "id": 1,
    "title": "作品标题",
    "original_title": "原始标题",
    "author": "作者",
    "series": "系列名",
    "volume_index": "1",
    "language": "zh-CN",
    "publish_year": 2023,
    "isbn": "978-xxx",
    "tags": "标签",
    "description": "简介",
    "cover_url": "封面URL",
    "extra_metadata": {},
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00"
  },
  "ebook_files": [
    {
      "id": 1,
      "file_path": "/path/to/file.epub",
      "format": "epub",
      "file_size_mb": 5.0,
      "source_site_id": "site1",
      "source_torrent_id": "torrent1",
      "download_task_id": 123,
      "created_at": "2023-01-01T00:00:00"
    }
  ],
  "audiobooks": [
    {
      "id": 1,
      "title": "作品标题",
      "format": "mp3",
      "duration_seconds": 3600,
      "bitrate_kbps": 128,
      "sample_rate_hz": 44100,
      "channels": 2,
      "narrator": "朗读者",
      "language": "zh-CN",
      "file_size_mb": 50.0,
      "source_site_id": "site1",
      "download_task_id": 124,
      "created_at": "2023-01-01T00:00:00"
    }
  ],
  "comics": [
    {
      "id": 1,
      "title": "漫画标题",
      "series": "系列名",
      "volume_index": 1,
      "author": "作者",
      "illustrator": "作画",
      "language": "zh-CN",
      "region": "CN",
      "publish_year": 2023,
      "cover_url": "封面URL",
      "tags": "标签"
    }
  ],
  "comic_files": [
    {
      "id": 1,
      "comic_id": 1,
      "file_path": "/path/to/comic.cbz",
      "file_size_mb": 10.0,
      "format": "cbz",
      "page_count": 100,
      "source_site_id": "site1",
      "source_torrent_id": "torrent1",
      "download_task_id": 125,
      "created_at": "2023-01-01T00:00:00"
    }
  ]
}
```

#### 聚合查询逻辑

1. **查询 EBook + EBookFile 列表**:
   - 如果 EBook 不存在，返回 404
   - 查询所有未删除的 EBookFile，按创建时间降序

2. **查询关联的 Audiobook**:
   - 使用 `AudiobookFile.ebook_id == ebook_id` 查询
   - 扁平化为 `WorkAudiobookFile` 列表
   - 每个有声书文件包含 EBook 的标题信息

3. **查询"相关漫画"**（启发式匹配）:
   - **匹配规则**:
     - 如果 `ebook.series` 不为空：优先匹配 `Comic.series ilike ebook.series`
     - 否则：匹配 `Comic.title ilike ebook.title`
   - 限制最多 50 条
   - 同时查询对应的 `ComicFile`（通过 `comic_id` 批量查询）
   - **注意**: 这是启发式匹配，会有误差，属于"软关联"

### 二、前端 WorkDetail.vue 升级

**文件**: `src/pages/WorkDetail.vue`

#### 主要改动

1. **API 调用**:
   - 从分别调用 `ebookApi.getEbook()` 和 `audiobookApi.getAudiobooksByEbook()` 
   - 改为只调用 `workApi.getWorkDetail(ebookId)`

2. **数据展示区块**:
   - **顶部**: 作品信息卡片（基于 `work.ebook`）
     - 标题 / 系列 / 卷号 / 作者 / 语言 / 出版年 / ISBN / 简介 / tags
   - **区块 1**: 电子书文件（`ebook_files`）
     - 列表展示：格式 / 大小 / 来源站点 / 路径 / 创建时间
   - **区块 2**: 有声书（`audiobooks`）
     - 列表展示：标题 / 时长 / 音质 / 朗读者 / 来源站点
   - **区块 3**: 相关漫画（`comics + comic_files`）
     - 按卷聚合：每卷显示 title / series / 卷号 / 地区 / 文件数
     - 展开可看到 ComicFile 列表（格式 / 大小 / 来源站点）
     - **提示文案**: "相关漫画基于系列名 / 标题自动匹配，可能包含误差。"

#### 类型定义

**文件**: `src/types/work.ts`

定义了完整的 TypeScript 接口，对应后端的 Pydantic Schema。

#### API 封装

**文件**: `src/services/api.ts`

新增 `workApi.getWorkDetail(ebookId)` 方法。

## 测试

### 测试文件

**`tests/test_work_detail_api.py`**: 5 个测试用例

1. `test_work_detail_basic_ebook_only`: 只有 ebook 和 ebook_files，没有 audiobook/comic
2. `test_work_detail_with_audiobooks`: 有 audiobook 关联，验证 audiobooks 数组
3. `test_work_detail_with_comics_by_series_match`: 通过 series 匹配漫画
4. `test_work_detail_with_comics_by_title_match`: 通过 title 匹配漫画
5. `test_work_detail_not_found`: ebook_id 不存在时返回 404

**测试状态**: ✅ 全部通过

## 漫画关联规则

### 匹配逻辑

漫画是通过 **启发式匹配** 关联到作品的，属于"软关联"：

1. **优先匹配 series**:
   - 如果 EBook 有 `series` 字段，优先匹配 `Comic.series ilike ebook.series`
   - 使用 `ilike`（不区分大小写）进行模糊匹配

2. **回退到 title 匹配**:
   - 如果没有 `series` 或 series 匹配失败，使用 `Comic.title ilike ebook.title`

3. **限制数量**:
   - 最多返回 50 条匹配的漫画

4. **注意事项**:
   - 匹配结果可能有误差（例如同名不同作品）
   - UI 上会显示提示："相关漫画基于系列名 / 标题自动匹配，可能包含误差。"
   - 未来可以扩展为真正的 Work 表，建立强关联

## 总结

本次实现完成了作品中心从"以 ebook 为核心"到"多形态聚合"的升级：

1. ✅ **统一 API**: `/api/works/{ebook_id}` 提供聚合查询
2. ✅ **多形态支持**: 电子书、有声书、漫画
3. ✅ **启发式匹配**: 漫画通过 title/series 自动关联
4. ✅ **前端重构**: WorkDetail.vue 只调用一个接口
5. ✅ **测试覆盖**: 5 个测试用例全部通过

作品中心现已支持多形态聚合展示，为用户提供更完整的作品信息视图。

