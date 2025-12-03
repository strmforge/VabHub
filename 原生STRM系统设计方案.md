# 原生STRM系统设计方案

## 📋 设计理念

**系统原生集成STRM，提供完整的自动化工作流，比第三方插件更强大、更智能。**

### 核心优势
1. ✅ **完整工作流**：从下载到STRM生成的端到端自动化
2. ✅ **智能文件管理**：支持复制/移动，保留做种或清理空间
3. ✅ **字幕同步处理**：自动上传和生成字幕文件
4. ✅ **多媒体服务器支持**：Plex、Jellyfin、Emby
5. ✅ **灵活配置**：可选的网盘刮削、STRM生成、媒体库刷新
6. ✅ **增量更新**：文件树管理和增量STRM生成

## 🎯 完整工作流程

```
1. 下载完成
   ↓
2. 文件识别和重命名
   ├── 识别媒体信息（TMDB/豆瓣）
   ├── 重命名文件
   └── 分类整理
   ↓
3. 字幕处理（如果有）
   ├── 识别字幕文件
   ├── 重命名字幕文件
   └── 准备上传
   ↓
4. 上传到网盘
   ├── 选择上传模式（复制/移动）
   ├── 上传媒体文件
   ├── 上传字幕文件
   └── 网盘内重命名和分类
   ↓
5. 网盘刮削（可选）
   ├── 在网盘进行元数据刮削
   └── 更新网盘文件信息
   ↓
6. 生成STRM文件到本地媒体库
   ├── 对应网盘目录结构
   ├── 生成STRM文件
   ├── 生成字幕文件（如果有）
   └── 生成NFO文件（元数据）
   ↓
7. 本地刮削
   ├── 对STRM文件进行元数据刮削
   └── 下载海报、剧照等
   ↓
8. 通知媒体服务器刷新
   ├── Plex刷新
   ├── Jellyfin刷新
   └── Emby刷新
   ↓
9. 清理本地文件（如果选择移动模式）
   ├── 删除已上传的源文件
   └── 删除空文件夹
```

## 📁 系统架构

### 1. 核心模块

```
backend/app/modules/strm/
├── __init__.py
├── generator.py              # STRM文件生成器
├── workflow.py               # STRM工作流管理器
├── uploader.py               # 文件上传管理器
├── subtitle_handler.py       # 字幕文件处理器
├── scraper.py                # 元数据刮削器（本地/网盘）
├── media_server_notifier.py  # 媒体服务器通知器
├── file_tree_manager.py      # 文件树管理器
└── config.py                 # STRM配置管理
```

### 2. 数据模型

```python
# backend/app/models/strm.py

class STRMWorkflowTask(Base):
    """STRM工作流任务"""
    id: int
    download_task_id: int          # 关联的下载任务ID
    media_file_path: str           # 本地媒体文件路径
    subtitle_files: List[str]      # 字幕文件列表
    upload_mode: str               # 上传模式：copy/move
    cloud_storage: str             # 云存储类型：115/123
    cloud_path: str                # 云存储路径
    strm_path: str                 # STRM文件路径
    status: str                    # 任务状态
    progress: float                # 进度（0-100）
    metadata: Dict                 # 媒体元数据
    created_at: datetime
    updated_at: datetime

class STRMFile(Base):
    """STRM文件记录"""
    id: int
    media_file_id: int             # 关联的媒体文件ID
    strm_path: str                 # STRM文件路径
    cloud_file_id: str             # 云存储文件ID
    cloud_storage: str             # 云存储类型
    media_type: str                # 媒体类型：movie/tv
    title: str                     # 标题
    year: int                      # 年份
    season: int                    # 季（电视剧）
    episode: int                   # 集（电视剧）
    subtitle_files: List[str]      # 字幕文件列表
    nfo_path: str                  # NFO文件路径
    created_at: datetime
    updated_at: datetime

class STRMFileTree(Base):
    """STRM文件树记录"""
    id: int
    path: str                      # 文件路径（唯一）
    file_id: int                   # 文件ID
    parent_id: int                 # 父目录ID
    file_name: str                 # 文件名
    file_type: str                 # 文件类型：file/folder
    file_size: BigInteger          # 文件大小
    sha1: str                      # 文件SHA1
    cloud_file_id: str             # 云存储文件ID
    cloud_storage: str             # 云存储类型
    update_time: BigInteger        # 更新时间
    create_time: BigInteger        # 创建时间

class STRMLifeEvent(Base):
    """STRM生命周期事件"""
    id: int
    type: int                      # 事件类型：1-创建，2-更新，3-删除
    file_id: int                   # 文件ID
    parent_id: int                 # 父目录ID
    file_name: str                 # 文件名
    file_category: int             # 文件分类
    file_type: int                 # 文件类型
    file_size: BigInteger          # 文件大小
    sha1: str                      # 文件SHA1
    pick_code: str                 # 云存储pick_code
    update_time: BigInteger        # 更新时间
    create_time: BigInteger        # 创建时间
```

