# INBOX-NOVEL-AUTO-1 完成文档

## 概述

将统一收件箱中的 TXT 小说文件自动走 NovelToEbookPipeline → EBookImporter 入库流程，实现从 INBOX_ROOT 到 EBook + Work Hub 的完整自动化链路。

## 实现内容

### 一、完整流程描述

**TXT 小说从 INBOX_ROOT 到 EBook + Work Hub 的完整流程**:

```
INBOX_ROOT（待整理目录中的 TXT 文件）
  ↓
InboxScanner 扫描文件
  ↓
MediaTypeDetectionService 检测 media_type="novel_txt"
  （基于文件大小 + 内容 + 章节标记）
  ↓
InboxRouter.route() 路由到 NovelToEbookPipeline
  ↓
_handle_novel_txt() 处理：
  1. 检查文件存在性
  2. 构造 NovelMetadata（清洗标题、添加 tags）
  3. 创建 LocalTxtNovelSourceAdapter
  4. 执行 NovelToEbookPipeline.run()
     - 从 TXT 读取章节
     - EpubBuilder 生成 EPUB/TXT 占位文件
     - EBookImporter 导入到 EBook 库
  5. 成功后将 TXT 归档到 NOVEL_UPLOAD_ROOT/source_txt
  ↓
返回 "handled:novel_txt"
  ↓
文件从 INBOX_ROOT 中"消失"（已移动到归档目录）
  ↓
新作品出现在：
  - EBook 库（/api/library/preview）
  - Work Hub（/api/works/{ebook_id}）
```

### 二、NovelMetadata 从 InboxItem 的派生规则

**文件**: `app/modules/inbox/router.py` - `_handle_novel_txt()` 方法

#### 构造规则

1. **title（标题）**:
   - 从 `Path(file_path).stem` 获取（不含扩展名的文件名）
   - 使用 `_clean_title_for_display()` 清洗：
     - 移除常见标记：`[精校]`、`[全本]`、`[完本]`、`[EPUB]`、`[完整版]`、`[校对]` 等
     - 移除圆括号标记：`(精校)`、`(全本)`、`(完本)` 等
   - 如果清洗后为空，使用原始文件名

2. **author（作者）**:
   - 暂时为 `None`
   - 未来可以从文件名（如 "作者 - 书名.txt"）或 PT 信息中提取

3. **description（简介）**:
   - 固定字符串：`"Imported from INBOX"`

4. **language（语言）**:
   - 默认：`"zh-CN"`

5. **tags（标签）**:
   - 基础标签：`["from_inbox_novel_txt"]`
   - 合并 `InboxItem.source_tags`：
     - 如果是列表：直接扩展
     - 如果是字符串（逗号分隔）：分割后添加
   - 例如：`source_tags=["tag1", "tag2"]` → `tags=["from_inbox_novel_txt", "tag1", "tag2"]`

### 三、文件归档策略

**成功导入后 TXT 被移动到哪里**:

- **归档目录**: `NOVEL_UPLOAD_ROOT / "source_txt"`
- **文件名处理**:
  - 使用 `_create_safe_filename()` 生成安全文件名：
    - 清理特殊字符（只保留字母、数字、中文、下划线、连字符）
    - 保持原扩展名
    - 如果清理后为空，使用时间戳 + UUID
  - 如果目标文件已存在，添加时间戳后缀：`{stem}_{timestamp}{suffix}`

**示例**:
```
原始文件: INBOX_ROOT / "三体[精校].txt"
  ↓
归档到: NOVEL_UPLOAD_ROOT / source_txt / "三体精校.txt"
```

**失败处理**:
- 如果 pipeline 失败，TXT 文件**不移动**，保留在 INBOX_ROOT
- 用户可以在 Dev Inbox Preview 页面看到失败项，调整后重试

### 四、run-once 中 novel_txt 的结果标记

#### 结果字符串格式

1. **`"handled:novel_txt"`**:
   - 表示成功处理
   - NovelToEbookPipeline 执行成功
   - EBook 已入库
   - TXT 文件已归档到 `NOVEL_UPLOAD_ROOT/source_txt`

2. **`"skipped:novel_txt_disabled"`**:
   - 表示跳过处理
   - `INBOX_ENABLE_NOVEL_TXT = False`
   - 文件保留在 INBOX_ROOT

3. **`"failed:novel_txt_file_not_found"`**:
   - 表示文件不存在
   - 文件路径无效或文件已被删除

4. **`"failed:novel_txt_invalid_path"`**:
   - 表示路径不是文件
   - 可能是目录或其他类型

5. **`"failed:novel_txt_import_failed"`**:
   - 表示导入失败
   - NovelToEbookPipeline.run() 返回 None
   - 文件保留在 INBOX_ROOT

