# MEDIA-ORGANIZE-1 Phase 1 设计笔记

> 基于现有 TransferHistory + transfer_service 实现媒体整理中心 + 手动整理功能

---

## 1. 现状架构分析

### 1.1 当前「下载 → 整理 → 转移历史」调用链

```
下载完成 → TransferService.transfer_file() → TransferHandler.transfer_file() 
         → 自动记录 TransferHistory → 前端 TransferHistory.vue 展示
```

**关键组件**：
- `TransferService`: 文件整理核心逻辑，支持 copy/move/link/softlink
- `TransferHistoryService`: 历史记录管理，支持分页、搜索、状态过滤
- `MediaOrganizer`: 媒体识别和路径生成（基于 TMDB）
- `DirectoryConfig`: 目录配置模型，定义源/目标路径和操作方式

### 1.2 TransferHistory 记录机制

**写入时机**：
- 每次 `TransferService.transfer_file()` 执行后自动写入
- 成功/失败状态都会记录，包含错误信息
- 支持文件大小、媒体信息、下载器关联等完整元数据

**关键字段**：
```python
# 基础路径信息
src/dest: 源文件和目标文件路径
src_storage/dest_storage: 存储类型（local/115等）
mode: 操作模式（move/copy/link/softlink）

# 媒体识别信息
type: 媒体类型（movie/tv）
title/year/tmdbid: TMDB 识别信息
seasons/episodes: 剧集信息

# 状态和错误
status: 成功/失败（True/False）
errmsg: 错误信息（失败时记录）

# 下载关联
downloader/download_hash: 下载任务关联
```

### 1.3 TransferService 核心逻辑

**整理流程**：
1. 确定操作模式（基于 DirectoryConfig.transfer_type）
2. HR 保护检查（Local Intel，防止删除 PT 源文件）
3. 创建 FileOperationConfig
4. 执行 TransferHandler.transfer_file()
5. 自动记录 TransferHistory

**依赖关系**：
- 需要 `DirectoryConfig` 对象来执行整理
- 自动处理媒体信息回填到历史记录
- 支持多种存储类型和操作模式

---

## 2. 新增能力设计

### 2.1 手动整理能力

**目标**：对失败记录发起"手动整理"，支持重新配置参数并执行

**实现策略**：
- 基于现有 `TransferService.transfer_file()` 核心逻辑
- 手动构造 `DirectoryConfig` 对象
- 创建新的 `TransferHistory` 记录（不覆盖原记录）
- 支持重新指定媒体信息（TMDB ID、类型等）

**关键接口**：
```python
# 获取历史记录配置信息
GET /transfer-history/{history_id}/manual-config

# 执行手动整理
POST /transfer-history/manual-transfer
```

### 2.2 TMDB 搜索能力

**目标**：在手动整理弹窗中提供 TMDB 搜索，回填准确的媒体信息

**实现策略**：
- 独立的 TMDB 搜索 API
- 支持电影/电视剧分类搜索
- 返回结构化的媒体信息用于回填表单

**关键接口**：
```python
# TMDB 搜索
GET /media/search-tmdb?q=关键词&type=movie|tv&year=2023
```

---

## 3. 技术实现要点

### 3.1 手动整理流程设计

```python
async def manual_transfer(history_id: int, config: ManualTransferRequest):
    # 1. 读取原始 TransferHistory 记录
    original = await get_transfer_history(history_id)
    
    # 2. 构造新的 DirectoryConfig
    directory_config = DirectoryConfig(
        library_path=config.dest_path,
        storage=config.dest_storage,
        library_storage=config.dest_storage,
        transfer_type=config.operation_mode,
        media_type=config.media_type
    )
    
    # 3. 构造媒体信息（优先使用用户指定的 TMDB 信息）
    media_info = build_media_info(
        original_media=original.media_info,
        user_tmdb_id=config.tmdb_id,
        user_media_type=config.media_type,
        reuse_history_meta=config.reuse_history_meta
    )
    
    # 4. 调用 TransferService 执行整理
    result = await transfer_service.transfer_file(
        source_path=original.src,
        target_path=generate_target_path(media_info, config),
        directory_config=directory_config,
        media_info=media_info
    )
    
    # 5. 返回结果（TransferService 会自动记录新历史）
    return result
```

