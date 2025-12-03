# 简化版STRM系统功能清单

## 📋 功能定位

**简化版STRM系统**：专注于核心功能，去除复杂的文件管理和工作流，只保留STRM文件生成的必要功能。

## 🎯 核心功能（必须）

### 1. STRM文件生成
- ✅ **生成STRM文件**：根据115网盘文件信息（pick_code）生成STRM文件到本地媒体库
- ✅ **URL生成**：支持两种模式
  - `direct`：直接使用115网盘下载地址（推荐，无需服务器）
  - `local_redirect`：使用本地服务重定向（用于链接刷新）
- ✅ **路径映射**：将115网盘路径映射到本地媒体库路径
  - 示例：`/115/电影/xxx (2023)/xxx.mkv` → `/media_library/Movies/xxx (2023)/xxx.strm`

### 2. 字幕文件处理（如果有）
- ✅ **识别字幕文件**：从115网盘获取视频字幕列表
- ✅ **生成字幕STRM**：为字幕文件生成STRM文件（指向115网盘字幕下载地址）
- ✅ **字幕文件命名**：字幕文件命名与媒体文件匹配

### 3. NFO文件生成（可选）
- ✅ **生成NFO文件**：生成媒体元数据文件（用于媒体服务器识别）
- ✅ **元数据来源**：使用TMDB/豆瓣API获取媒体信息

### 4. 媒体服务器刷新（可选）
- ✅ **通知刷新**：生成STRM文件后，通知媒体服务器（Plex/Jellyfin/Emby）刷新
- ✅ **延迟刷新**：可配置刷新延迟，避免频繁刷新

## 🔧 简化功能（移除）

### 1. 文件上传管理 ❌
- **原因**：这是文件操作模块的功能，不属于STRM系统
- **替代**：使用系统文件操作模块进行上传

### 2. 文件重命名 ❌
- **原因**：这是媒体重命名模块的功能，不属于STRM系统
- **替代**：使用媒体重命名模块进行重命名

### 3. 文件分类 ❌
- **原因**：这是媒体分类模块的功能，不属于STRM系统
- **替代**：使用媒体分类模块进行分类

### 4. 完整工作流 ❌
- **原因**：简化版不需要端到端的工作流，只需要STRM生成功能
- **替代**：由调用方（下载完成回调、手动触发等）控制流程
- **说明**：调用方根据需要组合各个模块（文件操作、媒体重命名、媒体分类、STRM生成等）完成工作

### 5. 文件树管理 ✅（新增）
- **功能**：调用主系统的文件树管理模块
- **实现**：直接调用 `FileTreeManager.scan_cloud_storage()` 和 `FileTreeManager.compare_file_trees()`
- **用途**：支持增量更新和全量同步功能

### 6. 增量更新 ✅（已移除）
- **功能**：已移除，因为系统已有完整工作流（下载→上传→STRM生成）
- **原因**：工作流模式本身就是增量同步，无需额外的自动增量同步功能
- **替代**：使用工作流模式（下载完成→上传→STRM生成）处理新文件

### 7. 全量同步 ✅（新增）
- **功能**：扫描所有文件并生成STRM文件，用于初始化或修复
- **实现**：使用文件树管理模块全量扫描网盘，对比本地STRM文件树
- **API**：`POST /api/strm/sync/full`

### 8. 网盘刮削 ✅（可选，调用主系统，可配置开关）
- **功能**：调用主系统的网盘刮削模块（如果实现）
- **实现**：调用 `MediaScraperService.scrape_cloud_file()`
- **配置**：`scrape_cloud_files: bool = False`（默认关闭）
- **说明**：可选功能，可配置开关控制是否对网盘文件进行刮削

### 9. 本地STRM刮削 ✅（可选，调用主系统，可配置开关）
- **功能**：调用主系统的本地STRM文件刮削模块（如果实现）
- **实现**：调用 `MediaScraperService.scrape_local_strm()`
- **配置**：`scrape_local_strm: bool = True`（默认开启）
- **说明**：可选功能，可配置开关控制是否对本地STRM文件进行刮削

### 10. 覆盖模式 ✅（调用主系统）
- **功能**：调用主系统的覆盖模式处理模块
- **实现**：调用 `OverwriteHandler.check_overwrite()`
- **说明**：用于文件操作（上传、移动、复制），不属于STRM系统本身

