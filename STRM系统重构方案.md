# STRM系统重构方案

## 📋 用户需求分析

### 核心功能
1. **STRM文件生成**：将115网盘的媒体文件生成STRM文件保存到本地STRM媒体库文件夹
2. **媒体库识别**：让Emby等媒体库识别并播放存在115网盘的媒体
3. **覆盖模式**：支持never、always、size三种覆盖模式
4. **刮削集成**：
   - 115网盘刮削（可选，由用户决定）
   - 如果115网盘已开启刮削并完成刮削，生成本地STRM文件时同步下载刮削文件到本地
   - 如果本地STRM媒体库文件夹开启刮削功能，生成本地STRM文件时要顺便刮削
   - 如果都没开，都不刮削
5. **服务开关**：如果系统中不开启STRM服务功能，也不会生成STRM文件

### 非核心功能（应移除或独立）
- 上传媒体文件
- 重命名文件
- 分类文件
- 新建文件夹
- 移动、复制文件

## 🎯 重构目标

1. **简化STRM系统**：只保留核心功能（生成STRM文件）
2. **整合VabHub-1实现**：使用VabHub-1中更完整的STRM实现
3. **实现覆盖模式**：参考MoviePilot的实现
4. **实现刮削集成**：支持115网盘和本地刮削
5. **实现服务开关**：支持全局开关控制

## 📊 架构设计

### 1. STRM系统核心模块

```
STRM系统
├── STRMGenerator (核心生成器)
│   ├── 生成STRM文件
│   ├── 覆盖模式处理
│   └── 刮削文件处理
├── STRMService (服务层)
│   ├── 系统认证集成
│   ├── 115网盘API客户端
│   └── 服务开关控制
├── STRMConfig (配置管理)
│   ├── 媒体库路径配置
│   ├── 覆盖模式配置
│   ├── 刮削配置
│   └── 服务开关配置
└── STRMAPI (API端点)
    ├── 生成STRM文件
    ├── 重定向服务
    └── 服务状态
```

### 2. 覆盖模式实现

```python
class OverwriteMode(str, Enum):
    """覆盖模式"""
    NEVER = "never"  # 从不覆盖
    ALWAYS = "always"  # 总是覆盖
    SIZE = "size"  # 按大小覆盖（大覆盖小）
```

**覆盖逻辑**：
- `never`：如果目标文件已存在，跳过生成
- `always`：如果目标文件已存在，直接覆盖
- `size`：如果目标文件已存在，比较文件大小，新文件更大时覆盖

### 3. 刮削功能集成

```python
class ScrapeConfig(BaseModel):
    """刮削配置"""
    # 115网盘刮削
    scrape_on_cloud: bool = False  # 是否在115网盘刮削
    download_scrape_files: bool = True  # 是否下载115网盘的刮削文件到本地
    
    # 本地STRM媒体库刮削
    scrape_on_local: bool = False  # 是否在本地STRM媒体库刮削
    
    # 刮削文件类型
    scrape_file_types: List[str] = ["nfo", "jpg", "png"]  # 刮削文件类型
```

**刮削流程**：
1. 如果115网盘已开启刮削并完成刮削，生成本地STRM文件时同步下载刮削文件到本地
2. 如果本地STRM媒体库文件夹开启刮削功能，生成本地STRM文件时要顺便刮削
3. 如果都没开，都不刮削

### 4. 服务开关

```python
class STRMConfig(BaseModel):
    """STRM配置"""
    # 服务开关
    enabled: bool = True  # STRM服务是否启用
    
    # 其他配置...
```

**服务开关逻辑**：
- 如果`enabled=False`，不生成STRM文件
- 如果`enabled=True`，正常生成STRM文件

## 🔧 实现步骤

### 步骤1：简化STRM系统
- [ ] 移除上传、重命名、分类等非核心功能
- [ ] 只保留STRM文件生成核心功能
- [ ] 更新API端点，移除非核心功能

### 步骤2：整合VabHub-1实现
- [ ] 整合`StrmFileGenerator`类
- [ ] 整合`CloudStorageStrmManager`类
- [ ] 整合覆盖模式处理逻辑
- [ ] 整合文件树管理

### 步骤3：实现覆盖模式
- [ ] 实现`OverwriteMode`枚举
- [ ] 实现覆盖模式检查逻辑
- [ ] 实现文件大小比较逻辑
- [ ] 更新STRM生成器，支持覆盖模式

