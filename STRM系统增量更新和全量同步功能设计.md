# STRM系统增量更新和全量同步功能设计

## 📋 功能说明

### "完整工作流 → 由调用方控制"的含义

**含义**：STRM系统不自动执行完整的文件处理流程，而是由调用方（下载完成回调、手动触发、定时任务等）根据需要组合各个模块来完成工作。

**示例**：
```python
# 方式1：由下载完成回调控制（推荐）
async def on_download_complete(download_task_id: int):
    """下载完成回调"""
    # 1. 使用文件操作模块上传文件
    await file_operation_service.upload_file(...)
    
    # 2. 使用媒体重命名模块重命名文件
    await media_renamer_service.rename_file(...)
    
    # 3. 使用媒体分类模块分类文件
    await media_classifier_service.classify_file(...)
    
    # 4. 使用STRM模块生成STRM文件
    await strm_service.generate_strm(...)
    
    # 5. 使用媒体服务器模块刷新
    await media_server_service.refresh_library(...)

# 方式2：由定时任务控制
@schedule.every(1).hours
async def sync_strm_files():
    """定时同步STRM文件"""
    # 1. 使用文件树管理模块扫描网盘
    cloud_tree = await file_tree_manager.scan_cloud_storage(...)
    
    # 2. 使用STRM同步管理器进行增量同步
    await strm_sync_manager.incremental_sync()
```

## 🎯 核心功能设计

### 1. 增量更新功能

**功能**：只同步新增和变更的文件，提高同步效率。

**实现方式**：
- 利用115网盘API的时间范围搜索功能
- 对比数据库中的文件树快照
- 只处理变更的文件

