# 视频字幕列表API在302跳转STRM中的应用分析

## 📋 概述

本文档分析"视频字幕列表"API（`get_video_subtitle_list`）在302跳转STRM系统中的重要作用，特别是对于**外网直接播放115网盘视频**场景下的字幕处理。

## 🎯 302跳转STRM的工作原理

### 1. 工作流程

```
用户播放STRM文件
    ↓
媒体服务器（Plex/Jellyfin/Emby）请求STRM文件中的URL
    ↓
STRM文件内容：http://your-nas:8000/api/strm/redirect/{token}
    ↓
重定向服务器（VabHub）接收请求
    ↓
302跳转到115网盘实际下载地址
    ↓
媒体服务器从115网盘直接流式播放视频
    ↓
用户在外网直接观看，无需本地NAS下载和上传
```

### 2. 核心优势

- ✅ **无需本地存储**：视频文件存储在115网盘，不占用本地NAS空间
- ✅ **外网直接播放**：通过302跳转，用户可以从外网直接播放115网盘中的视频
- ✅ **自动更新**：115网盘文件更新后，STRM文件可以自动同步
- ✅ **多设备访问**：任何设备都可以通过媒体服务器播放，无需下载

## 🔍 视频字幕列表API的作用

### 1. API功能

**API方法**: `get_video_subtitle_list(pick_code: str)`

**功能**：
- 根据视频文件的`pick_code`获取该视频的所有字幕列表
- 返回内嵌字幕（autoload）和用户上传的外挂字幕
- 提供字幕的详细信息：语言、标题、URL、类型、SHA1、file_id、pick_code等

### 2. 返回数据结构

```python
{
    "success": True,
    "pick_code": "视频文件提取码",
    "autoload": {
        "sid": "字幕ID",
        "language": "语言",
        "title": "字幕标题",
        "url": "字幕文件地址",
        "type": "字幕文件类型"
    },
    "list": [
        {
            "sid": "字幕ID",
            "language": "语言",
            "title": "字幕标题",
            "url": "字幕文件地址",
            "type": "字幕文件类型",
            "sha1": "字幕文件哈希值",
            "file_id": "字幕文件ID",
            "file_name": "外挂字幕文件名",
            "pick_code": "外挂字幕文件提取码",
            "caption_map_id": "字幕映射ID",
            "is_caption_map": 0/1,
            "sync_time": "字幕同步时间"
        },
        ...
    ],
    "count": 字幕数量
}
```

## 💡 在302跳转STRM中的应用场景

### 场景1：自动发现115网盘中的字幕

**问题**：
- 视频文件上传到115网盘后，可能已经有字幕文件（内嵌字幕或用户上传的外挂字幕）
- 传统方式需要手动下载字幕文件到本地媒体库
- 对于外网播放场景，字幕文件也需要通过302跳转访问

**解决方案**：
```python
# 1. 生成STRM文件时，获取视频的字幕列表
video_pick_code = "视频文件的pick_code"
subtitle_result = await cloud_115_api.get_video_subtitle_list(video_pick_code)

if subtitle_result.get("success"):
    # 2. 获取所有字幕（包括内嵌字幕和外挂字幕）
    autoload_subtitle = subtitle_result.get("autoload")
    subtitle_list = subtitle_result.get("list", [])
    
    # 3. 为每个字幕生成STRM字幕文件
    for subtitle in subtitle_list:
        subtitle_pick_code = subtitle.get("pick_code")
        subtitle_language = subtitle.get("language")
        subtitle_url = subtitle.get("url")
        
        # 4. 生成字幕文件的302跳转URL
        subtitle_strm_url = f"http://your-nas:8000/api/strm/redirect/{subtitle_token}"
        
        # 5. 生成本地字幕STRM文件
        subtitle_strm_path = generate_subtitle_strm(
            media_info=media_info,
            language=subtitle_language,
            strm_url=subtitle_strm_url
        )
```

### 场景2：同步字幕文件到本地媒体库

**工作流程**：
```
1. 视频文件上传到115网盘
    ↓
2. 获取视频文件的pick_code
    ↓
3. 调用get_video_subtitle_list(pick_code)获取字幕列表
    ↓
4. 为每个字幕文件生成302跳转URL
    ↓
5. 生成本地字幕STRM文件（.srt.strm或.ass.strm）
    ↓
6. 媒体服务器播放视频时，自动加载字幕STRM文件
    ↓
7. 字幕STRM文件302跳转到115网盘字幕文件
    ↓
8. 用户在外网播放时，自动显示字幕
```

### 场景3：字幕文件自动更新

**优势**：
- 115网盘中的字幕文件更新后，可以通过API自动发现
- 增量同步时，检查字幕文件是否有更新
- 自动更新本地字幕STRM文件

