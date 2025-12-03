# STRM系统功能澄清与覆盖模式实现方案

## 📋 功能澄清

### STRM系统的核心功能

**STRM文件生成**：将115网盘的媒体文件生成STRM文件保存到本地STRM媒体库文件夹，让Emby等媒体库识别并播放存在115网盘的媒体。

### 非STRM系统功能（应独立实现）

- ✅ **上传媒体文件**：下载完成后上传到115网盘（独立的文件操作模块）
- ✅ **重命名文件**：媒体文件重命名（独立的媒体重命名模块）
- ✅ **分类文件**：按类型分类媒体文件（独立的媒体分类模块）
- ✅ **新建文件夹**：创建目录结构（文件操作的一部分）
- ✅ **移动、复制文件**：文件操作（文件操作模块）

### 覆盖模式的应用场景

**覆盖模式不是用于STRM文件的**，而是用于系统文件操作：
- 上传媒体到115网盘时
- 移动文件到本地存储时
- 复制文件到本地存储时

## 🎯 覆盖模式实现

### 覆盖模式类型

| 模式 | 说明 | 行为 |
|------|------|------|
| `never` | 从不覆盖 | 如果目标文件已存在，跳过操作，返回失败 |
| `always` | 总是覆盖 | 如果目标文件已存在，直接覆盖 |
| `size` | 按文件大小 | 如果目标文件已存在，比较文件大小，新文件更大时覆盖 |
| `latest` | 仅保留最新 | 如果目标文件已存在，总是覆盖，并删除旧版本文件 |

### 覆盖模式实现逻辑

```python
# 1. 检查目标文件是否存在
if target_file.exists():
    # 2. 根据覆盖模式决定是否覆盖
    if overwrite_mode == 'never':
        # 不覆盖，返回失败
        return False, "目标文件已存在，覆盖模式为never"
    elif overwrite_mode == 'always':
        # 总是覆盖
        overwrite_flag = True
    elif overwrite_mode == 'size':
        # 比较文件大小
        if new_file_size > existing_file_size:
            overwrite_flag = True
        else:
            return False, "现有文件更大，跳过覆盖"
    elif overwrite_mode == 'latest':
        # 总是覆盖，并删除旧版本文件
        delete_version_files(target_file)
        overwrite_flag = True

# 3. 执行文件操作（如果overwrite_flag为True）
if overwrite_flag:
    # 执行文件操作（上传、移动、复制等）
    perform_file_operation()
```

### latest模式的版本文件删除

**功能**：删除同一目录下的其他版本文件（例如：`movie.mkv`, `movie.1080p.mkv`, `movie.720p.mkv`等）

**实现逻辑**：
1. 提取文件的基本名称（去除版本信息）
2. 扫描同一目录下的所有文件
3. 找到所有匹配基本名称的文件
4. 删除除当前文件外的所有版本文件

## 📊 实现方案

### 1. 文件操作覆盖模式模块

**文件**：`app/modules/file_operation/overwrite_handler.py`

**功能**：
- 实现覆盖模式检查逻辑
- 实现版本文件删除功能
- 支持本地存储和云存储

### 2. 文件操作模块更新

**文件**：`app/modules/file_operation/handler.py`

**功能**：
- 集成覆盖模式处理
- 支持上传到115网盘时的覆盖模式
- 支持移动到本地存储时的覆盖模式
- 支持复制到本地存储时的覆盖模式

### 3. STRM系统简化

**文件**：`app/modules/strm/generator.py`

**功能**：
- 移除覆盖模式相关代码
- 只保留STRM文件生成核心功能
- 简化配置和逻辑

### 4. 刮削功能集成

**文件**：`app/modules/strm/scraper.py`

**功能**：
- 115网盘刮削文件下载
- 本地STRM媒体库刮削
- 刮削文件同步

## 🔧 实现步骤

### 步骤1：创建覆盖模式处理模块

- [ ] 创建`overwrite_handler.py`
- [ ] 实现覆盖模式检查逻辑
- [ ] 实现版本文件删除功能
- [ ] 支持本地存储和云存储

### 步骤2：更新文件操作模块

