# STRM系统同步流程说明

## 📋 概述

STRM系统的同步流程分为三个阶段：
1. **首次全量同步**：第一次开启STRM功能时，自动全量同步一次
2. **增量同步**：实时监测115网盘，实现增量同步
3. **网盘删除自动删除本地STRM**：网盘文件删除时，自动删除本地对应的STRM文件

## 🔄 工作流程

### 1. 首次全量同步

#### 触发时机
- 第一次开启STRM功能时自动触发
- 通过检测数据库中是否有STRM文件记录来判断是否是第一次

#### 工作流程
```
1. 启动STRM同步管理器
   ↓
2. 检测是否是第一次同步（检查数据库中是否有STRM文件记录）
   ↓
3. 如果是第一次，执行全量同步：
   - 扫描网盘文件树
   - 扫描本地STRM文件树
   - 对比文件树，找出差异
   - 生成STRM文件（新增和更新的文件）
   - 删除本地STRM文件（如果网盘文件已删除）
   - 更新同步时间
   ↓
4. 标记已完成首次同步（通过STRM文件记录自动标记）
```

#### 实现方法
- `STRMSyncManager.start_sync()`：启动同步任务，自动检测并执行首次全量同步
- `STRMSyncManager._is_first_sync()`：检测是否是第一次同步
- `STRMSyncManager.full_sync()`：执行全量同步

### 2. 增量同步

#### 触发时机
- 首次同步后，定时执行（可配置间隔，如每1小时）
- 实时监测任务（可配置间隔，如每5分钟）

#### 工作流程
```
1. 获取上次同步时间（从STRM文件记录中获取最新的 updated_at 时间）
   ↓
2. 扫描网盘变更文件（利用115网盘开发者权限API，基于时间范围）
   ↓
3. 生成或更新STRM文件（新增和更新的文件）
   ↓
4. 检测并删除本地STRM文件（如果网盘文件已删除）
   - 通过对比数据库中的STRM文件和网盘文件列表检测删除的文件
   - 使用115网盘API检查文件是否存在
   - 自动删除本地STRM文件、NFO文件和字幕文件
   - 清理空文件夹
   - 记录删除事件到生命周期追踪
   ↓
5. 更新同步时间（通过STRM文件记录的 updated_at 字段自动维护）
```

#### 实现方法
- `STRMSyncManager.incremental_sync()`：执行增量同步
- `STRMSyncManager._scan_cloud_changes()`：扫描网盘变更文件
- `STRMSyncManager._detect_deleted_files()`：检测删除的文件
- `STRMSyncManager._delete_local_strm_files_from_cloud_deletes()`：删除本地STRM文件

### 3. 实时监测

#### 触发时机
- 启动同步管理器后，持续运行（可配置间隔，如每5分钟）

#### 工作流程
```
1. 获取网盘文件变更（使用115网盘API，检测文件变更）
   ↓
2. 处理新增和更新的文件（生成/更新STRM文件）
   ↓
3. 处理删除的文件（自动删除本地STRM文件）
```

#### 实现方法
- `STRMSyncManager._realtime_compare_loop()`：实时对比循环
- `STRMSyncManager._realtime_compare()`：实时对比网盘和本地STRM文件
- `STRMSyncManager._get_cloud_realtime_changes()`：获取网盘实时文件变更

### 4. 网盘删除自动删除本地STRM

#### 触发时机
- 增量同步时
- 全量同步时
- 实时对比时

#### 工作流程
```
1. 检测网盘删除的文件
   - 通过对比数据库中的STRM文件和网盘文件列表检测删除的文件
   - 使用115网盘API检查文件是否存在
   ↓
2. 删除本地STRM文件
   - 查询STRM文件记录
   - 删除本地STRM文件
   - 删除关联的NFO文件
   - 删除关联的字幕文件
   - 清理空文件夹
   ↓
3. 记录删除事件
   - 记录删除事件到生命周期追踪
   - 删除数据库记录
```

#### 实现方法
- `STRMSyncManager._detect_deleted_files()`：检测删除的文件
- `STRMSyncManager._delete_local_strm_files_from_cloud_deletes()`：删除本地STRM文件
- `STRMSyncManager._delete_strm_file_by_record()`：删除本地STRM文件（基于数据库记录）