### 12. 生命周期追踪 ✅（核心功能）
- **功能**：记录STRM文件从创建到删除的完整生命周期事件
- **用途**：用于审计、调试、恢复和增量同步
- **实现**：`LifecycleTracker` 服务模块
- **事件类型**：
  - 创建事件（type=1）：STRM文件生成时记录
  - 更新事件（type=2）：STRM文件更新时记录
  - 删除事件（type=3）：STRM文件删除时记录
- **参考文档**：`STRM生命周期追踪功能说明.md`

### 13. 网盘文件删除自动删除本地STRM ✅（核心功能）
- **功能**：当网盘中删除媒体文件时，自动删除本地对应的STRM文件
- **实现**：
  - 通过对比数据库中的STRM文件和网盘文件列表检测删除的文件
  - 使用115网盘API检查文件是否存在
  - 自动删除本地STRM文件、NFO文件和字幕文件
  - 清理空文件夹
  - 记录删除事件到生命周期追踪
- **配置**：`auto_delete_on_cloud_delete: bool = True`（在STRMSyncConfig中）
- **触发时机**：
  - 增量同步时
  - 全量同步时
  - 实时对比时

## 📊 功能对比

| 功能 | 完整版 | 简化版 | 说明 |
|------|--------|--------|------|
| STRM文件生成 | ✅ | ✅ | 核心功能 |
| 字幕文件处理 | ✅ | ✅ | 核心功能 |
| NFO文件生成 | ✅ | ✅ | 可选功能 |
| 媒体服务器刷新 | ✅ | ✅ | 可选功能 |
| 文件上传管理 | ✅ | ❌ | 文件操作模块 |
| 文件重命名 | ✅ | ❌ | 媒体重命名模块 |
| 文件分类 | ✅ | ❌ | 媒体分类模块 |
| 完整工作流 | ✅ | ❌ | 由调用方控制 |
| 文件树管理 | ✅ | ✅ | 调用主系统模块 |
| 首次全量同步 | ✅ | ✅ | 核心功能，自动检测并执行 |
| 增量同步 | ✅ | ❌ | 已移除，由工作流模式替代 |
| 全量同步 | ✅ | ✅ | 手动触发功能 |
| 网盘刮削 | ✅ | ✅ | 可选，调用主系统，可配置开关 |
| 本地STRM刮削 | ✅ | ✅ | 可选，调用主系统，可配置开关 |
| 覆盖模式 | ✅ | ✅ | 调用主系统模块 |
| 生命周期追踪 | ✅ | ✅ | 核心功能，STRM系统负责 |
| 网盘删除自动删除本地STRM | ✅ | ✅ | 核心功能，自动检测和删除 |

## 🎯 简化版API设计

### 1. 生成STRM文件

```python
@router.post("/strm/generate")
async def generate_strm(
    cloud_file_id: str,
    cloud_storage: str = "115",
    media_info: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    生成STRM文件（简化版）
    
    Args:
        cloud_file_id: 115网盘文件pick_code
        cloud_storage: 云存储类型（115/123）
        media_info: 媒体信息（可选，如果没有则从文件名解析）
    
    Returns:
        STRM文件路径
    """
    # 1. 获取115网盘文件信息
    # 2. 解析媒体信息（如果未提供）
    # 3. 构建本地媒体库路径
    # 4. 生成STRM文件
    # 5. 生成字幕文件（如果有）
    # 6. 生成NFO文件（可选）
    # 7. 通知媒体服务器刷新（可选）
    pass
```

### 2. 批量生成STRM文件

```python
@router.post("/strm/batch-generate")
async def batch_generate_strm(
    file_list: List[Dict[str, str]],
    db: AsyncSession = Depends(get_db)
):
    """
    批量生成STRM文件（简化版）
    
    Args:
        file_list: 文件列表，每个文件包含cloud_file_id、cloud_storage、media_info等
    
    Returns:
        生成结果列表
    """
    # 遍历文件列表，逐个生成STRM文件
    pass
```

### 3. 增量同步STRM文件（新增）

```python
@router.post("/strm/sync/incremental")
async def incremental_sync_strm(
    cloud_storage: str = "115",
    last_sync_time: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    增量同步STRM文件（新增功能）
    
    Args:
        cloud_storage: 云存储类型（115/123）
        last_sync_time: 上次同步时间（可选，如果不提供则从数据库获取）
    
    Returns:
        同步结果
    """
    # 1. 调用文件树管理模块扫描网盘变更
    # 2. 调用STRM生成模块生成STRM文件
    # 3. 调用媒体服务器模块刷新
    pass
```

