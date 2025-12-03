# STRM字幕从115网盘检测实现总结

**更新时间**: 2025-01-XX  
**功能**: 从115网盘检测字幕，同时支持本地播放和外网播放

---

## 📋 一、问题背景

### 1.1 用户需求

**问题**:
- 外出播放时，视频从115网盘直接播放（通过STRM 302跳转或代理）
- 如果字幕文件只保存在本地NAS，外网播放时无法访问
- 导致：有字幕选择但无法加载的问题

**需求**:
- **本地播放**：使用本地NAS中的字幕文件（快速、可靠）
- **外网播放**：从115网盘实时获取字幕（不需要访问本地NAS）

### 1.2 解决方案

**双重策略**:
1. **下载字幕到本地** - 供本地播放使用
2. **记录115网盘字幕信息** - 供外网播放时通过API获取

---

## 📋 二、实现方案

### 2.1 配置选项

**新增配置**: `detect_subtitles_from_cloud`

```python
detect_subtitles_from_cloud: bool = Field(
    default=True,
    description="是否从115网盘检测字幕（推荐开启，外网播放时字幕可用）。如果开启，系统会：1) 下载字幕到本地STRM目录（供本地播放使用），2) 同时记录115网盘字幕信息（供外网播放时通过API获取）"
)
```

### 2.2 工作流程

**生成STRM文件时**:

1. **从115网盘检测字幕**:
   - 调用 `get_video_subtitle_list(pick_code)` 获取视频字幕列表
   - 提取字幕信息（pick_code、language、file_name等）

2. **下载字幕到本地**:
   - 使用字幕的pick_code下载字幕文件
   - 保存到本地STRM目录（与STRM文件同目录）
   - 供本地播放使用

3. **记录115网盘字幕信息**:
   - 将字幕信息（pick_code、language等）保存到数据库
   - 供外网播放时通过API获取

### 2.3 API端点

**字幕API端点**: `/api/strm/subtitle/{storage_type}/{token}`

**功能**:
- 根据JWT token中的`subtitle_pick_code`获取115网盘字幕下载地址
- 支持302跳转或代理模式
- 供外网播放时使用

**使用方式**:
```
GET /api/strm/subtitle/115/{token}
```

**Token内容**:
```json
{
  "subtitle_pick_code": "cg16zx93h3xy6ddf1",
  "storage_type": "115",
  "exp": 1234567890
}
```

---

## 📋 三、代码实现

### 3.1 字幕检测方法

**`_detect_subtitles_from_115`**:
```python
async def _detect_subtitles_from_115(
    self,
    video_pick_code: str,
    cloud_115_api: Any
) -> List[Dict[str, Any]]:
    """
    从115网盘检测视频字幕列表
    
    Returns:
        字幕信息列表，每个字幕包含：
        - pick_code: 字幕文件pick_code
        - language: 语言
        - title: 字幕标题
        - file_name: 文件名
        - url: 字幕文件地址（如果有）
    """
```

**流程**:
1. 调用 `cloud_115_api.get_video_subtitle_list(pick_code=video_pick_code)`
2. 解析返回的字幕列表
3. 提取字幕信息（pick_code、language、file_name等）
4. 返回字幕信息列表

### 3.2 字幕下载方法

**`_download_subtitles_from_115_to_local`**:
```python
async def _download_subtitles_from_115_to_local(
    self,
    local_path: Path,
    cloud_subtitle_info: List[Dict[str, Any]],
    media_info: Dict[str, Any],
    cloud_115_api: Any
) -> List[str]:
    """
    从115网盘下载字幕到本地STRM目录（供本地播放使用）
    
    同时记录115网盘字幕信息（供外网播放API使用）
    """
```

**流程**:
1. 遍历115网盘字幕信息列表
2. 使用字幕的pick_code下载字幕文件
3. 保存到本地STRM目录（与STRM文件同目录）
4. 返回下载成功的字幕文件路径列表

### 3.3 字幕API端点

**`stream_subtitle`**:
```python
@router.get("/subtitle/{storage_type}/{token}")
async def stream_subtitle(
    storage_type: str,
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    STRM字幕文件流媒体重定向端点
    
    根据JWT token中的字幕pick_code获取115网盘字幕下载地址并302重定向或代理
    """
```

**流程**:
1. 验证JWT token
2. 提取`subtitle_pick_code`
3. 获取115网盘API客户端
4. 调用`get_download_url(pick_code=subtitle_pick_code)`获取下载地址
5. 根据请求头决定使用302跳转或代理模式

---

## 📋 四、使用场景

### 4.1 本地播放