## 🔧 核心功能实现

### 1. STRM文件生成器

```python
# backend/app/modules/strm/generator.py

class STRMGenerator:
    """STRM文件生成器"""
    
    def __init__(self, config: STRMConfig):
        self.config = config
        self.media_library_path = config.media_library_path
        self.cloud_storage_mapping = config.cloud_storage_mapping
    
    async def generate_strm_file(
        self,
        media_info: Dict[str, Any],
        cloud_file_id: str,
        cloud_storage: str,
        cloud_path: str,
        subtitle_files: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        生成STRM文件
        
        Args:
            media_info: 媒体信息
            cloud_file_id: 云存储文件ID
            cloud_storage: 云存储类型（115/123）
            cloud_path: 云存储路径
            subtitle_files: 字幕文件列表
        
        Returns:
            生成的文件路径字典
        """
        # 1. 构建本地媒体库路径（对应网盘目录结构）
        local_path = self._build_local_path(media_info, cloud_path)
        
        # 2. 生成STRM文件
        strm_path = await self._generate_strm(
            local_path, cloud_file_id, cloud_storage, media_info
        )
        
        # 3. 生成字幕文件（如果有）
        subtitle_paths = []
        if subtitle_files:
            subtitle_paths = await self._generate_subtitle_files(
                local_path, subtitle_files, media_info
            )
        
        # 4. 生成NFO文件
        nfo_path = await self._generate_nfo(local_path, media_info)
        
        return {
            'strm_path': strm_path,
            'subtitle_paths': subtitle_paths,
            'nfo_path': nfo_path
        }
    
    def _build_local_path(
        self,
        media_info: Dict[str, Any],
        cloud_path: str
    ) -> Path:
        """构建本地媒体库路径（对应网盘目录结构）"""
        # 根据云存储路径映射到本地媒体库路径
        # 例如：/115/电影/xxx (2023)/xxx (2023).mkv
        # 映射到：/media_library/Movies/xxx (2023)/xxx (2023).strm
        
        media_type = media_info.get('type')
        if media_type == 'movie':
            base_path = Path(self.media_library_path) / 'Movies'
        elif media_type == 'tv':
            base_path = Path(self.media_library_path) / 'TV Shows'
        else:
            base_path = Path(self.media_library_path) / 'Other'
        
        # 从云存储路径提取相对路径
        # 例如：/115/电影/xxx (2023)/xxx (2023).mkv
        # 提取：电影/xxx (2023)/
        relative_path = self._extract_relative_path(cloud_path)
        
        return base_path / relative_path
```

### 2. 文件上传管理器