```python
# 增量同步字幕文件
async def sync_subtitles(video_pick_code: str, last_sync_time: datetime):
    # 1. 获取当前字幕列表
    subtitle_result = await cloud_115_api.get_video_subtitle_list(video_pick_code)
    
    if not subtitle_result.get("success"):
        return
    
    subtitle_list = subtitle_result.get("list", [])
    
    # 2. 检查每个字幕文件是否有更新
    for subtitle in subtitle_list:
        subtitle_sync_time = subtitle.get("sync_time")
        
        # 3. 如果字幕文件有更新，更新本地STRM文件
        if subtitle_sync_time > last_sync_time:
            update_subtitle_strm(subtitle)
```

### 场景4：多语言字幕支持

**功能**：
- 115网盘中的视频可能有多个语言的字幕（中文、英文、日文等）
- 通过API可以获取所有语言的字幕
- 为每个语言生成对应的字幕STRM文件
- 媒体服务器可以根据用户偏好自动选择字幕

```python
# 生成多语言字幕STRM文件
async def generate_multi_language_subtitles(video_pick_code: str, media_info: Dict):
    subtitle_result = await cloud_115_api.get_video_subtitle_list(video_pick_code)
    
    if not subtitle_result.get("success"):
        return
    
    subtitle_list = subtitle_result.get("list", [])
    
    # 按语言分组
    subtitles_by_language = {}
    for subtitle in subtitle_list:
        language = subtitle.get("language", "unknown")
        if language not in subtitles_by_language:
            subtitles_by_language[language] = []
        subtitles_by_language[language].append(subtitle)
    
    # 为每个语言生成字幕STRM文件
    for language, subtitles in subtitles_by_language.items():
        # 选择最佳字幕（通常选择第一个或根据优先级）
        best_subtitle = subtitles[0]
        
        # 生成字幕STRM文件
        generate_subtitle_strm(
            media_info=media_info,
            language=language,
            subtitle=best_subtitle
        )
```

## 🔧 实现建议

### 1. 集成到STRM生成流程

**修改 `STRMGenerator.generate_strm_file` 方法**：

```python
async def generate_strm_file(
    self,
    media_info: Dict[str, Any],
    cloud_file_id: str,
    cloud_storage: str,
    cloud_path: str,
    cloud_115_api: Optional[Cloud115API] = None,  # 新增参数
    subtitle_files: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    生成STRM文件，包括视频STRM和字幕STRM
    """
    # 1. 生成视频STRM文件
    strm_path = await self._generate_strm(...)
    
    # 2. 如果提供了115 API客户端，自动获取字幕列表
    subtitle_strm_paths = []
    if cloud_115_api and cloud_storage == "115":
        # 获取视频文件的pick_code
        video_pick_code = await self._get_video_pick_code(cloud_file_id, cloud_115_api)
        
        if video_pick_code:
            # 获取字幕列表
            subtitle_result = await cloud_115_api.get_video_subtitle_list(video_pick_code)
            
            if subtitle_result.get("success"):
                # 生成字幕STRM文件
                subtitle_strm_paths = await self._generate_subtitle_strm_files(
                    media_info=media_info,
                    subtitle_result=subtitle_result,
                    local_path=local_path
                )
    
    # 3. 如果提供了本地字幕文件，也生成字幕STRM
    if subtitle_files:
        local_subtitle_strm_paths = await self._generate_local_subtitle_strm_files(
            subtitle_files=subtitle_files,
            media_info=media_info,
            local_path=local_path
        )
        subtitle_strm_paths.extend(local_subtitle_strm_paths)
    
    return {
        'strm_path': strm_path,
        'subtitle_strm_paths': subtitle_strm_paths,
        'nfo_path': nfo_path
    }
```

### 2. 字幕STRM文件生成

**新增方法 `_generate_subtitle_strm_files`**：

