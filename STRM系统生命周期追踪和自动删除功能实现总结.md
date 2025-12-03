# STRM系统生命周期追踪和自动删除功能实现总结

## 📋 功能概述

### 1. 生命周期追踪功能

**功能**：记录STRM文件从创建到删除的完整生命周期事件，用于审计、调试、恢复和增量同步。

**实现模块**：`app/modules/strm/lifecycle_tracker.py`

**事件类型**：
- **创建事件（type=1）**：STRM文件生成时记录
- **更新事件（type=2）**：STRM文件更新时记录
- **删除事件（type=3）**：STRM文件删除时记录

### 2. 网盘删除自动删除本地STRM功能

**功能**：当网盘中删除媒体文件时，自动检测并删除本地对应的STRM文件。

**实现方式**：
- 通过对比数据库中的STRM文件和网盘文件列表检测删除的文件
- 使用115网盘API检查文件是否存在
- 自动删除本地STRM文件、NFO文件和字幕文件
- 清理空文件夹
- 记录删除事件到生命周期追踪

## 🔧 实现详情

### 1. 生命周期追踪器（LifecycleTracker）

#### 类定义

```python
class LifecycleTracker:
    """STRM生命周期追踪器"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
```

#### 核心方法

1. **`record_create_event`**：记录STRM文件创建事件
2. **`record_update_event`**：记录STRM文件更新事件
3. **`record_delete_event`**：记录STRM文件删除事件
4. **`get_file_lifecycle`**：获取文件的完整生命周期事件
5. **`get_recent_changes`**：获取最近N小时内的变更事件

#### 使用示例

```python
from app.modules.strm.lifecycle_tracker import LifecycleTracker

# 创建生命周期追踪器
tracker = LifecycleTracker(db)

# 记录创建事件
await tracker.record_create_event(
    strm_file_id=1,
    cloud_file_id="pick_code_123",
    cloud_storage="115",
    file_info={
        "file_name": "movie.mkv",
        "file_size": 1024 * 1024 * 1024,
        "sha1": "abc123...",
        "parent_id": "0",
        "file_category": 1,
        "file_type": 4,
        "update_time": 1234567890
    }
)

# 获取文件生命周期
events = await tracker.get_file_lifecycle(
    strm_file_id=1
)
```

### 2. STRM生成器集成生命周期追踪

#### 修改内容

在 `STRMGenerator.__init__` 中初始化生命周期追踪器：

```python
def __init__(self, config: STRMConfig, db: Optional[Any] = None):
    # ... 原有代码 ...
    
    # 初始化生命周期追踪器（如果提供了数据库会话）
    if self.db:
        from .lifecycle_tracker import LifecycleTracker
        self._lifecycle_tracker = LifecycleTracker(self.db)
```

### 3. 同步管理器集成生命周期追踪和自动删除

#### 修改内容

1. **导入生命周期追踪器**：
```python
from .lifecycle_tracker import LifecycleTracker
from app.models.strm import STRMFile
from sqlalchemy import select
```

2. **初始化生命周期追踪器**：
```python
self.lifecycle_tracker = LifecycleTracker(db)
```

3. **在生成STRM文件时记录创建/更新事件**：
```python
# 在 _generate_strm_files 方法中
if existing_strm_file:
    # 更新现有记录
    await self.lifecycle_tracker.record_update_event(...)
else:
    # 创建新记录
    await self.lifecycle_tracker.record_create_event(...)
```

4. **检测网盘删除的文件**：
```python
async def _detect_deleted_files(self) -> List[Dict[str, Any]]:
    """检测网盘中已删除的文件"""
    # 获取数据库中的所有STRM文件记录
    # 检查每个STRM文件对应的网盘文件是否还存在
    # 返回删除的文件列表
```

5. **自动删除本地STRM文件**：
```python
async def _delete_local_strm_files_from_cloud_deletes(self, deleted_files: List[Dict[str, Any]]):
    """从网盘删除的文件中删除本地对应的STRM文件"""
    # 查询STRM文件记录
    # 删除本地STRM文件、NFO文件和字幕文件
    # 清理空文件夹
    # 记录删除事件
    # 删除数据库记录
```

6. **在实时对比中集成自动删除**：
```python
async def _realtime_compare(self):
    """实时对比网盘和本地STRM文件"""
    # 获取网盘文件变更
    changes = await self._get_cloud_realtime_changes()
    
    # 处理删除的文件（自动删除本地STRM文件）
    if changes.get('deleted') and self.sync_config.auto_delete_on_cloud_delete:
        await self._delete_local_strm_files_from_cloud_deletes(changes['deleted'])
```

## 📊 工作流程

### 1. STRM文件生成流程