```python
# backend/app/modules/strm/uploader.py

class FileUploader:
    """文件上传管理器"""
    
    def __init__(self, config: STRMConfig):
        self.config = config
        self.cloud_clients = {}  # 云存储客户端
    
    async def upload_media_file(
        self,
        local_file_path: str,
        cloud_storage: str,
        cloud_target_path: str,
        upload_mode: str = 'copy',  # copy/move
        rename_file: bool = True,
        organize_by_type: bool = True
    ) -> Dict[str, Any]:
        """
        上传媒体文件到网盘
        
        Args:
            local_file_path: 本地文件路径
            cloud_storage: 云存储类型（115/123）
            cloud_target_path: 云存储目标路径
            upload_mode: 上传模式（copy/move）
            rename_file: 是否重命名文件
            organize_by_type: 是否按类型组织
        
        Returns:
            上传结果
        """
        # 1. 识别媒体文件
        media_info = await self._identify_media(local_file_path)
        
        # 2. 重命名文件（如果需要）
        if rename_file:
            new_name = self._generate_cloud_filename(media_info)
            cloud_target_path = f"{cloud_target_path}/{new_name}"
        
        # 3. 上传文件
        upload_result = await self._upload_file(
            local_file_path, cloud_storage, cloud_target_path
        )
        
        # 4. 处理上传模式
        if upload_mode == 'move':
            # 移动模式：上传完成后删除本地文件
            await self._delete_local_file(local_file_path)
            # 删除空文件夹
            await self._cleanup_empty_folders(local_file_path)
        # copy模式：保留本地文件，可以继续做种
        
        return {
            'success': True,
            'cloud_file_id': upload_result['file_id'],
            'cloud_path': upload_result['path'],
            'media_info': media_info
        }
    
    async def upload_with_subtitles(
        self,
        media_file_path: str,
        subtitle_files: List[str],
        cloud_storage: str,
        cloud_target_path: str,
        upload_mode: str = 'copy'
    ) -> Dict[str, Any]:
        """
        上传媒体文件和字幕文件
        
        Args:
            media_file_path: 媒体文件路径
            subtitle_files: 字幕文件列表
            cloud_storage: 云存储类型
            cloud_target_path: 云存储目标路径
            upload_mode: 上传模式
        
        Returns:
            上传结果
        """
        # 1. 上传媒体文件
        media_result = await self.upload_media_file(
            media_file_path, cloud_storage, cloud_target_path, upload_mode
        )
        
        # 2. 上传字幕文件
        subtitle_results = []
        for subtitle_file in subtitle_files:
            # 重命名字幕文件（匹配媒体文件名）
            subtitle_name = self._generate_subtitle_name(
                media_result['media_info'], subtitle_file
            )
            subtitle_path = f"{cloud_target_path}/{subtitle_name}"
            
            subtitle_result = await self._upload_file(
                subtitle_file, cloud_storage, subtitle_path
            )
            subtitle_results.append(subtitle_result)
            
            # 处理上传模式
            if upload_mode == 'move':
                await self._delete_local_file(subtitle_file)
        
        return {
            'media': media_result,
            'subtitles': subtitle_results
        }
```

### 3. 字幕文件处理器

```python
# backend/app/modules/strm/subtitle_handler.py

class SubtitleHandler:
    """字幕文件处理器"""
    
    async def find_subtitle_files(
        self,
        media_file_path: str
    ) -> List[str]:
        """
        查找媒体文件关联的字幕文件
        
        Args:
            media_file_path: 媒体文件路径
        
        Returns:
            字幕文件列表
        """
        media_path = Path(media_file_path)
        media_dir = media_path.parent
        media_stem = media_path.stem
        
        # 查找同名的字幕文件
        subtitle_extensions = ['.srt', '.ass', '.ssa', '.vtt']
        subtitle_files = []
        
        for ext in subtitle_extensions:
            # 精确匹配：movie.srt
            subtitle_path = media_dir / f"{media_stem}{ext}"
            if subtitle_path.exists():
                subtitle_files.append(str(subtitle_path))
            
            # 语言匹配：movie.chi.zh-cn.srt
            for lang_code in ['chi', 'eng', 'zh-cn', 'en']:
                subtitle_path = media_dir / f"{media_stem}.{lang_code}{ext}"
                if subtitle_path.exists():
                    subtitle_files.append(str(subtitle_path))
        
        return subtitle_files
    
    def generate_subtitle_name(
        self,
        media_info: Dict[str, Any],
        subtitle_file: str,
        language: str = 'chi'
    ) -> str:
        """
        生成字幕文件名（匹配媒体文件名）
        
        Args:
            media_info: 媒体信息
            subtitle_file: 字幕文件路径
            language: 语言代码
        
        Returns:
            新的字幕文件名
        """
        media_type = media_info.get('type')
        
        if media_type == 'movie':
            # 电影：Title (Year).chi.srt
            base_name = f"{media_info['title']} ({media_info.get('year', '')})"
        elif media_type == 'tv':
            # 电视剧：Title - S01E01.chi.srt
            base_name = f"{media_info['title']} - S{media_info.get('season', 1):02d}E{media_info.get('episode', 1):02d}"
        else:
            base_name = media_info.get('title', 'unknown')
        
        # 获取字幕文件扩展名
        subtitle_ext = Path(subtitle_file).suffix
        
        return f"{base_name}.{language}{subtitle_ext}"
    
    async def generate_subtitle_strm(
        self,
        strm_path: str,
        subtitle_files: List[str],
        media_info: Dict[str, Any]
    ) -> List[str]:
        """
        生成字幕文件到STRM目录
        
        Args:
            strm_path: STRM文件路径
            subtitle_files: 字幕文件列表（云存储路径）
            media_info: 媒体信息
        
        Returns:
            生成的字幕文件路径列表
        """
        strm_dir = Path(strm_path).parent
        subtitle_paths = []
        
        for subtitle_file in subtitle_files:
            # 从云存储路径提取文件名
            subtitle_name = Path(subtitle_file).name
            
            # 生成本地字幕文件路径
            local_subtitle_path = strm_dir / subtitle_name
            
            # 创建字幕文件（指向云存储）
            # 注意：字幕文件通常是直接下载，不是STRM格式
            # 但我们可以创建软链接或复制
            subtitle_paths.append(str(local_subtitle_path))
        
        return subtitle_paths
```