**API设计**：
```python
@router.post("/strm/sync/incremental")
async def incremental_sync(
    cloud_storage: str = "115",
    last_sync_time: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    增量同步STRM文件
    
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

### 2. 全量同步功能

**功能**：扫描所有文件并生成STRM文件，用于初始化或修复。

**实现方式**：
- 使用文件树管理模块全量扫描网盘
- 对比本地STRM文件树
- 生成缺失的STRM文件
- 删除多余的STRM文件（可选）

**API设计**：
```python
@router.post("/strm/sync/full")
async def full_sync(
    cloud_storage: str = "115",
    root_path: str = "/",
    db: AsyncSession = Depends(get_db)
):
    """
    全量同步STRM文件
    
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

## 🔧 主系统模块集成

### 1. 文件上传管理 → 文件操作模块

**调用方式**：
```python
from app.modules.file_operation.transfer_handler import TransferHandler
from app.modules.file_operation.file_operation_mode import FileOperationConfig, FileOperationMode

# 上传文件到115网盘
config = FileOperationConfig(
    source_storage="local",
    target_storage="115",
    operation_mode=FileOperationMode.COPY,  # 或 MOVE
    source_path="/local/path/to/file.mkv",
    target_path="/115/电影/xxx.mkv",
    overwrite_mode="never"  # 或 "always", "size", "latest"
)

result = await TransferHandler.handle_transfer(config)
```

### 2. 文件重命名 → 媒体重命名模块

**调用方式**：
```python
from app.modules.media_renamer.service import MediaRenamerService

# 重命名媒体文件
renamer = MediaRenamerService(db)
result = await renamer.rename_file(
    file_path="/path/to/file.mkv",
    media_info=media_info,  # 从TMDB/豆瓣获取
    target_path="/target/path/to/file.mkv"
)
```

### 3. 文件分类 → 媒体分类模块

**调用方式**：
```python
from app.modules.media_classifier.service import MediaClassifierService

# 分类媒体文件
classifier = MediaClassifierService(db)
result = await classifier.classify_file(
    file_path="/path/to/file.mkv",
    media_info=media_info,
    target_category="movie"  # 或 "tv", "anime", "other"
)
```

### 4. 文件树管理 → 高级功能（直接调用主系统的）

**调用方式**：
```python
from app.modules.strm.file_tree_manager import FileTreeManager
from app.core.cloud_storage.providers.cloud_115_api import Cloud115API

# 获取115 API客户端
cloud_115_api = await get_115_api_client()

# 创建文件树管理器
file_tree_manager = FileTreeManager(db, cloud_115_api=cloud_115_api)

# 扫描网盘文件树
cloud_tree = await file_tree_manager.scan_cloud_storage(
    cloud_storage="115",
    root_path="/",
    file_type=4  # 4:视频
)

# 对比文件树
differences = await file_tree_manager.compare_file_trees(
    cloud_storage="115",
    local_tree=local_tree,
    cloud_tree=cloud_tree
)
```

### 5. 网盘刮削 → 高级功能

**调用方式**：
```python
from app.modules.media_scraper.service import MediaScraperService

# 网盘刮削（如果实现了）
scraper = MediaScraperService(db)
result = await scraper.scrape_cloud_file(
    cloud_storage="115",
    cloud_file_id="pick_code",
    media_info=media_info
)
```

### 6. 覆盖模式 → 文件操作功能

**调用方式**：
```python
from app.modules.file_operation.overwrite_handler import OverwriteHandler, OverwriteMode

# 检查覆盖模式
should_overwrite, message = await OverwriteHandler.check_overwrite(
    target_path=Path("/target/path/to/file.mkv"),
    overwrite_mode=OverwriteMode.LATEST,  # 或 NEVER, ALWAYS, SIZE
    new_file_size=file_size,
    storage_type="115",
    storage_oper=cloud_storage_oper
)
```

## 📊 STRM同步管理器设计

### 1. STRM同步管理器类

```python
from app.modules.strm.sync_manager import STRMSyncManager
from app.modules.strm.file_operation_mode import STRMSyncConfig
from app.modules.strm.config import STRMConfig

# 创建同步配置
sync_config = STRMSyncConfig(
    strm_library_path="/media_library",
    first_sync_mode="full",  # 或 "incremental"
    auto_sync=True,
    sync_interval=3600,  # 1小时
    realtime_compare=True,
    compare_interval=300,  # 5分钟
    auto_delete_on_cloud_delete=True,
    sync_file_types=[".mkv", ".mp4", ".avi"],
    exclude_paths=["/115/备份"],
    include_paths=["/115/电影", "/115/电视剧"]
)

# 创建STRM配置
strm_config = STRMConfig(
    media_library_path="/media_library",
    strm_url_mode="direct",
    generate_nfo=True,
    generate_subtitle_files=True
)

# 创建同步管理器
sync_manager = STRMSyncManager(
    db=db,
    sync_config=sync_config,
    strm_config=strm_config,
    cloud_storage="115",
    cloud_115_api=cloud_115_api
)

# 启动同步
await sync_manager.start_sync()

# 停止同步
await sync_manager.stop_sync()
```

### 2. 增量同步实现

```python
async def incremental_sync(self):
    """增量同步"""
    # 1. 获取上次同步时间
    last_sync_time = await self._get_last_sync_time()
    
    # 2. 调用文件树管理模块扫描网盘变更
    changed_files = await self.file_tree_manager.scan_cloud_changes(
        cloud_storage=self.cloud_storage,
        last_sync_time=last_sync_time,
        file_type=4  # 4:视频
    )
    
    # 3. 调用STRM生成模块生成STRM文件
    for file_info in changed_files:
        # 3.1 调用媒体识别模块识别媒体信息（如果需要）
        media_info = await self._identify_media(file_info)
        
        # 3.2 调用STRM生成模块生成STRM文件
        await self.strm_generator.generate_strm_file(
            media_info=media_info,
            cloud_file_id=file_info["file_id"],
            cloud_storage=self.cloud_storage,
            cloud_path=file_info["path"],
            subtitle_files=file_info.get("subtitle_files", [])
        )
    
    # 4. 调用媒体服务器模块刷新（如果需要）
    if self.strm_config.media_servers:
        await self._refresh_media_servers()
    
    # 5. 更新同步时间
    await self._update_last_sync_time()
```

### 3. 全量同步实现

```python
async def full_sync(self):
    """全量同步"""
    # 1. 调用文件树管理模块全量扫描网盘
    cloud_tree = await self.file_tree_manager.scan_cloud_storage(
        cloud_storage=self.cloud_storage,
        root_path="/",
        file_type=4  # 4:视频
    )
    
    # 2. 扫描本地STRM文件树
    local_tree = await self._scan_local_strm_files()
    
    # 3. 对比文件树
    differences = await self.file_tree_manager.compare_file_trees(
        cloud_storage=self.cloud_storage,
        local_tree=local_tree,
        cloud_tree=cloud_tree
    )
    
    # 4. 生成STRM文件
    for file_info in differences["added"] + differences["updated"]:
        # 4.1 调用媒体识别模块识别媒体信息（如果需要）
        media_info = await self._identify_media(file_info)
        
        # 4.2 调用STRM生成模块生成STRM文件
        await self.strm_generator.generate_strm_file(
            media_info=media_info,
            cloud_file_id=file_info["file_id"],
            cloud_storage=self.cloud_storage,
            cloud_path=file_info["path"],
            subtitle_files=file_info.get("subtitle_files", [])
        )
    
    # 5. 删除本地STRM文件（如果网盘文件已删除）
    if self.sync_config.auto_delete_on_cloud_delete:
        await self._delete_local_strm_files(differences["deleted"])
    
    # 6. 调用媒体服务器模块刷新（如果需要）
    if self.strm_config.media_servers:
        await self._refresh_media_servers()
```

## 🎯 API端点设计

### 1. 增量同步API

```python
@router.post("/api/strm/sync/incremental")
async def incremental_sync_strm(
    cloud_storage: str = "115",
    last_sync_time: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    增量同步STRM文件
    
    Args:
        cloud_storage: 云存储类型（115/123）
        last_sync_time: 上次同步时间（可选）
    
    Returns:
        同步结果
    """
    # 1. 获取同步配置
    sync_config = await get_strm_sync_config(db)
    strm_config = await get_strm_config(db)
    
    # 2. 获取115 API客户端
    cloud_115_api = await get_115_api_client(db)
    
    # 3. 创建同步管理器
    sync_manager = STRMSyncManager(
        db=db,
        sync_config=sync_config,
        strm_config=strm_config,
        cloud_storage=cloud_storage,
        cloud_115_api=cloud_115_api
    )
    
    # 4. 执行增量同步
    result = await sync_manager.incremental_sync()
    
    return {
        "success": True,
        "result": result
    }