**场景**: 用户在本地网络（内网）播放视频

**流程**:
1. 媒体服务器（Emby/Jellyfin/Plex）扫描STRM目录
2. 检测到本地字幕文件（与STRM文件同目录）
3. 直接读取本地字幕文件
4. 显示字幕选择，用户选择后正常显示

**优势**:
- ✅ 快速（本地文件读取）
- ✅ 可靠（不依赖网络）
- ✅ 无需额外API调用

### 4.2 外网播放

**场景**: 用户外出时通过外网播放视频

**流程**:
1. 媒体服务器播放STRM文件（通过302跳转或代理）
2. 媒体服务器检测到本地字幕文件（占位符或实际文件）
3. 用户选择字幕后，媒体服务器请求字幕文件
4. 字幕文件URL指向 `/api/strm/subtitle/115/{token}`
5. STRM API从115网盘获取字幕并返回

**优势**:
- ✅ 外网可访问（不依赖本地NAS）
- ✅ 实时获取（从115网盘）
- ✅ 与视频播放方式一致

---

## 📋 五、配置说明

### 5.1 推荐配置

**启用从115网盘检测字幕**:
```json
{
  "generate_subtitle_files": true,
  "detect_subtitles_from_cloud": true
}
```

**效果**:
- ✅ 自动从115网盘检测字幕
- ✅ 下载字幕到本地（供本地播放）
- ✅ 记录115网盘字幕信息（供外网播放）

### 5.2 禁用从115网盘检测字幕

**配置**:
```json
{
  "generate_subtitle_files": true,
  "detect_subtitles_from_cloud": false
}
```

**效果**:
- ✅ 使用提供的字幕文件列表
- ✅ 下载字幕到本地（供本地播放）
- ❌ 不记录115网盘字幕信息（外网播放可能无法访问）

---

## 📋 六、技术细节

### 6.1 字幕信息存储

**数据库字段**: `STRMFile.subtitle_files` (JSON)

**存储格式**:
```json
[
  {
    "pick_code": "cg16zx93h3xy6ddf1",
    "language": "zh",
    "title": "简体中文",
    "file_name": "movie.zh.srt",
    "url": "https://...",
    "type": "srt",
    "sid": "12345"
  }
]
```

### 6.2 字幕文件命名

**规则**:
1. 优先使用115返回的`file_name`
2. 如果没有，根据语言生成：`{base_name}.{language}.{ext}`
3. 扩展名根据`type`确定（.srt/.ass/.ssa/.vtt）

**示例**:
- `movie.zh.srt` - 简体中文字幕
- `movie.en.srt` - 英文字幕
- `movie.zh.ass` - 简体中文ASS字幕

### 6.3 字幕API Token生成

**Token内容**:
```python
{
  "subtitle_pick_code": "cg16zx93h3xy6ddf1",  # 字幕文件pick_code
  "storage_type": "115",
  "exp": int(time.time()) + 3600  # 1小时过期
}
```

**生成方式**:
- 在生成STRM文件时，为每个字幕生成对应的token
- Token可以嵌入到字幕文件的URL中
- 或者通过数据库查询获取

---

## 📋 七、优势总结

### 7.1 本地播放优势

- ✅ **快速** - 本地文件读取，无需网络请求
- ✅ **可靠** - 不依赖115网盘API
- ✅ **离线可用** - 即使115网盘不可用也能播放

### 7.2 外网播放优势

- ✅ **外网可访问** - 不依赖本地NAS
- ✅ **实时获取** - 从115网盘实时获取最新字幕
- ✅ **与视频一致** - 使用相同的302跳转或代理模式

### 7.3 双重保障

- ✅ **本地播放** - 使用本地字幕文件（快速、可靠）
- ✅ **外网播放** - 从115网盘获取字幕（外网可访问）
- ✅ **自动切换** - 根据播放环境自动选择字幕来源

---

## 📋 八、注意事项

### 8.1 字幕文件大小

**字幕文件通常很小**（几KB到几十KB）:
- 302跳转模式即可满足需求
- 代理模式主要用于兼容性

### 8.2 字幕文件格式

**支持格式**:
- `.srt` - SubRip字幕
- `.ass` - Advanced SubStation Alpha
- `.ssa` - SubStation Alpha
- `.vtt` - WebVTT

### 8.3 字幕语言检测

**语言识别**:
- 优先使用115返回的`language`字段
- 如果没有，使用`title`字段推断
- 默认使用`unknown`

---

**文档生成时间**: 2025-01-XX  
**实现状态**: ✅ 已完成  
**测试状态**: ⏳ 待测试