### 步骤4：实现刮削集成
- [ ] 实现`ScrapeConfig`配置类
- [ ] 实现115网盘刮削文件下载
- [ ] 实现本地STRM媒体库刮削
- [ ] 更新STRM生成器，支持刮削功能

### 步骤5：实现服务开关
- [ ] 在`STRMConfig`中添加`enabled`字段
- [ ] 在STRM生成器中检查服务开关
- [ ] 在API端点中检查服务开关
- [ ] 更新前端界面，支持服务开关

## 📝 代码结构

### 1. STRM生成器（简化版）

```python
class STRMGenerator:
    """STRM文件生成器（核心功能）"""
    
    def __init__(self, config: STRMConfig, db: Optional[Any] = None):
        self.config = config
        self.db = db
        self._strm_service: Optional[STRMService] = None
    
    async def generate_strm_file(
        self,
        cloud_file_id: str,
        cloud_storage: str,
        media_info: Dict[str, Any],
        overwrite_mode: OverwriteMode = OverwriteMode.NEVER
    ) -> Optional[Path]:
        """
        生成STRM文件（核心功能）
        
        Args:
            cloud_file_id: 云存储文件ID（pick_code）
            cloud_storage: 云存储类型（115/123）
            media_info: 媒体信息
            overwrite_mode: 覆盖模式
        
        Returns:
            生成的STRM文件路径，如果跳过则返回None
        """
        # 1. 检查服务开关
        if not self.config.enabled:
            logger.info("STRM服务未启用，跳过生成")
            return None
        
        # 2. 检查覆盖模式
        strm_path = self._get_strm_path(media_info)
        if strm_path.exists():
            if not await self._should_overwrite(strm_path, overwrite_mode):
                logger.info(f"STRM文件已存在，跳过生成: {strm_path}")
                return None
        
        # 3. 生成STRM文件
        # ...
        
        # 4. 处理刮削文件
        if self.config.scrape_config.download_scrape_files:
            await self._download_scrape_files(cloud_file_id, cloud_storage, strm_path.parent)
        
        if self.config.scrape_config.scrape_on_local:
            await self._scrape_local_strm(strm_path, media_info)
        
        return strm_path
```

### 2. 覆盖模式处理

```python
async def _should_overwrite(
    self,
    existing_path: Path,
    overwrite_mode: OverwriteMode
) -> bool:
    """检查是否应该覆盖现有文件"""
    if overwrite_mode == OverwriteMode.NEVER:
        return False
    elif overwrite_mode == OverwriteMode.ALWAYS:
        return True
    elif overwrite_mode == OverwriteMode.SIZE:
        # 需要获取新文件大小进行比较
        # 这里需要从115网盘获取文件大小
        new_size = await self._get_cloud_file_size(cloud_file_id)
        existing_size = existing_path.stat().st_size
        return new_size > existing_size
    return False
```

### 3. 刮削文件处理

```python
async def _download_scrape_files(
    self,
    cloud_file_id: str,
    cloud_storage: str,
    local_dir: Path
):
    """下载115网盘的刮削文件到本地"""
    if not self.config.scrape_config.scrape_on_cloud:
        return
    
    # 获取115网盘API客户端
    api_client = await self._get_115_api_client()
    if not api_client:
        return
    
    # 获取文件信息（包括刮削文件）
    file_info = await api_client.get_file_info(file_id=cloud_file_id)
    
    # 下载刮削文件（NFO、封面等）
    scrape_files = await api_client.get_scrape_files(cloud_file_id)
    for scrape_file in scrape_files:
        await self._download_file(scrape_file, local_dir)
```

## 📚 参考实现

### MoviePilot覆盖模式
- `never`：从不覆盖
- `always`：总是覆盖
- `size`：按大小覆盖（大覆盖小）

### VabHub-1 STRM实现
- `StrmFileGenerator`：STRM文件生成器
- `CloudStorageStrmManager`：云存储STRM管理器
- `StrmFileConfig`：STRM文件配置
- 覆盖模式：支持never、always、smart

## ✅ 完成标准

1. ✅ STRM系统只保留核心功能（生成STRM文件）
2. ✅ 整合VabHub-1中的完整STRM实现
3. ✅ 实现覆盖模式（never、always、size）
4. ✅ 实现刮削功能集成（115网盘和本地）
5. ✅ 实现服务开关
6. ✅ 移除非核心功能（上传、重命名、分类等）