### 3.2 TMDB 搜索集成

**复用现有组件**：
- `MediaIdentifier`: 已有 TMDB 识别逻辑
- `MediaOrganizer`: 已有路径生成逻辑

**搜索流程**：
```python
async def search_tmdb(query: str, media_type: str = None, year: int = None):
    identifier = MediaIdentifier(settings.TMDB_API_KEY)
    results = await identifier.search_tmdb(query, media_type, year)
    return format_search_results(results)
```

### 3.3 路径生成策略

**关键问题**：如何根据 TMDB 信息生成正确的目标路径？

**解决方案**：
- 复用 `MediaOrganizer` 的路径生成逻辑
- 支持用户自定义目标基础路径
- 按媒体类型自动分类（电影/电视剧/动漫）

---

## 4. 数据模型扩展

### 4.1 TransferHistory 扩展（可选）

**建议新增字段**：
```python
parent_history_id: Optional[int] = None  # 关联原始失败记录
manual_retry: bool = False               # 标记是否为手动重试
```

**目的**：
- 追踪手动整理与原始记录的关联关系
- 便于统计手动重试成功率
- 为后续优化提供数据支持

### 4.2 ManualTransferRequest 设计

```python
class ManualTransferRequest(BaseModel):
    history_id: int                                    # 原始记录ID
    dest_storage: str                                  # 目标存储
    dest_path: str                                     # 目标基础路径
    operation_mode: Literal["move","copy","link","auto"]
    media_type: Literal["auto","movie","tv","anime"]
    tmdb_id: Optional[int] = None
    season: Optional[int] = None
    episodes: Optional[str] = None
    use_classification: bool = True
    delete_source: bool = False
    reuse_history_meta: bool = True
```

---

## 5. 前端交互设计

### 5.1 TransferHistory.vue 增强

**新增功能**：
- 失败记录显示"手动整理"按钮
- 点击后拉取配置信息并弹出手动整理对话框
- 详情页面展示完整的媒体识别信息

**状态过滤**：
- 保持现有的 全部/成功/失败 过滤
- 默认显示"全部"，便于用户查看所有记录

### 5.2 ManualTransferDialog 设计

**布局设计**：标准媒体整理弹窗布局

**表单分区**：
1. **目的配置**：存储类型、操作模式、目标路径
2. **媒体识别**：类型、TMDB ID、季集信息
3. **高级选项**：分类规则、源文件处理、元数据复用

**TMDB 搜索集成**：
- 内嵌搜索对话框
- 支持关键词搜索和结果选择
- 自动回填媒体信息到表单

---

## 6. 实施优先级

### Phase 1: P0-P1（基础框架）
- ✅ 现状调研和设计文档
- 🔄 手动整理 API 基础实现
- 🔄 TMDB 搜索 API 实现

### Phase 2: P2-P3（前端集成）
- 🔄 TransferHistory.vue 页面增强
- 🔄 ManualTransferDialog 组件实现
- 🔄 TMDB 搜索弹窗集成

### Phase 3: P4-P5（闭环完善）
- 🔄 下载→整理→手动整理完整流程
- 🔄 错误处理和边界情况
- 🔄 QA 验收和文档完善

---

## 7. 风险和注意事项

### 7.1 技术风险
- **路径冲突**：手动整理可能与自动整理产生路径冲突
- **权限控制**：需要确保用户只能整理自己的文件
- **存储限制**：不同存储类型的路径格式差异

### 7.2 用户体验风险
- **复杂度控制**：手动整理表单不宜过于复杂
- **错误提示**：需要友好的错误信息和操作指导
- **性能考虑**：TMDB 搜索响应时间优化

### 7.3 缓解措施
- 复用现有成熟的 TransferService 逻辑
- 提供合理的默认配置和智能提示
- 实施适当的缓存和限流机制

---

**设计版本**: v1.0  
**创建时间**: 2025-11  
**下一步**: 开始 P1 手动整理 API 基础实现
