# MoviePilot文件操作模式参考实现总结

## 📋 文件操作模式

### 1. 本地存储到本地存储

**支持的模式**：
- `copy`：复制文件
- `move`：移动文件
- `link`：硬链接
- `softlink`：软链接

**实现逻辑**（`transhandler.py:346-364`）：
```python
if fileitem.storage == "local" and target_storage == "local":
    # 创建目录
    if not target_file.parent.exists():
        target_file.parent.mkdir(parents=True)
    # 本地到本地
    if transfer_type == "copy":
        state = source_oper.copy(fileitem, target_file.parent, target_file.name)
    elif transfer_type == "move":
        state = source_oper.move(fileitem, target_file.parent, target_file.name)
    elif transfer_type == "link":
        state = source_oper.link(fileitem, target_file)
    elif transfer_type == "softlink":
        state = source_oper.softlink(fileitem, target_file)
```

### 2. 本地存储到云存储（115网盘等）

**支持的模式**：
- `copy`：上传文件到云存储，保留本地文件
- `move`：上传文件到云存储，删除本地文件

**实现逻辑**（`transhandler.py:365-397`）：
```python
elif fileitem.storage == "local" and target_storage != "local":
    # 本地到网盘
    filepath = Path(fileitem.path)
    if not filepath.exists():
        return None, f"文件 {filepath} 不存在"
    if transfer_type == "copy":
        # 复制：上传文件，保留本地文件
        target_fileitem = target_oper.get_folder(target_file.parent)
        if target_fileitem:
            new_item = target_oper.upload(target_fileitem, filepath, target_file.name)
            if new_item:
                return new_item, ""
    elif transfer_type == "move":
        # 移动：上传文件，删除本地文件
        target_fileitem = target_oper.get_folder(target_file.parent)
        if target_fileitem:
            new_item = target_oper.upload(target_fileitem, filepath, target_file.name)
            if new_item:
                source_oper.delete(fileitem)  # 删除本地文件
                return new_item, ""
```

### 3. 云存储到本地存储

**支持的模式**：
- `copy`：下载文件到本地，保留云存储文件
- `move`：下载文件到本地，删除云存储文件

**实现逻辑**（`transhandler.py:398-418`）：
```python
elif fileitem.storage != "local" and target_storage == "local":
    # 网盘到本地
    if target_file.exists():
        logger.warn(f"文件已存在：{target_file}")
        return __get_targetitem(target_file), ""
    # 网盘到本地
    if transfer_type in ["copy", "move"]:
        # 下载
        tmp_file = source_oper.download(fileitem=fileitem, path=target_file.parent)
        if tmp_file:
            # 创建目录
            if not target_file.parent.exists():
                target_file.parent.mkdir(parents=True)
            # 将tmp_file移动到target_file
            SystemUtils.move(tmp_file, target_file)
            if transfer_type == "move":
                # 删除源文件
                source_oper.delete(fileitem)
            return __get_targetitem(target_file), ""
```

### 4. 云存储到云存储

**支持的模式**：
- `copy`：复制文件到新目录
- `move`：移动文件到新目录

**实现逻辑**（`transhandler.py:419-442`）：
```python
elif fileitem.storage == target_storage:
    # 同一网盘
    if transfer_type == "copy":
        # 复制文件到新目录
        target_fileitem = target_oper.get_folder(target_file.parent)
        if target_fileitem:
            if source_oper.copy(fileitem, Path(target_fileitem.path), target_file.name):
                return target_oper.get_item(target_file), ""
    elif transfer_type == "move":
        # 移动文件到新目录
        target_fileitem = target_oper.get_folder(target_file.parent)
        if target_fileitem:
            if source_oper.move(fileitem, Path(target_fileitem.path), target_file.name):
                return target_oper.get_item(target_file), ""
```

## 🔧 StorageBase接口方法

### 本地存储（LocalStorage）

**方法签名**（`storages/local.py`）：
```python
def copy(self, fileitem: FileItem, path: Path, new_name: str) -> bool:
    """复制文件"""
    pass

def move(self, fileitem: FileItem, path: Path, new_name: str) -> bool:
    """移动文件"""
    pass

def link(self, fileitem: FileItem, target_file: Path) -> bool:
    """创建硬链接"""
    pass

def softlink(self, fileitem: FileItem, target_file: Path) -> bool:
    """创建软链接"""
    pass
```

### 115网盘存储（U115Storage）

**方法签名**（`storages/u115.py`）：
```python
def copy(self, fileitem: FileItem, path: Path, new_name: str) -> bool:
    """复制文件（同一网盘内）"""
    # 调用115 API: /open/ufile/copy
    pass

def move(self, fileitem: FileItem, path: Path, new_name: str) -> bool:
    """移动文件（同一网盘内）"""
    # 调用115 API: /open/ufile/move
    pass

def link(self, fileitem: FileItem, target_file: Path) -> bool:
    """硬链接（不支持）"""
    return False

def softlink(self, fileitem: FileItem, target_file: Path) -> bool:
    """软链接（不支持）"""
    return False

def upload(self, folder_item: FileItem, local_path: Path, new_name: str) -> Optional[FileItem]:
    """上传文件到115网盘"""
    pass

def download(self, fileitem: FileItem, path: Path) -> Optional[Path]:
    """下载文件到本地"""
    pass
```

