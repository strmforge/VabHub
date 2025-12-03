# STRM生命周期追踪功能说明

## 📋 功能概述

**生命周期追踪**：记录STRM文件从创建到删除的完整生命周期事件，用于审计、调试和恢复。

## 🎯 功能说明

### 1. 生命周期事件类型

生命周期事件记录在 `STRMLifeEvent` 数据模型中，包括以下事件类型：

| 事件类型 | type值 | 说明 | 触发时机 |
|---------|--------|------|----------|
| 创建 | 1 | 文件创建事件 | STRM文件生成时 |
| 更新 | 2 | 文件更新事件 | STRM文件更新时（如重新生成、路径变更） |
| 删除 | 3 | 文件删除事件 | STRM文件删除时（如网盘文件删除、手动删除） |

### 2. 记录的信息

每个生命周期事件记录以下信息：

- **事件类型** (`type`): 1-创建，2-更新，3-删除
- **文件ID** (`file_id`): 关联的文件ID
- **父目录ID** (`parent_id`): 父目录ID
- **文件名** (`file_name`): 文件名
- **文件分类** (`file_category`): 文件分类（0-文件夹，1-文件）
- **文件类型** (`file_type`): 文件类型（1-文档，2-图片，3-音乐，4-视频，5-压缩，6-应用，7-书籍）
- **文件大小** (`file_size`): 文件大小（字节）
- **SHA1** (`sha1`): 文件SHA1哈希值
- **pick_code** (`pick_code`): 云存储文件提取码
- **更新时间** (`update_time`): 文件更新时间戳
- **创建时间** (`create_time`): 文件创建时间戳

### 3. 使用场景

#### 场景1：文件变更审计
```python
# 查询文件的完整生命周期
life_events = await db.query(STRMLifeEvent).filter(
    STRMLifeEvent.file_id == file_id
).order_by(STRMLifeEvent.create_time).all()

# 输出文件变更历史
for event in life_events:
    event_type = "创建" if event.type == 1 else "更新" if event.type == 2 else "删除"
    print(f"{event_type}: {event.file_name} at {event.create_time}")
```

#### 场景2：文件恢复
```python
# 从生命周期事件中恢复文件信息
deleted_event = await db.query(STRMLifeEvent).filter(
    STRMLifeEvent.type == 3,  # 删除事件
    STRMLifeEvent.file_id == file_id
).first()

if deleted_event:
    # 获取删除前的文件信息
    file_info = {
        "file_name": deleted_event.file_name,
        "file_size": deleted_event.file_size,
        "sha1": deleted_event.sha1,
        "pick_code": deleted_event.pick_code,
        "cloud_path": deleted_event.parent_id
    }
    # 可以根据这些信息恢复文件
```

#### 场景3：同步状态检查
```python
# 检查文件的同步状态
latest_event = await db.query(STRMLifeEvent).filter(
    STRMLifeEvent.file_id == file_id
).order_by(STRMLifeEvent.create_time.desc()).first()

if latest_event:
    if latest_event.type == 3:  # 已删除
        print("文件已删除，需要从网盘重新同步")
    elif latest_event.type == 2:  # 已更新
        print("文件已更新，需要更新本地STRM文件")
    elif latest_event.type == 1:  # 已创建
        print("文件已创建，同步正常")
```

#### 场景4：增量同步
```python
# 根据生命周期事件进行增量同步
# 只同步自上次同步后创建或更新的文件
last_sync_time = await get_last_sync_time()
new_events = await db.query(STRMLifeEvent).filter(
    STRMLifeEvent.create_time > last_sync_time,
    STRMLifeEvent.type.in_([1, 2])  # 创建或更新
).all()

for event in new_events:
    # 同步这些文件
    await sync_file(event.file_id)
```

## 🔧 实现方式

### 1. 记录创建事件

```python
async def record_create_event(
    db: AsyncSession,
    file_id: int,
    file_info: Dict[str, Any]
):
    """记录文件创建事件"""
    event = STRMLifeEvent(
        type=1,  # 创建
        file_id=file_id,
        parent_id=file_info.get("parent_id"),
        file_name=file_info.get("file_name"),
        file_category=file_info.get("file_category", 1),
        file_type=file_info.get("file_type", 4),  # 4:视频
        file_size=file_info.get("file_size"),
        sha1=file_info.get("sha1"),
        pick_code=file_info.get("pick_code"),
        update_time=file_info.get("update_time"),
        create_time=file_info.get("create_time")
    )
    db.add(event)
    await db.commit()
```