6. **`"failed:novel_txt_import_error"`**:
   - 表示导入异常
   - NovelToEbookPipeline 抛出异常
   - 文件保留在 INBOX_ROOT

#### 统计逻辑

在 `/api/dev/inbox/run-once` 中：
- `handled_count`: 统计所有 `result.startswith("handled:")` 的项
- `skipped_count`: 统计所有 `result.startswith("skipped:")` 的项
- `failed_count`: 统计所有 `result.startswith("failed:")` 的项

因此，`"handled:novel_txt"` 和 `"failed:novel_txt_*"` 都会被正确统计。

### 五、实现细节

#### 辅助方法

1. **`_clean_title_for_display(title: str) -> str`**:
   - 清洗标题，移除常见标记
   - 用于显示，不用于匹配（保留原始大小写）

2. **`_create_safe_filename(original_filename: str) -> str`**:
   - 生成安全的文件名
   - 清理特殊字符，避免路径注入
   - 保持原扩展名

3. **`_handle_novel_txt(item: InboxItem) -> str`**:
   - 处理小说 TXT 文件的核心逻辑
   - 包含文件检查、metadata 构造、pipeline 执行、文件归档

#### 错误处理

- 所有异常都被捕获，返回相应的 `failed:*` 结果
- 归档失败不影响导入结果（EBook 已入库），但会记录警告日志
- 文件不存在或路径无效时，不调用 pipeline，直接返回失败

### 六、测试

#### 测试文件

1. **`tests/test_inbox_novel_txt_integration.py`**: 5 个测试用例
   - `test_inbox_router_skip_novel_txt_when_disabled`: 禁用时跳过
   - `test_inbox_router_calls_novel_pipeline_when_enabled`: 启用时调用 pipeline 并归档
   - `test_inbox_router_novel_pipeline_failure_marks_failed`: pipeline 失败时标记为失败
   - `test_inbox_router_novel_txt_file_not_found`: 文件不存在时的处理
   - `test_inbox_router_novel_txt_exception_handling`: 异常处理

2. **`tests/test_novel_pipeline_inbox_metadata.py`**: 4 个测试用例
   - `test_clean_title_for_display`: 标题清洗功能
   - `test_create_safe_filename`: 安全文件名生成
   - `test_handle_novel_txt_metadata_construction`: metadata 构造验证
   - `test_handle_novel_txt_with_source_tags_string`: source_tags 字符串处理

**测试用例总数**: 9 个

**测试状态**: ✅ 全部通过

#### 兼容性测试

- **`tests/test_smart_health_inbox.py`**: 无需修改
  - 现有的健康检查测试保持绿色
  - `get_inbox_health()` 使用 `InboxRunLog` 统计，兼容新的结果前缀

### 七、配置要求

#### 环境变量

```env
# 启用小说 TXT 处理
INBOX_ENABLE_NOVEL_TXT=true

# 小说上传根目录（用于归档）
NOVEL_UPLOAD_ROOT=./data/novel_uploads

# 电子书库根目录（用于存放生成的 EPUB）
EBOOK_LIBRARY_ROOT=./data/library/ebook
```

### 八、使用示例

#### 场景 1: 自动导入 TXT 小说

1. 将 TXT 文件放入 `INBOX_ROOT`
2. 调用 `POST /api/dev/inbox/run-once`
3. 系统自动：
   - 检测为 `novel_txt`
   - 转换为 EBook 并入库
   - 归档 TXT 文件到 `NOVEL_UPLOAD_ROOT/source_txt`
4. 在 `/api/library/preview` 和 `/works/{ebook_id}` 中查看新作品

#### 场景 2: 查看处理结果

- 在 `/api/dev/inbox/run-once` 的响应中，可以看到每个文件的 `result` 字段
- 在 `/api/smart/health` 的 `features.inbox` 中，可以看到整体统计

## 总结

本次实现完成了 TXT 小说从统一收件箱到 EBook + Work Hub 的完整自动化流程：

1. ✅ **InboxRouter 集成**: 在 `route()` 方法中处理 `novel_txt` 类型
2. ✅ **Metadata 构造**: 从 InboxItem 派生 NovelMetadata（清洗标题、合并 tags）
3. ✅ **Pipeline 执行**: 调用 NovelToEbookPipeline 完成转换和入库
4. ✅ **文件归档**: 成功后将 TXT 移动到 `NOVEL_UPLOAD_ROOT/source_txt`
5. ✅ **错误处理**: 完善的异常处理和结果标记
6. ✅ **测试覆盖**: 9 个测试用例，全部通过

TXT 小说现已完全集成到统一收件箱自动化流程中，无需手动操作即可完成从待整理到作品中心的完整链路。