### 4. STRM工作流管理器

```python
# backend/app/modules/strm/workflow.py

class STRMWorkflowManager:
    """STRM工作流管理器"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.uploader = FileUploader()
        self.generator = STRMGenerator()
        self.subtitle_handler = SubtitleHandler()
        self.scraper = MediaScraper()
        self.notifier = MediaServerNotifier()
    
    async def process_download_complete(
        self,
        download_task_id: int,
        media_file_path: str,
        config: STRMWorkflowConfig
    ) -> STRMWorkflowTask:
        """
        处理下载完成的工作流
        
        Args:
            download_task_id: 下载任务ID
            media_file_path: 媒体文件路径
            config: 工作流配置
        
        Returns:
            STRM工作流任务
        """
        # 1. 创建工作任务
        task = STRMWorkflowTask(
            download_task_id=download_task_id,
            media_file_path=media_file_path,
            upload_mode=config.upload_mode,
            cloud_storage=config.cloud_storage,
            status='pending'
        )
        self.db.add(task)
        await self.db.commit()
        
        try:
            # 2. 文件识别和重命名
            task.status = 'identifying'
            task.progress = 10
            await self.db.commit()
            
            media_info = await self._identify_media(media_file_path)
            task.metadata = media_info
            
            # 3. 查找字幕文件
            task.status = 'finding_subtitles'
            task.progress = 20
            await self.db.commit()
            
            subtitle_files = await self.subtitle_handler.find_subtitle_files(
                media_file_path
            )
            task.subtitle_files = subtitle_files
            
            # 4. 上传到网盘
            task.status = 'uploading'
            task.progress = 30
            await self.db.commit()
            
            upload_result = await self.uploader.upload_with_subtitles(
                media_file_path=media_file_path,
                subtitle_files=subtitle_files,
                cloud_storage=config.cloud_storage,
                cloud_target_path=config.cloud_target_path,
                upload_mode=config.upload_mode
            )
            task.cloud_path = upload_result['media']['cloud_path']
            
            # 5. 网盘刮削（可选）
            if config.scrape_on_cloud:
                task.status = 'scraping_cloud'
                task.progress = 50
                await self.db.commit()
                
                await self.scraper.scrape_cloud_file(
                    cloud_storage=config.cloud_storage,
                    cloud_file_id=upload_result['media']['cloud_file_id'],
                    media_info=media_info
                )
            
            # 6. 生成STRM文件
            task.status = 'generating_strm'
            task.progress = 60
            await self.db.commit()
            
            strm_result = await self.generator.generate_strm_file(
                media_info=media_info,
                cloud_file_id=upload_result['media']['cloud_file_id'],
                cloud_storage=config.cloud_storage,
                cloud_path=upload_result['media']['cloud_path'],
                subtitle_files=subtitle_files
            )
            task.strm_path = strm_result['strm_path']
            
            # 7. 本地刮削
            task.status = 'scraping_local'
            task.progress = 80
            await self.db.commit()
            
            await self.scraper.scrape_local_strm(
                strm_path=strm_result['strm_path'],
                media_info=media_info
            )
            
            # 8. 通知媒体服务器刷新
            task.status = 'refreshing_media_server'
            task.progress = 90
            await self.db.commit()
            
            await self.notifier.refresh_media_servers(
                media_servers=config.media_servers,  # ['plex', 'jellyfin', 'emby']
                strm_path=strm_result['strm_path'],
                media_info=media_info
            )
            
            # 9. 完成
            task.status = 'completed'
            task.progress = 100
            await self.db.commit()
            
            return task
            
        except Exception as e:
            task.status = 'failed'
            task.error_message = str(e)
            await self.db.commit()
            raise
```