```

### 2. 全量同步API

```python
@router.post("/api/strm/sync/full")
async def full_sync_strm(
    cloud_storage: str = "115",
    root_path: str = "/",
    db: AsyncSession = Depends(get_db)
):
    """
    全量同步STRM文件
    
    Args:
        cloud_storage: 云存储类型（115/123）
        root_path: 根路径（默认"/"）
    
    Returns:
        同步结果
    """
    # 1. 获取同步配置
    sync_config = await get_strm_sync_config(db)
    strm_config = await get_strm_config(db)
    
    # 2. 获取115 API客户端
    cloud_115_api = await get_115_api_client(db)
    
    # 3. 创建同步管理器
    sync_manager = STRMSyncManager(
        db=db,
        sync_config=sync_config,
        strm_config=strm_config,
        cloud_storage=cloud_storage,
        cloud_115_api=cloud_115_api
    )
    
    # 4. 执行全量同步
    result = await sync_manager.full_sync()
    
    return {
        "success": True,
        "result": result
    }
```

### 3. 启动自动同步API

```python
@router.post("/api/strm/sync/start")
async def start_auto_sync(
    cloud_storage: str = "115",
    db: AsyncSession = Depends(get_db)
):
    """
    启动自动同步
    
    Args:
        cloud_storage: 云存储类型（115/123）
    
    Returns:
        启动结果
    """
    # 1. 获取同步配置
    sync_config = await get_strm_sync_config(db)
    strm_config = await get_strm_config(db)
    
    # 2. 获取115 API客户端
    cloud_115_api = await get_115_api_client(db)
    
    # 3. 创建同步管理器
    sync_manager = STRMSyncManager(
        db=db,
        sync_config=sync_config,
        strm_config=strm_config,
        cloud_storage=cloud_storage,
        cloud_115_api=cloud_115_api
    )
    
    # 4. 启动自动同步
    await sync_manager.start_sync()
    
    return {
        "success": True,
        "message": "自动同步已启动"
    }
```

### 4. 停止自动同步API

```python
@router.post("/api/strm/sync/stop")
async def stop_auto_sync(
    cloud_storage: str = "115",
    db: AsyncSession = Depends(get_db)
):
    """
    停止自动同步
    
    Args:
        cloud_storage: 云存储类型（115/123）
    
    Returns:
        停止结果
    """
    # 1. 获取同步管理器（从内存或数据库）
    sync_manager = await get_sync_manager(cloud_storage)
    
    # 2. 停止自动同步
    await sync_manager.stop_sync()
    
    return {
        "success": True,
        "message": "自动同步已停止"
    }