- [ ] 在文件操作模块中集成覆盖模式
- [ ] 支持上传到115网盘时的覆盖模式
- [ ] 支持移动到本地存储时的覆盖模式
- [ ] 支持复制到本地存储时的覆盖模式

### 步骤3：简化STRM系统

- [ ] 移除STRM生成器中的覆盖模式相关代码
- [ ] 只保留STRM文件生成核心功能
- [ ] 简化配置和逻辑

### 步骤4：实现刮削功能集成

- [ ] 实现115网盘刮削文件下载
- [ ] 实现本地STRM媒体库刮削
- [ ] 实现刮削文件同步

### 步骤5：实现服务开关

- [ ] 在STRM配置中添加服务开关
- [ ] 在STRM生成器中检查服务开关
- [ ] 在API端点中检查服务开关

## 📝 代码结构

### 1. 覆盖模式处理模块

```python
class OverwriteHandler:
    """覆盖模式处理器"""
    
    @staticmethod
    async def check_overwrite(
        target_path: Path,
        overwrite_mode: str,
        new_file_size: Optional[int] = None,
        storage_type: str = "local"
    ) -> tuple[bool, str]:
        """
        检查是否应该覆盖现有文件
        
        Args:
            target_path: 目标文件路径
            overwrite_mode: 覆盖模式（never/always/size/latest）
            new_file_size: 新文件大小（用于size模式）
            storage_type: 存储类型（local/115/123）
        
        Returns:
            (是否覆盖, 原因说明)
        """
        # 实现覆盖模式检查逻辑
        pass
    
    @staticmethod
    async def delete_version_files(
        target_path: Path,
        storage_type: str = "local"
    ) -> List[str]:
        """
        删除版本文件（latest模式）
        
        Args:
            target_path: 目标文件路径
            storage_type: 存储类型（local/115/123）
        
        Returns:
            删除的文件列表
        """
        # 实现版本文件删除逻辑
        pass
```

### 2. 文件操作模块更新

```python
class FileOperationHandler:
    """文件操作处理器"""
    
    async def upload_to_cloud(
        self,
        source_path: Path,
        target_path: str,
        cloud_storage: str,
        overwrite_mode: str = "never"
    ):
        """上传文件到云存储（应用覆盖模式）"""
        # 1. 检查目标文件是否存在（云存储）
        # 2. 应用覆盖模式
        # 3. 执行上传操作
        pass
    
    async def move_to_local(
        self,
        source_path: Path,
        target_path: Path,
        overwrite_mode: str = "never"
    ):
        """移动文件到本地存储（应用覆盖模式）"""
        # 1. 检查目标文件是否存在
        # 2. 应用覆盖模式
        # 3. 执行移动操作
        pass
```

### 3. STRM系统简化

```python
class STRMGenerator:
    """STRM文件生成器（简化版，只保留核心功能）"""
    
    async def generate_strm_file(
        self,
        cloud_file_id: str,
        cloud_storage: str,
        media_info: Dict[str, Any]
    ) -> Optional[Path]:
        """
        生成STRM文件（核心功能）
        
        Args:
            cloud_file_id: 云存储文件ID（pick_code）
            cloud_storage: 云存储类型（115/123）
            media_info: 媒体信息
        
        Returns:
            生成的STRM文件路径
        """
        # 1. 检查服务开关
        if not self.config.enabled:
            return None
        
        # 2. 生成STRM文件
        # 3. 处理刮削文件
        # 4. 返回STRM文件路径
        pass
```

## ✅ 完成标准

1. ✅ STRM系统只保留核心功能（生成STRM文件）
2. ✅ 覆盖模式应用于文件操作（上传、移动、复制）
3. ✅ 实现四种覆盖模式（never、always、size、latest）
4. ✅ 实现版本文件删除功能（latest模式）
5. ✅ 实现刮削功能集成（115网盘和本地）
6. ✅ 实现服务开关

## 📚 参考实现

### MoviePilot覆盖模式
- `never`：从不覆盖
- `always`：总是覆盖
- `size`：按大小覆盖（大覆盖小）
- `latest`：仅保留最新版本

### VabHub-1 STRM实现
- `StrmFileGenerator`：STRM文件生成器
- `CloudStorageStrmManager`：云存储STRM管理器
- 覆盖模式：支持never、always、size、latest

