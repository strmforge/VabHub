# STRM 302跳转问题分析与解决方案

**问题时间**: 2025-01-XX  
**问题描述**: Emby通过302跳转播放时，字幕选择不生效，部分视频无声音

---

## 📋 一、问题分析

### 1.1 用户反馈

用户使用MoviePilot的mediawarp插件（302跳转）配合Emby播放时遇到：
1. **字幕选择不生效** - 明明有显示字幕选择，但选择后不生效
2. **部分视频无声音** - 有些视频播放时没有声音

### 1.2 根本原因

**302跳转的局限性**:
- ❌ **无法传递请求头** - 302跳转时，浏览器/客户端会重新发起请求，但不会传递原始请求的所有头信息
- ❌ **Range请求丢失** - 视频播放需要Range请求支持断点续传，302跳转后Range头可能丢失
- ❌ **Accept头丢失** - 客户端无法告诉服务器需要什么格式的音频/视频
- ❌ **User-Agent可能改变** - 某些服务器需要特定的User-Agent

**具体问题**:

1. **字幕问题**:
   - Emby播放STRM文件时，会在STRM文件所在目录查找字幕文件
   - 如果字幕文件没有正确下载到本地，Emby无法找到
   - 即使找到了，如果视频是通过302跳转播放的，字幕关联可能失效

2. **音频问题**:
   - 视频播放时，客户端会发送`Accept: video/mp4; codecs="avc1.42E01E, mp4a.40.2"`等头信息
   - 302跳转后，这些头信息可能丢失
   - 115网盘服务器可能返回不兼容的音频格式

3. **Range请求问题**:
   - 视频播放需要支持Range请求（`Range: bytes=0-1023`）
   - 302跳转后，Range头可能丢失
   - 导致视频无法正常播放或卡顿

---

## 📋 二、解决方案

### 方案1: 代理模式（推荐）⭐⭐⭐⭐⭐

**优势**:
- ✅ 完全控制请求头和响应
- ✅ 支持Range请求
- ✅ 支持所有HTTP头信息传递
- ✅ 可以添加缓存和错误处理

**实现**:
```python
@router.get("/stream/{storage_type}/{token}")
async def stream_file(
    storage_type: str,
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    代理流媒体请求（而不是302跳转）
    """
    # 1. 验证token并获取下载地址
    download_url = await get_download_url_from_token(token, storage_type, db)
    
    # 2. 构建请求头（传递原始请求的所有头信息）
    headers = {}
    if "range" in request.headers:
        headers["range"] = request.headers["range"]
    if "accept" in request.headers:
        headers["accept"] = request.headers["accept"]
    if "user-agent" in request.headers:
        headers["user-agent"] = request.headers["user-agent"]
    # ... 传递其他必要的头信息
    
    # 3. 代理请求
    async with httpx.AsyncClient() as client:
        response = await client.get(
            download_url,
            headers=headers,
            follow_redirects=True
        )
        
        # 4. 返回流式响应
        return StreamingResponse(
            response.iter_bytes(),
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type", "video/mp4")
        )
```

### 方案2: 改进302跳转（不推荐）⭐⭐

**问题**:
- ⚠️ 仍然无法完全控制请求头
- ⚠️ 某些客户端可能不支持
- ⚠️ 兼容性问题

**实现**:
```python
# 在302跳转时，尝试在URL中添加参数
# 但这不适用于所有情况
redirect_url = f"{download_url}?range={request.headers.get('range', '')}"
return RedirectResponse(url=redirect_url, status_code=302)
```

### 方案3: 混合模式（推荐）⭐⭐⭐⭐

**思路**:
- 默认使用代理模式（保证兼容性）
- 提供配置选项，允许用户选择302跳转模式（节省服务器资源）

**实现**:
```python
# 在STRM配置中添加
strm_url_mode: Literal["direct", "local_redirect", "proxy"] = "proxy"

# 根据配置选择模式
if config.strm_url_mode == "proxy":
    return await proxy_stream(...)
elif config.strm_url_mode == "local_redirect":
    return RedirectResponse(...)
else:
    return RedirectResponse(...)
```