### 4. 全量同步STRM文件（新增）

```python
@router.post("/strm/sync/full")
async def full_sync_strm(
    cloud_storage: str = "115",
    root_path: str = "/",
    db: AsyncSession = Depends(get_db)
):
    """
    全量同步STRM文件（新增功能）
    
    Args:
        cloud_storage: 云存储类型（115/123）
        root_path: 根路径（默认"/"）
    
    Returns:
        同步结果
    """
    # 1. 调用文件树管理模块全量扫描网盘
    # 2. 调用STRM生成模块批量生成STRM文件
    # 3. 调用媒体服务器模块刷新
    pass
```

### 5. 启动自动同步（新增）

```python
@router.post("/strm/sync/start")
async def start_auto_sync(
    cloud_storage: str = "115",
    db: AsyncSession = Depends(get_db)
):
    """
    启动自动同步（新增功能）
    
    Args:
        cloud_storage: 云存储类型（115/123）
    
    Returns:
        启动结果
    """
    # 启动自动同步任务
    pass
```

### 6. 停止自动同步（新增）

```python
@router.post("/strm/sync/stop")
async def stop_auto_sync(
    cloud_storage: str = "115",
    db: AsyncSession = Depends(get_db)
):
    """
    停止自动同步（新增功能）
    
    Args:
        cloud_storage: 云存储类型（115/123）
    
    Returns:
        停止结果
    """
    # 停止自动同步任务
    pass
```

### 7. 删除STRM文件

```python
@router.delete("/strm/delete/{strm_file_id}")
async def delete_strm(
    strm_file_id: int,
    db: AsyncSession = Depends(get_db
):
    """
    删除STRM文件（简化版）
    
    Args:
        strm_file_id: STRM文件ID
    
    Returns:
        删除结果
    """
    # 1. 查找STRM文件记录
    # 2. 删除本地STRM文件
    # 3. 删除字幕文件（如果有）
    # 4. 删除NFO文件（如果有）
    # 5. 删除数据库记录
    # 6. 通知媒体服务器刷新（可选）
    pass
```

## 🔧 配置模型（简化版）

```python
class STRMConfig(BaseModel):
    """STRM系统配置（简化版）"""
    
    # 服务开关
    enabled: bool = True  # 是否启用STRM系统
    
    # 媒体库路径
    media_library_path: str = '/media_library'
    movie_path: str = '/media_library/Movies'
    tv_path: str = '/media_library/TV Shows'
    anime_path: str = '/media_library/Anime'
    other_path: str = '/media_library/Other'
    
    # STRM URL生成模式
    strm_url_mode: str = 'direct'  # direct/local_redirect
    
    # 本地重定向配置（仅当strm_url_mode为local_redirect时使用）
    local_redirect_host: str = ''  # 空字符串表示自动检测
    local_redirect_port: int = 0  # 0表示使用系统端口
    local_redirect_base_path: str = '/api/strm/stream'
    
    # 字幕配置
    generate_subtitle_files: bool = True  # 是否生成字幕文件
    
    # NFO配置
    generate_nfo: bool = True  # 是否生成NFO文件
    
    # 刮削配置（新增）
    scrape_cloud_files: bool = False  # 是否对网盘文件进行刮削（获取元数据、海报等）
    scrape_local_strm: bool = True  # 是否对本地STRM文件进行刮削（获取元数据、海报等）
    
    # 媒体服务器配置
    media_servers: List[str] = []  # 媒体服务器列表（['plex', 'jellyfin', 'emby']）
    auto_refresh: bool = True  # 是否自动刷新
    refresh_delay: int = 300  # 刷新延迟（秒）
```

## 📝 数据模型（简化版）

```python
class STRMFile(Base):
    """STRM文件记录（简化版）"""
    id: int
    cloud_file_id: str  # 115网盘文件pick_code
    cloud_storage: str  # 云存储类型（115/123）
    strm_path: str  # STRM文件路径
    media_type: str  # 媒体类型（movie/tv/anime）
    title: str  # 标题
    year: Optional[int]  # 年份
    season: Optional[int]  # 季（电视剧）
    episode: Optional[int]  # 集（电视剧）
    subtitle_files: List[str]  # 字幕文件列表
    nfo_path: Optional[str]  # NFO文件路径
    created_at: datetime
    updated_at: datetime
```