### 5. 媒体服务器通知器

```python
# backend/app/modules/strm/media_server_notifier.py

class MediaServerNotifier:
    """媒体服务器通知器"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.plex_client = None
        self.jellyfin_client = None
        self.emby_client = None
    
    async def refresh_media_servers(
        self,
        media_servers: List[str],
        strm_path: str,
        media_info: Dict[str, Any]
    ):
        """
        通知媒体服务器刷新
        
        Args:
            media_servers: 媒体服务器列表（['plex', 'jellyfin', 'emby']）
            strm_path: STRM文件路径
            media_info: 媒体信息
        """
        tasks = []
        
        for server in media_servers:
            if server == 'plex':
                tasks.append(self._refresh_plex(strm_path, media_info))
            elif server == 'jellyfin':
                tasks.append(self._refresh_jellyfin(strm_path, media_info))
            elif server == 'emby':
                tasks.append(self._refresh_emby(strm_path, media_info))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _refresh_plex(self, strm_path: str, media_info: Dict[str, Any]):
        """刷新Plex媒体库"""
        from app.modules.media_server.plex_client import PlexClient
        
        # 获取Plex客户端
        plex_servers = await self._get_media_servers('plex')
        
        for server in plex_servers:
            client = PlexClient(server)
            # 刷新媒体库
            await client.refresh_library(strm_path)
    
    async def _refresh_jellyfin(self, strm_path: str, media_info: Dict[str, Any]):
        """刷新Jellyfin媒体库"""
        from app.modules.media_server.jellyfin_client import JellyfinClient
        
        # 获取Jellyfin客户端
        jellyfin_servers = await self._get_media_servers('jellyfin')
        
        for server in jellyfin_servers:
            client = JellyfinClient(server)
            # 刷新媒体库
            await client.refresh_library(strm_path)
    
    async def _refresh_emby(self, strm_path: str, media_info: Dict[str, Any]):
        """刷新Emby媒体库"""
        from app.modules.media_server.emby_client import EmbyClient
        
        # 获取Emby客户端
        emby_servers = await self._get_media_servers('emby')
        
        for server in emby_servers:
            client = EmbyClient(server)
            # 刷新媒体库
            await client.refresh_library(strm_path)
```

### 6. 文件树管理器

```python
# backend/app/modules/strm/file_tree_manager.py

class FileTreeManager:
    """文件树管理器（参考MoviePilot插件）"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def scan_cloud_storage(
        self,
        cloud_storage: str,
        root_path: str = '/'
    ) -> Dict[str, Any]:
        """
        扫描云存储文件树
        
        Args:
            cloud_storage: 云存储类型（115/123）
            root_path: 根路径
        
        Returns:
            文件树结构
        """
        # 1. 获取云存储客户端
        client = await self._get_cloud_client(cloud_storage)
        
        # 2. 递归扫描文件树
        file_tree = await self._scan_directory(client, root_path)
        
        # 3. 保存到数据库
        await self._save_file_tree(cloud_storage, file_tree)
        
        return file_tree
    
    async def compare_file_trees(
        self,
        cloud_storage: str,
        local_tree: Dict[str, Any],
        cloud_tree: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        对比本地和云存储文件树
        
        Args:
            cloud_storage: 云存储类型
            local_tree: 本地文件树
            cloud_tree: 云存储文件树
        
        Returns:
            差异结果：新增、更新、删除的文件列表
        """
        differences = {
            'added': [],      # 新增的文件
            'updated': [],    # 更新的文件
            'deleted': []     # 删除的文件
        }
        
        # 对比文件树
        local_files = self._flatten_tree(local_tree)
        cloud_files = self._flatten_tree(cloud_tree)
        
        local_file_map = {f['path']: f for f in local_files}
        cloud_file_map = {f['path']: f for f in cloud_files}
        
        # 找出新增和更新的文件
        for cloud_path, cloud_file in cloud_file_map.items():
            if cloud_path not in local_file_map:
                differences['added'].append(cloud_path)
            else:
                local_file = local_file_map[cloud_path]
                if cloud_file['sha1'] != local_file.get('sha1'):
                    differences['updated'].append(cloud_path)
        
        # 找出删除的文件
        for local_path in local_file_map:
            if local_path not in cloud_file_map:
                differences['deleted'].append(local_path)
        
        return differences
    
    async def incremental_generate_strm(
        self,
        cloud_storage: str,
        differences: Dict[str, List[str]],
        overwrite_mode: str = 'never'  # never/always/smart
    ) -> Dict[str, Any]:
        """
        增量生成STRM文件
        
        Args:
            cloud_storage: 云存储类型
            differences: 文件差异
            overwrite_mode: 覆盖模式
        
        Returns:
            生成结果
        """
        results = {
            'generated': [],
            'skipped': [],
            'failed': []
        }
        
        # 处理新增和更新的文件
        files_to_process = differences['added'] + differences['updated']
        
        for file_path in files_to_process:
            # 检查覆盖模式
            if overwrite_mode == 'never':
                # 检查STRM文件是否已存在
                strm_path = await self._get_strm_path(file_path)
                if strm_path and Path(strm_path).exists():
                    results['skipped'].append(file_path)
                    continue
            
            # 生成STRM文件
            try:
                strm_result = await self._generate_strm_for_file(
                    cloud_storage, file_path
                )
                results['generated'].append(file_path)
            except Exception as e:
                results['failed'].append({'path': file_path, 'error': str(e)})
        
        return results
```

