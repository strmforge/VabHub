# MoviePilot文件操作模式分析

## 📋 概述

MoviePilot通过**目录配置**来决定源文件下载之后的操作模式，支持以下四种模式：

1. **下载器监控** (`monitor_type: "downloader"`)
2. **目录监控** (`monitor_type: "directory"`)
3. **手动整理** (`monitor_type: null` 且 `transfer_type` 不为空)
4. **不整理** (`monitor_type: null` 且 `transfer_type` 为空)

## 🏷️ 标签机制（下载器监控的核心）

### 1. 标签配置

**文件**: `MoviePilot-2/app/core/config.py`

```python
# 种子标签
TORRENT_TAG: str = "MOVIEPILOT"
```

- 默认标签为 `"MOVIEPILOT"`
- 可在系统配置中自定义标签
- 用于标识MoviePilot添加的下载任务

### 2. 添加下载任务时打标签

**文件**: `MoviePilot-2/app/modules/qbittorrent/__init__.py`

```python
def download(self, content: Union[Path, str, bytes], download_dir: Path, cookie: str,
             episodes: Set[int] = None, category: Optional[str] = None, 
             label: Optional[str] = None, downloader: Optional[str] = None):
    # 生成随机Tag（用于识别刚添加的任务）
    tag = StringUtils.generate_random_str(10)
    
    # 添加标签
    if label:
        tags = label.split(',') + [tag]
    elif settings.TORRENT_TAG:
        tags = [tag, settings.TORRENT_TAG]  # 随机标签 + MoviePilot标签
    else:
        tags = [tag]
    
    # 添加任务
    state = server.add_torrent(
        content=content,
        download_dir=str(download_dir),
        is_paused=is_paused,
        tag=tags,  # 打上标签
        cookie=cookie,
        category=category
    )
```

**关键点**:
- 每个MoviePilot添加的下载任务都会自动打上 `TORRENT_TAG` 标签
- 如果任务已存在，也会检查并打上标签

### 3. 查询下载任务时过滤标签

**文件**: `MoviePilot-2/app/modules/qbittorrent/qbittorrent.py`

```python
def get_torrents(self, ids: Union[str, list] = None, status: str = None,
                 tags: Union[str, list] = None) -> Tuple[List[TorrentDictionary], bool]:
    """获取种子列表"""
    torrents = self.qbc.torrents_info(torrent_hashes=ids, status_filter=status)
    
    if tags:
        results = []
        if not isinstance(tags, list):
            tags = tags.split(',')
        for torrent in torrents:
            torrent_tags = [str(tag).strip() for tag in torrent.get("tags").split(',')]
            # 只返回包含指定标签的种子
            if set(tags).issubset(set(torrent_tags)):
                results.append(torrent)
        return results, False
    return torrents or [], False

def get_completed_torrents(self, ids: Union[str, list] = None,
                           tags: Union[str, list] = None):
    """获取已完成的种子"""
    torrents, error = self.get_torrents(status="seeding", ids=ids, tags=tags)
    return None if error else torrents or []

def get_downloading_torrents(self, ids: Union[str, list] = None,
                             tags: Union[str, list] = None):
    """获取正在下载的种子"""
    torrents, error = self.get_torrents(ids=ids, status="downloading", tags=tags)
    return None if error else torrents or []
```

**关键点**:
- 所有查询下载任务的方法都支持 `tags` 参数
- 只返回包含指定标签的下载任务
- WebUI也只显示打了标签的任务

## 📁 目录配置模型

**文件**: `MoviePilot-2/app/schemas/transfer.py`

```python
class TransferDirectoryConf(BaseModel):
    """目录配置"""
    # 目录路径
    download_path: Optional[str] = None  # 下载目录
    library_path: Optional[str] = None   # 媒体库目录
    
    # 存储类型
    storage: str = "local"              # 源存储类型（local/115/123等）
    library_storage: str = "local"       # 目标存储类型
    
    # 监控类型（决定文件操作模式）
    monitor_type: Optional[str] = None  # "downloader" | "directory" | null
    
    # 整理方式（transfer_type）
    transfer_type: Optional[str] = None  # "copy" | "move" | "link" | "softlink"
    
    # 媒体类型和类别
    media_type: Optional[str] = None     # "movie" | "tv" | "anime"
    media_category: Optional[str] = None # 媒体类别
    
    # 优先级
    priority: int = 0
```

## 🔄 文件操作模式详解

### 1. 下载器监控 (`monitor_type: "downloader"`)

**实现文件**: `MoviePilot-2/app/chain/transfer.py`

**工作流程**:
1. 定时任务（每5分钟）扫描下载器中的已完成任务
2. **只查询打了 `TORRENT_TAG` 标签的任务**
3. 检查任务是否在下载器监控目录中
4. 查询下载历史记录（识别媒体信息）
5. 执行文件整理（根据 `transfer_type`）

**关键代码**:
```python
def process(self) -> bool:
    """获取下载器中的种子列表，并执行整理"""
    # 获取下载器监控目录
    download_dirs = DirectoryHelper().get_download_dirs()
    
    # 只处理下载器监控目录
    if not any(dir_info.monitor_type == "downloader" and dir_info.storage == "local"
               for dir_info in download_dirs):
        return True
    
    # 从下载器获取种子列表（只获取打了标签的任务）
    torrents: Optional[List[TransferTorrent]] = self.list_torrents(
        status=TorrentStatus.TRANSFER,
        tags=settings.TORRENT_TAG  # 只查询打了标签的任务
    )
    
    for torrent in torrents:
        # 检查是否为下载器监控目录中的文件
        is_downloader_monitor = False
        for dir_info in download_dirs:
            if dir_info.monitor_type != "downloader":
                continue
            if file_path.is_relative_to(Path(dir_info.download_path)):
                is_downloader_monitor = True
                break
        
        if not is_downloader_monitor:
            continue
        
        # 执行整理
        self.do_transfer(...)
```