---

## 📋 三、字幕问题解决方案

### 3.1 问题分析

**Emby字幕查找逻辑**:
1. 播放STRM文件时，Emby会在STRM文件所在目录查找字幕文件
2. 字幕文件名需要匹配视频文件名（如：`video.strm` -> `video.zh.srt`）
3. 如果字幕文件不在本地，Emby无法找到

### 3.2 解决方案

**确保字幕文件正确下载**:
```python
# 在STRM生成时，确保字幕文件下载到本地
async def _generate_subtitle_files(...):
    # 1. 从网盘下载字幕文件
    # 2. 保存到STRM文件同目录
    # 3. 确保文件名匹配
    local_subtitle_path = strm_dir / f"{video_name}.{language}.srt"
```

**字幕文件命名规则**:
- 视频文件: `Movie (2024).strm`
- 字幕文件: `Movie (2024).zh.srt` 或 `Movie (2024).en.srt`

---

## 📋 四、音频问题解决方案

### 4.1 问题分析

**可能原因**:
1. **音频格式不兼容** - 某些设备不支持DTS、TrueHD等格式
2. **Accept头丢失** - 302跳转后，客户端无法告诉服务器需要什么格式
3. **服务器返回错误格式** - 115网盘可能返回不兼容的音频格式

### 4.2 解决方案

**使用代理模式**:
- ✅ 传递Accept头，告诉服务器客户端支持的格式
- ✅ 可以添加音频转码（如果需要）
- ✅ 可以添加格式检测和警告

**实现**:
```python
# 在代理请求时，传递Accept头
headers = {
    "Accept": request.headers.get("accept", "video/mp4, audio/mp4"),
    "Range": request.headers.get("range", ""),
    "User-Agent": request.headers.get("user-agent", "VabHub/1.0")
}
```

---

## 📋 五、实现建议

### 5.1 优先级

1. **高优先级**: 实现代理模式
   - 解决Range请求问题
   - 解决请求头传递问题
   - 保证兼容性

2. **中优先级**: 改进字幕文件处理
   - 确保字幕文件正确下载
   - 确保文件名匹配
   - 添加字幕文件检测

3. **低优先级**: 添加配置选项
   - 允许用户选择代理/302模式
   - 添加性能监控
   - 添加错误日志

### 5.2 实现步骤

1. **修改STRM重定向端点** - 改为代理模式
2. **添加请求头传递** - 传递Range、Accept等关键头信息
3. **测试字幕功能** - 确保字幕文件正确下载和关联
4. **测试音频功能** - 确保音频格式兼容
5. **添加配置选项** - 允许用户选择模式

---

## 📋 六、代码实现

### 6.1 代理模式实现

```python
@router.get("/stream/{storage_type}/{token}")
async def stream_file(
    storage_type: str,
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    代理流媒体请求（支持Range请求和所有HTTP头）
    """
    try:
        # 1. 验证token并获取下载地址
        download_url = await get_download_url_from_token(token, storage_type, db)
        
        # 2. 构建请求头（传递原始请求的关键头信息）
        headers = {}
        
        # Range请求（关键！）
        if "range" in request.headers:
            headers["range"] = request.headers["range"]
        
        # Accept头（告诉服务器客户端支持的格式）
        if "accept" in request.headers:
            headers["accept"] = request.headers["accept"]
        else:
            headers["accept"] = "video/mp4, audio/mp4, */*"
        
        # User-Agent
        if "user-agent" in request.headers:
            headers["user-agent"] = request.headers["user-agent"]
        
        # Referer（某些服务器需要）
        if "referer" in request.headers:
            headers["referer"] = request.headers["referer"]
        
        # 3. 代理请求
        import httpx
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=True
        ) as client:
            response = await client.get(
                download_url,
                headers=headers
            )
            
            # 4. 构建响应头
            response_headers = {}
            
            # 传递关键响应头
            if "content-type" in response.headers:
                response_headers["content-type"] = response.headers["content-type"]
            if "content-length" in response.headers:
                response_headers["content-length"] = response.headers["content-length"]
            if "content-range" in response.headers:
                response_headers["content-range"] = response.headers["content-range"]
            if "accept-ranges" in response.headers:
                response_headers["accept-ranges"] = response.headers["accept-ranges"]
            
            # 5. 返回流式响应
            return StreamingResponse(
                response.iter_bytes(),
                status_code=response.status_code,
                headers=response_headers,
                media_type=response.headers.get("content-type", "video/mp4")
            )
            
    except Exception as e:
        logger.error(f"代理流媒体请求失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"代理请求失败: {str(e)}"
        )
```

