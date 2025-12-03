# 小说源到电子书/有声书流程设计文档

## 背景

VabHub 已支持 EBook/EBookFile + AudiobookFile + 统一预览功能。用户希望从"小说源"自动生成电子书/有声书，但目前只在小说网站看小说，没有现成电子书文件。

本文档设计了一个从小说源到 VabHub 入库的完整流程，保持站点无关、内容合法导入的视角。

## 总体流程

```
小说源 → 章节流 (ChapterStream) → 标准化章节结构 (StandardChapter) 
  → 电子书文件 (EPUB/TXT) → VabHub EBookImporter → 可选：有声书生成/挂载
```

### 1. 小说源 → 章节流 (ChapterStream)

**源类型：**
- 官方/合法 API
- 用户导出的本地 txt/epub 文件
- 用户自己编写的轻量采集脚本（不在 VabHub 核心仓库中维护）

**抽象接口：`NovelSourceAdapter`**
- 负责根据 book_id/title 获取章节列表
- 提供按章节依次拉取内容的 generator/iterator
- 不关心具体站点实现，只定义接口规范

### 2. 章节流 → 标准化章节结构（StandardChapter）

**标准结构：**
```python
@dataclass
class StandardChapter:
    index: int          # 章节顺序
    title: str          # 章节标题
    content: str        # 章节内容（纯文本 / 简单 HTML）
```

**内容清洗：**
- 去除广告、站点水印（前提是内容合法）
- 统一编码格式
- 规范化换行和段落

### 3. 章节结构 → 电子书文件（EPUB/TXT 等）

**EpubBuilder（或 BookBuilder）：**
- 输入：metadata（书名、作者、简介）、章节列表
- 输出：epub/txt 文件路径
- 可以先只设计接口，具体实现留到未来任务

### 4. 生成的电子书 → VabHub EBookImporter

通过调用现有 `EBookImporter.import_ebook_from_file(...)` 将生成的 epub 文件入库。

利用 Open Library 等现有元数据增强机制补充信息（ISBN、封面、描述等）。

### 5. 可选：有声书挂载

**未来扩展：**
- 通过 TTS（文本转语音）等生成有声书
- 生成的音频文件通过 `AudiobookImporter.import_audiobook_from_file(...)` 入库
- 目前只在设计文档中注明，不实现具体逻辑

## 模块拆分

```
app/modules/novel/
├── __init__.py
├── models.py              # StandardChapter, NovelMetadata 等数据结构
├── source_base.py         # NovelSourceAdapter 抽象基类
├── sources/               # 不同来源的适配器（用户实现）
│   └── __init__.py
├── epub_builder.py        # EpubBuilder
└── pipeline.py            # NovelToEbookPipeline orchestrator
```

## 安全与合规

**重要原则：**

1. **VabHub 不内置任何绕过版权/付费的爬虫**
   - 只提供抽象接口和流水线
   - 具体来源由用户自己实现
   - 用户对内容合法性负责

2. **只处理合法来源：**
   - 官方/合法 API
   - 用户自己拥有的内容（本地文件）
   - 用户授权的采集脚本

3. **内容清洗只做技术处理：**
   - 去除技术性水印（如站点标识）
   - 不修改版权信息
   - 不绕过付费/DRM

## 实现优先级

**Phase 1（当前）：**
- ✅ 定义数据结构和抽象接口
- ✅ 实现 Pipeline 骨架
- ⏳ EpubBuilder 接口（占位实现）

**Phase 2（未来）：**
- 实现真正的 EPUB 构建逻辑
- 支持更多电子书格式（MOBI、AZW3 等）
- 内容清洗和格式化工具

**Phase 3（未来）：**
- TTS 集成（有声书生成）
- 批量处理多个小说源
- 定时任务支持

## 与现有模块的集成

### EBookImporter 集成
- 直接调用 `EBookImporter.import_ebook_from_file(...)`
- 复用现有的 WorkResolver 去重逻辑
- 利用元数据增强服务补充信息

### AudiobookImporter 集成（未来）
- 生成的音频文件通过 `AudiobookImporter.import_audiobook_from_file(...)` 入库
- 共享同一个 EBook 作品（通过 ebook_id 关联）

### 统一预览支持
- 生成的电子书/有声书自动出现在 `/api/library/preview` 中
- 支持按媒体类型过滤

## 使用示例（未来）

```python
# 用户实现自己的 NovelSourceAdapter
class MyNovelSource(NovelSourceAdapter):
    def get_metadata(self) -> NovelMetadata:
        return NovelMetadata(title="示例小说", author="示例作者")
    
    def iter_chapters(self) -> Iterable[StandardChapter]:
        # 从合法来源获取章节
        for i, chapter_data in enumerate(self.fetch_chapters()):
            yield StandardChapter(
                index=i + 1,
                title=chapter_data['title'],
                content=chapter_data['content']
            )

# 使用 Pipeline
pipeline = NovelToEbookPipeline(db, ebook_importer, epub_builder)
source = MyNovelSource(...)
pipeline.run(source, output_dir=Path("/tmp/novels"))
```

## 注意事项

1. **不实现具体爬虫**：所有站点相关的实现都在用户侧
2. **保持接口简洁**：抽象接口只定义必要方法
3. **错误处理**：每个步骤都要有完善的错误处理和日志
4. **可扩展性**：为未来功能（TTS、批量处理等）预留接口