## 🔧 配置模型

```python
# backend/app/modules/strm/config.py

class STRMWorkflowConfig(BaseModel):
    """STRM工作流配置"""
    # 上传配置
    upload_mode: str = 'copy'  # copy/move
    cloud_storage: str = '115'  # 115/123
    cloud_target_path: str = '/电影'  # 云存储目标路径
    rename_on_upload: bool = True  # 上传时重命名
    organize_by_type: bool = True  # 按类型组织
    
    # 字幕配置
    upload_subtitles: bool = True  # 上传字幕文件
    rename_subtitles: bool = True  # 重命名字幕文件
    generate_subtitle_files: bool = True  # 生成字幕文件到STRM目录
    
    # 刮削配置
    scrape_on_cloud: bool = False  # 在网盘进行刮削
    scrape_on_local: bool = True  # 在本地进行刮削
    
    # STRM生成配置
    generate_strm: bool = True  # 生成STRM文件
    generate_nfo: bool = True  # 生成NFO文件
    media_library_path: str = '/media_library'  # 本地媒体库路径
    map_cloud_path: bool = True  # 映射云存储路径到本地
    
    # 媒体服务器配置
    media_servers: List[str] = ['plex', 'jellyfin', 'emby']  # 媒体服务器列表
    auto_refresh: bool = True  # 自动刷新媒体库
    refresh_delay: int = 300  # 刷新延迟（秒）
    
    # 文件树配置
    enable_file_tree: bool = True  # 启用文件树管理
    enable_incremental: bool = True  # 启用增量更新
    overwrite_mode: str = 'never'  # 覆盖模式：never/always/smart
```

## 📊 API端点

### 1. 工作流API

```python
# backend/app/api/strm_workflow.py

@router.post("/workflow/start")
async def start_strm_workflow(
    download_task_id: int,
    config: STRMWorkflowConfig,
    db = Depends(get_db)
):
    """启动STRM工作流"""
    workflow_manager = STRMWorkflowManager(db)
    task = await workflow_manager.process_download_complete(
        download_task_id, media_file_path, config
    )
    return task

@router.get("/workflow/{task_id}")
async def get_workflow_task(
    task_id: int,
    db = Depends(get_db)
):
    """获取工作流任务状态"""
    # ...

@router.post("/workflow/{task_id}/cancel")
async def cancel_workflow_task(
    task_id: int,
    db = Depends(get_db)
):
    """取消工作流任务"""
    # ...
```

### 2. STRM生成API

```python
@router.post("/generate")
async def generate_strm_file(
    media_info: Dict[str, Any],
    cloud_file_id: str,
    cloud_storage: str,
    cloud_path: str,
    db = Depends(get_db)
):
    """生成STRM文件"""
    generator = STRMGenerator()
    result = await generator.generate_strm_file(
        media_info, cloud_file_id, cloud_storage, cloud_path
    )
    return result

@router.post("/batch-generate")
async def batch_generate_strm(
    file_list: List[Dict[str, Any]],
    db = Depends(get_db)
):
    """批量生成STRM文件"""
    # ...
```