### 6.2 字幕文件处理改进

```python
async def _generate_subtitle_files(
    self,
    local_path: Path,
    subtitle_files: List[str],
    media_info: Dict[str, Any],
    cloud_115_api: Optional[Any] = None
) -> List[str]:
    """
    生成字幕文件到STRM目录
    
    确保字幕文件：
    1. 下载到STRM文件同目录
    2. 文件名匹配视频文件名
    3. 支持多语言字幕
    """
    subtitle_paths = []
    strm_dir = local_path.parent
    video_name = local_path.stem  # 视频文件名（不含扩展名）
    
    for subtitle_file in subtitle_files:
        try:
            # 1. 提取pick_code
            pick_code = self._extract_pick_code_from_path(subtitle_file)
            if not pick_code:
                continue
            
            # 2. 确定字幕文件名
            # 尝试从原始文件名提取语言信息
            original_name = Path(subtitle_file).name
            language = self._extract_language_from_filename(original_name) or "zh"
            
            # 生成匹配的字幕文件名
            subtitle_ext = Path(original_name).suffix or ".srt"
            subtitle_name = f"{video_name}.{language}{subtitle_ext}"
            local_subtitle_path = strm_dir / subtitle_name
            
            # 3. 下载字幕文件
            success = await self._download_subtitle_from_cloud(
                cloud_115_api, pick_code, local_subtitle_path
            )
            
            if success:
                subtitle_paths.append(str(local_subtitle_path))
                logger.info(f"字幕文件下载成功: {local_subtitle_path}")
                
        except Exception as e:
            logger.error(f"处理字幕文件时出错: {e}")
            continue
    
    return subtitle_paths
```

---

## 📋 七、测试建议

### 7.1 功能测试

1. **Range请求测试**
   - 测试视频播放的断点续传
   - 测试快进/快退功能
   - 测试不同Range值

2. **字幕测试**
   - 测试字幕文件下载
   - 测试字幕文件关联
   - 测试多语言字幕

3. **音频测试**
   - 测试不同音频格式
   - 测试音频轨道选择
   - 测试无声音问题

### 7.2 兼容性测试

1. **Emby测试**
   - 测试Web端播放
   - 测试移动端播放
   - 测试字幕选择

2. **Plex测试**
   - 测试Web端播放
   - 测试客户端播放

3. **Jellyfin测试**
   - 测试Web端播放
   - 测试客户端播放

---

## 📋 八、总结

### 8.1 问题根源

- ❌ **302跳转无法传递请求头** - 导致Range、Accept等关键头信息丢失
- ❌ **字幕文件关联问题** - 字幕文件可能没有正确下载或命名
- ❌ **音频格式兼容性** - 某些格式可能不兼容

### 8.2 解决方案

- ✅ **使用代理模式** - 完全控制请求头和响应
- ✅ **改进字幕处理** - 确保字幕文件正确下载和命名
- ✅ **传递关键头信息** - Range、Accept、User-Agent等

### 8.3 实现优先级

1. **高优先级**: 实现代理模式（解决核心问题）
2. **中优先级**: 改进字幕文件处理
3. **低优先级**: 添加配置选项和性能优化

---

**文档生成时间**: 2025-01-XX  
**建议**: 优先实现代理模式，这是解决字幕和音频问题的关键