## 🎯 使用场景

### 场景1：下载完成后生成STRM

```python
# 1. 下载完成，文件已上传到115网盘
download_task = await download_service.get_task(download_task_id)
cloud_file_id = download_task.cloud_file_id

# 2. 调用STRM生成API
result = await strm_service.generate_strm(
    cloud_file_id=cloud_file_id,
    cloud_storage="115",
    media_info=media_info
)

# 3. STRM文件已生成到本地媒体库
# 4. 媒体服务器自动刷新（如果配置了）
```

### 场景2：手动生成STRM

```python
# 1. 用户在115网盘中选择了文件
cloud_file_id = "xxx"

# 2. 调用STRM生成API
result = await strm_service.generate_strm(
    cloud_file_id=cloud_file_id,
    cloud_storage="115"
)

# 3. STRM文件已生成
```

### 场景3：批量生成STRM

```python
# 1. 扫描115网盘目录，获取文件列表
file_list = await cloud_storage_service.list_files("/电影")

# 2. 批量生成STRM
results = await strm_service.batch_generate_strm(file_list)

# 3. 所有STRM文件已生成
```

## ✅ 简化版优势

1. **专注核心功能**：只保留STRM文件生成的必要功能
2. **易于使用**：API简单明了，易于集成
3. **易于维护**：代码量少，逻辑清晰
4. **灵活扩展**：可以基于简化版逐步添加高级功能

## 🔄 从简化版升级到完整版

如果需要完整版功能，可以：
1. 使用文件操作模块进行文件上传
2. 使用媒体重命名模块进行文件重命名
3. 使用媒体分类模块进行文件分类
4. 在工作流中组合这些模块，实现完整功能

## 📚 总结

**简化版STRM系统**专注于核心功能：
- ✅ STRM文件生成
- ✅ 字幕文件处理
- ✅ NFO文件生成（可选）
- ✅ 媒体服务器刷新（可选）
- ✅ **增量更新（新增）**
- ✅ **全量同步（新增）**

**移除的功能**由其他模块提供：
- ❌ 文件上传 → 文件操作模块（`TransferHandler.handle_transfer()`）
- ❌ 文件重命名 → 媒体重命名模块（`MediaRenamerService.rename_file()`）
- ❌ 文件分类 → 媒体分类模块（`MediaClassifierService.classify_file()`）
- ❌ 工作流管理 → 由调用方控制（下载完成回调、手动触发、定时任务等）

**调用主系统模块**：
- ✅ 文件树管理 → `FileTreeManager.scan_cloud_storage()` 和 `FileTreeManager.compare_file_trees()`
- ✅ 网盘刮削 → `MediaScraperService.scrape_cloud_file()`（可选，可配置开关 `scrape_cloud_files`）
- ✅ 本地STRM刮削 → `MediaScraperService.scrape_local_strm()`（可选，可配置开关 `scrape_local_strm`）
- ✅ 覆盖模式 → `OverwriteHandler.check_overwrite()`

**STRM系统核心功能**：
- ✅ **生命周期追踪** → `LifecycleTracker` 服务模块（STRM系统负责）
  - 记录创建事件（type=1）：STRM文件生成时
  - 记录更新事件（type=2）：STRM文件更新时
  - 记录删除事件（type=3）：STRM文件删除时
- ✅ **网盘删除自动删除本地STRM** → 自动检测网盘文件删除并删除本地STRM文件
  - 通过对比数据库和网盘文件列表检测删除的文件
  - 自动删除本地STRM文件、NFO文件和字幕文件
  - 清理空文件夹
  - 记录删除事件到生命周期追踪

**简化版的优势**：
- 代码量少，易于维护
- 功能明确，易于使用
- 可以基于简化版逐步扩展
- 模块化设计，职责清晰
- 灵活扩展，易于集成

## 📖 详细文档

详细的功能设计和实现方案请参考：
- **`STRM系统增量更新和全量同步功能设计.md`**：详细的功能设计和实现方案
- **`STRM系统功能澄清与覆盖模式实现方案.md`**：功能澄清和覆盖模式实现
- **`STRM生命周期追踪功能说明.md`**：生命周期追踪功能说明
- **`原生STRM系统设计方案.md`**：完整的STRM系统设计方案