```python
async def _generate_subtitle_strm_files(
    self,
    media_info: Dict[str, Any],
    subtitle_result: Dict[str, Any],
    local_path: Path
) -> List[str]:
    """
    生成字幕STRM文件
    """
    subtitle_strm_paths = []
    
    # 获取字幕列表
    autoload_subtitle = subtitle_result.get("autoload")
    subtitle_list = subtitle_result.get("list", [])
    
    # 处理自动载入字幕
    if autoload_subtitle:
        subtitle_strm_path = await self._generate_single_subtitle_strm(
            media_info=media_info,
            subtitle=autoload_subtitle,
            local_path=local_path,
            is_autoload=True
        )
        if subtitle_strm_path:
            subtitle_strm_paths.append(subtitle_strm_path)
    
    # 处理外挂字幕
    for subtitle in subtitle_list:
        subtitle_strm_path = await self._generate_single_subtitle_strm(
            media_info=media_info,
            subtitle=subtitle,
            local_path=local_path,
            is_autoload=False
        )
        if subtitle_strm_path:
            subtitle_strm_paths.append(subtitle_strm_path)
    
    return subtitle_strm_paths

async def _generate_single_subtitle_strm(
    self,
    media_info: Dict[str, Any],
    subtitle: Dict[str, Any],
    local_path: Path,
    is_autoload: bool
) -> Optional[str]:
    """
    生成单个字幕STRM文件
    """
    # 1. 获取字幕信息
    subtitle_language = subtitle.get("language", "chi")
    subtitle_type = subtitle.get("type", "srt")  # srt, ass, vtt等
    subtitle_pick_code = subtitle.get("pick_code")
    
    # 2. 生成字幕文件名
    media_name = self._get_media_name(media_info)
    subtitle_filename = f"{media_name}.{subtitle_language}.{subtitle_type}.strm"
    subtitle_strm_path = local_path / subtitle_filename
    
    # 3. 生成302跳转URL
    # 使用JWT token或加密token保护字幕文件访问
    subtitle_token = self._generate_subtitle_token(
        pick_code=subtitle_pick_code,
        file_id=subtitle.get("file_id"),
        language=subtitle_language
    )
    subtitle_strm_url = f"{self.config.redirect_server_url}{self.config.redirect_server_base_path}/{subtitle_token}"
    
    # 4. 写入STRM文件
    subtitle_strm_path.parent.mkdir(parents=True, exist_ok=True)
    with open(subtitle_strm_path, 'w', encoding='utf-8') as f:
        f.write(subtitle_strm_url)
    
    logger.info(f"生成字幕STRM文件: {subtitle_strm_path} -> {subtitle_strm_url}")
    return str(subtitle_strm_path)
```

### 3. 字幕重定向服务器

**在重定向服务器中添加字幕文件支持**：

```python
# 在 STRMRedirectServer 中添加字幕文件处理
async def handle_subtitle_redirect(self, request: Request) -> Response:
    """
    处理字幕文件302跳转
    """
    token = request.match_info["token"]
    
    # 验证token
    payload = self.token_manager.verify_token(token)
    if not payload:
        return Response(status=401, text="Invalid token")
    
    # 获取字幕文件信息
    subtitle_pick_code = payload.get("pick_code")
    subtitle_file_id = payload.get("file_id")
    
    # 获取字幕文件下载地址
    download_url = await self._get_subtitle_download_url(
        pick_code=subtitle_pick_code,
        file_id=subtitle_file_id
    )
    
    if not download_url:
        return Response(status=404, text="Subtitle not found")
    
    # 302跳转到字幕文件下载地址
    return Response(
        status=302,
        headers={"Location": download_url}
    )
```

## 📊 优势总结

### 1. 自动化字幕发现

- ✅ **自动发现**：无需手动查找和下载字幕文件
- ✅ **多语言支持**：自动获取所有可用语言的字幕
- ✅ **实时更新**：115网盘字幕更新后自动同步

### 2. 外网播放支持

- ✅ **302跳转**：字幕文件也通过302跳转访问，支持外网播放
- ✅ **无需本地存储**：字幕文件不占用本地NAS空间
- ✅ **自动加载**：媒体服务器自动加载字幕STRM文件

### 3. 完整的字幕管理

- ✅ **内嵌字幕支持**：支持115网盘自动识别的内嵌字幕
- ✅ **外挂字幕支持**：支持用户上传的外挂字幕文件
- ✅ **字幕元数据**：保存字幕的语言、类型、SHA1等元数据

### 4. 与媒体服务器集成

- ✅ **标准格式**：生成标准格式的字幕STRM文件
- ✅ **自动识别**：媒体服务器自动识别和加载字幕
- ✅ **多语言切换**：用户可以在媒体服务器中切换不同语言的字幕

## 🎯 结论

**视频字幕列表API对302跳转STRM非常有用**，主要体现在：

1. **自动化字幕发现**：自动获取115网盘中的字幕文件，无需手动处理
2. **外网播放支持**：字幕文件也通过302跳转访问，支持外网播放
3. **多语言支持**：自动获取和生成多语言字幕STRM文件
4. **实时同步**：115网盘字幕更新后自动同步到本地媒体库
5. **完整集成**：与STRM生成流程完整集成，提供端到端的字幕管理

**建议**：
- ✅ 在STRM生成流程中集成视频字幕列表API
- ✅ 为每个字幕文件生成对应的字幕STRM文件
- ✅ 在重定向服务器中添加字幕文件302跳转支持
- ✅ 在增量同步时检查字幕文件更新
- ✅ 保存字幕元数据到数据库，便于管理和查询

这样，用户就可以在外网直接播放115网盘中的视频，并自动加载对应的字幕文件，提供完整的媒体播放体验。