## 📊 同步策略对比

| 同步方式 | 触发时机 | 扫描范围 | 效率 | 用途 |
|---------|---------|---------|------|------|
| 首次全量同步 | 第一次开启STRM功能 | 所有网盘文件 | 低 | 初始化STRM文件 |
| 增量同步 | 定时执行（如每1小时） | 基于时间范围的变更文件 | 高 | 定期同步变更 |
| 实时监测 | 持续运行（如每5分钟） | 实时检测文件变更 | 中 | 快速响应变更 |

## ⚙️ 配置选项

### STRMSyncConfig 配置

```python
class STRMSyncConfig(BaseModel):
    """STRM同步配置"""
    
    # 自动同步
    auto_sync: bool = True  # 是否自动增量同步
    sync_interval: int = 3600  # 增量同步间隔（秒），默认1小时
    
    # 实时对比
    realtime_compare: bool = True  # 是否实时监测
    compare_interval: int = 300  # 实时对比间隔（秒），默认5分钟
    
    # 自动删除
    auto_delete_on_cloud_delete: bool = True  # 是否在网盘文件删除时自动删除本地STRM文件
```

### 使用示例

```python
# 创建同步配置
sync_config = STRMSyncConfig(
    auto_sync=True,  # 启用自动增量同步
    sync_interval=3600,  # 每1小时执行一次增量同步
    realtime_compare=True,  # 启用实时监测
    compare_interval=300,  # 每5分钟执行一次实时对比
    auto_delete_on_cloud_delete=True  # 启用网盘删除自动删除本地STRM
)

# 创建同步管理器
sync_manager = STRMSyncManager(
    db=db,
    sync_config=sync_config,
    strm_config=strm_config,
    cloud_storage='115',
    cloud_115_api=cloud_115_api
)

# 启动同步任务
await sync_manager.start_sync()
```

## 🔍 检测机制

### 1. 首次同步检测

通过检查数据库中是否有STRM文件记录来判断是否是第一次同步：

```python
async def _is_first_sync(self) -> bool:
    """检测是否是第一次同步"""
    # 查询数据库中是否有STRM文件记录
    result = await self.db.execute(
        select(STRMFile).where(STRMFile.cloud_storage == self.cloud_storage).limit(1)
    )
    strm_file = result.scalar_one_or_none()
    
    # 如果没有记录，说明是第一次同步
    return strm_file is None
```

### 2. 删除文件检测

通过对比数据库中的STRM文件和网盘文件列表检测删除的文件：

```python
async def _detect_deleted_files(self) -> List[Dict[str, Any]]:
    """检测网盘中已删除的文件"""
    # 获取数据库中的所有STRM文件记录
    # 检查每个STRM文件对应的网盘文件是否还存在
    # 使用115网盘API检查文件是否存在
    # 如果文件不存在，添加到删除列表
```

### 3. 同步时间获取

从STRM文件记录中获取最新的 `updated_at` 时间作为上次同步时间：

```python
async def _get_last_sync_time(self) -> datetime:
    """获取上次同步时间"""
    # 查询最新的STRM文件更新时间
    # 如果没有记录，返回24小时前的时间
```

## ✅ 优势

1. **自动化**：首次开启STRM功能时，自动全量同步一次，无需手动干预
2. **高效**：之后使用增量同步，只处理变更文件，提高效率
3. **实时**：实时监测115网盘变更，快速响应文件变更
4. **一致性**：网盘删除文件时，自动删除本地STRM文件，保持数据一致性
5. **可追溯**：记录生命周期事件，便于审计和调试

## 📝 注意事项

1. **首次同步时间**：首次全量同步可能需要较长时间，取决于网盘文件数量
2. **同步间隔**：建议增量同步间隔设置为1小时，实时监测间隔设置为5分钟
3. **删除检测**：删除文件检测依赖于115网盘API，如果API不可用，可能无法及时检测删除
4. **数据一致性**：建议定期执行全量同步，确保数据一致性

## 🔄 下一步

1. ✅ 实现首次全量同步检测
2. ✅ 实现增量同步
3. ✅ 实现实时监测
4. ✅ 实现网盘删除自动删除本地STRM
5. ⏳ 优化同步性能
6. ⏳ 添加同步状态监控
7. ⏳ 添加同步错误处理

