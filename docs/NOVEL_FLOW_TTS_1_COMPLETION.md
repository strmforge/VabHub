# NOVEL-FLOW-TTS-1 完成文档

## 概述

在现有 Novel 流水线（TXT → 电子书）的基础上，增加了可选的 TTS（文本转语音）支路，实现一条龙流程：

**TXT → NovelSourceAdapter → Novel Pipeline → EBookImporter → (可选) TTS → AudiobookImporter**

## 实现内容

### 一、配置层：TTS 相关开关

**文件**: `app/core/config.py`

新增配置项：

```python
# --- Novel / TTS ---
SMART_TTS_ENABLED: bool = False  # 是否启用 TTS（默认关闭）
SMART_TTS_PROVIDER: str = "dummy"  # TTS 提供商：dummy/http/edge_tts 等
SMART_TTS_DEFAULT_VOICE: Optional[str] = None  # 默认语音
SMART_TTS_MAX_CHAPTERS: int = 200  # 防止一次性小说章节太多
SMART_TTS_CHAPTER_STRATEGY: str = "per_chapter"  # "per_chapter" | "all_in_one"
SMART_TTS_OUTPUT_ROOT: str = "./data/tts_output"  # TTS 临时音频文件输出目录
```

**要求**:
- 默认 `SMART_TTS_ENABLED = False`，保证开箱不调用任何外部 TTS
- 所有配置项支持通过环境变量覆盖

### 二、TTS 抽象层

#### 2.1 base.py：定义协议与数据结构

**文件**: `app/modules/tts/base.py`

定义了：
- `TTSRequest`: TTS 请求模型（text, language, voice, speed, pitch, 元信息等）
- `TTSResult`: TTS 结果（audio_path, duration_seconds）
- `TTSEngine`: TTS 引擎协议（async synthesize 方法）

#### 2.2 dummy.py：DummyTTSEngine

**文件**: `app/modules/tts/dummy.py`

实现了开发用的假 TTS 引擎：
- 创建 1 秒静音 WAV 文件作为占位
- 记录日志：`[DummyTTSEngine] synthesize called for ebook_id=xxx chapter=yyy`
- 返回 `TTSResult(audio_path=target_path, duration_seconds=1)`

#### 2.3 factory.py：根据配置选择 provider

**文件**: `app/modules/tts/factory.py`

实现了 `get_tts_engine(settings: Settings) -> Optional[TTSEngine]`：
- 如果 `SMART_TTS_ENABLED = False`，返回 `None`
- 如果 `SMART_TTS_PROVIDER = "dummy"`，返回 `DummyTTSEngine()`
- 未知 provider 时 fallback 到 `DummyTTSEngine()` 并记录 warning

### 三、Novel → EBook → Audiobook 流水线扩展

**文件**: `app/modules/novel/pipeline.py`

#### 3.1 NovelPipelineResult

新增结果类，包含：
- `epub_path: Optional[Path]`
- `ebook: Optional[EBook]`
- `audiobook_files: List[AudiobookFile]`

#### 3.2 NovelToEbookPipeline 扩展

**新增参数**:
- `tts_engine: Optional[TTSEngine] = None`
- `audiobook_importer: Optional[AudiobookImporter] = None`
- `settings: Optional[Settings] = None`

**run() 方法扩展**:
- 新增 `generate_audiobook: bool = False` 参数
- 返回类型改为 `NovelPipelineResult`
- 在 EBook 成功入库后，如果 `generate_audiobook=True` 且 TTS 启用，进入 TTS 分支

#### 3.3 TTS 生成逻辑

**`_generate_audiobook_from_chapters()` 方法**:
1. 限制章节数量（`SMART_TTS_MAX_CHAPTERS`）
2. 按章节生成音频文件（`per_chapter` 策略）：
   - 为每个章节调用 `tts_engine.synthesize()`
   - 生成文件名：`ebook_{ebook.id}_ch{idx:03d}.wav`
3. 将音频文件导入为 AudiobookFile：
   - 调用 `audiobook_importer.import_audiobook_from_file()`
   - 失败时只记录日志，不影响整体流程

**错误处理**:
- 任何 TTS 或 AudiobookImporter 失败都不影响 EBook 入库
- 所有异常都被捕获并记录日志

### 四、INBOX 集成 TTS 支持

**文件**: `app/modules/inbox/router.py`

#### 4.1 InboxRouter.__init__ 扩展

在创建 `NovelToEbookPipeline` 时：
- 如果 `settings.SMART_TTS_ENABLED = True`，创建 TTS 引擎和有声书导入器
- 传入 `NovelToEbookPipeline` 构造函数

#### 4.2 _handle_novel_txt() 扩展

- 调用 `pipeline.run()` 时传入 `generate_audiobook=settings.SMART_TTS_ENABLED`
- 处理 `NovelPipelineResult` 返回类型
- 记录有声书生成情况（如果有）

**向后兼容**:
- `INBOX_ENABLE_NOVEL_TXT` 配置仍然生效
- 返回结果字符串仍然以 `"handled:novel_txt"` 开头

### 五、Dev API 扩展

**文件**: `app/api/novel_demo.py`

#### 5.1 ImportLocalTxtRequest 扩展

新增字段：
- `generate_audiobook: bool = False`

#### 5.2 ImportLocalTxtResponse / UploadTxtNovelResponse 扩展

新增字段：
- `audiobook_created: bool = False`
- `audiobook_files_count: int = 0`

#### 5.3 _run_novel_pipeline() 重构

- 返回类型改为 `NovelPipelineResult`
- 新增 `generate_audiobook` 参数
- 根据配置创建 TTS 引擎和有声书导入器

#### 5.4 upload_txt_novel() 扩展