## 📊 覆盖模式集成

### 覆盖模式检查时机

覆盖模式检查在文件操作之前进行（`transhandler.py:237-278`）：

```python
# 判断是否要覆盖
overflag = False
# 目标目录
target_diritem = target_oper.get_folder(folder_path)
# 目标文件
target_item = target_oper.get_item(new_file)
if target_item:
    # 目标文件已存在
    if overwrite_mode == 'always':
        # 总是覆盖同名文件
        overflag = True
    elif overwrite_mode == 'size':
        # 存在时大覆盖小
        if target_item.size < fileitem.size:
            overflag = True
        else:
            # 跳过，返回失败
            return self.result.copy()
    elif overwrite_mode == 'never':
        # 存在不覆盖
        return self.result.copy()
    elif overwrite_mode == 'latest':
        # 仅保留最新版本
        overflag = True
else:
    if overwrite_mode == 'latest':
        # 文件不存在，但仅保留最新版本
        # 删除已有版本文件
        self.__delete_version_files(target_oper, new_file)

# 整理文件（如果overflag为True或文件不存在）
new_item, err_msg = self.__transfer_file(
    fileitem=fileitem,
    mediainfo=mediainfo,
    target_storage=target_storage,
    target_file=new_file,
    transfer_type=transfer_type,
    over_flag=overflag,
    source_oper=source_oper,
    target_oper=target_oper
)
```

## ✅ VabHub实现要点

### 1. 文件操作模式枚举

```python
class FileOperationMode(str, Enum):
    """文件操作模式"""
    COPY = "copy"  # 复制
    MOVE = "move"  # 移动
    HARDLINK = "link"  # 硬链接（仅本地存储）
    SYMLINK = "softlink"  # 软链接（仅本地存储）
```

### 2. 存储类型判断

```python
def get_available_modes(source_storage: str, target_storage: str) -> List[FileOperationMode]:
    """获取可用的文件操作模式"""
    if source_storage == "local" and target_storage == "local":
        # 本地到本地：支持所有模式
        return [FileOperationMode.COPY, FileOperationMode.MOVE, 
                FileOperationMode.HARDLINK, FileOperationMode.SYMLINK]
    else:
        # 本地到云存储、云存储到本地、云存储到云存储：只支持复制和移动
        return [FileOperationMode.COPY, FileOperationMode.MOVE]
```

### 3. 文件操作实现

```python
async def handle_file_operation(
    source_path: Path,
    target_path: Path,
    operation_mode: FileOperationMode,
    source_storage: str,
    target_storage: str,
    overwrite_mode: str = "never",
    source_oper: Optional[Any] = None,
    target_oper: Optional[Any] = None
):
    """处理文件操作"""
    # 1. 检查覆盖模式
    should_overwrite, reason = await OverwriteHandler.check_overwrite(
        target_path=target_path,
        overwrite_mode=overwrite_mode,
        new_file_size=source_path.stat().st_size if source_storage == "local" else None,
        storage_type=target_storage,
        storage_oper=target_oper
    )
    
    if not should_overwrite:
        return {"success": False, "reason": reason}
    
    # 2. 如果是latest模式，删除版本文件
    if overwrite_mode == "latest":
        await OverwriteHandler.delete_version_files(
            target_path=target_path,
            storage_type=target_storage,
            storage_oper=target_oper
        )
    
    # 3. 执行文件操作
    if source_storage == "local" and target_storage == "local":
        # 本地到本地
        if operation_mode == FileOperationMode.COPY:
            return await _copy_local_to_local(source_path, target_path)
        elif operation_mode == FileOperationMode.MOVE:
            return await _move_local_to_local(source_path, target_path)
        elif operation_mode == FileOperationMode.HARDLINK:
            return await _hardlink_local_to_local(source_path, target_path)
        elif operation_mode == FileOperationMode.SYMLINK:
            return await _symlink_local_to_local(source_path, target_path)
    elif source_storage == "local" and target_storage != "local":
        # 本地到云存储
        if operation_mode == FileOperationMode.COPY:
            return await _upload_to_cloud(source_path, target_path, target_oper, delete_source=False)
        elif operation_mode == FileOperationMode.MOVE:
            return await _upload_to_cloud(source_path, target_path, target_oper, delete_source=True)
    elif source_storage != "local" and target_storage == "local":
        # 云存储到本地
        if operation_mode == FileOperationMode.COPY:
            return await _download_from_cloud(source_path, target_path, source_oper, delete_source=False)
        elif operation_mode == FileOperationMode.MOVE:
            return await _download_from_cloud(source_path, target_path, source_oper, delete_source=True)
    elif source_storage == target_storage:
        # 云存储到云存储
        if operation_mode == FileOperationMode.COPY:
            return await _copy_cloud_to_cloud(source_path, target_path, source_oper)
        elif operation_mode == FileOperationMode.MOVE:
            return await _move_cloud_to_cloud(source_path, target_path, source_oper)
```

## 📝 下一步

1. **更新文件操作模式枚举**：参考MoviePilot的实现
2. **实现文件操作处理器**：支持所有存储类型和操作模式
3. **集成覆盖模式处理**：在文件操作之前检查覆盖模式
4. **实现StorageBase接口**：为本地存储和115网盘存储实现统一接口