```

## 🔄 工作流示例

### 示例1：下载完成后自动同步STRM

```python
async def on_download_complete(download_task_id: int):
    """下载完成回调"""
    # 1. 获取下载任务信息
    download_task = await download_service.get_task(download_task_id)
    local_file_path = download_task.file_path
    
    # 2. 使用文件操作模块上传文件到115网盘
    upload_config = FileOperationConfig(
        source_storage="local",
        target_storage="115",
        operation_mode=FileOperationMode.COPY,  # 保留源文件做种
        source_path=local_file_path,
        target_path=f"/115/电影/{Path(local_file_path).name}",
        overwrite_mode="never"
    )
    upload_result = await TransferHandler.handle_transfer(upload_config)
    
    if not upload_result["success"]:
        logger.error(f"文件上传失败: {upload_result['error']}")
        return
    
    # 3. 使用媒体重命名模块识别和重命名文件
    media_info = await media_renamer_service.identify_media(local_file_path)
    rename_result = await media_renamer_service.rename_file(
        file_path=upload_result["target_path"],
        media_info=media_info
    )
    
    # 4. 使用媒体分类模块分类文件
    classify_result = await media_classifier_service.classify_file(
        file_path=rename_result["target_path"],
        media_info=media_info
    )
    
    # 5. 使用STRM模块生成STRM文件
    strm_result = await strm_service.generate_strm(
        cloud_file_id=upload_result["cloud_file_id"],
        cloud_storage="115",
        media_info=media_info
    )
    
    # 6. 使用媒体服务器模块刷新
    if strm_config.media_servers:
        await media_server_service.refresh_library(
            media_servers=strm_config.media_servers,
            strm_path=strm_result["strm_path"]
        )
```

### 示例2：定时增量同步STRM

```python
@schedule.every(1).hours
async def sync_strm_files():
    """定时增量同步STRM文件"""
    # 1. 调用增量同步API
    result = await incremental_sync_strm(
        cloud_storage="115",
        last_sync_time=None  # 从数据库获取
    )
    
    logger.info(f"增量同步完成: {result}")
```

### 示例3：手动全量同步STRM

```python
@router.post("/api/strm/sync/full-manual")
async def manual_full_sync(
    cloud_storage: str = "115",
    root_path: str = "/",
    db: AsyncSession = Depends(get_db)
):
    """手动全量同步STRM文件"""
    # 1. 调用全量同步API
    result = await full_sync_strm(
        cloud_storage=cloud_storage,
        root_path=root_path,
        db=db
    )
    
    return {
        "success": True,
        "result": result
    }
```

## 📝 配置模型

### STRM同步配置

```python
class STRMSyncConfig(BaseModel):
    """STRM同步配置"""
    
    # STRM媒体库路径
    strm_library_path: str = '/media_library'
    
    # 首次同步模式
    first_sync_mode: str = 'full'  # full/incremental
    
    # 自动同步
    auto_sync: bool = True
    sync_interval: int = 3600  # 同步间隔（秒）
    
    # 实时对比
    realtime_compare: bool = True
    compare_interval: int = 300  # 对比间隔（秒）
    
    # 自动删除（网盘文件删除时自动删除本地STRM文件）
    auto_delete_on_cloud_delete: bool = True  # 是否在网盘文件删除时自动删除本地STRM文件
    
    # 文件类型过滤
    sync_file_types: List[str] = ['.mkv', '.mp4', '.avi', '.mov']
    
    # 路径过滤
    exclude_paths: List[str] = []
    include_paths: List[str] = []
```

### STRM配置（更新）

```python
class STRMConfig(BaseModel):
    """STRM系统配置"""
    
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

## ✅ 总结

### 核心设计理念

1. **模块化设计**：STRM系统只负责STRM文件生成，其他功能由主系统模块提供
2. **调用方控制**：由调用方（下载完成回调、手动触发、定时任务等）组合各个模块完成工作
3. **增量更新**：利用115网盘API的时间范围搜索功能，只同步变更的文件
4. **全量同步**：扫描所有文件并生成STRM文件，用于初始化或修复

### 功能集成

- ✅ **文件上传管理** → 调用 `TransferHandler.handle_transfer()`
- ✅ **文件重命名** → 调用 `MediaRenamerService.rename_file()`
- ✅ **文件分类** → 调用 `MediaClassifierService.classify_file()`
- ✅ **文件树管理** → 调用 `FileTreeManager.scan_cloud_storage()`
- ✅ **网盘刮削** → 调用 `MediaScraperService.scrape_cloud_file()`（如果实现）
- ✅ **覆盖模式** → 调用 `OverwriteHandler.check_overwrite()`
- ✅ **增量更新** → 调用 `STRMSyncManager.incremental_sync()`
- ✅ **全量同步** → 调用 `STRMSyncManager.full_sync()`

### 优势

1. **职责清晰**：每个模块只负责自己的功能
2. **易于维护**：模块之间解耦，易于测试和维护
3. **灵活扩展**：可以轻松添加新功能或修改现有功能
4. **高效同步**：增量更新只处理变更的文件，提高同步效率