- 新增 `generate_audiobook: bool = Form(False)` 参数
- 在响应中包含有声书生成情况

### 六、测试

#### 6.1 test_tts_dummy.py

**测试用例**:
1. `test_dummy_tts_creates_file`: 验证 DummyTTSEngine.synthesize 后目标路径存在
2. `test_dummy_tts_returns_result`: 验证返回的 audio_path 正确、duration_seconds 为有效值

**测试状态**: ✅ 2 passed

#### 6.2 test_novel_pipeline_tts.py

**测试用例**:
1. `test_run_without_tts_behaves_as_before`: 验证 `generate_audiobook=False` 时行为不变
2. `test_run_with_tts_calls_tts_engine_and_importer`: 验证 `generate_audiobook=True` 时，DummyTTSEngine 被调用，多次调用 AudiobookImporter
3. `test_tts_failure_does_not_break_ebook_import`: 验证模拟 TTS 抛异常，EBook 仍然入库成功
4. `test_audiobook_import_failure_logged_only`: 验证模拟 AudiobookImporter 抛异常，不影响整体

**测试状态**: ✅ 4 passed

#### 6.3 test_inbox_novel_tts_integration.py

**测试用例**:
1. `test_inbox_novel_tts_integration`: 验证 INBOX 中 TXT 文件在 TTS 启用时生成有声书

**测试状态**: ✅ 1 passed

**总计**: ✅ 7 passed

### 七、代码风格与注意事项

#### 向后兼容

- **不破坏现有函数签名**: `run()` 方法新增参数有默认值，保持完全兼容
- **默认行为不变**: `generate_audiobook=False` 时行为与之前完全一致
- **错误隔离**: TTS 失败不影响 EBook 入库

#### 错误处理

- 所有新逻辑遇到异常必须 `logger.exception(...)`
- 保证主流程（电子书入库）正常结束
- TTS 和 AudiobookImporter 失败只记录日志

#### 避免循环导入

- 在函数内使用延迟导入（如 `_run_novel_pipeline` 中导入 TTS 相关模块）

#### 不引入重型依赖

- 当前阶段只实现 Dummy provider
- 后续 TTS 实现可以在新任务中做

## 文件列表

### 新增文件

1. `app/modules/tts/__init__.py` - TTS 模块初始化
2. `app/modules/tts/base.py` - TTS 抽象层（协议与数据结构）
3. `app/modules/tts/dummy.py` - Dummy TTS 引擎
4. `app/modules/tts/factory.py` - TTS 引擎工厂
5. `tests/test_tts_dummy.py` - Dummy TTS 测试
6. `tests/test_novel_pipeline_tts.py` - Novel Pipeline TTS 集成测试
7. `tests/test_inbox_novel_tts_integration.py` - INBOX Novel TTS 集成测试
8. `docs/NOVEL_FLOW_TTS_1_COMPLETION.md` - 本文档

### 修改文件

1. `app/core/config.py` - 新增 TTS 相关配置项
2. `app/modules/novel/pipeline.py` - 扩展支持 TTS → Audiobook
3. `app/modules/inbox/router.py` - 集成 TTS 支持
4. `app/api/novel_demo.py` - Dev API 扩展支持 TTS

## 行为概述

### 默认行为（TTS 未启用）

- TXT 文件 → 电子书入库（与之前完全一致）
- 不生成有声书

### TTS 启用后

1. **TXT 文件 → 电子书入库**（必须成功）
2. **（可选）章节文本 → TTS → 音频文件 → AudiobookFile 入库**
   - 如果 TTS 失败：只记录日志，不影响电子书
   - 如果 AudiobookImporter 失败：只记录日志，不影响电子书

### 配置示例

```bash
# 启用 TTS
SMART_TTS_ENABLED=true
SMART_TTS_PROVIDER=dummy
SMART_TTS_OUTPUT_ROOT=./data/tts_output
SMART_TTS_MAX_CHAPTERS=200
SMART_TTS_CHAPTER_STRATEGY=per_chapter

# INBOX 自动处理
INBOX_ENABLE_NOVEL_TXT=true
```

## 测试结果

- ✅ `test_tts_dummy.py`: 2 passed
- ✅ `test_novel_pipeline_tts.py`: 4 passed
- ✅ `test_inbox_novel_tts_integration.py`: 1 passed
- **总计**: ✅ 7 passed

## 后续扩展

1. **实现真实 TTS 提供商**:
   - HTTP TTS API 适配器
   - Edge TTS 适配器
   - 其他 TTS 服务商适配器

2. **优化策略**:
   - 实现 `all_in_one` 策略（将所有章节合并成一个文件）
   - 支持批量 TTS 请求优化

3. **性能优化**:
   - 并发 TTS 请求
   - 音频文件缓存

4. **功能增强**:
   - 支持自定义语音参数（speed, pitch）
   - 支持多语言 TTS
   - 支持章节级别的 TTS 配置

## 总结

本次实现完成了在 Novel 流水线中集成可选的 TTS 功能：

1. ✅ **配置层**: 新增 TTS 相关配置项，默认关闭
2. ✅ **TTS 抽象层**: 创建了可插拔的 TTS 适配层（base + dummy + factory）
3. ✅ **流水线扩展**: NovelToEbookPipeline 支持可选的 TTS → Audiobook 支路
4. ✅ **INBOX 集成**: 统一收件箱在 TTS 启用时自动生成有声书
5. ✅ **Dev API 扩展**: 开发 API 支持手动触发 TTS
6. ✅ **测试覆盖**: 7 个测试用例全部通过
7. ✅ **向后兼容**: 不破坏现有功能，默认行为不变

用户现在可以通过配置 `SMART_TTS_ENABLED=true` 来启用 TTS 功能，实现 TXT 小说 → 电子书 + 有声书的一条龙流程。