**特点**:
- ✅ 只监控MoviePilot添加的下载任务（通过标签过滤）
- ✅ 定时检查（每5分钟）
- ✅ 自动识别媒体信息（通过下载历史记录）
- ✅ 支持所有下载器（qBittorrent、Transmission等）

### 2. 目录监控 (`monitor_type: "directory"`)

**实现文件**: `MoviePilot-2/app/monitor.py`

**工作流程**:
1. 使用文件系统监控（watchdog）实时监测目录变化
2. 检测到新增或修改的文件时，自动触发整理
3. 不依赖下载器，适用于手动下载的文件

**特点**:
- ✅ 实时监控（文件系统事件触发）
- ✅ 不依赖下载器
- ✅ 适用于手动下载的文件
- ⚠️ 避免对网盘目录使用（容易触发大量API请求）

### 3. 手动整理 (`monitor_type: null` 且 `transfer_type` 不为空)

**实现文件**: `MoviePilot-2/app/chain/transfer.py`

**工作流程**:
1. 用户在WebUI中手动选择文件或目录
2. 调用手动整理API
3. 执行文件整理（根据 `transfer_type`）

**特点**:
- ✅ 用户主动触发
- ✅ 支持批量整理
- ✅ 支持复杂条件筛选

### 4. 不整理 (`monitor_type: null` 且 `transfer_type` 为空)

**特点**:
- ❌ 不自动整理
- ❌ 不手动整理
- ✅ 仅作为下载目录使用

## 📊 模式对比

| 模式 | monitor_type | transfer_type | 触发方式 | 适用场景 |
|------|-------------|---------------|---------|---------|
| **下载器监控** | `"downloader"` | 必需 | 定时（5分钟） | MoviePilot自动下载的任务 |
| **目录监控** | `"directory"` | 必需 | 实时（文件系统事件） | 手动下载的文件 |
| **手动整理** | `null` | 必需 | 用户手动触发 | 需要用户干预的文件 |
| **不整理** | `null` | `null` | - | 仅作为下载目录 |

## 🎯 关键设计点

### 1. 标签过滤机制

**为什么需要标签？**
- 区分MoviePilot添加的下载任务和其他方式添加的任务
- 避免整理非MoviePilot管理的下载任务
- 提高监控效率（只查询相关任务）

**实现方式**:
- 添加任务时自动打标签
- 查询任务时过滤标签
- WebUI只显示打了标签的任务

### 2. 目录配置优先级

**匹配逻辑**:
1. 按 `priority` 排序
2. 匹配 `media_type` 和 `media_category`
3. 同盘优先（如果源目录和目标目录在同一磁盘）

### 3. 下载历史记录

**作用**:
- 存储下载任务的媒体信息（TMDB ID、豆瓣ID等）
- 用于下载器监控时的媒体识别
- 避免重复识别，提高效率

## 💡 VabHub实现建议

### 1. 标签机制

```python
# 配置
TORRENT_TAG: str = "VABHUB"  # 默认标签

# 添加下载任务时
tags = [random_tag, settings.TORRENT_TAG]

# 查询下载任务时
torrents = downloader.get_completed_torrents(tags=settings.TORRENT_TAG)
```

### 2. 目录配置模型

```python
class DirectoryConfig(BaseModel):
    """目录配置"""
    download_path: Optional[str] = None
    library_path: Optional[str] = None
    storage: str = "local"
    library_storage: str = "local"
    
    # 监控类型（决定文件操作模式）
    monitor_type: Optional[str] = None  # "downloader" | "directory" | null
    
    # 整理方式
    transfer_type: Optional[str] = None  # "copy" | "move" | "link" | "softlink"
    
    # 媒体类型
    media_type: Optional[str] = None
    media_category: Optional[str] = None
    
    priority: int = 0
```

### 3. 下载器监控实现

```python
async def monitor_downloader():
    """下载器监控（定时任务，每5分钟）"""
    # 获取下载器监控目录
    download_dirs = get_downloader_monitor_dirs()
    
    # 只查询打了标签的任务
    torrents = await downloader.get_completed_torrents(tags=TORRENT_TAG)
    
    for torrent in torrents:
        # 检查是否在下载器监控目录中
        if not is_in_downloader_monitor_dir(torrent.path, download_dirs):
            continue
        
        # 查询下载历史记录
        download_history = get_download_history(torrent.hash)
        
        # 执行整理
        await transfer_file(
            file_path=torrent.path,
            media_info=download_history.media_info,
            transfer_type=dir_config.transfer_type
        )
```

## 📝 总结

1. **标签机制是下载器监控的核心**：
   - MoviePilot通过标签区分自己添加的下载任务
   - 只监控打了标签的任务，避免整理其他任务
   - WebUI也只显示打了标签的任务

2. **目录配置决定文件操作模式**：
   - `monitor_type` 决定监控方式（下载器监控/目录监控/不监控）
   - `transfer_type` 决定整理方式（复制/移动/硬链接/软链接）

3. **下载历史记录提高效率**：
   - 存储媒体信息，避免重复识别
   - 下载器监控时直接使用历史记录中的媒体信息

4. **VabHub应该实现类似的机制**：
   - 添加下载任务时自动打标签
   - 查询下载任务时过滤标签
   - 目录配置支持多种监控模式
   - 下载历史记录存储媒体信息