### 2. 记录更新事件

```python
async def record_update_event(
    db: AsyncSession,
    file_id: int,
    file_info: Dict[str, Any]
):
    """记录文件更新事件"""
    event = STRMLifeEvent(
        type=2,  # 更新
        file_id=file_id,
        parent_id=file_info.get("parent_id"),
        file_name=file_info.get("file_name"),
        file_category=file_info.get("file_category", 1),
        file_type=file_info.get("file_type", 4),
        file_size=file_info.get("file_size"),
        sha1=file_info.get("sha1"),
        pick_code=file_info.get("pick_code"),
        update_time=file_info.get("update_time"),
        create_time=int(datetime.now().timestamp())
    )
    db.add(event)
    await db.commit()
```

### 3. 记录删除事件

```python
async def record_delete_event(
    db: AsyncSession,
    file_id: int,
    file_info: Dict[str, Any]
):
    """记录文件删除事件"""
    event = STRMLifeEvent(
        type=3,  # 删除
        file_id=file_id,
        parent_id=file_info.get("parent_id"),
        file_name=file_info.get("file_name"),
        file_category=file_info.get("file_category", 1),
        file_type=file_info.get("file_type", 4),
        file_size=file_info.get("file_size"),
        sha1=file_info.get("sha1"),
        pick_code=file_info.get("pick_code"),
        update_time=file_info.get("update_time"),
        create_time=int(datetime.now().timestamp())
    )
    db.add(event)
    await db.commit()
```

## 📊 数据模型

### STRMLifeEvent 模型

```python
class STRMLifeEvent(Base):
    """STRM生命周期事件"""
    __tablename__ = 'strm_life_events'
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(Integer, nullable=False, index=True)  # 事件类型：1-创建，2-更新，3-删除
    file_id = Column(Integer, nullable=True, index=True)  # 文件ID
    parent_id = Column(Integer, nullable=True, index=True)  # 父目录ID
    file_name = Column(String(500), nullable=True)  # 文件名
    file_category = Column(Integer, nullable=False)  # 文件分类（0-文件夹，1-文件）
    file_type = Column(Integer, nullable=False, index=True)  # 文件类型（1-文档，2-图片，3-音乐，4-视频，5-压缩，6-应用，7-书籍）
    file_size = Column(BigInteger, nullable=True)  # 文件大小
    sha1 = Column(String(40), nullable=True)  # 文件SHA1
    pick_code = Column(String(50), nullable=True)  # 云存储pick_code
    update_time = Column(BigInteger, nullable=True)  # 更新时间
    create_time = Column(BigInteger, nullable=True)  # 创建时间
```

## 🔍 查询示例

### 查询文件生命周期

```python
# 查询特定文件的生命周期事件
async def get_file_lifecycle(db: AsyncSession, file_id: int):
    """获取文件的完整生命周期"""
    events = await db.query(STRMLifeEvent).filter(
        STRMLifeEvent.file_id == file_id
    ).order_by(STRMLifeEvent.create_time).all()
    
    return events
```

### 查询删除的文件

```python
# 查询所有已删除的文件
async def get_deleted_files(db: AsyncSession):
    """获取所有已删除的文件"""
    deleted_events = await db.query(STRMLifeEvent).filter(
        STRMLifeEvent.type == 3  # 删除事件
    ).all()
    
    return deleted_events
```

### 查询最近变更的文件

```python
# 查询最近变更的文件
async def get_recent_changes(db: AsyncSession, hours: int = 24):
    """获取最近N小时内变更的文件"""
    since_time = int((datetime.now() - timedelta(hours=hours)).timestamp())
    
    events = await db.query(STRMLifeEvent).filter(
        STRMLifeEvent.create_time > since_time
    ).order_by(STRMLifeEvent.create_time.desc()).all()
    
    return events
```

## ✅ 优势

1. **完整审计**：记录文件的完整生命周期，便于审计和调试
2. **数据恢复**：可以从生命周期事件中恢复文件信息
3. **增量同步**：可以根据生命周期事件进行增量同步
4. **状态检查**：可以检查文件的同步状态
5. **历史追踪**：可以追踪文件的变更历史

## 📝 总结

生命周期追踪是STRM系统的高级功能，用于记录文件的完整生命周期事件。虽然简化版STRM系统不包含此功能，但完整版STRM系统可以包含此功能，用于审计、调试和恢复。