```
1. 生成STRM文件
   ↓
2. 保存或更新STRM文件记录到数据库
   ↓
3. 记录生命周期事件（创建或更新）
   ↓
4. 完成
```

### 2. 网盘文件删除检测流程

```
1. 获取数据库中的所有STRM文件记录
   ↓
2. 遍历每个STRM文件记录
   ↓
3. 使用115网盘API检查文件是否存在
   ↓
4. 如果文件不存在，添加到删除列表
   ↓
5. 返回删除的文件列表
```

### 3. 自动删除本地STRM文件流程

```
1. 检测到网盘文件删除
   ↓
2. 查询STRM文件记录
   ↓
3. 删除本地STRM文件
   ↓
4. 删除关联的NFO文件
   ↓
5. 删除关联的字幕文件
   ↓
6. 清理空文件夹
   ↓
7. 记录删除事件到生命周期追踪
   ↓
8. 删除数据库记录
   ↓
9. 完成
```

## 🔍 检测删除文件的方法

### 方法1：对比数据库和网盘文件列表

```python
async def _detect_deleted_files(self) -> List[Dict[str, Any]]:
    """检测网盘中已删除的文件"""
    # 1. 获取数据库中的所有STRM文件记录
    # 2. 遍历每个STRM文件记录
    # 3. 使用115网盘API检查文件是否存在
    # 4. 如果文件不存在，添加到删除列表
    # 5. 返回删除的文件列表
```

### 方法2：使用115网盘API的文件变更API

```python
# 如果115网盘API支持文件变更通知，可以使用以下方法：
changes = await self.cloud_115_api.get_file_changes(
    last_sync_time=last_sync_time,
    file_type=4  # 4:视频
)
```

### 方法3：定期全量扫描对比

```python
# 在增量同步或全量同步时，对比文件列表找出删除的文件
differences = await self.file_tree_manager.compare_file_trees(
    cloud_storage=self.cloud_storage,
    local_tree=local_tree,
    cloud_tree=cloud_tree
)
deleted_files = differences['deleted']
```

## ✅ 功能特性

### 1. 生命周期追踪

- ✅ 记录创建事件
- ✅ 记录更新事件
- ✅ 记录删除事件
- ✅ 查询文件生命周期
- ✅ 查询最近变更事件

### 2. 自动删除本地STRM文件

- ✅ 自动检测网盘文件删除
- ✅ 自动删除本地STRM文件
- ✅ 自动删除关联的NFO文件
- ✅ 自动删除关联的字幕文件
- ✅ 自动清理空文件夹
- ✅ 记录删除事件到生命周期追踪
- ✅ 删除数据库记录

### 3. 配置选项

- ✅ `auto_delete_on_cloud_delete: bool = True`：是否在网盘文件删除时自动删除本地STRM文件
- ✅ 可在 `STRMSyncConfig` 中配置

## 📝 API使用示例

### 1. 查询文件生命周期

```python
from app.modules.strm.lifecycle_tracker import LifecycleTracker

tracker = LifecycleTracker(db)

# 查询文件的完整生命周期
events = await tracker.get_file_lifecycle(
    strm_file_id=1
)

# 查询最近24小时内的变更事件
recent_events = await tracker.get_recent_changes(hours=24)

# 查询最近24小时内的删除事件
deleted_events = await tracker.get_recent_changes(hours=24, event_type=3)
```

### 2. 手动触发删除检测

```python
# 在同步管理器中
sync_manager = STRMSyncManager(...)

# 检测删除的文件
deleted_files = await sync_manager._detect_deleted_files()

# 删除本地STRM文件
if deleted_files:
    await sync_manager._delete_local_strm_files_from_cloud_deletes(deleted_files)
```

## 🎯 优势

1. **完整的生命周期追踪**：记录STRM文件从创建到删除的完整生命周期
2. **自动删除**：网盘文件删除时自动删除本地STRM文件，保持同步
3. **数据一致性**：通过生命周期追踪确保数据库和文件系统的一致性
4. **易于调试**：通过生命周期事件可以追踪文件变更历史
5. **易于恢复**：可以从生命周期事件中恢复文件信息

## 📚 相关文档

- **`STRM生命周期追踪功能说明.md`**：生命周期追踪功能详细说明
- **`简化版STRM系统功能清单.md`**：STRM系统功能清单
- **`STRM系统增量更新和全量同步功能设计.md`**：增量更新和全量同步功能设计

## 🔄 下一步

1. ✅ 实现生命周期追踪器
2. ✅ 集成到STRM生成器
3. ✅ 集成到同步管理器
4. ✅ 实现自动删除功能
5. ⏳ 测试功能
6. ⏳ 优化性能
7. ⏳ 添加API端点