### 3. 文件树API

```python
@router.post("/file-tree/scan")
async def scan_file_tree(
    cloud_storage: str,
    root_path: str = '/',
    db = Depends(get_db)
):
    """扫描云存储文件树"""
    tree_manager = FileTreeManager(db)
    file_tree = await tree_manager.scan_cloud_storage(cloud_storage, root_path)
    return file_tree

@router.post("/file-tree/incremental-generate")
async def incremental_generate_strm(
    cloud_storage: str,
    overwrite_mode: str = 'never',
    db = Depends(get_db)
):
    """增量生成STRM文件"""
    tree_manager = FileTreeManager(db)
    differences = await tree_manager.compare_file_trees(...)
    results = await tree_manager.incremental_generate_strm(
        cloud_storage, differences, overwrite_mode
    )
    return results
```

## 🎯 工作流程示例

### 示例1：下载完成后自动生成STRM

```python
# 1. 下载完成触发工作流
download_task = await download_service.get_task(download_task_id)
media_file_path = download_task.file_path

# 2. 配置工作流
config = STRMWorkflowConfig(
    upload_mode='copy',  # 复制模式，保留源文件做种
    cloud_storage='115',
    cloud_target_path='/电影',
    scrape_on_cloud=False,  # 不在网盘刮削
    scrape_on_local=True,  # 在本地刮削
    generate_strm=True,
    generate_nfo=True,
    media_servers=['plex', 'jellyfin'],  # 通知Plex和Jellyfin刷新
    auto_refresh=True
)

# 3. 启动工作流
workflow_manager = STRMWorkflowManager(db)
task = await workflow_manager.process_download_complete(
    download_task_id, media_file_path, config
)
```

### 示例2：移动模式（上传后删除本地文件）

```python
config = STRMWorkflowConfig(
    upload_mode='move',  # 移动模式，上传后删除本地文件
    cloud_storage='115',
    cloud_target_path='/电影',
    # ... 其他配置
)
```

### 示例3：网盘内复制/移动

```python
# 网盘内复制文件
await cloud_storage_service.copy_file(
    cloud_storage='115',
    source_path='/电影/xxx.mkv',
    target_path='/电影/备份/xxx.mkv',
    operation='copy'  # copy/move
)
```

## 🎉 系统优势总结

### 1. 完整工作流
- ✅ 从下载到STRM生成的端到端自动化
- ✅ 支持多种触发方式（下载完成、手动触发、定时任务）

### 2. 智能文件管理
- ✅ 支持复制/移动模式
- ✅ 保留做种或清理空间
- ✅ 自动清理空文件夹

### 3. 字幕同步处理
- ✅ 自动识别和上传字幕文件
- ✅ 重命名字幕文件匹配媒体文件
- ✅ 生成字幕文件到STRM目录

### 4. 多媒体服务器支持
- ✅ Plex、Jellyfin、Emby全支持
- ✅ 自动刷新媒体库
- ✅ 可配置刷新延迟

### 5. 灵活配置
- ✅ 可选的网盘刮削
- ✅ 可选的STRM生成
- ✅ 可选的媒体库刷新
- ✅ 可选的覆盖模式

### 6. 增量更新
- ✅ 文件树管理
- ✅ 增量STRM生成
- ✅ 生命周期追踪

### 7. 原生集成
- ✅ 系统原生功能，非插件
- ✅ 深度集成下载、上传、媒体管理
- ✅ 统一配置和管理

## 📋 实现优先级

### 高优先级（核心功能）
1. ✅ STRM文件生成器（基础功能）
2. ✅ 文件上传管理器（支持复制/移动）
3. ✅ 字幕文件处理器
4. ✅ STRM工作流管理器（完整流程）

### 中优先级（增强功能）
5. ✅ 媒体服务器通知器（Plex/Jellyfin/Emby）
6. ✅ 文件树管理器（增量更新）
7. ✅ 覆盖模式控制
8. ✅ 生命周期追踪

### 低优先级（高级功能）
9. ✅ 网盘刮削功能
10. ✅ 本地刮削优化
11. ✅ 网盘内复制/移动操作

